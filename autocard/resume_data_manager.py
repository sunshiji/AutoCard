import os
import sys
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    ResumeData, PersonalInfo, EducationExperience,
    WorkExperience, ProjectExperience
)


class ResumeDataManager:
    DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    DEFAULT_DATA_FILE = "resume_data.json"
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or self.DEFAULT_DATA_DIR
        self.data_file = os.path.join(self.data_dir, self.DEFAULT_DATA_FILE)
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
    
    def _datetime_to_str(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        return dt.strftime("%Y-%m-%d")
    
    def _str_to_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m")
            except ValueError:
                return None
    
    def resume_data_to_dict(self, resume_data: ResumeData) -> Dict[str, Any]:
        data = {
            "personal_info": {
                "name": resume_data.personal_info.name,
                "phone": resume_data.personal_info.phone,
                "email": resume_data.personal_info.email,
                "gender": resume_data.personal_info.gender,
                "birthday": self._datetime_to_str(resume_data.personal_info.birthday) if resume_data.personal_info.birthday else None,
                "current_address": resume_data.personal_info.current_address,
                "work_years": resume_data.personal_info.work_years,
                "current_salary": resume_data.personal_info.current_salary,
                "expected_salary": resume_data.personal_info.expected_salary,
                "job_status": resume_data.personal_info.job_status,
                "self_introduction": resume_data.personal_info.self_introduction,
            },
            "education_experiences": [],
            "work_experiences": [],
            "project_experiences": [],
            "skills": resume_data.skills,
        }
        
        for exp in resume_data.education_experiences:
            data["education_experiences"].append({
                "school": exp.school,
                "major": exp.major,
                "education": exp.education,
                "start_date": self._datetime_to_str(exp.start_date),
                "end_date": self._datetime_to_str(exp.end_date),
                "description": exp.description,
            })
        
        for exp in resume_data.work_experiences:
            data["work_experiences"].append({
                "company": exp.company,
                "position": exp.position,
                "industry": exp.industry,
                "start_date": self._datetime_to_str(exp.start_date),
                "end_date": self._datetime_to_str(exp.end_date),
                "description": exp.description,
                "salary": exp.salary,
            })
        
        for exp in resume_data.project_experiences:
            data["project_experiences"].append({
                "project_name": exp.project_name,
                "role": exp.role,
                "start_date": self._datetime_to_str(exp.start_date),
                "end_date": self._datetime_to_str(exp.end_date),
                "description": exp.description,
                "technologies": exp.technologies,
            })
        
        return data
    
    def dict_to_resume_data(self, data: Dict[str, Any]) -> ResumeData:
        resume_data = ResumeData()
        
        personal_info = data.get("personal_info", {})
        resume_data.personal_info = PersonalInfo(
            name=personal_info.get("name"),
            phone=personal_info.get("phone"),
            email=personal_info.get("email"),
            gender=personal_info.get("gender"),
            birthday=self._str_to_datetime(personal_info.get("birthday")),
            current_address=personal_info.get("current_address"),
            work_years=personal_info.get("work_years"),
            current_salary=personal_info.get("current_salary"),
            expected_salary=personal_info.get("expected_salary"),
            job_status=personal_info.get("job_status"),
            self_introduction=personal_info.get("self_introduction"),
        )
        
        for exp_data in data.get("education_experiences", []):
            exp = EducationExperience(
                school=exp_data.get("school"),
                major=exp_data.get("major"),
                education=exp_data.get("education"),
                start_date=self._str_to_datetime(exp_data.get("start_date")),
                end_date=self._str_to_datetime(exp_data.get("end_date")),
                description=exp_data.get("description"),
            )
            resume_data.education_experiences.append(exp)
        
        for exp_data in data.get("work_experiences", []):
            exp = WorkExperience(
                company=exp_data.get("company"),
                position=exp_data.get("position"),
                industry=exp_data.get("industry"),
                start_date=self._str_to_datetime(exp_data.get("start_date")),
                end_date=self._str_to_datetime(exp_data.get("end_date")),
                description=exp_data.get("description"),
                salary=exp_data.get("salary"),
            )
            resume_data.work_experiences.append(exp)
        
        for exp_data in data.get("project_experiences", []):
            exp = ProjectExperience(
                project_name=exp_data.get("project_name"),
                role=exp_data.get("role"),
                start_date=self._str_to_datetime(exp_data.get("start_date")),
                end_date=self._str_to_datetime(exp_data.get("end_date")),
                description=exp_data.get("description"),
                technologies=exp_data.get("technologies"),
            )
            resume_data.project_experiences.append(exp)
        
        resume_data.skills = data.get("skills", [])
        
        return resume_data
    
    def save_to_json(self, resume_data: ResumeData, file_path: str = None) -> str:
        save_path = file_path or self.data_file
        data = self.resume_data_to_dict(resume_data)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 简历数据已保存到: {save_path}")
        return save_path
    
    def load_from_json(self, file_path: str = None) -> Optional[ResumeData]:
        load_path = file_path or self.data_file
        
        if not os.path.exists(load_path):
            print(f"⚠ 数据文件不存在: {load_path}")
            return None
        
        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            resume_data = self.dict_to_resume_data(data)
            print(f"\n✓ 已从 {load_path} 加载简历数据")
            return resume_data
        except Exception as e:
            print(f"✗ 加载数据失败: {e}")
            return None
    
    def has_saved_data(self, file_path: str = None) -> bool:
        check_path = file_path or self.data_file
        return os.path.exists(check_path)
    
    def manual_input(self, existing_data: ResumeData = None) -> ResumeData:
        print("\n" + "=" * 60)
        print("手动录入简历数据")
        print("=" * 60)
        print("\n提示：")
        print("  - 直接按回车键跳过可选字段")
        print("  - 日期格式：YYYY-MM 或 YYYY-MM-DD（如 2020-06 或 2020-06-15）")
        print("\n" + "-" * 60)
        
        resume_data = existing_data or ResumeData()
        
        print("\n【个人信息】")
        print("-" * 40)
        
        default_name = resume_data.personal_info.name or ""
        resume_data.personal_info.name = self._input_with_default("姓名 *", default_name, required=True)
        
        default_phone = resume_data.personal_info.phone or ""
        resume_data.personal_info.phone = self._input_with_default("手机号 *", default_phone, required=True)
        
        default_email = resume_data.personal_info.email or ""
        resume_data.personal_info.email = self._input_with_default("邮箱 *", default_email, required=True)
        
        default_gender = resume_data.personal_info.gender or ""
        resume_data.personal_info.gender = self._input_with_default("性别 (男/女)", default_gender)
        
        default_birthday = self._datetime_to_str(resume_data.personal_info.birthday) or ""
        birthday_str = self._input_with_default("出生日期", default_birthday)
        if birthday_str:
            resume_data.personal_info.birthday = self._str_to_datetime(birthday_str)
        
        default_intro = resume_data.personal_info.self_introduction or ""
        print(f"\n自我介绍（多行输入，输入空行结束，当前: {len(default_intro)} 字符）:")
        intro_lines = []
        while True:
            line = input()
            if not line.strip():
                break
            intro_lines.append(line)
        if intro_lines:
            resume_data.personal_info.self_introduction = "\n".join(intro_lines)
        elif default_intro:
            resume_data.personal_info.self_introduction = default_intro
        
        print("\n【教育经历】")
        print("-" * 40)
        
        if resume_data.education_experiences:
            print(f"已存在 {len(resume_data.education_experiences)} 条教育经历")
            use_existing = input("是否保留现有教育经历？(y/n): ").strip().lower()
            if use_existing != 'y':
                resume_data.education_experiences = []
        
        while True:
            add_more = input("\n是否添加教育经历？(y/n): ").strip().lower()
            if add_more != 'y':
                break
            
            exp = EducationExperience()
            print("\n--- 教育经历 ---")
            exp.school = self._input_with_default("学校名称", "", required=True)
            exp.major = self._input_with_default("专业", "")
            exp.education = self._input_with_default("学历 (如：本科、硕士)", "")
            
            start_str = self._input_with_default("开始时间 (YYYY-MM)", "")
            if start_str:
                exp.start_date = self._str_to_datetime(start_str)
            
            end_str = self._input_with_default("结束时间 (YYYY-MM，至今则留空)", "")
            if end_str:
                exp.end_date = self._str_to_datetime(end_str)
            
            resume_data.education_experiences.append(exp)
        
        print("\n【工作经历】")
        print("-" * 40)
        
        if resume_data.work_experiences:
            print(f"已存在 {len(resume_data.work_experiences)} 条工作经历")
            use_existing = input("是否保留现有工作经历？(y/n): ").strip().lower()
            if use_existing != 'y':
                resume_data.work_experiences = []
        
        while True:
            add_more = input("\n是否添加工作经历？(y/n): ").strip().lower()
            if add_more != 'y':
                break
            
            exp = WorkExperience()
            print("\n--- 工作经历 ---")
            exp.company = self._input_with_default("公司名称", "", required=True)
            exp.position = self._input_with_default("职位", "", required=True)
            exp.industry = self._input_with_default("行业", "")
            
            start_str = self._input_with_default("开始时间 (YYYY-MM)", "")
            if start_str:
                exp.start_date = self._str_to_datetime(start_str)
            
            end_str = self._input_with_default("结束时间 (YYYY-MM，至今则留空)", "")
            if end_str:
                exp.end_date = self._str_to_datetime(end_str)
            
            print("工作描述（多行输入，输入空行结束）:")
            desc_lines = []
            while True:
                line = input()
                if not line.strip():
                    break
                desc_lines.append(line)
            if desc_lines:
                exp.description = "\n".join(desc_lines)
            
            resume_data.work_experiences.append(exp)
        
        print("\n【项目经历】")
        print("-" * 40)
        
        if resume_data.project_experiences:
            print(f"已存在 {len(resume_data.project_experiences)} 条项目经历")
            use_existing = input("是否保留现有项目经历？(y/n): ").strip().lower()
            if use_existing != 'y':
                resume_data.project_experiences = []
        
        while True:
            add_more = input("\n是否添加项目经历？(y/n): ").strip().lower()
            if add_more != 'y':
                break
            
            exp = ProjectExperience()
            print("\n--- 项目经历 ---")
            exp.project_name = self._input_with_default("项目名称", "", required=True)
            exp.role = self._input_with_default("担任角色", "")
            
            start_str = self._input_with_default("开始时间 (YYYY-MM)", "")
            if start_str:
                exp.start_date = self._str_to_datetime(start_str)
            
            end_str = self._input_with_default("结束时间 (YYYY-MM，至今则留空)", "")
            if end_str:
                exp.end_date = self._str_to_datetime(end_str)
            
            print("项目描述（多行输入，输入空行结束）:")
            desc_lines = []
            while True:
                line = input()
                if not line.strip():
                    break
                desc_lines.append(line)
            if desc_lines:
                exp.description = "\n".join(desc_lines)
            
            tech_str = self._input_with_default("技术栈（用顿号、逗号或空格分隔）", "")
            if tech_str:
                import re
                exp.technologies = [t.strip() for t in re.split(r'[,，、\s]+', tech_str) if t.strip()]
            
            resume_data.project_experiences.append(exp)
        
        print("\n【技能】")
        print("-" * 40)
        
        default_skills = "、".join(resume_data.skills) if resume_data.skills else ""
        skills_str = self._input_with_default("技能列表（用顿号、逗号或空格分隔）", default_skills)
        if skills_str:
            import re
            resume_data.skills = [s.strip() for s in re.split(r'[,，、\s]+', skills_str) if s.strip()]
        
        print("\n" + "=" * 60)
        print("录入完成！")
        print("=" * 60)
        self._print_resume_summary(resume_data)
        
        save_choice = input("\n是否保存数据到本地？(y/n): ").strip().lower()
        if save_choice == 'y':
            custom_path = input(f"保存路径（直接回车使用默认: {self.data_file}）: ").strip()
            save_path = custom_path if custom_path else None
            self.save_to_json(resume_data, save_path)
        
        return resume_data
    
    def _input_with_default(self, prompt: str, default: str, required: bool = False) -> str:
        if default:
            display_prompt = f"{prompt} [{default}]: "
        else:
            display_prompt = f"{prompt}: "
        
        while True:
            user_input = input(display_prompt).strip()
            if user_input:
                return user_input
            if default:
                return default
            if not required:
                return ""
            print("  ⚠ 此字段为必填项，请输入内容")
    
    def _print_resume_summary(self, resume_data: ResumeData):
        print("\n简历数据摘要:")
        print(f"  - 姓名: {resume_data.personal_info.name or '未填写'}")
        print(f"  - 手机: {resume_data.personal_info.phone or '未填写'}")
        print(f"  - 邮箱: {resume_data.personal_info.email or '未填写'}")
        print(f"  - 教育经历: {len(resume_data.education_experiences)} 条")
        print(f"  - 工作经历: {len(resume_data.work_experiences)} 条")
        print(f"  - 项目经历: {len(resume_data.project_experiences)} 条")
        print(f"  - 技能: {len(resume_data.skills)} 个")
