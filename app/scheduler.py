"""스케줄러 서비스"""

import asyncio
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import PROJECT_ROOT, TIMEZONE

# 스케줄러 인스턴스
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

# 작업별 content 저장소 (APScheduler는 kwargs 검증이 엄격해서 별도 저장)
_job_content: dict[str, str] = {}

# 내부 API 라우터 (localhost에서만 접근 가능)
router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class JobCreate(BaseModel):
    """반복 작업 생성 요청"""
    id: str
    cron: str  # "0 8 * * *" 형식
    content: str  # OpenCode에 전달할 프롬프트


class OneTimeJobCreate(BaseModel):
    """일회성 작업 생성 요청"""
    id: str
    run_at: str  # "2024-01-15 15:30" 또는 "15:30" (오늘)
    content: str  # OpenCode에 전달할 프롬프트


class JobResponse(BaseModel):
    """작업 응답"""
    id: str
    cron: str
    content: str
    next_run: Optional[str] = None


async def run_scheduled_task(content: str) -> bool:
    """스케줄 작업 실행 - content를 OpenCode에 전달"""
    # 스케줄러에 의한 요청임을 명시
    prompt = f"[스케줄러에 의한 자동 실행]\n\n{content}"

    print(f"\n>>> [Scheduler] OpenCode 실행")
    print(f">>> Content: {content[:100]}...")

    try:
        process = await asyncio.create_subprocess_exec(
            "opencode", "run", prompt,
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=600.0  # 10분 타임아웃
        )

        if process.returncode == 0:
            print(f">>> [Scheduler] OpenCode 완료")
            return True
        else:
            print(f">>> [Scheduler] OpenCode 에러: {stderr.decode()}")
            return False

    except asyncio.TimeoutError:
        print(f">>> [Scheduler] OpenCode 타임아웃")
        return False
    except Exception as e:
        print(f">>> [Scheduler] OpenCode 실행 실패: {e}")
        return False


def create_job_func(content: str):
    """스케줄 작업 함수 생성"""
    async def job_func():
        await run_scheduled_task(content)
    return job_func


# ===== 기본 스케줄 작업 =====

DEFAULT_JOBS = [
    {
        "id": "daily-summary",
        "cron": "0 8 * * *",
        "content": "/daily-summary 스킬을 실행해서 24시간 텔레그램 메시지를 수집하고 요약해줘",
    }
]


def register_default_jobs():
    """기본 작업 등록"""
    for job in DEFAULT_JOBS:
        parts = job["cron"].split()
        minute, hour, day, month, day_of_week = parts

        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone=TIMEZONE,
        )

        # content를 별도 저장소에 저장
        _job_content[job["id"]] = job["content"]

        scheduler.add_job(
            create_job_func(job["content"]),
            trigger,
            id=job["id"],
            replace_existing=True,
        )
        print(f"[Scheduler] 기본 작업 등록: {job['id']} ({job['cron']})")


# ===== 내부 API 엔드포인트 =====

@router.get("/jobs")
async def list_jobs() -> list[dict]:
    """등록된 작업 목록"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
            "content": _job_content.get(job.id, ""),
        })
    return jobs


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    """단일 작업 조회"""
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"작업을 찾을 수 없음: {job_id}")

    return {
        "id": job.id,
        "next_run": str(job.next_run_time) if job.next_run_time else None,
        "trigger": str(job.trigger),
        "content": _job_content.get(job_id, ""),
    }


@router.post("/jobs")
async def add_job(job: JobCreate) -> dict:
    """작업 추가"""
    try:
        # cron 문자열 파싱 (분 시 일 월 요일)
        parts = job.cron.split()
        if len(parts) != 5:
            raise ValueError("cron 형식: '분 시 일 월 요일' (예: '0 8 * * *')")

        minute, hour, day, month, day_of_week = parts

        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone=TIMEZONE,
        )

        # content를 별도 저장소에 저장
        _job_content[job.id] = job.content

        scheduler.add_job(
            create_job_func(job.content),
            trigger,
            id=job.id,
            replace_existing=True,
        )

        print(f"[Scheduler] 작업 추가: {job.id} ({job.cron})")
        print(f"[Scheduler] Content: {job.content[:100]}...")
        return {"status": "ok", "id": job.id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/once")
async def add_one_time_job(job: OneTimeJobCreate) -> dict:
    """일회성 작업 추가"""
    try:
        # run_at 파싱
        run_at = parse_run_at(job.run_at)

        # 과거 시간 체크
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(str(TIMEZONE)))
        if run_at <= now:
            raise ValueError(f"실행 시간이 과거입니다: {run_at}")

        trigger = DateTrigger(run_date=run_at, timezone=TIMEZONE)

        # content 저장
        _job_content[job.id] = job.content

        # 일회성 작업은 실행 후 자동 삭제됨
        # content 저장소도 정리하기 위해 래퍼 함수 사용
        def create_one_time_job_func(job_id: str, content: str):
            async def job_func():
                await run_scheduled_task(content)
                # 실행 후 content 저장소에서 삭제
                _job_content.pop(job_id, None)
            return job_func

        scheduler.add_job(
            create_one_time_job_func(job.id, job.content),
            trigger,
            id=job.id,
            replace_existing=True,
        )

        print(f"[Scheduler] 일회성 작업 추가: {job.id} ({run_at})")
        print(f"[Scheduler] Content: {job.content[:100]}...")
        return {"status": "ok", "id": job.id, "run_at": str(run_at)}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def parse_run_at(run_at: str) -> datetime:
    """run_at 문자열을 datetime으로 변환

    지원 형식:
    - "2024-01-15 15:30" - 특정 날짜/시간
    - "15:30" - 오늘 해당 시간
    - "15:30:00" - 오늘 해당 시간 (초 포함)
    """
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(str(TIMEZONE))
    now = datetime.now(tz)

    # 시간만 있는 경우 (HH:MM 또는 HH:MM:SS)
    if ":" in run_at and "-" not in run_at:
        parts = run_at.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) > 2 else 0
        return now.replace(hour=hour, minute=minute, second=second, microsecond=0)

    # 날짜+시간 형식
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
        try:
            dt = datetime.strptime(run_at, fmt)
            return dt.replace(tzinfo=tz)
        except ValueError:
            continue

    raise ValueError(f"지원하지 않는 시간 형식: {run_at} (예: '15:30' 또는 '2024-01-15 15:30')")


@router.delete("/jobs/{job_id}")
async def remove_job(job_id: str) -> dict:
    """작업 삭제"""
    try:
        scheduler.remove_job(job_id)
        _job_content.pop(job_id, None)  # content 저장소에서도 삭제
        print(f"[Scheduler] 작업 삭제: {job_id}")
        return {"status": "ok", "id": job_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"작업을 찾을 수 없음: {job_id}")


@router.post("/trigger/{job_id}")
async def trigger_job(job_id: str) -> dict:
    """작업 수동 실행"""
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"작업을 찾을 수 없음: {job_id}")

    # content 추출하여 즉시 실행
    content = _job_content.get(job_id, "")
    if content:
        asyncio.create_task(run_scheduled_task(content))
        print(f"[Scheduler] 작업 수동 실행: {job_id}")
        return {"status": "triggered", "id": job_id}
    else:
        raise HTTPException(status_code=400, detail="작업에 content가 없음")


# ===== 스케줄러 제어 =====

def start():
    """스케줄러 시작"""
    register_default_jobs()
    scheduler.start()
    print("[Scheduler] 스케줄러 시작됨")


def shutdown():
    """스케줄러 종료"""
    scheduler.shutdown()
    print("[Scheduler] 스케줄러 종료됨")
