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

    print(f"\n{'ID':<20} {'다음 실행':<25} {'트리거'}")
    print("-" * 70)
    for job in jobs:
        print(f"{job['id']:<20} {job.get('next_run', 'N/A'):<25} {job.get('trigger', '')}")
    print()


def add_job(job_id: str, cron: str, command: str):
    """작업 추가"""
    payload = {
        "id": job_id,
        "cron": cron,
        "command": command,
    }
    response = httpx.post(f"{BASE_URL}/jobs", json=payload)
    result = response.json()

    if response.status_code == 200:
        print(f"작업 추가됨: {job_id}")
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


def main():
    parser = argparse.ArgumentParser(description="스케줄러 작업 관리")
    subparsers = parser.add_subparsers(dest="command", help="명령")

    # list
    subparsers.add_parser("list", help="작업 목록 조회")

    # add
    add_parser = subparsers.add_parser("add", help="작업 추가")
    add_parser.add_argument("--id", required=True, help="작업 ID")
    add_parser.add_argument("--cron", required=True, help="cron 표현식 (예: '0 8 * * *')")
    add_parser.add_argument("--command", required=True, help="실행 명령 (예: /daily-summary)")

    # remove
    remove_parser = subparsers.add_parser("remove", help="작업 삭제")
    remove_parser.add_argument("job_id", help="작업 ID")

    # trigger
    trigger_parser = subparsers.add_parser("trigger", help="작업 수동 실행")
    trigger_parser.add_argument("job_id", help="작업 ID")

    args = parser.parse_args()

    if args.command == "list":
        list_jobs()
    elif args.command == "add":
        add_job(args.id, args.cron, args.command)
    elif args.command == "remove":
        remove_job(args.job_id)
    elif args.command == "trigger":
        trigger_job(args.job_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
