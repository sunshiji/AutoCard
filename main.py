import os
import sys
import argparse
from typing import Optional

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
        
        print(f"\n[4/5] 导航到目标页面...")
        print(f"  URL: {target_url}")
        
        browser_manager.navigate(target_url)
        print("  ✓ 页面加载完成")
        
        print("\n" + "=" * 50)
        print("请在浏览器中完成登录操作...")
        print("登录完成后，请按回车键继续...")
        print("=" * 50)
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
