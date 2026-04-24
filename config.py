import os
from typing import Dict, List, Optional


class Config:
    BROWSER_HEADLESS = False
    BROWSER_SLOW_MO = 100
    BROWSER_VIEWPORT = {"width": 1920, "height": 1080}
    
    INPUT_DELAY_MIN = 0.1
    INPUT_DELAY_MAX = 0.3
    CLICK_DELAY_MIN = 0.2
    CLICK_DELAY_MAX = 0.5
    PAGE_LOAD_TIMEOUT = 30000
    ELEMENT_WAIT_TIMEOUT = 10000
    
    ANTI_DETECTION_ENABLED = True
    RANDOM_USER_AGENT = True
    RANDOM_VIEWPORT = False
    MOUSE_MOVEMENT_SIMULATION = True
    
    PLATFORM_CONFIGS: Dict[str, Dict] = {
        "liepin": {
            "name": "猎聘",
            "login_url": "https://www.liepin.com/",
            "resume_url": "https://c.liepin.com/resume/editresume.shtml",
            "field_selectors": {}
        },
        "boss": {
            "name": "Boss直聘",
            "login_url": "https://www.zhipin.com/",
            "resume_url": "https://www.zhipin.com/geek/new/index/resume",
            "field_selectors": {}
        }
    }
    
    FIELD_MAPPINGS: Dict[str, List[str]] = {
        "name": ["姓名", "名字", "真实姓名", "name", "fullName", "realName"],
        "phone": ["手机号", "手机号码", "电话", "联系电话", "手机", "phone", "mobile", "telephone"],
        "email": ["邮箱", "电子邮箱", "email", "mail"],
        "gender": ["性别", "gender", "sex"],
        "birthday": ["生日", "出生日期", "出生年月", "birthday", "birthDate"],
        "education": ["学历", "教育程度", "education", "degree"],
        "school": ["学校", "毕业院校", "院校", "school", "university", "college"],
        "major": ["专业", "所学专业", "major"],
        "start_date": ["开始时间", "起始时间", "入学时间", "startDate", "beginDate"],
        "end_date": ["结束时间", "终止时间", "毕业时间", "endDate", "finishDate"],
        "company": ["公司", "公司名称", "企业", "company", "enterprise", "corporation"],
        "position": ["职位", "岗位", "职务", "position", "post", "jobTitle"],
        "work_description": ["工作描述", "工作内容", "职责描述", "workDescription", "jobDescription"],
        "project_name": ["项目名称", "项目名", "projectName", "project"],
        "project_role": ["项目角色", "担任角色", "projectRole", "role"],
        "project_description": ["项目描述", "项目介绍", "projectDescription"],
        "skill": ["技能", "专业技能", "skill", "ability", "expertise"],
        "self_introduction": ["自我介绍", "个人简介", "自我评价", "selfIntroduction", "introduction", "evaluation"]
    }


config = Config()
