import os
import sys
import random
import time
import subprocess
import platform
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Callable, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, get_system_chrome_path, get_default_user_data_dir


@dataclass
class BrowserConfig:
    headless: bool = False
    slow_mo: int = 100
    viewport: Dict[str, int] = None
    user_agent: str = None
    locale: str = "zh-CN"
    timeout: int = 30000
    
    browser_type: str = "chromium"
    executable_path: Optional[str] = None
    user_data_dir: Optional[str] = None
    
    use_cdp: bool = False
    cdp_endpoint: str = "http://localhost:9222"
    
    use_system_browser: bool = True
    launch_args: List[str] = field(default_factory=list)
    extra_headers: Dict[str, str] = field(default_factory=dict)


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
        self._browser_process = None
        self._connection_mode = None
    
    def initialize(self, browser_type: str = "chromium"):
        from playwright.sync_api import sync_playwright
        
        self._playwright = sync_playwright().start()
        
        if self.browser_config.use_cdp:
            return self._connect_via_cdp()
        
        if self.browser_config.executable_path or self.browser_config.use_system_browser:
            return self._launch_with_system_browser(browser_type)
        
        return self._launch_default_browser(browser_type)
    
    def _connect_via_cdp(self):
        self._connection_mode = "cdp"
        print(f"[Browser] 通过 CDP 连接到: {self.browser_config.cdp_endpoint}")
        
        try:
            self.browser = self._playwright.chromium.connect_over_cdp(
                self.browser_config.cdp_endpoint
            )
            
            self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
            
            if not self.context.pages:
                self.page = self.context.new_page()
            else:
                self.page = self.context.pages[0]
            
            if config.ANTI_DETECTION_ENABLED:
                self._apply_anti_detection()
            
            print("[Browser] CDP 连接成功!")
            return self.page
            
        except Exception as e:
            print(f"[Browser] CDP 连接失败: {e}")
            print("[Browser] 请确保浏览器已使用 --remote-debugging-port=9222 参数启动")
            raise
    
    def _launch_with_system_browser(self, browser_type: str):
        self._connection_mode = "system"
        
        executable_path = self.browser_config.executable_path
        
        if not executable_path and self.browser_config.use_system_browser:
            executable_path = get_system_chrome_path()
            if executable_path:
                print(f"[Browser] 检测到系统浏览器: {executable_path}")
            else:
                print("[Browser] 未检测到系统 Chrome/Edge，尝试使用 Playwright 内置浏览器")
                return self._launch_default_browser(browser_type)
        
        if not os.path.exists(executable_path):
            raise FileNotFoundError(f"浏览器可执行文件不存在: {executable_path}")
        
        print(f"[Browser] 使用系统浏览器: {executable_path}")
        
        browser_launcher = getattr(self._playwright, browser_type)
        
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-popup-blocking",
            "--disable-extensions-exclude",
            "--allow-running-insecure-content",
            "--disable-web-security",
        ]
        
        if self.browser_config.launch_args:
            args.extend(self.browser_config.launch_args)
        
        launch_args = {
            "executable_path": executable_path,
            "headless": self.browser_config.headless,
            "slow_mo": self.browser_config.slow_mo,
            "args": args,
        }
        
        if self.browser_config.user_data_dir:
            launch_args["args"].append(f"--user-data-dir={self.browser_config.user_data_dir}")
            print(f"[Browser] 使用用户数据目录: {self.browser_config.user_data_dir}")
        
        try:
            self.browser = browser_launcher.launch(**launch_args)
            
            context_args = {
                "viewport": self.browser_config.viewport or config.BROWSER_VIEWPORT,
                "locale": self.browser_config.locale,
                "user_agent": self.browser_config.user_agent or self._get_random_user_agent(),
            }
            
            if self.browser_config.extra_headers:
                context_args["extra_http_headers"] = self.browser_config.extra_headers
            
            self.context = self.browser.new_context(**context_args)
            
            if config.ANTI_DETECTION_ENABLED:
                self._apply_anti_detection()
            
            self.page = self.context.new_page()
            
            print("[Browser] 系统浏览器启动成功!")
            return self.page
            
        except Exception as e:
            print(f"[Browser] 系统浏览器启动失败: {e}")
            print("[Browser] 尝试使用 Playwright 内置浏览器...")
            return self._launch_default_browser(browser_type)
    
    def _launch_default_browser(self, browser_type: str):
        self._connection_mode = "default"
        print("[Browser] 使用 Playwright 内置浏览器")
        
        browser_launcher = getattr(self._playwright, browser_type)
        
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]
        
        if self.browser_config.launch_args:
            args.extend(self.browser_config.launch_args)
        
        launch_args = {
            "headless": self.browser_config.headless,
            "slow_mo": self.browser_config.slow_mo,
            "args": args,
        }
        
        try:
            self.browser = browser_launcher.launch(**launch_args)
            
            context_args = {
                "viewport": self.browser_config.viewport or config.BROWSER_VIEWPORT,
                "locale": self.browser_config.locale,
                "user_agent": self.browser_config.user_agent or self._get_random_user_agent(),
            }
            
            if self.browser_config.extra_headers:
                context_args["extra_http_headers"] = self.browser_config.extra_headers
            
            self.context = self.browser.new_context(**context_args)
            
            if config.ANTI_DETECTION_ENABLED:
                self._apply_anti_detection()
            
            self.page = self.context.new_page()
            
            print("[Browser] Playwright 浏览器启动成功!")
            return self.page
            
        except Exception as e:
            print(f"[Browser] Playwright 浏览器启动失败: {e}")
            print("")
            print("=" * 60)
            print("解决办法:")
            print("=" * 60)
            print("")
            print("方法 1: 使用国内镜像安装 Playwright 浏览器")
            print("  Windows (CMD):")
            print("    set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright")
            print("    playwright install chromium")
            print("")
            print("  Windows (PowerShell):")
            print("    $env:PLAYWRIGHT_DOWNLOAD_HOST='https://npmmirror.com/mirrors/playwright'")
            print("    playwright install chromium")
            print("")
            print("  Linux/macOS:")
            print("    PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright playwright install chromium")
            print("")
            print("方法 2: 使用系统已安装的 Chrome/Edge 浏览器 (推荐)")
            print("  脚本会自动检测系统中的 Chrome/Edge，无需额外安装")
            print("")
            print("方法 3: 使用 CDP 连接已运行的浏览器")
            print("  1. 先启动 Chrome 并开启调试端口:")
            print("     chrome.exe --remote-debugging-port=9222")
            print("  2. 然后运行脚本时使用 --cdp 参数")
            print("")
            print("=" * 60)
            raise
    
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
