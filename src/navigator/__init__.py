import hashlib
import textwrap

import playwright.async_api
from playwright.async_api import Playwright, Browser, Page, BrowserContext, ElementHandle

import logging
import os
import sys
from pathlib import Path
from typing import Literal
from lxml.html import fromstring

from config_dict import ConfigDict

FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s %(lineno)d — %(message)s")


async def get_doc(cfg: ConfigDict, p: Playwright, url: str, page: str):
    path = await download_url(cfg, p, url, page)
    with open(path) as f:
        content = f.read()
    doc = fromstring(content)
    doc.make_links_absolute(cfg.base_url)
    return doc


def get_path(cfg: ConfigDict, url: str, txt: str) -> Path:
    txt = txt.replace(" ", '_').replace("/", '--')
    upath = hash_url_and_split(url)
    path = prefix_data_cached(cfg, upath, txt)
    return path


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_logger(logger_name, default_level="DEBUG"):
    _logger = logging.getLogger(logger_name)
    if 'LOG_LEVEL' in os.environ:
        _logger.setLevel(os.environ['LOG_LEVEL'])  # better to have too much log than not enough
    else:
        _logger.setLevel(default_level)  # better to have too much log than not enough

    if not _logger.hasHandlers():
        _logger.addHandler(get_console_handler())
    # with this pattern, it's rarely necessary to propagate the error up to parent
    _logger.propagate = False
    return _logger


class Navigator:

    def __init__(self, p: Playwright, headless=False):
        """ Must start inside playwright async context"""
        self.__lg = get_logger('navigator')
        self.__p = p
        self.__headless = headless
        self.__browser: Browser | None = None
        self.__current_page: Page | None = None
        self.__current_context: BrowserContext | None = None

    async def start(self, saved_session: Path | None = None, reset=False):
        """ Starts a browser"""
        if reset and self.__browser:
            self.__lg.debug("resetting browser")
            await self.__browser.close()
            self.__browser = None
        if not self.__browser:
            self.__lg.debug("launching browser")
            self.__browser = await self.__p.firefox.launch(headless=self.__headless)
        else:
            self.__lg.warning("A browser is already running, reusing, will start new context")
        if saved_session:
            self.__lg.debug(f"trying to load session file: {saved_session}")
            self.__current_context = await self.__browser.new_context(storage_state=saved_session)
        else:
            self.__lg.debug("using empty context")
            self.__current_context = await self.__browser.new_context()
        self.__current_page = await self.__current_context.new_page()

    def page(self):
        return self.__current_page

    async def wait_for(self, selector: str, state=Literal["attached", "detached", "hidden", "visible"] | None,
                       timeout=None) -> ElementHandle | None:
        """ Wait for an element to be available, timeout is ms"""
        try:
            return await self.__current_page.wait_for_selector(
                selector=selector,
                state=state,
                timeout=timeout
            )
        except playwright.async_api.Error:
            return None

    async def click(self, selector: str, timeout=None) -> bool:
        try:
            elm = await self.wait_for(selector, timeout=timeout)
            await elm.click()
            self.__lg.debug(f"Clicked: {selector}")
            return True
        except (playwright.async_api.Error, AttributeError):
            self.__lg.warning(f"Was not able to click: {selector}")
            return False

    async def goto(self, url: str):
        """ Load a webpage, If no page, start a new context and load page"""
        if not self.__current_page:
            self.__lg.debug("no context loaded, starting new")
            await self.start()
        await self.__current_page.goto(url)

    async def wait_for_state(self, timeout: float | None = None, state="load"):
        self.__lg.debug(f"Waiting for {state} for {timeout}")
        await self.__current_page.wait_for_load_state(state, timeout=timeout)
        self.__lg.debug(f"state reached")

    async def fill_input(self, selector: str, val: str) -> bool | None:
        try:
            elm: ElementHandle = await self.__current_page.wait_for_selector(selector)
            await elm.fill(val)
        except playwright.async_api.Error:
            return False

    async def store_session(self, path):
        await self.__current_context.storage_state(path=path)

    async def exit(self):
        if self.__browser:
            await self.__browser.close()


def hash_url_and_split(url, how_many=2) -> str:
    encoded = int(hashlib.sha256(url.encode('utf-8')).hexdigest(), 16) % 10 ** 8
    broken = textwrap.wrap(str(encoded), how_many)
    return "/".join(broken)


def prefix_data_cached(cfg: ConfigDict, path: str, prefix: str) -> Path:
    p = cfg.cache_dir / path
    p.mkdir(exist_ok=True, parents=True)
    file = p / f"{prefix}.html"
    return file


async def download_url(cfg, p, url, page) -> Path:
    path = get_path(cfg, url, page)
    if path.exists():
        return path
    nav = Navigator(p, headless=True)
    await nav.start()
    await nav.goto(url)
    page = nav.page()
    content = await page.inner_html('//html')
    with open(path, 'w', encoding="utf-8") as f:
        f.write(content)
    await nav.exit()
    return path
