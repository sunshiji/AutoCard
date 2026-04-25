from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date


@dataclass
class PersonalInfo:
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    current_address: Optional[str] = None
    work_years: Optional[str] = None
    current_salary: Optional[str] = None
    expected_salary: Optional[str] = None
    job_status: Optional[str] = None
    self_introduction: Optional[str] = None


@dataclass
class EducationExperience:
    school: Optional[str] = None
    major: Optional[str] = None
    education: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


@dataclass
class WorkExperience:
    company: Optional[str] = None
    position: Optional[str] = None
    industry: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    salary: Optional[str] = None


@dataclass
class ProjectExperience:
    project_name: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None


@dataclass
class ResumeData:
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)
    education_experiences: List[EducationExperience] = field(default_factory=list)
    work_experiences: List[WorkExperience] = field(default_factory=list)
    project_experiences: List[ProjectExperience] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldLocatorConfig:
    field_name: str
    label_texts: List[str]
    selectors: List[str]
    input_type: str = "text"
    required: bool = False
    platform_specific: Dict[str, str] = field(default_factory=dict)


@dataclass
class LocatedField:
    field_name: str
    selector: str
    label_text: Optional[str] = None
    input_type: str = "text"
    element_handle: Any = None
    is_required: bool = False
    frame_context: Any = None


@dataclass
class FillResult:
    success: bool
    field_name: str
    value: Any
    error_message: Optional[str] = None
    selector_used: Optional[str] = None


@dataclass
class FormValidationError:
    field_name: str
    error_message: str
    element_selector: Optional[str] = None
