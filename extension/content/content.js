(function() {
  'use strict';
  
  console.log('[AutoCard] 简历自动填写助手已加载');
  console.log('[AutoCard] 页面 URL:', window.location.href);
  
  let resumeData = null;
  let currentPlatform = null;
  
  const PLATFORM_CONFIGS = {
    liepin: {
      name: '猎聘',
      patterns: ['liepin.com', 'liepin'],
      fieldSelectors: {}
    },
    boss: {
      name: 'BOSS直聘',
      patterns: ['zhipin.com', 'boss'],
      fieldSelectors: {}
    },
    beisen: {
      name: '北森招聘',
      patterns: ['zhiye.com', 'beisen', '北森'],
      fieldSelectors: {
        name: ['input[name*="name"]', 'input[name*="realName"]', 'input[name*="username"]', 'input[placeholder*="姓名"]'],
        phone: ['input[name*="phone"]', 'input[name*="mobile"]', 'input[name*="telephone"]', 'input[placeholder*="手机"]'],
        email: ['input[name*="email"]', 'input[name*="mail"]', 'input[placeholder*="邮箱"]'],
        gender: ['select[name*="gender"]', 'select[name*="sex"]', 'input[name*="gender"][type="radio"]'],
        birthday: ['input[name*="birthday"]', 'input[name*="birthDate"]', 'input[placeholder*="生日"]'],
        school: ['input[name*="school"]', 'input[name*="university"]', 'input[name*="college"]', 'input[placeholder*="学校"]'],
        major: ['input[name*="major"]', 'input[placeholder*="专业"]'],
        education: ['select[name*="education"]', 'select[name*="degree"]'],
        company: ['input[name*="company"]', 'input[name*="enterprise"]', 'input[placeholder*="公司"]'],
        position: ['input[name*="position"]', 'input[name*="post"]', 'input[name*="jobTitle"]'],
        startDate: ['input[name*="startDate"]', 'input[name*="beginDate"]', 'input[placeholder*="开始"]'],
        endDate: ['input[name*="endDate"]', 'input[name*="finishDate"]', 'input[placeholder*="结束"]']
      }
    }
  };
  
  function init() {
    console.log('[AutoCard] 初始化...');
    
    currentPlatform = detectPlatform();
    console.log('[AutoCard] 当前平台:', currentPlatform);
    
    injectFloatingButton();
    listenForMessages();
    
    console.log('[AutoCard] 初始化完成');
  }
  
  function detectPlatform() {
    const url = window.location.href.toLowerCase();
    console.log('[AutoCard] 检测平台，URL:', url);
    
    for (const [platformKey, config] of Object.entries(PLATFORM_CONFIGS)) {
      for (const pattern of config.patterns) {
        if (url.includes(pattern.toLowerCase())) {
          console.log('[AutoCard] 检测到平台:', config.name);
          return platformKey;
        }
      }
    }
    
    console.log('[AutoCard] 未识别到特定平台，使用通用模式');
    return null;
  }
  
  function getPlatformSelectors() {
    if (currentPlatform && PLATFORM_CONFIGS[currentPlatform]) {
      return PLATFORM_CONFIGS[currentPlatform].fieldSelectors || {};
    }
    return {};
  }
  
  function injectFloatingButton() {
    const existingButton = document.getElementById('autocard-float-btn');
    if (existingButton) {
      console.log('[AutoCard] 浮动按钮已存在，跳过');
      return;
    }
    
    console.log('[AutoCard] 注入浮动按钮...');
    
    const button = document.createElement('div');
    button.id = 'autocard-float-btn';
    button.innerHTML = `
      <div class="autocard-icon">📝</div>
      <div class="autocard-tooltip">AutoCard 简历填写</div>
    `;
    
    Object.assign(button.style, {
      position: 'fixed',
      right: '20px',
      bottom: '20px',
      width: '56px',
      height: '56px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      borderRadius: '50%',
      boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
      cursor: 'pointer',
      zIndex: '999999',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'all 0.3s ease',
      userSelect: 'none'
    });
    
    const icon = button.querySelector('.autocard-icon');
    Object.assign(icon.style, {
      fontSize: '24px',
      transition: 'transform 0.3s ease'
    });
    
    const tooltip = button.querySelector('.autocard-tooltip');
    Object.assign(tooltip.style, {
      position: 'absolute',
      right: '70px',
      background: '#333',
      color: 'white',
      padding: '8px 16px',
      borderRadius: '8px',
      fontSize: '14px',
      whiteSpace: 'nowrap',
      opacity: '0',
      visibility: 'hidden',
      transition: 'all 0.3s ease',
      pointerEvents: 'none'
    });
    
    button.addEventListener('mouseenter', () => {
      button.style.transform = 'scale(1.1)';
      icon.style.transform = 'rotate(360deg)';
      tooltip.style.opacity = '1';
      tooltip.style.visibility = 'visible';
    });
    
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'scale(1)';
      icon.style.transform = 'rotate(0deg)';
      tooltip.style.opacity = '0';
      tooltip.style.visibility = 'hidden';
    });
    
    button.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log('[AutoCard] 浮动按钮被点击');
      showFloatingPanel();
    });
    
    document.body.appendChild(button);
    console.log('[AutoCard] 浮动按钮已注入');
  }
  
  function showFloatingPanel() {
    console.log('[AutoCard] 显示浮动面板...');
    
    const existingPanel = document.getElementById('autocard-float-panel');
    if (existingPanel) {
      existingPanel.style.display = 'flex';
      updatePanelUI();
      return;
    }
    
    const panel = document.createElement('div');
    panel.id = 'autocard-float-panel';
    panel.innerHTML = `
      <div class="autocard-panel-header">
        <span class="autocard-panel-title">📝 AutoCard 简历填写助手</span>
        <button class="autocard-panel-close">&times;</button>
      </div>
      <div class="autocard-panel-body">
        <div class="autocard-section">
          <div class="autocard-section-title">📄 简历数据</div>
          <div class="autocard-section-content">
            <div class="autocard-status">
              <span class="autocard-status-dot" id="autocard-data-status"></span>
              <span id="autocard-data-status-text">未加载简历数据</span>
            </div>
            <div style="margin-top: 12px;">
              <button class="autocard-btn autocard-btn-secondary" id="autocard-btn-paste-panel" style="width: 100%; margin-bottom: 10px;">
                📋 粘贴 JSON 数据
              </button>
              <button class="autocard-btn autocard-btn-secondary" id="autocard-btn-set-example" style="width: 100%;">
                📋 加载示例数据
              </button>
            </div>
          </div>
        </div>
        
        <div class="autocard-section">
          <div class="autocard-section-title">🌐 当前平台</div>
          <div class="autocard-section-content">
            <div id="autocard-platform-info-panel" style="padding: 12px; background: #f5f5f5; border-radius: 8px;">
              检测中...
            </div>
          </div>
        </div>
        
        <div class="autocard-section">
          <div class="autocard-section-title">⚡ 操作</div>
          <div class="autocard-section-content">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
              <button class="autocard-btn autocard-btn-success" id="autocard-btn-fill-all-panel">
                ✨ 智能填写全部
              </button>
              <button class="autocard-btn autocard-btn-info" id="autocard-btn-fill-personal-panel">
                👤 个人信息
              </button>
              <button class="autocard-btn autocard-btn-info" id="autocard-btn-fill-education-panel">
                🎓 教育经历
              </button>
              <button class="autocard-btn autocard-btn-info" id="autocard-btn-fill-work-panel">
                💼 工作经历
              </button>
            </div>
          </div>
        </div>
        
        <div class="autocard-section">
          <div class="autocard-section-title">📊 填写结果</div>
          <div class="autocard-section-content">
            <div id="autocard-results-panel" style="max-height: 200px; overflow-y: auto; font-size: 13px;">
              <div style="color: #888; text-align: center; padding: 20px;">
                暂无填写记录
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    
    Object.assign(panel.style, {
      position: 'fixed',
      right: '20px',
      bottom: '90px',
      width: '400px',
      maxHeight: '80vh',
      background: 'white',
      borderRadius: '16px',
      boxShadow: '0 10px 40px rgba(0, 0, 0, 0.15)',
      zIndex: '999998',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      border: '1px solid #e8e8e8',
      color: '#333',
      lineHeight: '1.5'
    });
    
    document.body.appendChild(panel);
    
    injectPanelStyles();
    bindPanelEvents(panel);
    updatePanelUI();
    
    console.log('[AutoCard] 浮动面板已显示');
  }
  
  function injectPanelStyles() {
    const styleId = 'autocard-panel-styles';
    if (document.getElementById(styleId)) return;
    
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      #autocard-float-panel .autocard-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        flex-shrink: 0;
      }
      #autocard-float-panel .autocard-panel-title {
        font-weight: 600;
        font-size: 16px;
        margin: 0;
      }
      #autocard-float-panel .autocard-panel-close {
        background: none;
        border: none;
        color: white;
        font-size: 24px;
        cursor: pointer;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background 0.2s;
      }
      #autocard-float-panel .autocard-panel-close:hover {
        background: rgba(255, 255, 255, 0.2);
      }
      #autocard-float-panel .autocard-panel-body {
        padding: 16px 20px;
        overflow-y: auto;
        flex-grow: 1;
      }
      #autocard-float-panel .autocard-section {
        margin-bottom: 16px;
      }
      #autocard-float-panel .autocard-section:last-child {
        margin-bottom: 0;
      }
      #autocard-float-panel .autocard-section-title {
        font-weight: 600;
        font-size: 14px;
        color: #333;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      #autocard-float-panel .autocard-section-content {
        background: #fafafa;
        border-radius: 12px;
        padding: 14px;
      }
      #autocard-float-panel .autocard-status {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #666;
        font-size: 14px;
      }
      #autocard-float-panel .autocard-status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #ccc;
      }
      #autocard-float-panel .autocard-status-dot.ready {
        background: #52c41a;
      }
      #autocard-float-panel .autocard-btn {
        padding: 10px 16px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
      }
      #autocard-float-panel .autocard-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }
      #autocard-float-panel .autocard-btn:active {
        transform: translateY(0);
      }
      #autocard-float-panel .autocard-btn-secondary {
        background: #f0f0f0;
        color: #333;
      }
      #autocard-float-panel .autocard-btn-success {
        background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
        color: white;
      }
      #autocard-float-panel .autocard-btn-info {
        background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
        color: white;
      }
      #autocard-float-panel .autocard-result-item {
        padding: 8px 12px;
        margin-bottom: 6px;
        background: white;
        border-radius: 6px;
        border-left: 3px solid #ccc;
      }
      #autocard-float-panel .autocard-result-item.success {
        border-left-color: #52c41a;
      }
      #autocard-float-panel .autocard-result-item.fail {
        border-left-color: #ff4d4f;
      }
      #autocard-float-panel .autocard-result-field {
        font-weight: 500;
        color: #333;
      }
      #autocard-float-panel .autocard-result-value {
        color: #666;
        font-size: 12px;
        margin-top: 2px;
        word-break: break-all;
      }
      #autocard-float-panel .autocard-result-error {
        color: #ff4d4f;
        font-size: 12px;
        margin-top: 2px;
      }
    `;
    document.head.appendChild(style);
  }
  
  function bindPanelEvents(panel) {
    panel.querySelector('.autocard-panel-close').addEventListener('click', () => {
      panel.style.display = 'none';
    });
    
    document.getElementById('autocard-btn-paste-panel').addEventListener('click', () => {
      const jsonStr = prompt('请粘贴简历 JSON 数据：\n\n示例：\n{"personalInfo":{"name":"张三","phone":"13800138000","email":"zhangsan@example.com"}}');
      if (jsonStr) {
        try {
          console.log('[AutoCard] 用户输入的 JSON:', jsonStr);
          const data = JSON.parse(jsonStr);
          console.log('[AutoCard] 解析成功:', data);
          resumeData = data;
          updatePanelUI();
          alert('JSON 数据加载成功！');
        } catch (e) {
          console.error('[AutoCard] JSON 解析失败:', e);
          alert('JSON 格式错误：' + e.message);
        }
      }
    });
    
    document.getElementById('autocard-btn-set-example').addEventListener('click', () => {
      resumeData = {
        personalInfo: {
          name: '张三',
          phone: '13800138000',
          email: 'zhangsan@example.com',
          gender: '男',
          selfIntroduction: '5年软件开发经验，精通Java和Spring Boot技术栈。'
        },
        educationExperiences: [
          {
            school: '北京大学',
            major: '计算机科学与技术',
            education: '本科',
            startDate: '2016-09',
            endDate: '2020-06'
          }
        ],
        workExperiences: [
          {
            company: '阿里巴巴',
            position: '高级工程师',
            startDate: '2020-07',
            endDate: '2023-03',
            description: '负责电商平台核心系统开发。'
          }
        ],
        projectExperiences: [],
        skills: ['Java', 'Spring Boot', 'MySQL', 'Redis']
      };
      console.log('[AutoCard] 已设置示例数据:', resumeData);
      updatePanelUI();
      alert('示例数据已加载！\n姓名: 张三\n手机: 13800138000\n邮箱: zhangsan@example.com');
    });
    
    document.getElementById('autocard-btn-fill-all-panel').addEventListener('click', async () => {
      console.log('[AutoCard] 点击：智能填写全部');
      await executeFill('fillAll');
    });
    
    document.getElementById('autocard-btn-fill-personal-panel').addEventListener('click', async () => {
      console.log('[AutoCard] 点击：填写个人信息');
      await executeFill('personal');
    });
    
    document.getElementById('autocard-btn-fill-education-panel').addEventListener('click', async () => {
      console.log('[AutoCard] 点击：填写教育经历');
      await executeFill('education');
    });
    
    document.getElementById('autocard-btn-fill-work-panel').addEventListener('click', async () => {
      console.log('[AutoCard] 点击：填写工作经历');
      await executeFill('work');
    });
    
    document.addEventListener('click', (e) => {
      const floatBtn = document.getElementById('autocard-float-btn');
      
      if (panel && panel.style.display === 'flex') {
        if (!floatBtn?.contains(e.target) && !panel.contains(e.target)) {
          panel.style.display = 'none';
        }
      }
    });
  }
  
  function updatePanelUI() {
    console.log('[AutoCard] updatePanelUI, resumeData:', resumeData);
    
    const statusDot = document.getElementById('autocard-data-status');
    const statusText = document.getElementById('autocard-data-status-text');
    const platformInfo = document.getElementById('autocard-platform-info-panel');
    
    if (resumeData && resumeData.personalInfo && resumeData.personalInfo.name) {
      statusDot.classList.add('ready');
      const name = resumeData.personalInfo.name;
      statusText.textContent = `已加载 (${name})`;
      console.log('[AutoCard] UI 状态: 数据已就绪');
    } else {
      statusDot.classList.remove('ready');
      statusText.textContent = '未加载简历数据';
      console.log('[AutoCard] UI 状态: 无数据');
    }
    
    if (currentPlatform && PLATFORM_CONFIGS[currentPlatform]) {
      platformInfo.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 24px;">🌐</span>
          <div>
            <div style="font-weight: 600; color: #333;">${PLATFORM_CONFIGS[currentPlatform].name}</div>
            <div style="font-size: 12px; color: #52c41a;">✓ 已识别平台</div>
          </div>
        </div>
      `;
    } else {
      platformInfo.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 24px;">🌐</span>
          <div>
            <div style="font-weight: 600; color: #333;">通用模式</div>
            <div style="font-size: 12px; color: #666;">将使用通用字段定位策略</div>
          </div>
        </div>
      `;
    }
  }
  
  async function executeFill(action) {
    console.log('[AutoCard] executeFill 被调用, action:', action);
    console.log('[AutoCard] resumeData:', resumeData);
    
    if (!resumeData || !resumeData.personalInfo) {
      alert('请先加载简历数据！\n\n点击"加载示例数据"或"粘贴 JSON 数据"来设置简历信息。');
      return;
    }
    
    if (!resumeData.personalInfo.name) {
      alert('简历数据不完整！请确保包含姓名、手机、邮箱等基本信息。');
      return;
    }
    
    const platformSelectors = getPlatformSelectors();
    console.log('[AutoCard] platformSelectors:', platformSelectors);
    
    if (window.AutoCardFieldLocator) {
      console.log('[AutoCard] 设置平台选择器到 FieldLocator');
      window.AutoCardFieldLocator.setPlatformSelectors(platformSelectors);
    } else {
      console.warn('[AutoCard] AutoCardFieldLocator 未找到');
    }
    
    if (window.AutoCardFormFiller) {
      console.log('[AutoCard] 初始化 FormFiller');
      window.AutoCardFormFiller.init(resumeData, platformSelectors);
      
      let results = [];
      
      try {
        switch (action) {
          case 'fillAll':
            console.log('[AutoCard] 执行 fillAll');
            results = await window.AutoCardFormFiller.fillAll();
            break;
          case 'personal':
            console.log('[AutoCard] 执行 fillPersonalInfo');
            results = await window.AutoCardFormFiller.fillPersonalInfo();
            break;
          case 'education':
            console.log('[AutoCard] 执行 fillEducationExperiences');
            results = await window.AutoCardFormFiller.fillEducationExperiences();
            break;
          case 'work':
            console.log('[AutoCard] 执行 fillWorkExperiences');
            results = await window.AutoCardFormFiller.fillWorkExperiences();
            break;
          case 'project':
            console.log('[AutoCard] 执行 fillProjectExperiences');
            results = await window.AutoCardFormFiller.fillProjectExperiences();
            break;
          case 'skills':
            console.log('[AutoCard] 执行 fillSkills');
            results = await window.AutoCardFormFiller.fillSkills();
            break;
        }
        
        console.log('[AutoCard] 填写结果:', results);
        
        displayResults(results);
        
        const successCount = results.filter(r => r.success).length;
        const failCount = results.length - successCount;
        
        alert(`填写完成！\n成功: ${successCount} 个字段\n失败: ${failCount} 个字段`);
        
      } catch (e) {
        console.error('[AutoCard] 填写出错:', e);
        alert('填写过程中出错：' + e.message);
      }
    } else {
      console.error('[AutoCard] AutoCardFormFiller 未找到');
      alert('填写模块未加载！请刷新页面后重试。');
    }
  }
  
  function displayResults(results) {
    const container = document.getElementById('autocard-results-panel');
    if (!container) return;
    
    console.log('[AutoCard] displayResults:', results);
    
    if (!results || results.length === 0) {
      container.innerHTML = `
        <div style="color: #888; text-align: center; padding: 20px;">
          暂无填写结果
        </div>
      `;
      return;
    }
    
    container.innerHTML = results.map(r => `
      <div class="autocard-result-item ${r.success ? 'success' : 'fail'}">
        <div class="autocard-result-field">
          ${r.success ? '✅' : '❌'} ${r.fieldName}
        </div>
        ${r.errorMessage ? 
          `<div class="autocard-result-error">${r.errorMessage}</div>` :
          `<div class="autocard-result-value">${String(r.value || '').substring(0, 50)}${String(r.value || '').length > 50 ? '...' : ''}</div>`
        }
      </div>
    `).join('');
  }
  
  function listenForMessages() {
    console.log('[AutoCard] 开始监听消息...');
    
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      console.log('[AutoCard] content.js 收到消息:', request.action);
      
      switch (request.action) {
        case 'setResumeData':
          console.log('[AutoCard] 设置简历数据:', request.data?.personalInfo?.name);
          resumeData = request.data;
          updatePanelUI();
          sendResponse({ success: true });
          break;
          
        case 'getResumeData':
          sendResponse({ success: true, data: resumeData });
          break;
          
        case 'executeFill':
          console.log('[AutoCard] 收到 executeFill 请求:', request.fillAction);
          if (request.resumeData) {
            resumeData = request.resumeData;
            console.log('[AutoCard] 使用传入的 resumeData');
          }
          executeFill(request.fillAction);
          sendResponse({ success: true });
          break;
          
        case 'showPanel':
          showFloatingPanel();
          sendResponse({ success: true });
          break;
          
        case 'getPlatformInfo':
          sendResponse({ 
            success: true, 
            platform: currentPlatform,
            url: window.location.href
          });
          break;
          
        case 'resumeDataUpdated':
          console.log('[AutoCard] 收到数据更新通知');
          if (request.data) {
            resumeData = request.data;
            updatePanelUI();
          }
          sendResponse({ success: true });
          break;
          
        default:
          console.log('[AutoCard] 未知消息类型:', request.action);
          sendResponse({ success: false, error: 'Unknown action: ' + request.action });
      }
      
      return true;
    });
    
    console.log('[AutoCard] 消息监听器已设置');
  }
  
  init();
  
})();
