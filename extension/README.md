# AutoCard 浏览器插件 - 简历自动填写助手

## 📋 项目概述

AutoCard 是一个浏览器扩展，用于自动识别简历数据并智能填写求职网站的表单。基于原有的 Python + Playwright 项目迁移而来，完全使用原生 JavaScript 实现，无需额外依赖。

## 🚀 功能特性

### ✅ 已实现功能

1. **智能字段定位**
   - 10种定位策略：平台选择器、label文本、for属性、aria-labelledby、placeholder、name、id等
   - 自动支持 iframe 内的表单元素
   - 结果缓存提升性能

2. **多类型表单填写**
   - 文本输入框 (text, email, tel, password, number)
   - 下拉选择框 (select) - 原生和自定义组件
   - 日期选择器 (date) - 直接输入 + 日历点击
   - 文本域 (textarea) - 支持逐字模拟输入
   - 单选/多选按钮 (radio/checkbox)

3. **反检测模拟**
   - 人类行为模拟：随机延迟、鼠标轨迹、逐字输入
   - 遮罩层自动移除
   - 元素激活处理
   - 视口滚动处理

4. **平台特定适配**
   - 猎聘 (liepin.com)
   - BOSS直聘 (zhipin.com)
   - 北森招聘 (zhiye.com)
   - 通用模式支持所有网站

5. **数据管理**
   - 支持 JSON 格式简历数据导入
   - 手动录入简历信息
   - 本地存储持久化
   - 填写历史记录

6. **操作界面**
   - 弹出窗口 (Popup) - 功能控制中心
   - 浮动按钮 - 快捷入口
   - 浮动面板 - 详细操作界面

## 📁 目录结构

```
extension/
├── manifest.json           # 插件配置文件 (Manifest V3)
├── background.js           # 后台 Service Worker
├── content/                # 内容脚本 (注入页面)
│   ├── utils.js            # 工具函数
│   ├── anti-detection.js   # 反检测模块
│   ├── field-locator.js    # 字段定位器
│   ├── interaction-handler.js  # 交互处理器
│   ├── form-filler.js      # 表单填写器
│   ├── content.js          # 主内容脚本
│   └── content.css         # 内容脚本样式
├── popup/                  # 弹出窗口
│   ├── popup.html          # 弹窗界面
│   └── popup.js            # 弹窗逻辑
└── assets/                 # 资源文件
    └── icons/              # 图标 (需要自行添加)
```

## 🔧 安装说明

### 步骤 1: 准备图标文件

Chrome 扩展需要 PNG 格式的图标。请准备以下尺寸的图标：

- `icon16.png` - 16x16 像素
- `icon48.png` - 48x48 像素  
- `icon128.png` - 128x128 像素

将图标文件放置在 `extension/assets/icons/` 目录下。

> 💡 提示：可以使用在线工具将 SVG 转换为 PNG，或使用任意图标生成器。

### 步骤 2: 加载插件到 Chrome

1. 打开 Chrome 浏览器
2. 访问 `chrome://extensions/`
3. 开启右上角的 **"开发者模式"**
4. 点击 **"加载已解压的扩展程序"**
5. 选择 `extension` 文件夹
6. 插件加载完成！

### 步骤 3: 验证安装

- Chrome 工具栏右侧应该出现 AutoCard 图标
- 点击图标可以打开弹出窗口
- 访问任意网页，页面右下角应该出现浮动按钮

## 📖 使用指南

### 方式一: 通过弹出窗口

1. 点击 Chrome 工具栏的 AutoCard 图标
2. 在 **"简历"** 标签页设置简历数据：
   - 上传 JSON 文件
   - 粘贴 JSON 数据
   - 手动输入信息
3. 在 **"操作"** 标签页执行填写操作：
   - 智能填写全部
   - 分模块填写（个人信息、教育经历等）

### 方式二: 通过页面浮动按钮

1. 在任意页面右下角找到浮动按钮 📝
2. 点击按钮展开浮动面板
3. 加载简历数据后执行填写

### 简历数据格式

推荐使用以下 JSON 格式：

```json
{
  "personalInfo": {
    "name": "张三",
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "gender": "男",
    "selfIntroduction": "多年软件开发经验..."
  },
  "educationExperiences": [
    {
      "school": "北京大学",
      "major": "计算机科学与技术",
      "education": "本科",
      "startDate": "2016-09",
      "endDate": "2020-06"
    }
  ],
  "workExperiences": [
    {
      "company": "阿里巴巴",
      "position": "高级工程师",
      "startDate": "2020-07",
      "endDate": "2023-03",
      "description": "负责电商平台核心系统开发..."
    }
  ],
  "projectExperiences": [
    {
      "projectName": "双十一活动系统",
      "role": "技术负责人",
      "startDate": "2022-06",
      "endDate": "2022-11",
      "description": "支撑千万级并发..."
    }
  ],
  "skills": ["Java", "Spring Boot", "MySQL", "Redis"]
}
```

## 🔄 与原 Python 项目对比

| 特性 | Python + Playwright | 浏览器插件 |
|-----|---------------------|-----------|
| 运行环境 | 独立桌面应用 | 浏览器内部 |
| 安装方式 | Python + 依赖库 | Chrome 扩展 |
| 用户数据 | 本地文件系统 | Chrome 存储 |
| 简历解析 | PDF/DOCX 完整解析 | JSON/手动输入 |
| 反检测 | 完善 | 基础实现 |
| 平台适配 | 完善 | 基础实现 |

### Python 项目优势
- 完整的 PDF/DOCX 简历解析
- 更完善的反检测措施
- 更丰富的平台配置
- 支持连接已运行的浏览器

### 浏览器插件优势
- 无需安装 Python 环境
- 始终与用户浏览器保持同步
- 数据持久化存储
- 更轻量的使用方式

## 🔧 开发说明

### 架构说明

1. **Background Service Worker** (`background.js`)
   - 存储和管理简历数据
   - 处理扩展事件
   - 与内容脚本通信

2. **Content Scripts** (`content/*.js`)
   - 注入到页面执行
   - 字段定位和表单填写
   - 交互模拟和反检测

3. **Popup** (`popup/*`)
   - 用户交互界面
   - 数据输入和设置
   - 操作触发入口

### 模块依赖关系

```
content.js (主入口)
    ↓
utils.js (工具函数)
    ↓
anti-detection.js (反检测)
    ↓
field-locator.js (字段定位)
    ↓
interaction-handler.js (交互处理)
    ↓
form-filler.js (表单填写)
```

## 📝 已知限制

1. **简历文件解析**：浏览器环境无法直接解析 PDF/DOCX 文件，需要先转换为 JSON 格式
2. **跨域限制**：部分网站的 iframe 可能无法访问
3. **动态内容**：高度动态的页面（如 React/Vue 应用）可能需要额外适配
4. **图标缺失**：需要自行准备 PNG 格式的图标文件

## 🔮 后续优化建议

1. **简历解析增强**
   - 集成 PDF.js 解析 PDF 文件
   - 集成 mammoth.js 解析 Word 文件

2. **平台适配完善**
   - 增加更多求职网站的专用选择器
   - 自动识别更多平台

3. **UI 增强**
   - 添加字段映射配置界面
   - 支持自定义选择器
   - 添加填写预览功能

4. **数据同步**
   - 支持云同步简历数据
   - 多设备数据共享

## 📞 技术支持

如有问题或建议，请参考原 Python 项目的实现逻辑，或查看代码中的详细注释。

---

**AutoCard - 让简历填写更简单！** 🎯
