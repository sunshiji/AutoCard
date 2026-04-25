# AutoCard

一个能自动填写网站简历脚本

```
AutoCard/
├── config.py              # 配置文件
（字段映射、浏览器设置等）
├── models.py              # 数据模型
定义
├── main.py                # 主入口脚
本
├── requirements.txt       # 依赖配置
└── autocard/
    ├── __init__.py        # 包初始化
    ├── resume_parser.py   # 简历数据
    解析模块
    ├── browser_manager.py # 浏览器管
    理模块
    ├── field_locator.py   # 字段智能
    定位模块
    ├── interaction_handler.py # 复杂
    交互处理模块
    ├── anti_detection.py  # 防检测与
    表单验证模块
    └── form_filler.py     # 表单填充
    整合模块
```

## 核心功能

### 1. 简历数据解析 (resume\_parser.py)

- 支持 PDF 和 Word (.docx) 格式
- 智能提取：个人信息（姓名、手机、邮箱、性别）、教育经历、工作经历、项目经历、专业技能、自我介绍
- 支持日期格式解析、多段经历自动分割

### 2. 字段智能定位 (field\_locator.py)

8 种定位策略，按优先级尝试：

- Label 文本匹配（最常用）
- Label 的 for 属性关联
- aria-labelledby 关联
- placeholder 属性匹配
- name 属性匹配
- id 属性匹配
- 前兄弟节点文本匹配
- 父节点兄弟文本匹配

### 3. 复杂交互处理 (interaction\_handler.py)

- iframe 嵌套 ：自动检测和处理 iframe 内容
- 动态加载 ：等待元素出现/消失、滚动加载更多
- 下拉菜单 ：原生 <select> 和自定义下拉组件（ElementUI/Ant Design 等）
- 日期选择器 ：支持直接输入和日历选择两种模式
- 多段经历 ：自动点击"添加更多经历"按钮
- 保存/提交 ：智能定位保存按钮
- 单选/复选框 、 多行文本框 、 文件上传

### 4. 防检测与验证 (anti\_detection.py)

防检测措施：

- 禁用 navigator.webdriver 标志
- 模拟浏览器插件列表
- 添加语言属性
- 模拟 Chrome runtime
- WebGL 指纹伪装
- 随机用户代理
- 模拟人类输入延迟
  表单验证：
- 检测必填项
- 识别验证错误提示（支持 ElementUI、Ant Design 等主流框架）
- 等待验证完成

### 5. 表单填充整合 (form\_filler.py)

- 按模块填充：个人信息 → 教育经历 → 工作经历 → 项目经历 → 技能
- 多段经历自动添加
- 完整的进度追踪
- 填充结果记录

## 安装使用

### 1. 安装依赖

```
pip install -r requirements.txt
```

### 2. 安装 Playwright 浏览器

```
playwright install chromium
```

### 3. 运行脚本

```
# 基本用法
python main.py --resume 你的简历.pdf 
--url "https://目标网站简历填写页面"

# 使用平台预设（猎聘）
python main.py --resume 简历.docx 
--platform liepin

# 无头模式
python main.py --resume 简历.pdf 
--url "xxx" --headless
```

## 使用流程

1. 脚本启动浏览器并导航到目标 URL
2. 用户手动登录 （脚本暂停等待按回车）
3. 脚本自动：
   - 解析简历数据
   - 智能定位各字段
   - 按模块填充数据
   - 自动添加多段经历
4. 用户检查并手动保存

## 配置说明 (config.py)

可在配置文件中：

- 自定义字段名称映射（如"联系方式"可映射到哪些 Label 文本）
- 调整输入延迟、等待超时等参数
- 配置猎聘、Boss 直聘等平台的预设 URL
- 开启/关闭反检测措施

