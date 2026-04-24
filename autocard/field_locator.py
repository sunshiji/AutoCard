import os
import sys
import re
from typing import Optional, List, Dict, Any, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from models import LocatedField


class FieldLocator:
    LABEL_INPUT_STRATEGIES = [
        ("platform_selector", "平台特定选择器（优先）"),
        ("label_by_text", "通过label文本匹配"),
        ("label_for_attribute", "通过label的for属性匹配"),
        ("aria_labelledby", "通过aria-labelledby匹配"),
        ("placeholder", "通过placeholder匹配"),
        ("name_attribute", "通过name属性匹配"),
        ("id_attribute", "通过id属性匹配"),
        ("preceding_sibling", "通过前兄弟节点文本匹配"),
        ("parent_sibling", "通过父节点的兄弟文本匹配"),
    ]
    
    INPUT_TYPES = {
        "text": ["input[type='text']", "input:not([type])", "textarea"],
        "email": ["input[type='email']"],
        "phone": ["input[type='tel']"],
        "password": ["input[type='password']"],
        "number": ["input[type='number']"],
        "date": ["input[type='date']"],
        "select": ["select"],
        "checkbox": ["input[type='checkbox']"],
        "radio": ["input[type='radio']"],
        "textarea": ["textarea"],
    }
    
    def __init__(self, page, platform_selectors: Dict[str, List[str]] = None):
        self.page = page
        self._frame_contexts = []
        self._cache = {}
        self._platform_selectors = platform_selectors or {}
    
    def set_platform_selectors(self, selectors: Dict[str, List[str]]):
        self._platform_selectors = selectors
        self._cache = {}
    
    def locate_field(self, field_name: str, label_texts: List[str] = None) -> Optional[LocatedField]:
        if label_texts is None:
            label_texts = config.FIELD_MAPPINGS.get(field_name, [field_name])
        
        cache_key = f"{field_name}_{'_'.join(label_texts)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        contexts = [self.page]
        contexts.extend(self._get_all_frame_contexts())
        
        for context in contexts:
            for strategy, _ in self.LABEL_INPUT_STRATEGIES:
                located = self._try_locate_with_strategy(
                    context, field_name, label_texts, strategy
                )
                if located:
                    located.frame_context = context if context != self.page else None
                    self._cache[cache_key] = located
                    return located
        
        return None
    
    def locate_all_fields(self, field_names: List[str]) -> Dict[str, LocatedField]:
        results = {}
        
        for field_name in field_names:
            located = self.locate_field(field_name)
            if located:
                results[field_name] = located
        
        return results
    
    def _try_locate_with_strategy(
        self, 
        context, 
        field_name: str, 
        label_texts: List[str], 
        strategy: str
    ) -> Optional[LocatedField]:
        strategies = {
            "platform_selector": self._locate_by_platform_selector,
            "label_by_text": self._locate_by_label_text,
            "label_for_attribute": self._locate_by_label_for,
            "aria_labelledby": self._locate_by_aria_labelledby,
            "placeholder": self._locate_by_placeholder,
            "name_attribute": self._locate_by_name,
            "id_attribute": self._locate_by_id,
            "preceding_sibling": self._locate_by_preceding_sibling,
            "parent_sibling": self._locate_by_parent_sibling,
        }
        
        if strategy in strategies:
            return strategies[strategy](context, field_name, label_texts)
        
        return None
    
    def _locate_by_platform_selector(self, context, field_name: str, label_texts: List[str]) -> Optional[LocatedField]:
        if not self._platform_selectors:
            return None
        
        selectors = self._platform_selectors.get(field_name, [])
        if not selectors:
            return None
        
        for selector in selectors:
            try:
                elements = context.query_selector_all(selector)
                for element in elements:
                    if self._is_interactive_element(element):
                        return LocatedField(
                            field_name=field_name,
                            selector=selector,
                            label_text=label_texts[0] if label_texts else None,
                            input_type=self._get_input_type(element),
                            element_handle=element,
                            is_required=self._check_required(element)
                        )
            except Exception:
                continue
        
        return None
    
    def _locate_by_label_text(self, context, field_name: str, label_texts: List[str]) -> Optional[LocatedField]:
        for label_text in label_texts:
            escaped_text = self._escape_xpath_text(label_text)
            
            xpath_variants = [
                f"//label[contains(normalize-space(.), {escaped_text})]",
                f"//label[normalize-space(.) = {escaped_text}]",
                f"//*[self::label or self::span or self::div][contains(normalize-space(.), {escaped_text})]",
            ]
            
            for xpath in xpath_variants:
                labels = context.query_selector_all(xpath)
                for label in labels:
                    label_for = label.get_attribute("for")
                    if label_for:
                        input_elem = context.query_selector(f"#{label_for}")
                        if input_elem and self._is_interactive_element(input_elem):
                            return LocatedField(
                                field_name=field_name,
                                selector=f"#{label_for}",
                                label_text=label_text,
                                input_type=self._get_input_type(input_elem),
                                element_handle=input_elem,
                                is_required=self._check_required(input_elem)
                            )
                    
                    parent = label.evaluate_handle("el => el.parentElement")
                    if parent:
                        inputs = parent.as_element().query_selector_all("input, textarea, select")
                        for inp in inputs:
                            if self._is_interactive_element(inp):
                                return LocatedField(
                                    field_name=field_name,
                                    selector=self._generate_selector(inp),
                                    label_text=label_text,
                                    input_type=self._get_input_type(inp),
                                    element_handle=inp,
                                    is_required=self._check_required(inp)
                                )
                    
                    following = label.evaluate_handle("""
                        el => {
                            let next = el.nextElementSibling;
                            while (next) {
                                if (next.tagName.match(/^(INPUT|TEXTAREA|SELECT)$/i)) {
                                    return next;
                                }
                                let input = next.querySelector('input, textarea, select');
                                if (input) return input;
                                next = next.nextElementSibling;
                            }
                            return null;
                        }
                    """)
                    
                    if following and following.as_element():
                        elem = following.as_element()
                        if self._is_interactive_element(elem):
                            return LocatedField(
                                field_name=field_name,
                                selector=self._generate_selector(elem),
                                label_text=label_text,
                                input_type=self._get_input_type(elem),
                                element_handle=elem,
                                is_required=self._check_required(elem)
                            )
        
        return None
    
    def _locate_by_label_for(self, context, field_name: str, label_texts: List[str]) -> Optional[LocatedField]:
        for label_text in label_texts:
            escaped_text = self._escape_xpath_text(label_text)
            
            labels = context.query_selector_all(f"//label[contains(normalize-space(.), {escaped_text})]")
            for label in labels:
                label_for = label.get_attribute("for")
                if label_for:
                    input_elem = context.query_selector(f"[id='{label_for}']")
                    if input_elem and self._is_interactive_element(input_elem):
                        return LocatedField(
                            field_name=field_name,
                            selector=f"[id='{label_for}']",
                            label_text=label_text,
                            input_type=self._get_input_type(input_elem),
                            element_handle=input_elem,
                            is_required=self._check_required(input_elem)
                        )
        
        return None
    
    def _locate_by_aria_labelledby(self, context, field_name: str, label_texts: List[str]) -> Optional[LocatedField]:
        inputs = context.query_selector_all("input[aria-labelledby], textarea[aria-labelledby], select[aria-labelledby]")
        
        for inp in inputs:
            labelledby = inp.get_attribute("aria-labelledby")
            if labelledby:
                label_elem = context.query_selector(f"#{labelledby}")
                if label_elem:
                    label_text = label_elem.text_content() or ""
                    label_text = label_text.strip()
                    
                    for target_text in label_texts:
                        if self._text_matches(label_text, target_text):
                            return LocatedField(
                                field_name=field_name,
                                selector=self._generate_selector(inp),
                                label_text=label_text,
                                input_type=self._get_input_type(inp),
                                element_handle=inp,
                                is_required=self._check_required(inp)
                            )
        
        return None
    
    def _locate_by_placeholder(self, context, field_name: str, label_texts: List[str]) -> Optional[LocatedField]:
        inputs = context.query_selector_all("input[placeholder], textarea[placeholder]")
        
        for inp in inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            placeholder = placeholder.strip()
            
            for target_text in label_texts:
                if self._text_matches(placeholder, target_text):
                    return LocatedField(
                        field_name=field_name,
                        selector=self._generate_selector(inp),
                        label_text=placeholder,
                        input_type=self._get_input_type(inp),
                        element_handle=inp,
                        is_required=self._check_required(inp)
                    )
        
        return None
    
    def _locate_by_name(self, context, field_name: str, label_texts: List[str]) -> Optional[LocatedField]:
        name_patterns = [
            field_name.lower(),
            field_name.replace('_', ''),
            field_name.replace('_', '-'),
        ]
        
        name_patterns.extend([t.lower() for t in label_texts])
        
        for pattern in name_patterns:
            inputs = context.query_selector_all(f"input[name*='{pattern}'], textarea[name*='{pattern}'], select[name*='{pattern}']")
            for inp in inputs:
                name = (inp.get_attribute("name") or "").lower()
                if pattern in name:
                    return LocatedField(
                        field_name=field_name,
                        selector=self._generate_selector(inp),
                        input_type=self._get_input_type(inp),
                        element_handle=inp,
                        is_required=self._check_required(inp)
                    )
        
        return None
    
    def _locate_by_id(self, context, field_name: str, label_texts: List[str]) -> Optional[LocatedField]:
        id_patterns = [
            field_name.lower(),
            field_name.replace('_', ''),
            field_name.replace('_', '-'),
        ]
        
        id_patterns.extend([t.lower() for t in label_texts])
        
        for pattern in id_patterns:
            inputs = context.query_selector_all(f"input[id*='{pattern}'], textarea[id*='{pattern}'], select[id*='{pattern}']")
            for inp in inputs:
                elem_id = (inp.get_attribute("id") or "").lower()
                if pattern in elem_id:
                    return LocatedField(
                        field_name=field_name,
                        selector=self._generate_selector(inp),
                        input_type=self._get_input_type(inp),
                        element_handle=inp,
                        is_required=self._check_required(inp)
                    )
        
        return None
    
    def _locate_by_preceding_sibling(self, context, field_name: str, label_texts: List[str]) -> Optional[LocatedField]:
        inputs = context.query_selector_all("input, textarea, select")
        
        for inp in inputs:
            preceding_text = inp.evaluate("""
                el => {
                    let texts = [];
                    let prev = el.previousElementSibling;
                    while (prev) {
                        if (prev.textContent) {
                            texts.push(prev.textContent.trim());
                        }
                        prev = prev.previousElementSibling;
                    }
                    return texts.join(' ');
                }
            """)
            
            if preceding_text:
                for target_text in label_texts:
                    if self._text_matches(preceding_text, target_text):
                        return LocatedField(
                            field_name=field_name,
                            selector=self._generate_selector(inp),
                            label_text=preceding_text[:50],
                            input_type=self._get_input_type(inp),
                            element_handle=inp,
                            is_required=self._check_required(inp)
                        )
        
        return None
    
    def _locate_by_parent_sibling(self, context, field_name: str, label_texts: List[str]) -> Optional[LocatedField]:
        inputs = context.query_selector_all("input, textarea, select")
        
        for inp in inputs:
            parent_label = inp.evaluate("""
                el => {
                    let parent = el.parentElement;
                    let texts = [];
                    
                    while (parent) {
                        let prev = parent.previousElementSibling;
                        while (prev) {
                            if (prev.textContent) {
                                texts.push(prev.textContent.trim());
                            }
                            prev = prev.previousElementSibling;
                        }
                        
                        let children = parent.querySelectorAll(':scope > label, :scope > span, :scope > div');
                        for (let child of children) {
                            if (child.textContent) {
                                texts.push(child.textContent.trim());
                            }
                        }
                        
                        parent = parent.parentElement;
                    }
                    
                    return texts.join(' ');
                }
            """)
            
            if parent_label:
                for target_text in label_texts:
                    if self._text_matches(parent_label, target_text):
                        return LocatedField(
                            field_name=field_name,
                            selector=self._generate_selector(inp),
                            label_text=parent_label[:50] if parent_label else None,
                            input_type=self._get_input_type(inp),
                            element_handle=inp,
                            is_required=self._check_required(inp)
                        )
        
        return None
    
    def _get_all_frame_contexts(self):
        contexts = []
        
        def collect_frames(frames):
            for frame in frames:
                contexts.append(frame)
                if frame.child_frames:
                    collect_frames(frame.child_frames)
        
        if self.page:
            collect_frames(self.page.frames)
        
        return contexts
    
    def _escape_xpath_text(self, text: str) -> str:
        if "'" in text and '"' in text:
            parts = text.split("'")
            escaped = ", \"'\", ".join(f"'{p}'" for p in parts)
            return f"concat({escaped})"
        elif "'" in text:
            return f'"{text}"'
        else:
            return f"'{text}'"
    
    def _text_matches(self, source: str, target: str) -> bool:
        source_lower = source.lower()
        target_lower = target.lower()
        
        if target_lower == source_lower:
            return True
        
        if target_lower in source_lower:
            return True
        
        if source_lower in target_lower:
            return True
        
        return False
    
    def _is_interactive_element(self, element) -> bool:
        tag_name = element.evaluate("el => el.tagName.toLowerCase()")
        
        interactive_tags = ['input', 'textarea', 'select']
        
        if tag_name in interactive_tags:
            input_type = element.get_attribute("type") or ""
            input_type = input_type.lower()
            
            hidden_types = ['hidden', 'submit', 'reset', 'button']
            if input_type in hidden_types:
                return False
            
            return True
        
        return False
    
    def _get_input_type(self, element) -> str:
        tag_name = element.evaluate("el => el.tagName.toLowerCase()")
        
        if tag_name == 'textarea':
            return 'textarea'
        elif tag_name == 'select':
            return 'select'
        elif tag_name == 'input':
            input_type = element.get_attribute("type") or "text"
            input_type = input_type.lower()
            
            if input_type in ['text', 'email', 'tel', 'password', 'number', 'date', 'checkbox', 'radio']:
                return input_type
            
            return 'text'
        
        return 'text'
    
    def _check_required(self, element) -> bool:
        required = element.get_attribute("required")
        if required is not None:
            return True
        
        aria_required = element.get_attribute("aria-required")
        if aria_required and aria_required.lower() == 'true':
            return True
        
        parent_class = element.evaluate("el => el.parentElement?.className || ''")
        if 'required' in parent_class.lower():
            return True
        
        return False
    
    def _generate_selector(self, element) -> str:
        elem_id = element.get_attribute("id")
        if elem_id and not elem_id.startswith("__"):
            if self._is_valid_css_id(elem_id):
                return f"#{elem_id}"
            else:
                tag_name = element.evaluate("el => el.tagName.toLowerCase()")
                return f"{tag_name}[id='{elem_id}']"
        
        name = element.get_attribute("name")
        if name:
            tag_name = element.evaluate("el => el.tagName.toLowerCase()")
            return f"{tag_name}[name='{name}']"
        
        placeholder = element.get_attribute("placeholder")
        if placeholder:
            tag_name = element.evaluate("el => el.tagName.toLowerCase()")
            return f"{tag_name}[placeholder='{placeholder}']"
        
        css_path = element.evaluate("""
            el => {
                const path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.tagName.toLowerCase();
                    if (el.id) {
                        const idStr = el.id;
                        if (/^[a-zA-Z_-][a-zA-Z0-9_-]*$/.test(idStr)) {
                            selector += '#' + idStr;
                        } else {
                            selector += '[id="' + idStr + '"]';
                        }
                        path.unshift(selector);
                        break;
                    } else {
                        let sibling = el;
                        let nth = 1;
                        while (sibling = sibling.previousElementSibling) {
                            if (sibling.tagName.toLowerCase() === selector) nth++;
                        }
                        if (nth > 1) selector += ':nth-of-type(' + nth + ')';
                    }
                    path.unshift(selector);
                    el = el.parentNode;
                }
                return path.join(' > ');
            }
        """)
        
        return css_path or "input"
    
    def _is_valid_css_id(self, id_str: str) -> bool:
        if not id_str:
            return False
        if id_str[0].isdigit():
            return False
        if not re.match(r'^[a-zA-Z_-][a-zA-Z0-9_-]*$', id_str):
            return False
        return True
    
    def clear_cache(self):
        self._cache = {}
