"""스케줄러 서비스"""

import asyncio
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import PROJECT_ROOT, TIMEZONE

# 스케줄러 인스턴스
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

# 내부 API 라우터 (localhost에서만 접근 가능)
router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class JobCreate(BaseModel):
    """작업 생성 요청"""
    id: str
    cron: str  # "0 8 * * *" 형식
    command: str  # "/daily-summary" 형식


class JobResponse(BaseModel):
    """작업 응답"""
    id: str
    cron: str
    command: str
    next_run: Optional[str] = None


async def run_opencode(command: str) -> bool:
    """OpenCode 명령 실행"""
    print(f"\n>>> [Scheduler] OpenCode 실행: {command}")

    try:
        process = await asyncio.create_subprocess_exec(
            "opencode", "run", command,
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=600.0  # 10분 타임아웃
        )

        if process.returncode == 0:
            print(f">>> [Scheduler] OpenCode 완료: {command}")
            return True
        else:
            print(f">>> [Scheduler] OpenCode 에러: {stderr.decode()}")
            return False

    except asyncio.TimeoutError:
        print(f">>> [Scheduler] OpenCode 타임아웃: {command}")
        return False
    except Exception as e:
        print(f">>> [Scheduler] OpenCode 실행 실패: {e}")
        return False


def create_job_func(command: str):
    """스케줄 작업 함수 생성"""
    async def job_func():
        await run_opencode(command)
    return job_func


# ===== 기본 스케줄 작업 =====

async def daily_summary_job():
    """매일 08:00 - 일일 요약"""
    await run_opencode("/daily-summary")


def register_default_jobs():
    """기본 작업 등록"""
    scheduler.add_job(
        daily_summary_job,
        CronTrigger(hour=8, minute=0, timezone=TIMEZONE),
        id="daily-summary",
        replace_existing=True,
    )
    print("[Scheduler] 기본 작업 등록 완료: daily-summary (08:00)")


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
        })
    return jobs


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

        scheduler.add_job(
            create_job_func(job.command),
            trigger,
            id=job.id,
            replace_existing=True,
        )

        print(f"[Scheduler] 작업 추가: {job.id} ({job.cron}) -> {job.command}")
        return {"status": "ok", "id": job.id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/jobs/{job_id}")
async def remove_job(job_id: str) -> dict:
    """작업 삭제"""
    try:
        scheduler.remove_job(job_id)
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

    # 즉시 실행
    job.modify(next_run_time=None)
    scheduler.wakeup()

    print(f"[Scheduler] 작업 수동 실행: {job_id}")
    return {"status": "triggered", "id": job_id}


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
