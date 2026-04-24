import os
import sys
import random
import time
import re
from typing import Optional, List, Dict, Any, Callable
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
            
            element.scroll_into_view_if_needed()
            self.anti_detection.random_delay(0.1, 0.3)
            
            try:
                element.click(timeout=5000)
            except Exception as click_error:
                if "intercept" in str(click_error).lower() or "pointer" in str(click_error).lower():
                    print(f"  [提示] 点击被拦截，尝试使用JavaScript点击: {field_name}")
                    element.evaluate("el => el.click()")
                else:
                    raise click_error
            
            self.anti_detection.random_delay(0.1, 0.2)
            
            element.evaluate("el => el.value = ''")
            self.anti_detection.random_delay(0.05, 0.1)
            
            self.anti_detection.simulate_human_typing(element, str(value))
            
            self.anti_detection.random_delay(0.1, 0.2)
            
            return FillResult(
                success=True,
                field_name=field_name,
                value=value,
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
