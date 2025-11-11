import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_command(script: str, args: list[str]) -> None:
    cmd = [sys.executable, script] + args
    subprocess.run(cmd, cwd=BASE_DIR, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="境内药品定期更新爬虫")
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="可选，限制基础检索词；默认抓取国药准字H 与 国药准字S。",
    )
    parser.add_argument(
        "--max-segments",
        type=int,
        default=20,
        help="每次更新最多处理的分段数量，默认 20。",
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
    if args.max_segments:
        extra_args += ["--max-segments", str(args.max_segments)]

    run_command("crawler.py", extra_args)


if __name__ == "__main__":
    main()
