import os
import sys
import random
import time
import re
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config


@dataclass
class DatePickerConfig:
    format: str = "%Y-%m-%d"
    year_selector: str = ""
    month_selector: str = ""
    day_selector: str = ""
    use_input_directly: bool = True


@dataclass
class DropdownConfig:
    trigger_selector: str = ""
    option_selector: str = ""
    option_text_selector: str = ""
    is_custom_dropdown: bool = False


class InteractionHandler:
    def __init__(self, page):
        self.page = page
        self._last_interaction_time = 0
    
    def _wait_human_like(self, min_delay: float = None, max_delay: float = None):
        if min_delay is None:
            min_delay = config.INPUT_DELAY_MIN
        if max_delay is None:
            max_delay = config.INPUT_DELAY_MAX
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def handle_iframe(self, iframe_selector: str = None, iframe_url_pattern: str = None):
        if iframe_selector:
            iframe = self.page.query_selector(iframe_selector)
            if iframe:
                return iframe.content_frame()
        
        if iframe_url_pattern:
            for frame in self.page.frames:
                if iframe_url_pattern in frame.url:
                    return frame
        
        return None
    
    def wait_for_dynamic_content(self, selector: str, timeout: int = None):
        timeout = timeout or config.ELEMENT_WAIT_TIMEOUT
        
        try:
            element = self.page.wait_for_selector(selector, timeout=timeout, state="visible")
            return element
        except Exception:
            return None
    
    def wait_for_dynamic_content_to_disappear(self, selector: str, timeout: int = None):
        timeout = timeout or config.ELEMENT_WAIT_TIMEOUT
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout, state="hidden")
            return True
        except Exception:
            return False
    
    def scroll_to_load_more(self, direction: str = "down", iterations: int = 3):
        for i in range(iterations):
            if direction == "down":
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            else:
                self.page.evaluate("window.scrollTo(0, 0)")
            
            self._wait_human_like(0.5, 1.0)
    
    def handle_select_dropdown(self, selector: str, value: str = None, label: str = None):
        element = self.page.query_selector(selector)
        if not element:
            return False
        
        tag_name = element.evaluate("el => el.tagName.toLowerCase()")
        
        if tag_name == "select":
            try:
                if value:
                    self.page.select_option(selector, value=value)
                elif label:
                    self.page.select_option(selector, label=label)
                return True
            except Exception:
                return False
        
        return self._handle_custom_dropdown(selector, value, label)
    
    def _handle_custom_dropdown(self, trigger_selector: str, value: str = None, label: str = None):
        trigger = self.page.query_selector(trigger_selector)
        if not trigger:
            return False
        
        trigger.click()
        self._wait_human_like()
        
        option_selectors = [
            "li",
            ".dropdown-item",
            ".option",
            "[role='option']",
            ".el-select-dropdown__item",
            ".ant-select-dropdown-menu-item",
        ]
        
        for opt_sel in option_selectors:
            options = self.page.query_selector_all(opt_sel)
            for option in options:
                option_text = (option.text_content() or "").strip()
                
                if value and option.get_attribute("value") == value:
                    option.click()
                    return True
                
                if label and self._text_matches(option_text, label):
                    option.click()
                    return True
        
        return False
    
    def handle_date_picker(
        self, 
        selector: str, 
        date_value: datetime, 
        config: DatePickerConfig = None
    ):
        if config is None:
            config = DatePickerConfig()
        
        element = self.page.query_selector(selector)
        if not element:
            return False
        
        if config.use_input_directly:
            try:
                date_str = date_value.strftime(config.format)
                element.click()
                self._wait_human_like()
                
                element.evaluate("el => el.value = ''")
                element.fill(date_str)
                
                self.page.keyboard.press("Enter")
                self._wait_human_like()
                
                return True
            except Exception:
                pass
        
        return self._handle_calendar_date_picker(element, date_value, config)
    
    def _handle_calendar_date_picker(
        self, 
        element, 
        date_value: datetime, 
        config: DatePickerConfig
    ):
        element.click()
        self._wait_human_like()
        
        calendar_selectors = [
            ".el-date-picker",
            ".ant-calendar",
            ".datepicker-dropdown",
            ".ui-datepicker",
            "[role='dialog']",
        ]
        
        calendar = None
        for sel in calendar_selectors:
            calendar = self.page.query_selector(sel)
            if calendar:
                break
        
        if not calendar:
            return False
        
        target_year = date_value.year
        target_month = date_value.month
        target_day = date_value.day
        
        max_attempts = 24
        attempts = 0
        
        while attempts < max_attempts:
            current_year = self._get_current_calendar_year(calendar)
            current_month = self._get_current_calendar_month(calendar)
            
            if current_year == target_year and current_month == target_month:
                break
            
            if current_year > target_year or (current_year == target_year and current_month > target_month):
                self._click_previous_month(calendar)
            else:
                self._click_next_month(calendar)
            
            self._wait_human_like(0.2, 0.4)
            attempts += 1
        
        day_selector = f"//td[not(contains(@class, 'disabled')) and normalize-space(.)='{target_day}']"
        day_element = calendar.query_selector(f"xpath={day_selector}")
        
        if day_element:
            day_element.click()
            self._wait_human_like()
            return True
        
        return False
    
    def _get_current_calendar_year(self, calendar) -> int:
        year_selectors = [
            ".el-date-picker__header-label",
            ".ant-calendar-year-select",
            ".datepicker-years",
            ".ui-datepicker-year",
            "[data-year]",
        ]
        
        for sel in year_selectors:
            elem = calendar.query_selector(sel)
            if elem:
                text = elem.text_content() or ""
                year_match = re.search(r'(\d{4})', text)
                if year_match:
                    return int(year_match.group(1))
                
                data_year = elem.get_attribute("data-year")
                if data_year:
                    return int(data_year)
        
        return datetime.now().year
    
    def _get_current_calendar_month(self, calendar) -> int:
        month_map = {
            '一月': 1, '二月': 2, '三月': 3, '四月': 4, '五月': 5, '六月': 6,
            '七月': 7, '八月': 8, '九月': 9, '十月': 10, '十一月': 11, '十二月': 12,
            '1月': 1, '2月': 2, '3月': 3, '4月': 4, '5月': 5, '6月': 6,
            '7月': 7, '8月': 8, '9月': 9, '10月': 10, '11月': 11, '12月': 12,
            'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
            'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12,
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
        }
        
        month_selectors = [
            ".el-date-picker__header-label",
            ".ant-calendar-month-select",
            ".datepicker-months",
            ".ui-datepicker-month",
            "[data-month]",
        ]
        
        for sel in month_selectors:
            elem = calendar.query_selector(sel)
            if elem:
                text = elem.text_content() or ""
                
                for month_name, month_num in month_map.items():
                    if month_name in text:
                        return month_num
                
                data_month = elem.get_attribute("data-month")
                if data_month:
                    return int(data_month) + 1
                
                month_match = re.search(r'(\d{1,2})月?', text)
                if month_match:
                    return int(month_match.group(1))
        
        return datetime.now().month
    
    def _click_previous_month(self, calendar):
        prev_selectors = [
            ".el-date-picker__prev-btn",
            ".ant-calendar-prev-month-btn",
            ".datepicker-prev",
            ".ui-datepicker-prev",
            "[aria-label='Previous month']",
            "button[class*='prev']",
            "//button[contains(@class, 'prev')]",
        ]
        
        for sel in prev_selectors:
            try:
                if sel.startswith("//"):
                    btn = calendar.query_selector(f"xpath={sel}")
                else:
                    btn = calendar.query_selector(sel)
                if btn:
                    btn.click()
                    return
            except Exception:
                continue
    
    def _click_next_month(self, calendar):
        next_selectors = [
            ".el-date-picker__next-btn",
            ".ant-calendar-next-month-btn",
            ".datepicker-next",
            ".ui-datepicker-next",
            "[aria-label='Next month']",
            "button[class*='next']",
            "//button[contains(@class, 'next')]",
        ]
        
        for sel in next_selectors:
            try:
                if sel.startswith("//"):
                    btn = calendar.query_selector(f"xpath={sel}")
                else:
                    btn = calendar.query_selector(sel)
                if btn:
                    btn.click()
                    return
            except Exception:
                continue
    
    def click_add_more_button(self, button_texts: List[str] = None):
        if button_texts is None:
            button_texts = [
                "添加", "新增", "增加", "添加更多", "新增一条",
                "Add", "Add More", "+"
            ]
        
        for text in button_texts:
            selectors = [
                f"//button[contains(normalize-space(.), '{text}')]",
                f"//a[contains(normalize-space(.), '{text}')]",
                f"//span[contains(normalize-space(.), '{text}')]",
                f"//div[contains(normalize-space(.), '{text}') and @role='button']",
                f"button:has-text('{text}')",
            ]
            
            for sel in selectors:
                try:
                    if sel.startswith("//"):
                        btn = self.page.query_selector(f"xpath={sel}")
                    else:
                        btn = self.page.query_selector(sel)
                    
                    if btn and btn.is_visible():
                        btn.scroll_into_view_if_needed()
                        self._wait_human_like()
                        btn.click()
                        self._wait_human_like(0.5, 1.0)
                        return True
                except Exception:
                    continue
        
        return False
    
    def click_save_button(self, button_texts: List[str] = None):
        if button_texts is None:
            button_texts = [
                "保存", "提交", "确认", "确定", "完成",
                "Save", "Submit", "Confirm", "Done"
            ]
        
        for text in button_texts:
            selectors = [
                f"//button[contains(normalize-space(.), '{text}')]",
                f"//input[@type='submit' and @value='{text}']",
                f"//a[contains(normalize-space(.), '{text}')]",
                f"//div[contains(normalize-space(.), '{text}') and @role='button']",
            ]
            
            for sel in selectors:
                try:
                    btn = self.page.query_selector(f"xpath={sel}")
                    if btn and btn.is_visible():
                        btn.scroll_into_view_if_needed()
                        self._wait_human_like()
                        btn.click()
                        self._wait_human_like(0.5, 1.0)
                        return True
                except Exception:
                    continue
        
        return False
    
    def handle_radio_group(self, group_selector: str, value: str = None, label: str = None):
        radios = self.page.query_selector_all(f"{group_selector} input[type='radio']")
        
        for radio in radios:
            if value:
                radio_value = radio.get_attribute("value")
                if radio_value == value:
                    radio.click()
                    return True
            
            if label:
                radio_id = radio.get_attribute("id")
                if radio_id:
                    label_elem = self.page.query_selector(f"label[for='{radio_id}']")
                    if label_elem:
                        label_text = (label_elem.text_content() or "").strip()
                        if self._text_matches(label_text, label):
                            radio.click()
                            return True
                
                parent = radio.evaluate_handle("el => el.parentElement")
                if parent:
                    parent_text = (parent.as_element().text_content() or "").strip()
                    if self._text_matches(parent_text, label):
                        radio.click()
                        return True
        
        return False
    
    def handle_checkbox(self, selector: str, should_check: bool = True):
        checkbox = self.page.query_selector(selector)
        if not checkbox:
            return False
        
        is_checked = checkbox.is_checked()
        
        if should_check != is_checked:
            checkbox.click()
            self._wait_human_like()
        
        return True
    
    def handle_textarea(self, selector: str, value: str, char_by_char: bool = True):
        textarea = self.page.query_selector(selector)
        if not textarea:
            return False
        
        textarea.click()
        self._wait_human_like()
        
        textarea.evaluate("el => el.value = ''")
        
        if char_by_char:
            for char in value:
                textarea.type(char, delay=random.uniform(0.05, 0.15) * 1000)
                time.sleep(random.uniform(0.02, 0.05))
        else:
            textarea.fill(value)
        
        self._wait_human_like()
        return True
    
    def handle_file_upload(self, selector: str, file_path: str):
        file_input = self.page.query_selector(selector)
        if not file_input:
            return False
        
        file_input.set_input_files(file_path)
        self._wait_human_like(0.5, 1.0)
        return True
    
    def wait_for_spinner(self, timeout: int = 10000):
        spinner_selectors = [
            ".loading",
            ".spinner",
            "[class*='loading']",
            "[class*='spinner']",
            ".el-loading-mask",
            ".ant-spin",
        ]
        
        spinner = None
        for sel in spinner_selectors:
            spinner = self.page.query_selector(sel)
            if spinner:
                break
        
        if spinner:
            try:
                self.page.wait_for_selector(sel, timeout=timeout, state="hidden")
            except Exception:
                pass
        
        return True
    
    def simulate_mouse_movement(self, start_x: int, start_y: int, end_x: int, end_y: int):
        if not config.MOUSE_MOVEMENT_SIMULATION:
            self.page.mouse.move(end_x, end_y)
            return
        
        steps = random.randint(10, 30)
        
        for i in range(steps + 1):
            progress = i / steps
            progress = progress + random.uniform(-0.02, 0.02)
            progress = max(0, min(1, progress))
            
            x = start_x + (end_x - start_x) * progress
            y = start_y + (end_y - start_y) * progress
            
            self.page.mouse.move(int(x), int(y))
            time.sleep(random.uniform(0.01, 0.03))
    
    def _text_matches(self, source: str, target: str) -> bool:
        if not source or not target:
            return False
        
        source_lower = source.lower()
        target_lower = target.lower()
        
        if source_lower == target_lower:
            return True
        
        if target_lower in source_lower:
            return True
        
        if source_lower in target_lower:
            return True
        
        return False
