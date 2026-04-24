import os
import sys
import random
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config


@dataclass
class BrowserConfig:
    headless: bool = False
    slow_mo: int = 100
    viewport: Dict[str, int] = None
    user_agent: str = None
    locale: str = "zh-CN"
    timeout: int = 30000


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


class BrowserManager:
    def __init__(self, browser_config: Optional[BrowserConfig] = None):
        self.browser_config = browser_config or BrowserConfig()
        self.browser = None
        self.context = None
        self.page = None
        self._playwright = None
    
    def initialize(self, browser_type: str = "chromium"):
        from playwright.sync_api import sync_playwright
        
        self._playwright = sync_playwright().start()
        
        browser_launcher = getattr(self._playwright, browser_type)
        
        launch_args = {
            "headless": self.browser_config.headless,
            "slow_mo": self.browser_config.slow_mo,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        }
        
        self.browser = browser_launcher.launch(**launch_args)
        
        context_args = {
            "viewport": self.browser_config.viewport or config.BROWSER_VIEWPORT,
            "locale": self.browser_config.locale,
            "user_agent": self.browser_config.user_agent or self._get_random_user_agent(),
        }
        
        self.context = self.browser.new_context(**context_args)
        
        if config.ANTI_DETECTION_ENABLED:
            self._apply_anti_detection()
        
        self.page = self.context.new_page()
        
        return self.page
    
    def _get_random_user_agent(self) -> str:
        if config.RANDOM_USER_AGENT:
            return random.choice(USER_AGENTS)
        return USER_AGENTS[0]
    
    def _apply_anti_detection(self):
        if self.context is None:
            return
        
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            
            window.chrome = {
                runtime: {}
            };
            
            Object.defineProperty(Notification, 'permission', {
                get: () => 'granted'
            });
        """)
    
    def navigate(self, url: str, wait_until: str = "domcontentloaded"):
        if self.page is None:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        
        self.page.goto(url, wait_until=wait_until, timeout=config.PAGE_LOAD_TIMEOUT)
    
    def wait_for_selector(self, selector: str, timeout: int = None, state: str = "visible"):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        timeout = timeout or config.ELEMENT_WAIT_TIMEOUT
        return self.page.wait_for_selector(selector, timeout=timeout, state=state)
    
    def click(self, selector: str, delay: float = None):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        if delay is None:
            delay = random.uniform(config.CLICK_DELAY_MIN, config.CLICK_DELAY_MAX)
        
        time.sleep(delay)
        self.page.click(selector)
    
    def fill(self, selector: str, value: str, delay: float = None):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        element = self.wait_for_selector(selector)
        
        if element:
            element.click()
            element.fill('')
            
            if delay is None:
                char_delay = random.uniform(config.INPUT_DELAY_MIN, config.INPUT_DELAY_MAX)
            else:
                char_delay = delay
            
            for char in value:
                element.type(char, delay=char_delay * 1000)
                time.sleep(char_delay * 0.5)
    
    def type_text(self, selector: str, text: str, delay: float = None):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        if delay is None:
            delay = random.uniform(config.INPUT_DELAY_MIN, config.INPUT_DELAY_MAX)
        
        self.page.type(selector, text, delay=delay * 1000)
    
    def select_option(self, selector: str, value: str = None, label: str = None):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        if value:
            self.page.select_option(selector, value=value)
        elif label:
            self.page.select_option(selector, label=label)
    
    def get_element_text(self, selector: str) -> Optional[str]:
        if self.page is None:
            return None
        
        element = self.page.query_selector(selector)
        if element:
            return element.text_content()
        return None
    
    def get_element_attribute(self, selector: str, attribute: str) -> Optional[str]:
        if self.page is None:
            return None
        
        element = self.page.query_selector(selector)
        if element:
            return element.get_attribute(attribute)
        return None
    
    def is_element_visible(self, selector: str) -> bool:
        if self.page is None:
            return False
        
        element = self.page.query_selector(selector)
        if element:
            return element.is_visible()
        return False
    
    def get_all_frames(self):
        if self.page is None:
            return []
        
        frames = []
        for frame in self.page.frames:
            frames.append(frame)
        
        return frames
    
    def get_frame_by_url(self, url_pattern: str):
        if self.page is None:
            return None
        
        for frame in self.page.frames:
            if url_pattern in frame.url:
                return frame
        return None
    
    def get_frame_by_name(self, name: str):
        if self.page is None:
            return None
        
        for frame in self.page.frames:
            if frame.name == name:
                return frame
        return None
    
    def scroll_to_element(self, selector: str):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        element = self.page.query_selector(selector)
        if element:
            element.scroll_into_view_if_needed()
    
    def scroll_by(self, x: int, y: int):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        self.page.evaluate(f"window.scrollBy({x}, {y})")
    
    def wait_for_page_load(self, timeout: int = None):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        timeout = timeout or config.PAGE_LOAD_TIMEOUT
        self.page.wait_for_load_state("networkidle", timeout=timeout)
    
    def wait_for_selector_disappear(self, selector: str, timeout: int = None):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        timeout = timeout or config.ELEMENT_WAIT_TIMEOUT
        self.page.wait_for_selector(selector, timeout=timeout, state="hidden")
    
    def take_screenshot(self, path: str = None, full_page: bool = True):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        if path is None:
            timestamp = int(time.time())
            path = f"screenshot_{timestamp}.png"
        
        self.page.screenshot(path=path, full_page=full_page)
        return path
    
    def execute_script(self, script: str, *args):
        if self.page is None:
            raise RuntimeError("Browser not initialized.")
        
        return self.page.evaluate(script, *args)
    
    def close(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
        
        self.page = None
        self.context = None
        self.browser = None
        self._playwright = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    @contextmanager
    def new_page(self):
        if self.context is None:
            raise RuntimeError("Browser not initialized.")
        
        page = self.context.new_page()
        try:
            yield page
        finally:
            page.close()
