import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_command(args: list[str]) -> None:
    cmd = [sys.executable, "crawler_yuanliaoyao.py"] + args
    subprocess.run(cmd, cwd=BASE_DIR, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="原料药定期更新爬虫")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="默认仅抓取前 5 页，可按需调整。",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="日志级别，默认 INFO。",
    )
    args = parser.parse_args()

    extra_args: list[str] = ["--log-level", args.log_level]
    if args.max_pages:
        extra_args += ["--max-pages", str(args.max_pages)]

    run_command(extra_args)


if __name__ == "__main__":
    main()
