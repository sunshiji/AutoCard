import os
import sys
import random
import time
import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from models import FormValidationError


@dataclass
class AntiDetectionConfig:
    random_user_agent: bool = True
    random_viewport: bool = False
    simulate_mouse_movement: bool = True
    random_input_delay: bool = True
    random_scroll: bool = True
    disable_webdriver_flag: bool = True
    add_plugins: bool = True
    add_languages: bool = True
    add_chrome_runtime: bool = True


class AntiDetection:
    def __init__(self, page, config: AntiDetectionConfig = None):
        self.page = page
        self.config = config or AntiDetectionConfig()
        self._last_action_time = time.time()
    
    def apply_all_measures(self):
        if self.config.disable_webdriver_flag:
            self._disable_webdriver_flag()
        
        if self.config.add_plugins:
            self._add_plugins()
        
        if self.config.add_languages:
            self._add_languages()
        
        if self.config.add_chrome_runtime:
            self._add_chrome_runtime()
        
        self._add_permissions_api()
        self._add_outer_dimensions()
        self._fix_console_debug()
    
    def _disable_webdriver_flag(self):
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_;
            delete window.cdc_asdjflasutopfhvcZLmcfl_;
        """)
    
    def _add_plugins(self):
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        {
                            0: { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                            name: 'Chrome PDF Plugin',
                            filename: 'internal-pdf-viewer',
                            description: 'Portable Document Format'
                        },
                        {
                            0: { type: 'application/pdf', suffixes: 'pdf', description: '' },
                            name: 'Chrome PDF Viewer',
                            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                            description: ''
                        },
                        {
                            0: { type: 'application/x-nacl', suffixes: '', description: 'Native Client Executable' },
                            1: { type: 'application/x-pnacl', suffixes: '', description: 'Portable Native Client Executable' },
                            name: 'Native Client',
                            filename: 'internal-nacl-plugin',
                            description: ''
                        }
                    ];
                    return plugins;
                }
            });
            
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => {
                    const mimeTypes = {
                        'application/pdf': {
                            type: 'application/pdf',
                            suffixes: 'pdf',
                            description: '',
                            enabledPlugin: { name: 'Chrome PDF Viewer' }
                        }
                    };
                    return mimeTypes;
                }
            });
        """)
    
    def _add_languages(self):
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en', 'en-US']
            });
            
            Object.defineProperty(navigator, 'language', {
                get: () => 'zh-CN'
            });
        """)
    
    def _add_chrome_runtime(self):
        self.page.add_init_script("""
            window.chrome = {
                runtime: {
                    connect: () => ({
                        onDisconnect: { addListener: () => {} },
                        postMessage: () => {}
                    }),
                    sendMessage: () => {},
                    onMessage: { addListener: () => {} },
                    onConnect: { addListener: () => {} }
                }
            };
        """)
    
    def _add_permissions_api(self):
        self.page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            if (originalQuery) {
                window.navigator.permissions.query = (parameters) => {
                    if (parameters.name === 'notifications') {
                        return Promise.resolve({ state: Notification.permission });
                    }
                    return originalQuery(parameters);
                };
            }
        """)
    
    def _add_outer_dimensions(self):
        self.page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', {
                get: () => window.innerWidth
            });
            
            Object.defineProperty(window, 'outerHeight', {
                get: () => window.innerHeight
            });
        """)
    
    def _fix_console_debug(self):
        self.page.add_init_script("""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel(R) Iris(TM) Graphics 6100';
                }
                return getParameter(parameter);
            };
        """)
    
    def random_delay(self, min_delay: float = None, max_delay: float = None):
        if not self.config.random_input_delay:
            return
        
        if min_delay is None:
            min_delay = config.INPUT_DELAY_MIN
        if max_delay is None:
            max_delay = config.INPUT_DELAY_MAX
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def simulate_human_typing(self, element, text: str, base_delay: float = 0.1):
        for char in text:
            delay = base_delay * random.uniform(0.5, 1.5)
            element.type(char, delay=delay * 1000)
            time.sleep(delay * 0.3)
    
    def random_scroll(self, min_amount: int = 100, max_amount: int = 500):
        if not self.config.random_scroll:
            return
        
        amount = random.randint(min_amount, max_amount)
        direction = random.choice([1, -1])
        
        self.page.evaluate(f"window.scrollBy(0, {amount * direction})")
        self.random_delay(0.1, 0.3)
    
    def simulate_mouse_path(self, start_x: int, start_y: int, end_x: int, end_y: int):
        if not self.config.simulate_mouse_movement:
            self.page.mouse.move(end_x, end_y)
            return
        
        steps = random.randint(15, 40)
        
        for i in range(steps + 1):
            progress = i / steps
            jitter = random.uniform(-0.03, 0.03)
            progress += jitter
            progress = max(0, min(1, progress))
            
            x = start_x + (end_x - start_x) * progress
            y = start_y + (end_y - start_y) * progress
            
            self.page.mouse.move(int(x), int(y))
            time.sleep(random.uniform(0.005, 0.02))
    
    def random_pause_between_actions(self):
        elapsed = time.time() - self._last_action_time
        
        if elapsed < 0.5:
            pause_time = random.uniform(0.3, 0.8)
            time.sleep(pause_time)
        
        self._last_action_time = time.time()


class FormValidator:
    def __init__(self, page):
        self.page = page
    
    def check_required_fields(self, field_selectors: List[str]) -> List[FormValidationError]:
        errors = []
        
        for selector in field_selectors:
            element = self.page.query_selector(selector)
            if not element:
                continue
            
            is_required = self._check_is_required(element)
            
            if is_required:
                value = self._get_element_value(element)
                
                if not value or value.strip() == "":
                    errors.append(FormValidationError(
                        field_name=selector,
                        error_message="此字段为必填项",
                        element_selector=selector
                    ))
        
        return errors
    
    def detect_validation_errors(self) -> List[FormValidationError]:
        errors = []
        
        error_indicators = [
            ".error",
            ".field-error",
            ".validation-error",
            ".form-error",
            ".has-error",
            "[class*='error']",
            ".el-form-item__error",
            ".ant-form-item-explain",
            ".error-message",
        ]
        
        for indicator in error_indicators:
            elements = self.page.query_selector_all(indicator)
            for elem in elements:
                if elem.is_visible():
                    error_text = (elem.text_content() or "").strip()
                    if error_text:
                        errors.append(FormValidationError(
                            field_name=self._find_related_field(elem),
                            error_message=error_text,
                            element_selector=self._generate_selector(elem)
                        ))
        
        input_with_errors = self.page.query_selector_all("input[aria-invalid='true'], textarea[aria-invalid='true'], select[aria-invalid='true']")
        for inp in input_with_errors:
            error_desc = inp.get_attribute("aria-describedby")
            error_msg = ""
            
            if error_desc:
                error_elem = self.page.query_selector(f"#{error_desc}")
                if error_elem:
                    error_msg = (error_elem.text_content() or "").strip()
            
            if not error_msg:
                parent = inp.evaluate_handle("el => el.parentElement")
                if parent:
                    parent_elem = parent.as_element()
                    error_elems = parent_elem.query_selector_all(".error, [class*='error']")
                    for e in error_elems:
                        if e.is_visible():
                            error_msg = (e.text_content() or "").strip()
                            break
            
            errors.append(FormValidationError(
                field_name=self._get_field_identifier(inp),
                error_message=error_msg or "字段验证失败",
                element_selector=self._generate_selector(inp)
            ))
        
        return errors
    
    def wait_for_validation(self, timeout: int = 5000) -> List[FormValidationError]:
        start_time = time.time()
        
        while time.time() - start_time < timeout / 1000:
            errors = self.detect_validation_errors()
            if errors:
                return errors
            time.sleep(0.1)
        
        return []
    
    def _check_is_required(self, element) -> bool:
        required = element.get_attribute("required")
        if required is not None:
            return True
        
        aria_required = element.get_attribute("aria-required")
        if aria_required and aria_required.lower() == 'true':
            return True
        
        parent = element.evaluate_handle("el => el.parentElement")
        if parent:
            parent_class = parent.as_element().get_attribute("class") or ""
            if 'required' in parent_class.lower():
                return True
            
            grandparent = parent.as_element().evaluate_handle("el => el.parentElement")
            if grandparent:
                gp_class = grandparent.as_element().get_attribute("class") or ""
                if 'required' in gp_class.lower():
                    return True
        
        return False
    
    def _get_element_value(self, element) -> str:
        tag_name = element.evaluate("el => el.tagName.toLowerCase()")
        
        if tag_name == 'select':
            return element.evaluate("el => el.value") or ""
        
        input_type = element.get_attribute("type") or ""
        input_type = input_type.lower()
        
        if input_type in ['checkbox', 'radio']:
            return 'checked' if element.is_checked() else ''
        
        value = element.get_attribute("value")
        if value is not None:
            return value
        
        return (element.text_content() or "").strip()
    
    def _find_related_field(self, error_element) -> str:
        related_inputs = error_element.evaluate("""
            el => {
                let inputs = [];
                let parent = el.parentElement;
                while (parent) {
                    const found = parent.querySelectorAll('input, textarea, select');
                    if (found.length > 0) {
                        return found[0].getAttribute('name') || found[0].getAttribute('id') || '';
                    }
                    parent = parent.parentElement;
                }
                return '';
            }
        """)
        
        return related_inputs or "unknown_field"
    
    def _get_field_identifier(self, element) -> str:
        name = element.get_attribute("name")
        if name:
            return name
        
        elem_id = element.get_attribute("id")
        if elem_id:
            return elem_id
        
        placeholder = element.get_attribute("placeholder")
        if placeholder:
            return placeholder
        
        return self._generate_selector(element)
    
    def _generate_selector(self, element) -> str:
        name = element.get_attribute("name")
        if name:
            tag_name = element.evaluate("el => el.tagName.toLowerCase()")
            return f"{tag_name}[name='{name}']"
        
        elem_id = element.get_attribute("id")
        if elem_id:
            return f"#{elem_id}"
        
        css_path = element.evaluate("""
            el => {
                const path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.tagName.toLowerCase();
                    if (el.id) {
                        selector += '#' + el.id;
                        path.unshift(selector);
                        break;
                    }
                    path.unshift(selector);
                    el = el.parentNode;
                }
                return path.join(' > ');
            }
        """)
        
        return css_path or "unknown"
