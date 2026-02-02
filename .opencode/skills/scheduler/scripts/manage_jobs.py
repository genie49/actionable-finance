#!/usr/bin/env python3
"""스케줄러 작업 관리 스크립트"""

import argparse
import json
import sys

try:
    import httpx
except ImportError:
    print("Error: pip install httpx")
    sys.exit(1)

BASE_URL = "http://localhost:8000/scheduler"


def list_jobs():
    """작업 목록 조회"""
    response = httpx.get(f"{BASE_URL}/jobs")
    jobs = response.json()

    if not jobs:
        print("등록된 작업이 없습니다.")
        return

    print(f"\n{'ID':<20} {'다음 실행':<25} {'Content'}")
    print("-" * 80)
    for job in jobs:
        content = job.get('content', '')
        content_preview = content[:40] + "..." if len(content) > 40 else content
        print(f"{job['id']:<20} {job.get('next_run', 'N/A'):<25} {content_preview}")
    print()


def get_job(job_id: str):
    """단일 작업 조회"""
    response = httpx.get(f"{BASE_URL}/jobs/{job_id}")

    if response.status_code == 200:
        job = response.json()
        print(f"\nID: {job['id']}")
        print(f"다음 실행: {job.get('next_run', 'N/A')}")
        print(f"트리거: {job.get('trigger', 'N/A')}")
        print(f"Content:\n{job.get('content', '')}")
        print()
    else:
        result = response.json()
        print(f"오류: {result.get('detail', result)}")


def add_job(job_id: str, cron: str, content: str):
    """작업 추가"""
    payload = {
        "id": job_id,
        "cron": cron,
        "content": content,
    }
    response = httpx.post(f"{BASE_URL}/jobs", json=payload)
    result = response.json()

    if response.status_code == 200:
        print(f"작업 추가됨: {job_id}")
        print(f"Cron: {cron}")
        print(f"Content: {content[:50]}...")
    else:
        print(f"오류: {result.get('detail', result)}")


def remove_job(job_id: str):
    """작업 삭제"""
    response = httpx.delete(f"{BASE_URL}/jobs/{job_id}")

    if response.status_code == 200:
        print(f"작업 삭제됨: {job_id}")
    else:
        result = response.json()
        print(f"오류: {result.get('detail', result)}")


def trigger_job(job_id: str):
    """작업 수동 실행"""
    response = httpx.post(f"{BASE_URL}/trigger/{job_id}")

    if response.status_code == 200:
        print(f"작업 실행됨: {job_id}")
    else:
        result = response.json()
        print(f"오류: {result.get('detail', result)}")


def add_once_job(job_id: str, run_at: str, content: str):
    """일회성 작업 추가"""
    payload = {
        "id": job_id,
        "run_at": run_at,
        "content": content,
    }
    response = httpx.post(f"{BASE_URL}/jobs/once", json=payload)
    result = response.json()

    if response.status_code == 200:
        print(f"일회성 작업 추가됨: {job_id}")
        print(f"실행 시간: {result.get('run_at', run_at)}")
        print(f"Content: {content[:50]}...")
    else:
        print(f"오류: {result.get('detail', result)}")


def main():
    parser = argparse.ArgumentParser(description="스케줄러 작업 관리")
    subparsers = parser.add_subparsers(dest="command", help="명령")

    # list
    subparsers.add_parser("list", help="작업 목록 조회")

    # get
    get_parser = subparsers.add_parser("get", help="단일 작업 조회")
    get_parser.add_argument("job_id", help="작업 ID")

    # add (반복)
    add_parser = subparsers.add_parser("add", help="반복 작업 추가")
    add_parser.add_argument("--id", required=True, help="작업 ID")
    add_parser.add_argument("--cron", required=True, help="cron 표현식 (예: '0 8 * * *')")
    add_parser.add_argument("--content", required=True, help="OpenCode에 전달할 프롬프트")

    # once (일회성)
    once_parser = subparsers.add_parser("once", help="일회성 작업 추가")
    once_parser.add_argument("--id", required=True, help="작업 ID")
    once_parser.add_argument("--run-at", required=True, help="실행 시간 (예: '15:30' 또는 '2024-01-15 15:30')")
    once_parser.add_argument("--content", required=True, help="OpenCode에 전달할 프롬프트")

    # remove
    remove_parser = subparsers.add_parser("remove", help="작업 삭제")
    remove_parser.add_argument("job_id", help="작업 ID")

    # trigger
    trigger_parser = subparsers.add_parser("trigger", help="작업 수동 실행")
    trigger_parser.add_argument("job_id", help="작업 ID")

    args = parser.parse_args()

    if args.command == "list":
        list_jobs()
    elif args.command == "get":
        get_job(args.job_id)
    elif args.command == "add":
        add_job(args.id, args.cron, args.content)
    elif args.command == "once":
        add_once_job(args.id, args.run_at, args.content)
    elif args.command == "remove":
        remove_job(args.job_id)
    elif args.command == "trigger":
        trigger_job(args.job_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
