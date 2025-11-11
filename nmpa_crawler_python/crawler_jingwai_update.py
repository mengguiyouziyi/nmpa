import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_command(args: list[str]) -> None:
    cmd = [sys.executable, "crawler_jingwai.py"] + args
    subprocess.run(cmd, cwd=BASE_DIR, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="境外药品定期更新爬虫")
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="可选，指定基础检索词（默认包含国药准字H、国药准字S）。",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="日志级别，默认 INFO。",
    )
    args = parser.parse_args()

    extra_args: list[str] = ["--log-level", args.log_level]
    if args.queries:
        for query in args.queries:
            extra_args += ["--query", query]

    run_command(extra_args)


if __name__ == "__main__":
    main()
