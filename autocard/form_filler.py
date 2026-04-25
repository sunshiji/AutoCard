import os
import sys
import random
import time
import re
import json
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from models import (
    ResumeData, PersonalInfo, EducationExperience,
    WorkExperience, ProjectExperience, FillResult,
    FormValidationError, LocatedField
)
from .browser_manager import BrowserManager
from .field_locator import FieldLocator
from .interaction_handler import InteractionHandler, DatePickerConfig
from .anti_detection import AntiDetection, FormValidator, AntiDetectionConfig


@dataclass
class FillProgress:
    total_fields: int = 0
    filled_fields: int = 0
    failed_fields: int = 0
    current_section: str = ""
    current_field: str = ""
    errors: List[str] = field(default_factory=list)


class FormFiller:
    def __init__(
        self,
        browser_manager: BrowserManager,
        resume_data: ResumeData,
        platform_selectors: Dict[str, List[str]] = None
    ):
        self.browser_manager = browser_manager
        self.page = browser_manager.page
        self.resume_data = resume_data
        self._platform_selectors = platform_selectors or {}
        
        self.field_locator = FieldLocator(self.page, self._platform_selectors)
        self.interaction_handler = InteractionHandler(self.page)
        self.anti_detection = AntiDetection(self.page, AntiDetectionConfig())
        self.form_validator = FormValidator(self.page)
        
        self.progress = FillProgress()
        self._fill_results: List[FillResult] = []
    
    def set_platform_selectors(self, selectors: Dict[str, List[str]]):
        self._platform_selectors = selectors
        if self.field_locator:
            self.field_locator.set_platform_selectors(selectors)
    
    def fill_personal_info(self) -> List[FillResult]:
        self.progress.current_section = "个人信息"
        results = []
        
        personal_info = self.resume_data.personal_info
        
        field_mappings = {
            "name": personal_info.name,
            "phone": personal_info.phone,
            "email": personal_info.email,
            "gender": personal_info.gender,
            "self_introduction": personal_info.self_introduction,
        }
        
        for field_name, value in field_mappings.items():
            if value is None:
                continue
            
            self.progress.current_field = field_name
            
            result = self._fill_single_field(field_name, value)
            results.append(result)
            self._fill_results.append(result)
            
            if result.success:
                self.progress.filled_fields += 1
            else:
                self.progress.failed_fields += 1
                if result.error_message:
                    self.progress.errors.append(f"{field_name}: {result.error_message}")
        
        return results
    
    def fill_education_experiences(self) -> List[FillResult]:
        self.progress.current_section = "教育经历"
        results = []
        
        experiences = self.resume_data.education_experiences
        
        for idx, exp in enumerate(experiences):
            if idx > 0:
                added = self.interaction_handler.click_add_more_button()
                if added:
                    self.anti_detection.random_delay(0.5, 1.0)
                    self.field_locator.clear_cache()
            
            exp_results = self._fill_education_experience(exp, idx)
            results.extend(exp_results)
        
        return results
    
    def _fill_education_experience(self, exp: EducationExperience, index: int = 0) -> List[FillResult]:
        results = []
        
        field_mappings = {
            ("school", "学校"): exp.school,
            ("major", "专业"): exp.major,
            ("education", "学历"): exp.education,
            ("start_date", "开始时间"): exp.start_date,
            ("end_date", "结束时间"): exp.end_date,
        }
        
        for (field_name, label), value in field_mappings.items():
            if value is None:
                continue
            
            self.progress.current_field = f"{field_name}_{index}"
            
            if isinstance(value, datetime):
                result = self._fill_date_field(field_name, value, [label])
            elif field_name == "education":
                result = self._fill_select_field(field_name, value, [label])
            else:
                result = self._fill_single_field(field_name, value, [label])
            
            results.append(result)
            self._fill_results.append(result)
            
            if result.success:
                self.progress.filled_fields += 1
            else:
                self.progress.failed_fields += 1
        
        return results
    
    def fill_work_experiences(self) -> List[FillResult]:
        self.progress.current_section = "工作经历"
        results = []
        
        experiences = self.resume_data.work_experiences
        
        for idx, exp in enumerate(experiences):
            if idx > 0:
                added = self.interaction_handler.click_add_more_button()
                if added:
                    self.anti_detection.random_delay(0.5, 1.0)
                    self.field_locator.clear_cache()
            
            exp_results = self._fill_work_experience(exp, idx)
            results.extend(exp_results)
        
        return results
    
    def _fill_work_experience(self, exp: WorkExperience, index: int = 0) -> List[FillResult]:
        results = []
        
        field_mappings = {
            ("company", "公司"): exp.company,
            ("position", "职位"): exp.position,
            ("industry", "行业"): exp.industry,
            ("start_date", "开始时间"): exp.start_date,
            ("end_date", "结束时间"): exp.end_date,
            ("work_description", "工作描述"): exp.description,
        }
        
        for (field_name, label), value in field_mappings.items():
            if value is None:
                continue
            
            self.progress.current_field = f"{field_name}_{index}"
            
            if isinstance(value, datetime):
                result = self._fill_date_field(field_name, value, [label])
            elif field_name == "work_description":
                result = self._fill_textarea_field(field_name, value, [label])
            else:
                result = self._fill_single_field(field_name, value, [label])
            
            results.append(result)
            self._fill_results.append(result)
            
            if result.success:
                self.progress.filled_fields += 1
            else:
                self.progress.failed_fields += 1
        
        return results
    
    def fill_project_experiences(self) -> List[FillResult]:
        self.progress.current_section = "项目经历"
        results = []
        
        experiences = self.resume_data.project_experiences
        
        for idx, exp in enumerate(experiences):
            if idx > 0:
                added = self.interaction_handler.click_add_more_button()
                if added:
                    self.anti_detection.random_delay(0.5, 1.0)
                    self.field_locator.clear_cache()
            
            exp_results = self._fill_project_experience(exp, idx)
            results.extend(exp_results)
        
        return results
    
    def _fill_project_experience(self, exp: ProjectExperience, index: int = 0) -> List[FillResult]:
        results = []
        
        field_mappings = {
            ("project_name", "项目名称"): exp.project_name,
            ("project_role", "项目角色"): exp.role,
            ("start_date", "开始时间"): exp.start_date,
            ("end_date", "结束时间"): exp.end_date,
            ("project_description", "项目描述"): exp.description,
        }
        
        for (field_name, label), value in field_mappings.items():
            if value is None:
                continue
            
            self.progress.current_field = f"{field_name}_{index}"
            
            if isinstance(value, datetime):
                result = self._fill_date_field(field_name, value, [label])
            elif field_name == "project_description":
                result = self._fill_textarea_field(field_name, value, [label])
            else:
                result = self._fill_single_field(field_name, value, [label])
            
            results.append(result)
            self._fill_results.append(result)
            
            if result.success:
                self.progress.filled_fields += 1
            else:
                self.progress.failed_fields += 1
        
        return results
    
    def fill_skills(self) -> List[FillResult]:
        self.progress.current_section = "技能"
        results = []
        
        if not self.resume_data.skills:
            return results
        
        skills_text = "、".join(self.resume_data.skills)
        
        result = self._fill_single_field("skill", skills_text, ["技能", "专业技能"])
        results.append(result)
        self._fill_results.append(result)
        
        if result.success:
            self.progress.filled_fields += 1
        else:
            self.progress.failed_fields += 1
        
        return results
    
    def fill_all(self) -> List[FillResult]:
        all_results = []
        
        all_results.extend(self.fill_personal_info())
        all_results.extend(self.fill_education_experiences())
        all_results.extend(self.fill_work_experiences())
        all_results.extend(self.fill_project_experiences())
        all_results.extend(self.fill_skills())
        
        return all_results
    
    def _fill_single_field(
        self, 
        field_name: str, 
        value: str, 
        label_texts: List[str] = None
    ) -> FillResult:
        if label_texts is None:
            label_texts = config.FIELD_MAPPINGS.get(field_name, [field_name])
        
        located = self.field_locator.locate_field(field_name, label_texts)
        
        if not located:
            return FillResult(
                success=False,
                field_name=field_name,
                value=value,
                error_message=f"无法定位字段: {field_name}"
            )
        
        try:
            context = located.frame_context or self.page
            selector = located.selector
            input_type = located.input_type
            
            self.anti_detection.random_pause_between_actions()
            
            element = context.query_selector(selector)
            if not element:
                return FillResult(
                    success=False,
                    field_name=field_name,
                    value=value,
                    error_message=f"元素不存在: {selector}",
                    selector_used=selector
                )
            
            self._wait_for_overlay(element)
            
            is_in_viewport = self._check_element_in_viewport(element)
            if not is_in_viewport:
                print(f"  [提示] 字段 {field_name} 不在视口内，尝试滚动...")
                scroll_success = self._force_scroll_into_view(element)
                if not scroll_success:
                    print(f"  [警告] 滚动可能失败，继续尝试...")
            
            self.anti_detection.random_delay(0.1, 0.2)
            
            fill_success = False
            
            if input_type in ['text', 'email', 'tel', 'password', 'number', 'date', 'textarea']:
                print(f"  [提示] 使用直接填充策略 (input_type={input_type}): {field_name}")
                fill_success = self._fill_input_direct(element, str(value))
            elif input_type == 'select':
                print(f"  [提示] 使用选择框策略: {field_name}")
                fill_success = self._fill_select_field(element, str(value))
            else:
                print(f"  [提示] 使用通用点击+填充策略 (input_type={input_type}): {field_name}")
                click_success = self._safe_click(element, field_name)
                if not click_success:
                    print(f"  [警告] 点击字段 {field_name} 可能失败，尝试直接输入...")
                self.anti_detection.random_delay(0.1, 0.2)
                fill_success = self._safe_fill_input(element, str(value))
            
    def _fill_single_field(
        self, 
        field_name: str, 
        value: str, 
        label_texts: List[str] = None
    ) -> FillResult:
        if label_texts is None:
            label_texts = config.FIELD_MAPPINGS.get(field_name, [field_name])
        
        located = self.field_locator.locate_field(field_name, label_texts)
        
        if not located:
            return FillResult(
                success=False,
                field_name=field_name,
                value=value,
                error_message=f"无法定位字段: {field_name}"
            )
        
        try:
            context = located.frame_context or self.page
            selector = located.selector
            input_type = located.input_type
            
            self.anti_detection.random_pause_between_actions()
            
            element = context.query_selector(selector)
            if not element:
                return FillResult(
                    success=False,
                    field_name=field_name,
                    value=value,
                    error_message=f"元素不存在: {selector}",
                    selector_used=selector
                )
            
            print(f"\n  [处理字段] {field_name} (input_type={input_type})")
            
            self._aggressive_remove_overlays()
            
            element_info = self._get_element_info(element)
            print(f"    元素状态: {element_info}")
            
            if not element_info.get('is_interactable', False):
                print(f"    [警告] 元素可能不可交互，尝试激活...")
                self._try_activate_field(element, field_name)
            
            is_in_viewport = self._check_element_in_viewport(element)
            if not is_in_viewport:
                print(f"    字段不在视口内，尝试滚动...")
                scroll_success = self._force_scroll_into_view(element)
                if not scroll_success:
                    print(f"    [警告] 滚动可能失败，但继续尝试...")
            
            self.anti_detection.random_delay(0.1, 0.2)
            
            fill_success = False
            actual_value = None
            
            if input_type in ['text', 'email', 'tel', 'password', 'number', 'textarea']:
                print(f"    使用文本输入策略...")
                fill_success, actual_value = self._fill_text_field_with_verify(element, str(value), field_name)
            
            elif input_type == 'select':
                print(f"    使用选择框策略...")
                fill_success, actual_value = self._fill_select_with_verify(element, str(value), field_name)
            
            elif input_type == 'date':
                print(f"    使用日期选择器策略...")
                fill_success, actual_value = self._fill_date_field_with_verify(element, str(value), field_name)
            
            elif input_type in ['checkbox', 'radio']:
                print(f"    使用选择器策略...")
                fill_success, actual_value = self._fill_choice_field_with_verify(element, str(value), field_name)
            
            else:
                print(f"    使用通用策略 (input_type={input_type})...")
                fill_success, actual_value = self._fill_generic_with_verify(element, str(value), field_name)
            
            if fill_success:
                print(f"    [✓] 填充成功: '{actual_value}'")
            else:
                print(f"    [✗] 填充失败")
            
            self.anti_detection.random_delay(0.1, 0.2)
            
            return FillResult(
                success=fill_success,
                field_name=field_name,
                value=value,
                error_message=None if fill_success else "填充后验证失败",
                selector_used=selector
            )
            
        except Exception as e:
            print(f"    [✗] 异常: {e}")
            return FillResult(
                success=False,
                field_name=field_name,
                value=value,
                error_message=str(e),
                selector_used=located.selector
            )
    
    def _aggressive_remove_overlays(self):
        try:
            removed_count = self.page.evaluate("""
                () => {
                    let removed = 0;
                    
                    const selectors = [
                        '.loading', '.spinner', '.overlay', '.modal-backdrop', '.mask',
                        '[class*="loading"]', '[class*="spinner"]', '[class*="overlay"]',
                        '.el-loading-mask', '.ant-spin-container',
                        '#loading', '.fade-enter-active', '.fade-leave-active'
                    ];
                    
                    selectors.forEach(sel => {
                        const elements = document.querySelectorAll(sel);
                        elements.forEach(el => {
                            const style = window.getComputedStyle(el);
                            const pointerEvents = style.pointerEvents;
                            const zIndex = style.zIndex;
                            const opacity = style.opacity;
                            const display = style.display;
                            const visibility = style.visibility;
                            
                            if (pointerEvents === 'auto' && 
                                (zIndex !== 'auto' || opacity !== '0') &&
                                display !== 'none' && 
                                visibility !== 'hidden') {
                                el.style.display = 'none';
                                el.style.pointerEvents = 'none';
                                el.style.opacity = '0';
                                el.style.visibility = 'hidden';
                                removed++;
                            }
                        });
                    });
                    
                    const allElements = document.querySelectorAll('*');
                    allElements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        if (style.pointerEvents === 'auto' && 
                            style.zIndex !== 'auto' &&
                            parseInt(style.zIndex) > 1000) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                el.style.pointerEvents = 'none';
                                removed++;
                            }
                        }
                    });
                    
                    return removed;
                }
            """)
            
            if removed_count > 0:
                print(f"    [提示] 移除了 {removed_count} 个潜在的遮罩元素")
                
        except Exception as e:
            pass
    
    def _get_element_info(self, element) -> Dict[str, Any]:
        try:
            info = element.evaluate("""
                el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    const topElement = document.elementFromPoint(centerX, centerY);
                    
                    let isBlocked = false;
                    let blockingElement = null;
                    if (topElement && !el.contains(topElement) && topElement !== el) {
                        const topStyle = window.getComputedStyle(topElement);
                        const topPointerEvents = topStyle.pointerEvents;
                        const topDisplay = topStyle.display;
                        const topVisibility = topStyle.visibility;
                        const topOpacity = topStyle.opacity;
                        
                        if (topPointerEvents === 'auto' && 
                            topDisplay !== 'none' && 
                            topVisibility !== 'hidden' &&
                            topOpacity !== '0') {
                            isBlocked = true;
                            blockingElement = topElement.tagName + (topElement.className ? '.' + topElement.className.split(' ')[0] : '');
                        }
                    }
                    
                    return {
                        tagName: el.tagName,
                        type: el.type || null,
                        name: el.name || null,
                        id: el.id || null,
                        value: el.value || '',
                        isVisible: rect.width > 0 && rect.height > 0,
                        isEnabled: !el.disabled,
                        isReadOnly: el.readOnly,
                        pointerEvents: style.pointerEvents,
                        display: style.display,
                        visibility: style.visibility,
                        opacity: style.opacity,
                        rect: {
                            top: rect.top,
                            left: rect.left,
                            width: rect.width,
                            height: rect.height
                        },
                        isInViewport: rect.top >= 0 && rect.left >= 0 && 
                                     rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                                     rect.right <= (window.innerWidth || document.documentElement.clientWidth),
                        isBlocked: isBlocked,
                        blockingElement: blockingElement,
                        isInteractable: !el.disabled && 
                                       !el.readOnly && 
                                       rect.width > 0 && 
                                       rect.height > 0 &&
                                       style.display !== 'none' &&
                                       style.visibility !== 'hidden' &&
                                       style.opacity !== '0' &&
                                       !isBlocked
                    };
                }
            """)
            return info
        except Exception as e:
            return {"error": str(e), "is_interactable": True}
    
    def _try_activate_field(self, element, field_name: str):
        try:
            activated = element.evaluate(f"""
                el => {{
                    const fieldName = {json.dumps(field_name)};
                    
                    el.style.pointerEvents = 'auto';
                    el.readOnly = false;
                    el.disabled = false;
                    
                    if (el.parentElement) {{
                        el.parentElement.style.pointerEvents = 'auto';
                    }}
                    
                    const tabTexts = ['教育', '工作', '项目', '基本信息', '个人信息', '经历', '学历'];
                    const currentText = el.textContent || '';
                    const inputType = el.type || '';
                    
                    let needsActivation = false;
                    let selector = '';
                    
                    if (inputType === 'date' || fieldName.includes('date') || fieldName.includes('time')) {{
                        needsActivation = true;
                        selector = 'input[type="date"], input[placeholder*="日期"], input[placeholder*="时间"]';
                    }} else if (fieldName === 'education' || fieldName === 'gender' || 
                               currentText.includes('学历') || currentText.includes('性别')) {{
                        needsActivation = true;
                        selector = 'select, [role="combobox"], [class*="select"]';
                    }} else if (fieldName.includes('description') || fieldName === 'self_introduction') {{
                        needsActivation = true;
                        selector = 'textarea, [contenteditable="true"]';
                    }}
                    
                    if (needsActivation) {{
                        const focusEvent = new FocusEvent('focus', {{ bubbles: true }});
                        const clickEvent = new MouseEvent('click', {{ bubbles: true, cancelable: true }});
                        
                        el.dispatchEvent(focusEvent);
                        el.dispatchEvent(clickEvent);
                        
                        return true;
                    }}
                    
                    return false;
                }}
            """)
            
            if activated:
                print(f"    [提示] 尝试激活字段: {field_name}")
                self.anti_detection.random_delay(0.2, 0.4)
                
        except Exception as e:
            print(f"    [调试] 激活字段失败: {e}")
    
    def _get_actual_value(self, element) -> str:
        try:
            return element.evaluate("""
                el => {
                    if (el.tagName === 'SELECT') {
                        const selectedOpt = el.options[el.selectedIndex];
                        return selectedOpt ? (selectedOpt.value || selectedOpt.textContent || '') : '';
                    }
                    if (el.tagName === 'INPUT' && (el.type === 'checkbox' || el.type === 'radio')) {
                        return el.checked ? 'checked' : '';
                    }
                    return el.value || el.textContent || '';
                }
            """)
        except Exception:
            return ''
    
    def _fill_text_field_with_verify(self, element, value: str, field_name: str) -> Tuple[bool, str]:
        strategies = [
            ("playwright_fill_with_verify", self._fill_playwright_with_verify),
            ("js_with_events_and_verify", self._fill_js_with_events_and_verify),
            ("playwright_type_with_verify", self._fill_type_with_verify),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                self._aggressive_remove_overlays()
                self.anti_detection.random_delay(0.1, 0.2)
                
                success, actual_val = strategy_func(element, value)
                if success:
                    if strategy_name != "playwright_fill_with_verify":
                        print(f"    [提示] 使用策略 '{strategy_name}' 成功")
                    return True, actual_val
                
                self.anti_detection.random_delay(0.05, 0.1)
            except Exception as e:
                print(f"    [调试] 策略 '{strategy_name}' 失败: {e}")
                continue
        
        final_value = self._get_actual_value(element)
        return self._values_match(final_value, value), final_value
    
    def _fill_playwright_with_verify(self, element, value: str) -> Tuple[bool, str]:
        try:
            element.evaluate("el => { el.value = ''; el.focus(); }")
            self.anti_detection.random_delay(0.05, 0.1)
            
            element.fill(value)
            self.anti_detection.random_delay(0.1, 0.2)
            
            actual = self._get_actual_value(element)
            return self._values_match(actual, value), actual
        except Exception as e:
            print(f"    [调试] playwright_fill 失败: {e}")
            return False, self._get_actual_value(element)
    
    def _fill_js_with_events_and_verify(self, element, value: str) -> Tuple[bool, str]:
        try:
            success = element.evaluate(f"""
                el => {{
                    const targetValue = {json.dumps(value)};
                    
                    el.value = '';
                    el.focus();
                    
                    const inputEvent = new Event('input', {{ bubbles: true }});
                    el.dispatchEvent(inputEvent);
                    
                    el.value = targetValue;
                    
                    const inputEvent2 = new Event('input', {{ bubbles: true }});
                    const changeEvent = new Event('change', {{ bubbles: true }});
                    const blurEvent = new Event('blur', {{ bubbles: true }});
                    
                    el.dispatchEvent(inputEvent2);
                    el.dispatchEvent(changeEvent);
                    el.dispatchEvent(blurEvent);
                    
                    if (el.value === targetValue) {{
                        return true;
                    }}
                    
                    el.setAttribute('value', targetValue);
                    return el.value === targetValue || el.getAttribute('value') === targetValue;
                }}
            """)
            
            self.anti_detection.random_delay(0.1, 0.2)
            
            actual = self._get_actual_value(element)
            
            if success and self._values_match(actual, value):
                return True, actual
            
            return self._values_match(actual, value), actual
            
        except Exception as e:
            print(f"    [调试] js_with_events 失败: {e}")
            return False, self._get_actual_value(element)
    
    def _fill_type_with_verify(self, element, value: str) -> Tuple[bool, str]:
        try:
            element.evaluate("el => { el.value = ''; el.focus(); }")
            self.anti_detection.random_delay(0.05, 0.1)
            
            self.anti_detection.simulate_human_typing(element, value)
            self.anti_detection.random_delay(0.1, 0.2)
            
            element.evaluate("el => el.blur();")
            
            actual = self._get_actual_value(element)
            return self._values_match(actual, value), actual
        except Exception as e:
            print(f"    [调试] playwright_type 失败: {e}")
            return False, self._get_actual_value(element)
    
    def _fill_select_with_verify(self, element, value: str, field_name: str) -> Tuple[bool, str]:
        try:
            is_native_select = element.evaluate("el => el.tagName === 'SELECT'")
            
            if is_native_select:
                success = element.evaluate(f"""
                    el => {{
                        const targetValue = {json.dumps(value)};
                        const options = el.querySelectorAll('option');
                        
                        for (let opt of options) {{
                            const optText = (opt.textContent || '').trim();
                            const optValue = (opt.value || '').trim();
                            
                            if (optValue === targetValue || 
                                optText === targetValue ||
                                optText.includes(targetValue) ||
                                targetValue.includes(optText)) {{
                                opt.selected = true;
                                
                                const inputEvent = new Event('input', {{ bubbles: true }});
                                const changeEvent = new Event('change', {{ bubbles: true }});
                                el.dispatchEvent(inputEvent);
                                el.dispatchEvent(changeEvent);
                                
                                return true;
                            }}
                        }}
                        
                        return false;
                    }}
                """)
                
                if success:
                    self.anti_detection.random_delay(0.1, 0.2)
                    actual = self._get_actual_value(element)
                    return self._values_match(actual, value), actual
            
            print(f"    [提示] 不是原生 select，尝试自定义下拉框...")
            
            try:
                element.click(timeout=2000)
                self.anti_detection.random_delay(0.3, 0.5)
                
                option_selectors = [
                    'li', '.dropdown-item', '.option', "[role='option']",
                    '.el-select-dropdown__item', '.ant-select-dropdown-menu-item',
                    '.select-option', '.combobox-option'
                ]
                
                for sel in option_selectors:
                    try:
                        options = self.page.query_selector_all(sel)
                        for opt in options:
                            opt_text = opt.text_content() or ''
                            opt_text = opt_text.strip()
                            
                            if self._values_match(opt_text, value):
                                opt.click(timeout=2000)
                                self.anti_detection.random_delay(0.2, 0.3)
                                
                                actual = self._get_actual_value(element)
                                if self._values_match(actual, value) or self._values_match(opt_text, value):
                                    return True, actual or opt_text
                    except Exception:
                        continue
                
            except Exception as click_error:
                if "intercept" in str(click_error).lower() or "pointer" in str(click_error).lower():
                    print(f"    [提示] 点击被拦截，尝试 JavaScript 点击...")
                    element.evaluate("el => el.click()")
                    self.anti_detection.random_delay(0.3, 0.5)
            
            actual = self._get_actual_value(element)
            return self._values_match(actual, value), actual
            
        except Exception as e:
            print(f"    [调试] select 填充失败: {e}")
            return False, self._get_actual_value(element)
    
    def _fill_date_field_with_verify(self, element, value: str, field_name: str) -> Tuple[bool, str]:
        try:
            if isinstance(value, datetime):
                date_str = value.strftime("%Y-%m-%d")
            else:
                date_str = str(value)
            
            success = element.evaluate(f"""
                el => {{
                    const dateStr = {json.dumps(date_str)};
                    
                    el.value = '';
                    el.focus();
                    
                    el.value = dateStr;
                    el.setAttribute('value', dateStr);
                    
                    const inputEvent = new Event('input', {{ bubbles: true }});
                    const changeEvent = new Event('change', {{ bubbles: true }});
                    el.dispatchEvent(inputEvent);
                    el.dispatchEvent(changeEvent);
                    
                    return el.value === dateStr || el.getAttribute('value') === dateStr;
                }}
            """)
            
            self.anti_detection.random_delay(0.2, 0.3)
            
            actual = self._get_actual_value(element)
            
            if success and self._values_match(actual, date_str):
                return True, actual
            
            try:
                element.fill(date_str)
                self.anti_detection.random_delay(0.2, 0.3)
                actual = self._get_actual_value(element)
                return self._values_match(actual, date_str), actual
            except Exception:
                pass
            
            return self._values_match(actual, date_str), actual
            
        except Exception as e:
            print(f"    [调试] 日期填充失败: {e}")
            return False, self._get_actual_value(element)
    
    def _fill_choice_field_with_verify(self, element, value: str, field_name: str) -> Tuple[bool, str]:
        try:
            is_radio = element.evaluate("el => el.type === 'radio'")
            is_checkbox = element.evaluate("el => el.type === 'checkbox'")
            
            if is_radio:
                element.evaluate("""
                    el => {
                        el.checked = true;
                        const changeEvent = new Event('change', { bubbles: true });
                        el.dispatchEvent(changeEvent);
                    }
                """)
            elif is_checkbox:
                should_check = str(value).lower() in ['true', '1', 'yes', 'checked', '是']
                element.evaluate(f"""
                    el => {{
                        el.checked = {should_check};
                        const changeEvent = new Event('change', {{ bubbles: true }});
                        el.dispatchEvent(changeEvent);
                    }}
                """)
            
            self.anti_detection.random_delay(0.1, 0.2)
            
            actual = self._get_actual_value(element)
            return True, actual
            
        except Exception as e:
            print(f"    [调试] 选择字段填充失败: {e}")
            return False, self._get_actual_value(element)
    
    def _fill_generic_with_verify(self, element, value: str, field_name: str) -> Tuple[bool, str]:
        try:
            self._safe_click(element, field_name)
            self.anti_detection.random_delay(0.1, 0.2)
            
            return self._fill_text_field_with_verify(element, value, field_name)
            
        except Exception as e:
            print(f"    [调试] 通用填充失败: {e}")
            return False, self._get_actual_value(element)
    
    def _values_match(self, actual: str, expected: str) -> bool:
        if not actual and not expected:
            return True
        
        actual_lower = str(actual).lower().strip()
        expected_lower = str(expected).lower().strip()
        
        if actual_lower == expected_lower:
            return True
        
        if expected_lower in actual_lower:
            return True
        
        if actual_lower in expected_lower:
            return True
        
        actual_clean = re.sub(r'[\s\-_./\u4e00-\u9fa5]', '', actual_lower)
        expected_clean = re.sub(r'[\s\-_./\u4e00-\u9fa5]', '', expected_lower)
        
        if actual_clean == expected_clean:
            return True
        
        if len(actual_clean) > 0 and len(expected_clean) > 0:
            if actual_clean in expected_clean or expected_clean in actual_clean:
                return True
        
        return False
    
    def _safe_click(self, element, field_name: str) -> bool:
        click_strategies = [
            ("playwright_click", self._click_playwright),
            ("js_click", self._click_js),
            ("js_dispatch_click", self._click_dispatch_event),
            ("js_focus_only", self._focus_only),
        ]
        
        for strategy_name, strategy_func in click_strategies:
            try:
                success = strategy_func(element)
                if success:
                    if strategy_name != "playwright_click":
                        print(f"  [提示] 使用备用策略 '{strategy_name}' 点击: {field_name}")
                    return True
                self.anti_detection.random_delay(0.05, 0.1)
            except Exception as e:
                print(f"  [调试] 策略 '{strategy_name}' 失败: {e}")
                continue
        
        return False
    
    def _click_playwright(self, element) -> bool:
        try:
            element.click(timeout=3000, force=False)
            return True
        except Exception as click_error:
            error_msg = str(click_error).lower()
            if "intercept" in error_msg or "pointer" in error_msg or "clickable" in error_msg:
                return False
            raise click_error
    
    def _click_js(self, element) -> bool:
        try:
            element.evaluate("el => el.click()")
            return True
        except Exception:
            return False
    
    def _click_dispatch_event(self, element) -> bool:
        try:
            element.evaluate("""
                el => {
                    const events = ['mousedown', 'mouseup', 'click', 'focus'];
                    events.forEach(eventName => {
                        const evt = new MouseEvent(eventName, {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        el.dispatchEvent(evt);
                    });
                    return true;
                }
            """)
            return True
        except Exception:
            return False
    
    def _focus_only(self, element) -> bool:
        try:
            element.evaluate("el => el.focus()")
            return True
        except Exception:
            return False
    
    def _safe_fill_input(self, element, value: str) -> bool:
        fill_strategies = [
            ("playwright_fill", self._fill_playwright),
            ("playwright_type", self._fill_type),
            ("js_set_value", self._fill_js_set_value),
            ("js_set_value_with_events", self._fill_js_with_events),
        ]
        
        for strategy_name, strategy_func in fill_strategies:
            try:
                success = strategy_func(element, value)
                if success:
                    if strategy_name not in ["playwright_fill", "playwright_type"]:
                        pass
                    return True
                self.anti_detection.random_delay(0.05, 0.1)
            except Exception:
                continue
        
        return False
    
    def _fill_playwright(self, element, value: str) -> bool:
        try:
            element.evaluate("el => el.value = ''")
            self.anti_detection.random_delay(0.05, 0.1)
            element.fill(value)
            return True
        except Exception:
            return False
    
    def _fill_type(self, element, value: str) -> bool:
        try:
            element.evaluate("el => el.value = ''")
            self.anti_detection.random_delay(0.05, 0.1)
            self.anti_detection.simulate_human_typing(element, value)
            return True
        except Exception:
            return False
    
    def _fill_js_set_value(self, element, value: str) -> bool:
        try:
            element.evaluate(f"""
                el => {{
                    el.value = '';
                    el.value = {json.dumps(value)};
                    return true;
                }}
            """)
            return True
        except Exception:
            return False
    
    def _fill_js_with_events(self, element, value: str) -> bool:
        try:
            element.evaluate(f"""
                el => {{
                    el.value = '';
                    el.value = {json.dumps(value)};
                    
                    const inputEvent = new Event('input', {{ bubbles: true }});
                    const changeEvent = new Event('change', {{ bubbles: true }});
                    const blurEvent = new Event('blur', {{ bubbles: true }});
                    
                    el.dispatchEvent(inputEvent);
                    el.dispatchEvent(changeEvent);
                    el.dispatchEvent(blurEvent);
                    
                    return true;
                }}
            """)
            return True
        except Exception:
            return False
    
    def _wait_for_overlay(self, element, timeout: int = 5000):
        start_time = time.time()
        overlay_selectors = [
            ".loading",
            ".spinner",
            ".overlay",
            ".modal-backdrop",
            "[class*='loading']",
            "[class*='spinner']",
            "[class*='overlay']",
            ".el-loading-mask",
            ".ant-spin-container",
            ".mask",
            "#loading",
        ]
        
        while time.time() - start_time < timeout / 1000:
            try:
                is_blocked = element.evaluate("""
                    el => {
                        const rect = el.getBoundingClientRect();
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        const topElement = document.elementFromPoint(centerX, centerY);
                        if (topElement && !el.contains(topElement) && topElement !== el) {
                            const computedStyle = window.getComputedStyle(topElement);
                            const pointerEvents = computedStyle.pointerEvents;
                            const zIndex = computedStyle.zIndex;
                            const opacity = computedStyle.opacity;
                            const display = computedStyle.display;
                            const visibility = computedStyle.visibility;
                            
                            if (pointerEvents === 'none' || opacity === '0' || 
                                display === 'none' || visibility === 'hidden') {
                                return false;
                            }
                            
                            if (zIndex && zIndex !== 'auto') {
                                const elZIndex = window.getComputedStyle(el).zIndex;
                                if (parseInt(zIndex) > parseInt(elZIndex || '0')) {
                                    return true;
                                }
                            }
                            return topElement !== el;
                        }
                        return false;
                    }
                """)
                
                if not is_blocked:
                    return
                
                time.sleep(0.1)
                
            except Exception:
                time.sleep(0.1)
        
        for sel in overlay_selectors:
            try:
                overlays = self.page.query_selector_all(sel)
                for overlay in overlays:
                    try:
                        if overlay.is_visible():
                            overlay.evaluate("el => el.style.display = 'none'")
                            print(f"  [提示] 隐藏了遮罩元素: {sel}")
                    except Exception:
                        pass
            except Exception:
                pass
    
    def _fill_date_field(
        self, 
        field_name: str, 
        value: datetime, 
        label_texts: List[str]
    ) -> FillResult:
        located = self.field_locator.locate_field(field_name, label_texts)
        
        if not located:
            return FillResult(
                success=False,
                field_name=field_name,
                value=value,
                error_message=f"无法定位日期字段: {field_name}"
            )
        
        try:
            context = located.frame_context or self.page
            selector = located.selector
            
            self.anti_detection.random_pause_between_actions()
            
            date_config = DatePickerConfig(
                format="%Y-%m-%d",
                use_input_directly=True
            )
            
            success = self.interaction_handler.handle_date_picker(
                selector, value, date_config
            )
            
            if success:
                return FillResult(
                    success=True,
                    field_name=field_name,
                    value=value,
                    selector_used=selector
                )
            else:
                return FillResult(
                    success=False,
                    field_name=field_name,
                    value=value,
                    error_message="日期选择器填充失败",
                    selector_used=selector
                )
            
        except Exception as e:
            return FillResult(
                success=False,
                field_name=field_name,
                value=value,
                error_message=str(e),
                selector_used=located.selector
            )
    
    def _fill_select_field(
        self, 
        field_name: str, 
        value: str, 
        label_texts: List[str]
    ) -> FillResult:
        located = self.field_locator.locate_field(field_name, label_texts)
        
        if not located:
            return FillResult(
                success=False,
                field_name=field_name,
                value=value,
                error_message=f"无法定位选择框字段: {field_name}"
            )
        
        try:
            context = located.frame_context or self.page
            selector = located.selector
            
            self.anti_detection.random_pause_between_actions()
            
            success = self.interaction_handler.handle_select_dropdown(
                selector, label=value
            )
            
            if success:
                return FillResult(
                    success=True,
                    field_name=field_name,
                    value=value,
                    selector_used=selector
                )
            else:
                return self._fill_single_field(field_name, value, label_texts)
            
        except Exception as e:
            return FillResult(
                success=False,
                field_name=field_name,
                value=value,
                error_message=str(e),
                selector_used=located.selector
            )
    
    def _fill_textarea_field(
        self, 
        field_name: str, 
        value: str, 
        label_texts: List[str]
    ) -> FillResult:
        located = self.field_locator.locate_field(field_name, label_texts)
        
        if not located:
            return FillResult(
                success=False,
                field_name=field_name,
                value=value,
                error_message=f"无法定位文本框字段: {field_name}"
            )
        
        try:
            context = located.frame_context or self.page
            selector = located.selector
            
            self.anti_detection.random_pause_between_actions()
            
            success = self.interaction_handler.handle_textarea(
                selector, value, char_by_char=True
            )
            
            if success:
                return FillResult(
                    success=True,
                    field_name=field_name,
                    value=value,
                    selector_used=selector
                )
            else:
                return FillResult(
                    success=False,
                    field_name=field_name,
                    value=value,
                    error_message="文本框填充失败",
                    selector_used=selector
                )
            
        except Exception as e:
            return FillResult(
                success=False,
                field_name=field_name,
                value=value,
                error_message=str(e),
                selector_used=located.selector
            )
    
    def save_form(self) -> bool:
        self.anti_detection.random_pause_between_actions()
        return self.interaction_handler.click_save_button()
    
    def check_for_errors(self) -> List[FormValidationError]:
        return self.form_validator.detect_validation_errors()
    
    def get_fill_results(self) -> List[FillResult]:
        return self._fill_results
    
    def get_progress(self) -> FillProgress:
        return self.progress
    
    def take_debug_screenshot(self, prefix: str = "debug") -> str:
        timestamp = int(time.time())
        filename = f"{prefix}_{timestamp}.png"
        
        if self.page:
            self.page.screenshot(path=filename, full_page=True)
        
        return filename
