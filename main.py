import os
import sys
import argparse
import time
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config, get_default_user_data_dir
from models import ResumeData
from autocard.resume_parser import ResumeParser
from autocard.browser_manager import BrowserManager, BrowserConfig
from autocard.form_filler import FormFiller
from autocard.anti_detection import AntiDetection


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="AutoCard - 自动化简历填写脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:

  基本用法:
    python main.py --resume resume.pdf --url "https://example.com/resume/edit"

  使用系统已安装的 Chrome/Edge (推荐，无需额外下载):
    python main.py --resume resume.pdf --url "xxx" --use-system-browser

  使用用户数据目录 (保持登录状态，不用每次登录):
    python main.py --resume resume.pdf --url "xxx" --user-data-dir

  指定浏览器路径:
    python main.py --resume resume.pdf --url "xxx" --browser-path "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

  通过 CDP 连接已运行的浏览器:
    1. 先启动 Chrome: chrome.exe --remote-debugging-port=9222
    2. 然后运行: python main.py --resume resume.pdf --url "xxx" --cdp

  使用国内镜像安装 Playwright 浏览器 (如需要):
    Windows CMD:
      set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
      playwright install chromium

    Windows PowerShell:
      $env:PLAYWRIGHT_DOWNLOAD_HOST='https://npmmirror.com/mirrors/playwright'
      playwright install chromium
        """
    )
    
    parser.add_argument(
        "--resume", "-r",
        required=True,
        help="简历文件路径 (支持 .pdf, .docx)"
    )
    
    parser.add_argument(
        "--url", "-u",
        help="简历填写页面URL"
    )
    
    parser.add_argument(
        "--platform", "-p",
        choices=["liepin", "boss", "custom"],
        default="custom",
        help="目标平台 (liepin=猎聘, boss=Boss直聘, custom=自定义)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行浏览器"
    )
    
    parser.add_argument(
        "--slow-mo",
        type=int,
        default=100,
        help="操作延迟(毫秒)，默认100"
    )
    
    parser.add_argument(
        "--no-anti-detection",
        action="store_true",
        help="禁用反检测措施"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="调试模式，遇到错误时暂停"
    )
    
    browser_group = parser.add_argument_group("浏览器选项")
    
    browser_group.add_argument(
        "--use-system-browser",
        action="store_true",
        default=True,
        help="使用系统已安装的 Chrome/Edge 浏览器 (默认: True)"
    )
    
    browser_group.add_argument(
        "--no-system-browser",
        action="store_true",
        help="禁用系统浏览器，强制使用 Playwright 内置浏览器"
    )
    
    browser_group.add_argument(
        "--browser-path",
        type=str,
        help="指定浏览器可执行文件路径"
    )
    
    browser_group.add_argument(
        "--browser-type",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="浏览器类型 (默认: chromium)"
    )
    
    browser_group.add_argument(
        "--user-data-dir",
        nargs="?",
        const="default",
        help="使用用户数据目录 (保持登录状态)。可指定路径，或使用 'default' 使用默认路径"
    )
    
    cdp_group = parser.add_argument_group("CDP 连接选项")
    
    cdp_group.add_argument(
        "--cdp",
        action="store_true",
        help="通过 CDP 协议连接已运行的浏览器"
    )
    
    cdp_group.add_argument(
        "--cdp-endpoint",
        type=str,
        default="http://localhost:9222",
        help="CDP 端点地址 (默认: http://localhost:9222)"
    )
    
    return parser.parse_args()


def get_platform_url(platform: str) -> Optional[str]:
    platform_configs = config.PLATFORM_CONFIGS
    
    if platform in platform_configs:
        return platform_configs[platform].get("resume_url")
    
    return None


class LoginDetector:
    LOGIN_INDICATORS = [
        {"type": "text", "value": "登录", "description": "页面包含'登录'文字"},
        {"type": "text", "value": "扫码登录", "description": "页面包含'扫码登录'文字"},
        {"type": "text", "value": "微信登录", "description": "页面包含'微信登录'文字"},
        {"type": "text", "value": "账号密码", "description": "页面包含'账号密码'文字"},
        {"type": "selector", "value": "input[type='password']", "description": "页面包含密码输入框"},
        {"type": "selector", "value": "input[name*='password']", "description": "页面包含密码相关输入框"},
        {"type": "selector", "value": "button:has-text('登录')", "description": "页面包含登录按钮"},
        {"type": "selector", "value": "a:has-text('登录')", "description": "页面包含登录链接"},
        {"type": "class_pattern", "value": "login", "description": "页面class包含login"},
        {"type": "url_pattern", "value": "login", "description": "URL包含login"},
    ]
    
    LOGGED_IN_INDICATORS = [
        {"type": "text", "value": "退出", "description": "页面包含'退出'文字"},
        {"type": "text", "value": "注销", "description": "页面包含'注销'文字"},
        {"type": "text", "value": "个人中心", "description": "页面包含'个人中心'文字"},
        {"type": "text", "value": "我的简历", "description": "页面包含'我的简历'文字"},
        {"type": "selector", "value": "img[alt*='头像']", "description": "页面包含用户头像"},
        {"type": "selector", "value": ".avatar", "description": "页面包含头像元素"},
        {"type": "selector", "value": ".user-info", "description": "页面包含用户信息"},
    ]
    
    def __init__(self, page):
        self.page = page
    
    def check_login_required(self) -> bool:
        current_url = self.page.url
        page_content = self.page.content()
        
        for indicator in self.LOGIN_INDICATORS:
            if indicator["type"] == "url_pattern":
                if indicator["value"].lower() in current_url.lower():
                    print(f"  [检测] URL包含登录特征: {current_url}")
                    return True
            elif indicator["type"] == "text":
                if indicator["value"] in page_content:
                    print(f"  [检测] 页面包含登录相关文字: '{indicator['value']}'")
                    return True
            elif indicator["type"] == "selector":
                try:
                    element = self.page.query_selector(indicator["value"])
                    if element:
                        print(f"  [检测] 页面包含登录元素: {indicator['value']}")
                        return True
                except Exception:
                    pass
            elif indicator["type"] == "class_pattern":
                try:
                    elements = self.page.query_selector_all(f"[class*='{indicator['value']}']")
                    if elements:
                        print(f"  [检测] 页面包含登录相关class: {indicator['value']}")
                        return True
                except Exception:
                    pass
        
        return False
    
    def check_logged_in(self) -> bool:
        page_content = self.page.content()
        
        for indicator in self.LOGGED_IN_INDICATORS:
            if indicator["type"] == "text":
                if indicator["value"] in page_content:
                    print(f"  [检测] 检测到已登录状态: 包含'{indicator['value']}'")
                    return True
            elif indicator["type"] == "selector":
                try:
                    element = self.page.query_selector(indicator["value"])
                    if element and element.is_visible():
                        print(f"  [检测] 检测到已登录元素: {indicator['value']}")
                        return True
                except Exception:
                    pass
        
        return False
    
    def wait_for_login(self, timeout: int = 300) -> bool:
        print("\n" + "=" * 60)
        print("等待用户登录...")
        print("=" * 60)
        print("\n请在浏览器中完成登录操作：")
        print("  1. 使用微信扫码或账号密码登录")
        print("  2. 登录成功后系统会自动检测并继续")
        print("  3. 如需手动继续，请按回车键")
        print("\n" + "-" * 60)
        
        start_time = time.time()
        check_interval = 2
        
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            
            try:
                self.page.wait_for_load_state("domcontentloaded", timeout=1000)
            except Exception:
                pass
            
            if self.check_logged_in():
                print("\n✓ 检测到登录成功！")
                return True
            
            if not self.check_login_required():
                print("\n✓ 页面不再需要登录，可能已登录")
                return True
            
            print(f"\r  等待登录... (剩余 {remaining}秒，按回车继续)", end="", flush=True)
            
            try:
                import threading
                result = [False]
                
                def check_input():
                    try:
                        import sys
                        import msvcrt
                        if msvcrt.kbhit():
                            key = msvcrt.getch()
                            if key == b'\r':
                                result[0] = True
                    except Exception:
                        pass
                
                check_input()
                
                if result[0]:
                    print("\n用户手动确认继续...")
                    return True
                    
            except Exception:
                pass
            
            time.sleep(check_interval)
        
        print("\n⚠ 登录超时，尝试继续执行...")
        return True
    
    def is_on_target_page(self, target_url: str) -> bool:
        current_url = self.page.url
        
        target_parsed = urlparse(target_url)
        current_parsed = urlparse(current_url)
        
        if target_parsed.netloc == current_parsed.netloc:
            if target_parsed.path == current_parsed.path or current_parsed.path.endswith(target_parsed.path):
                return True
        
        if target_parsed.query:
            target_params = self._parse_query_params(target_parsed.query)
            current_params = self._parse_query_params(current_parsed.query)
            
            jobad_id = target_params.get('jobAdId') or target_params.get('jobadid')
            current_jobad_id = current_params.get('jobAdId') or current_params.get('jobadid')
            
            if jobad_id and current_jobad_id and jobad_id == current_jobad_id:
                return True
        
        return False
    
    def _parse_query_params(self, query_string: str) -> Dict[str, str]:
        params = {}
        for pair in query_string.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                params[key] = value
        return params


class SmartNavigator:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.page = browser_manager.page
        self.login_detector = LoginDetector(self.page)
    
    def navigate_with_login_handling(self, target_url: str, max_attempts: int = 3) -> bool:
        print(f"\n[智能导航] 目标URL: {target_url}")
        
        for attempt in range(max_attempts):
            print(f"\n[尝试 {attempt + 1}/{max_attempts}] 导航到目标页面...")
            
            try:
                self.browser_manager.navigate(target_url)
                time.sleep(1)
                
                if self.login_detector.is_on_target_page(target_url):
                    if not self.login_detector.check_login_required():
                        print("✓ 已在目标页面且无需登录")
                        return True
                    else:
                        print("⚠ 在目标页面但需要登录")
                else:
                    print("⚠ 当前不在目标页面，可能被重定向")
                
                if self.login_detector.check_login_required():
                    print("\n" + "=" * 60)
                    print("检测到需要登录")
                    print("=" * 60)
                    
                    if self.login_detector.wait_for_login():
                        print("\n登录完成，重新导航到目标页面...")
                        
                        time.sleep(1)
                        self.browser_manager.navigate(target_url)
                        time.sleep(2)
                        
                        if self.login_detector.is_on_target_page(target_url) or not self.login_detector.check_login_required():
                            print("✓ 成功导航到目标页面")
                            return True
                        else:
                            print("⚠ 仍然需要登录或未在目标页面，再次尝试")
                    else:
                        print("⚠ 登录等待完成，但状态不确定，尝试继续")
                        
            except Exception as e:
                print(f"✗ 导航出错: {e}")
                if attempt < max_attempts - 1:
                    print("  等待2秒后重试...")
                    time.sleep(2)
        
        print("\n⚠ 导航完成，但需要手动确认页面状态")
        print("\n" + "=" * 60)
        print("请确认：")
        print("  1. 是否已成功登录？")
        print("  2. 是否已在目标页面？")
        print("=" * 60)
        print("\n确认无误后按回车键继续...")
        input()
        return True


class PageDebugger:
    def __init__(self, page):
        self.page = page
    
    def analyze_page_structure(self) -> Dict[str, Any]:
        analysis = {
            "url": self.page.url,
            "title": self.page.title(),
            "forms": [],
            "inputs": [],
            "iframes": [],
            "visible_text": "",
        }
        
        try:
            forms = self.page.query_selector_all("form")
            for i, form in enumerate(forms):
                form_info = {
                    "index": i,
                    "id": form.get_attribute("id") or "",
                    "class": form.get_attribute("class") or "",
                    "action": form.get_attribute("action") or "",
                    "method": form.get_attribute("method") or "",
                    "input_count": len(form.query_selector_all("input, textarea, select")),
                }
                analysis["forms"].append(form_info)
        except Exception as e:
            analysis["forms_error"] = str(e)
        
        try:
            inputs = self.page.query_selector_all("input, textarea, select")
            for i, inp in enumerate(inputs[:50]):
                tag_name = inp.evaluate("el => el.tagName.toLowerCase()")
                input_info = {
                    "index": i,
                    "tag": tag_name,
                    "type": inp.get_attribute("type") or "",
                    "name": inp.get_attribute("name") or "",
                    "id": inp.get_attribute("id") or "",
                    "placeholder": inp.get_attribute("placeholder") or "",
                    "class": inp.get_attribute("class") or "",
                    "aria_label": inp.get_attribute("aria-label") or "",
                }
                
                preceding_text = inp.evaluate("""
                    el => {
                        let texts = [];
                        let prev = el.previousElementSibling;
                        while (prev) {
                            if (prev.textContent && prev.textContent.trim()) {
                                texts.push(prev.textContent.trim().substring(0, 30));
                            }
                            prev = prev.previousElementSibling;
                        }
                        return texts.join(' | ');
                    }
                """)
                input_info["preceding_text"] = preceding_text
                
                analysis["inputs"].append(input_info)
        except Exception as e:
            analysis["inputs_error"] = str(e)
        
        try:
            iframes = self.page.query_selector_all("iframe")
            for i, iframe in enumerate(iframes):
                iframe_info = {
                    "index": i,
                    "id": iframe.get_attribute("id") or "",
                    "class": iframe.get_attribute("class") or "",
                    "src": iframe.get_attribute("src") or "",
                    "name": iframe.get_attribute("name") or "",
                }
                analysis["iframes"].append(iframe_info)
        except Exception as e:
            analysis["iframes_error"] = str(e)
        
        return analysis
    
    def print_analysis(self, analysis: Dict[str, Any]):
        print("\n" + "=" * 70)
        print("页面结构分析报告")
        print("=" * 70)
        
        print(f"\n📌 页面信息:")
        print(f"   URL: {analysis.get('url', 'N/A')}")
        print(f"   标题: {analysis.get('title', 'N/A')}")
        
        print(f"\n📋 表单信息 ({len(analysis.get('forms', []))} 个表单):")
        for form in analysis.get("forms", []):
            print(f"\n   表单 {form['index'] + 1}:")
            print(f"      ID: {form['id'] or '无'}")
            print(f"      Class: {form['class'] or '无'}")
            print(f"      Action: {form['action'] or '无'}")
            print(f"      输入字段数: {form['input_count']}")
        
        print(f"\n📝 输入字段 (前{len(analysis.get('inputs', []))}个):")
        for inp in analysis.get("inputs", []):
            print(f"\n   字段 {inp['index'] + 1}:")
            print(f"      标签: <{inp['tag']}> type='{inp['type']}'")
            if inp['name']:
                print(f"      name: {inp['name']}")
            if inp['id']:
                print(f"      id: {inp['id']}")
            if inp['placeholder']:
                print(f"      placeholder: {inp['placeholder']}")
            if inp['aria_label']:
                print(f"      aria-label: {inp['aria_label']}")
            if inp['preceding_text']:
                print(f"      前置文本: {inp['preceding_text']}")
            if inp['class']:
                print(f"      class: {inp['class'][:50]}...")
        
        print(f"\n🔲 iframe信息 ({len(analysis.get('iframes', []))} 个):")
        for iframe in analysis.get("iframes", []):
            print(f"\n   iframe {iframe['index'] + 1}:")
            print(f"      ID: {iframe['id'] or '无'}")
            print(f"      Name: {iframe['name'] or '无'}")
            print(f"      Src: {iframe['src'] or '无'}")
            print(f"      Class: {iframe['class'] or '无'}")
        
        print("\n" + "=" * 70)
    
    def take_debug_screenshot(self, prefix: str = "debug") -> str:
        timestamp = int(time.time())
        filename = f"{prefix}_{timestamp}.png"
        
        try:
            self.page.screenshot(path=filename, full_page=True)
            print(f"\n📸 调试截图已保存: {filename}")
        except Exception as e:
            print(f"\n⚠ 截图失败: {e}")
            filename = ""
        
        return filename


def main():
    args = parse_arguments()
    
    use_system_browser = args.use_system_browser and not args.no_system_browser
    
    print("=" * 60)
    print("AutoCard - 自动化简历填写脚本")
    print("=" * 60)
    print(f"简历文件: {args.resume}")
    print(f"目标平台: {args.platform}")
    print(f"浏览器模式: {'CDP 连接' if args.cdp else ('系统浏览器' if use_system_browser else 'Playwright 内置')}")
    print(f"无头模式: {args.headless}")
    print("=" * 60)
    
    if not os.path.exists(args.resume):
        print(f"错误: 简历文件不存在: {args.resume}")
        sys.exit(1)
    
    print("\n[1/5] 解析简历数据...")
    resume_parser = ResumeParser()
    
    if not resume_parser.is_available(args.resume):
        ext = os.path.splitext(args.resume)[1].lower()
        if ext == '.pdf':
            print("警告: pdfplumber 未安装，尝试使用备用方法...")
            print("请运行: pip install pdfplumber")
        elif ext in ['.docx', '.doc']:
            print("警告: python-docx 未安装，尝试使用备用方法...")
            print("请运行: pip install python-docx")
    
    try:
        resume_data = resume_parser.parse(args.resume)
        print(f"  ✓ 解析成功")
        print(f"  - 姓名: {resume_data.personal_info.name or '未识别'}")
        print(f"  - 手机: {resume_data.personal_info.phone or '未识别'}")
        print(f"  - 邮箱: {resume_data.personal_info.email or '未识别'}")
        print(f"  - 教育经历: {len(resume_data.education_experiences)} 条")
        print(f"  - 工作经历: {len(resume_data.work_experiences)} 条")
        print(f"  - 项目经历: {len(resume_data.project_experiences)} 条")
        print(f"  - 技能: {len(resume_data.skills)} 个")
    except Exception as e:
        print(f"✗ 简历解析失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    target_url = args.url
    if not target_url and args.platform != "custom":
        target_url = get_platform_url(args.platform)
        if target_url:
            print(f"\n[2/5] 使用平台预设URL: {target_url}")
    
    if not target_url:
        print("\n错误: 未提供目标URL，请使用 --url 参数指定")
        sys.exit(1)
    
    print("\n[2/5] 准备浏览器...")
    
    user_data_dir = None
    if args.user_data_dir:
        if args.user_data_dir == "default":
            user_data_dir = get_default_user_data_dir()
            if user_data_dir:
                print(f"  使用默认用户数据目录: {user_data_dir}")
            else:
                print("  警告: 无法获取默认用户数据目录")
        else:
            user_data_dir = args.user_data_dir
            print(f"  使用指定用户数据目录: {user_data_dir}")
    
    browser_config = BrowserConfig(
        headless=args.headless,
        slow_mo=args.slow_mo,
        browser_type=args.browser_type,
        executable_path=args.browser_path,
        user_data_dir=user_data_dir,
        use_cdp=args.cdp,
        cdp_endpoint=args.cdp_endpoint,
        use_system_browser=use_system_browser,
    )
    
    browser_manager = BrowserManager(browser_config=browser_config)
    
    try:
        page = browser_manager.initialize()
        print("  ✓ 浏览器启动成功")
        
        if not args.no_anti_detection:
            print("\n[3/5] 应用反检测措施...")
            anti_detection = AntiDetection(page)
            anti_detection.apply_all_measures()
            print("  ✓ 反检测措施已应用")
        
        print(f"\n[4/5] 智能导航到目标页面...")
        
        smart_navigator = SmartNavigator(browser_manager)
        nav_success = smart_navigator.navigate_with_login_handling(target_url)
        
        if not nav_success:
            print("⚠ 导航可能存在问题，但继续尝试...")
        
        if args.debug:
            print("\n[调试模式] 分析页面结构...")
            debugger = PageDebugger(page)
            analysis = debugger.analyze_page_structure()
            debugger.print_analysis(analysis)
            debugger.take_debug_screenshot("before_fill")
            
            print("\n按回车键继续填写表单...")
            input()
        
        print("\n[5/5] 开始填写表单...")
        form_filler = FormFiller(browser_manager, resume_data)
        
        results = form_filler.fill_all()
        
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count
        
        print("\n" + "=" * 50)
        print("填写完成!")
        print(f"  成功: {success_count} 个字段")
        print(f"  失败: {fail_count} 个字段")
        print("=" * 50)
        
        if fail_count > 0:
            print("\n失败的字段:")
            for result in results:
                if not result.success:
                    print(f"  - {result.field_name}: {result.error_message}")
        
        print("\n请检查填写结果，确认无误后可手动保存。")
        print("按回车键退出...")
        input()
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"\n错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
            print("\n按回车键退出...")
            input()
    finally:
        print("\n关闭浏览器...")
        browser_manager.close()
        print("完成!")


if __name__ == "__main__":
    main()
