import argparse
import logging
import random
import sys
import time
from pathlib import Path
from typing import Iterable, List, Sequence

from DrissionPage import ChromiumOptions, ChromiumPage
from DrissionPage.errors import BrowserConnectError, ElementNotFoundError

LOGGER = logging.getLogger("nmpa.drission")

PROFILE_DIR = Path(__file__).resolve().parent / "chrome_profile"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def random_sleep(low: float, high: float) -> None:
    time.sleep(random.uniform(low, high))


class DrissionActor:
    SEARCH_URL = "https://www.nmpa.gov.cn/datasearch/search-result.html"
    DEFAULT_KEYWORDS: Sequence[str] = ("国药准字H", "国药准字S", "国药准字Z")

    def __init__(self, *, keywords: Iterable[str], interval: int, headless: bool) -> None:
        self.keywords = list(keywords) or list(self.DEFAULT_KEYWORDS)
        self.interval = interval
        self.headless = headless
        self.page: ChromiumPage | None = None

    def _ensure_page(self) -> ChromiumPage:
        if self.page is not None:
            return self.page
        LOGGER.info("初始化 DrissionPage 有头浏览器 ...")
        opts = ChromiumOptions()
        opts.set_argument("--start-maximized")
        opts.set_argument("--lang=zh-CN,zh")
        opts.set_argument("--disable-blink-features=AutomationControlled")
        opts.set_argument("--no-sandbox")
        opts.set_argument("--disable-dev-shm-usage")
        opts.set_argument("--disable-gpu")
        opts.set_argument(f"--user-data-dir={PROFILE_DIR}")
        opts.set_argument("--remote-debugging-port=0")
        if self.headless:
            opts.set_argument("--headless=new")
        try:
            opts.set_pref("intl.accept_languages", "zh-CN,zh")
        except AttributeError:
            pass
        try:
            page = ChromiumPage(addr_or_opts=opts)
        except BrowserConnectError as exc:
            LOGGER.error("浏览器连接失败：%s", exc)
            raise
        try:
            page.run_cdp(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
            )
        except Exception:
            pass
        self.page = page
        return page

    def _warmup(self, page: ChromiumPage) -> None:
        page.get("https://www.nmpa.gov.cn/")
        random_sleep(1.5, 2.5)
        page.get(self.SEARCH_URL)
        random_sleep(2, 3)

    def _candidate_contexts(self, page: ChromiumPage) -> List[ChromiumPage]:
        contexts: List[ChromiumPage] = [page]
        try:
            iframe_elements = page.eles("xpath://iframe", timeout=1)
        except ElementNotFoundError:
            iframe_elements = []
        for iframe in iframe_elements:
            try:
                frame_page = iframe.to_frame(timeout=2)
            except Exception:
                continue
            contexts.append(frame_page)
        return contexts

    def _type_keyword(self, page: ChromiumPage, keyword: str) -> None:
        selectors = [
            "css:input[placeholder*='关键字']",
            "css:input[name='keyword']",
            "css:.search-input input",
        ]
        input_box = None
        for context in self._candidate_contexts(page):
            for selector in selectors:
                try:
                    input_box = context.ele(selector, timeout=4)
                    if input_box:
                        break
                except ElementNotFoundError:
                    continue
            if input_box:
                break
        if input_box:
            input_box.clear()
            random_sleep(0.4, 0.8)
            input_box.input(keyword)
            random_sleep(0.4, 0.8)
            input_box.input("\n")
        else:
            LOGGER.warning("未找到搜索输入框，尝试使用 URL 参数搜索：%s", keyword)
            page.get(f"{self.SEARCH_URL}?keyword={keyword}")
        random_sleep(3, 5)

    def _click_detail(self, page: ChromiumPage) -> bool:
        selectors = [
            "css:.result-item a",
            "css:table tbody tr td a",
            "xpath://a[contains(text(),'详情')]",
        ]
        for context in self._candidate_contexts(page):
            for selector in selectors:
                try:
                    ele = context.ele(selector, timeout=4)
                except ElementNotFoundError:
                    ele = None
                if not ele:
                    continue
                ele.scroll.to_see()
                random_sleep(0.8, 1.4)
                ele.click()
                random_sleep(2, 3)
                new_tab = page.wait_tab(timeout=3)
                if new_tab:
                    new_tab.set_active()
                    random_sleep(2, 3)
                    new_tab.close()
                    page.set_active()
                else:
                    page.back()
                return True
        LOGGER.info("未找到详情链接。")
        return False

    def _click_next_page(self, page: ChromiumPage) -> bool:
        selectors = [
            "css:.el-pagination button.btn-next",
            "xpath://button[contains(@class,'btn-next')]",
            "xpath://a[contains(text(),'下一页')]",
            "xpath://*[@id='home']/div[3]/div[3]/div/div/button[2]",
        ]
        for context in self._candidate_contexts(page):
            for selector in selectors:
                try:
                    btn = context.ele(selector, timeout=4)
                except ElementNotFoundError:
                    btn = None
                if not btn:
                    continue
                btn.scroll.to_see()
                random_sleep(0.6, 1.2)
                btn.click()
                random_sleep(2, 3)
                return True
        LOGGER.info("未找到下一页按钮。")
        return False

    def perform_cycle(self) -> None:
        page = self._ensure_page()
        if page.url != self.SEARCH_URL:
            self._warmup(page)
        keyword = random.choice(self.keywords)
        LOGGER.info("模拟关键词：%s", keyword)
        self._type_keyword(page, keyword)
        random_sleep(2, 4)
        if self._click_next_page(page):
            LOGGER.info("翻页完成。")
        step_ratio = random.uniform(0.3, 0.9)
        try:
            page.scroll.to_bottom(step=step_ratio)
        except TypeError:
            page.scroll.to_bottom()
        random_sleep(1, 2)

    def run(self, *, once: bool, log_cycle: bool = True) -> None:
        cycle = 0
        try:
            while True:
                cycle += 1
                start = time.time()
                if log_cycle:
                    LOGGER.info("===== 自动化循环 #%d 开始 =====", cycle)
                try:
                    self.perform_cycle()
                except Exception as exc:  # noqa: BLE001
                    LOGGER.exception("自动化循环异常：%s", exc)
                if once:
                    break
                elapsed = time.time() - start
                wait_seconds = max(0.0, self.interval - elapsed)
                if log_cycle:
                    LOGGER.info("循环 #%d 完成，等待 %.1f 秒进入下一轮。", cycle, wait_seconds)
                time.sleep(wait_seconds)
        finally:
            if self.page:
                LOGGER.info("关闭浏览器。")
                self.page.quit()


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NMPA 页面 DrissionPage 模拟器")
    parser.add_argument(
        "--keyword",
        action="append",
        dest="keywords",
        help="添加一个搜索关键字，可多次使用；默认国药准字H/S/Z。",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1800,
        help="两轮之间的目标间隔（秒），默认 1800（30 分钟）。",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="仅执行一轮模拟后退出。",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="可选，将日志写入文件。",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="以 headless=new 模式运行（无界面）。",
    )
    return parser.parse_args(argv)


def configure_logging(log_file: str | None) -> None:
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    configure_logging(args.log_file)
    actor = DrissionActor(
        keywords=args.keywords or DrissionActor.DEFAULT_KEYWORDS,
        interval=args.interval,
        headless=args.headless,
    )
    LOGGER.info(
        "启动 DrissionPage 模拟器，间隔=%d 秒，关键词=%s，模式=%s",
        args.interval,
        ", ".join(actor.keywords),
        "单次" if args.once else "循环",
    )
    actor.run(once=args.once)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
