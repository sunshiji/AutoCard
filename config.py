import os
import platform
from typing import Dict, List, Optional


class Config:
    BROWSER_HEADLESS = False
    BROWSER_SLOW_MO = 100
    BROWSER_VIEWPORT = {"width": 1920, "height": 1080}
    
    BROWSER_TYPE = "chromium"
    BROWSER_EXECUTABLE_PATH = None
    BROWSER_USER_DATA_DIR = None
    
    USE_CDP = False
    CDP_ENDPOINT = "http://localhost:9222"
    
    USE_SELENIUM = False
    SELENIUM_DRIVER_PATH = None
    
    MIRROR_CONFIG = {
        "playwright": {
            "china": {
                "PLAYWRIGHT_DOWNLOAD_HOST": "https://npmmirror.com/mirrors/playwright",
                "PLAYWRIGHT_DOWNLOAD_HOST_CN": "https://cdn.npmmirror.com/binaries/playwright"
            }
        },
        "selenium": {
            "chrome_driver_mirror": "https://npmmirror.com/mirrors/chromedriver",
            "edge_driver_mirror": "https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"
        }
    }
    
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
        },
        "beisen": {
            "name": "北森招聘系统",
            "login_url": "",
            "resume_url": "",
            "field_selectors": {
                "name": ["input[name*='name']", "input[name*='realName']", "input[name*='username']", "input[placeholder*='姓名']"],
                "phone": ["input[name*='phone']", "input[name*='mobile']", "input[name*='telephone']", "input[placeholder*='手机']"],
                "email": ["input[name*='email']", "input[name*='mail']", "input[placeholder*='邮箱']"],
                "gender": ["select[name*='gender']", "select[name*='sex']", "input[name*='gender'][type='radio']"],
                "birthday": ["input[name*='birthday']", "input[name*='birthDate']", "input[placeholder*='生日']"],
                "school": ["input[name*='school']", "input[name*='university']", "input[name*='college']", "input[placeholder*='学校']"],
                "major": ["input[name*='major']", "input[placeholder*='专业']"],
                "education": ["select[name*='education']", "select[name*='degree']"],
                "company": ["input[name*='company']", "input[name*='enterprise']", "input[placeholder*='公司']"],
                "position": ["input[name*='position']", "input[name*='post']", "input[name*='jobTitle']"],
                "start_date": ["input[name*='startDate']", "input[name*='beginDate']", "input[placeholder*='开始']"],
                "end_date": ["input[name*='endDate']", "input[name*='finishDate']", "input[placeholder*='结束']"],
            },
            "login_indicators": [
                "text:登录",
                "text:扫码登录",
                "text:微信登录",
                "selector:input[type='password']",
                "selector:button:has-text('登录')",
            ],
            "logged_in_indicators": [
                "text:退出",
                "text:注销",
                "text:我的简历",
                "selector:.avatar",
                "selector:.user-info",
            ]
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


def get_system_chrome_path() -> Optional[str]:
    system = platform.system()
    
    if system == "Windows":
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                return path
    
    elif system == "Darwin":
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                return path
    
    elif system == "Linux":
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/microsoft-edge",
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                return path
    
    return None


def get_default_user_data_dir() -> Optional[str]:
    system = platform.system()
    
    if system == "Windows":
        return os.path.expandvars(r"%LocalAppData%\Google\Chrome\User Data")
    elif system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif system == "Linux":
        return os.path.expanduser("~/.config/google-chrome")
    
    return None

