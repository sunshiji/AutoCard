(function() {
  'use strict';
  
  console.log('[AutoCard] 简历自动填写助手已加载');
  
  let resumeData = null;
  let currentPlatform = null;
  let fillHistory = [];
  
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
    detectPlatform();
    injectFloatingButton();
    listenForMessages();
  }
  
  function detectPlatform() {
    const url = window.location.href.toLowerCase();
    
    for (const [platformKey, config] of Object.entries(PLATFORM_CONFIGS)) {
      for (const pattern of config.patterns) {
        if (url.includes(pattern.toLowerCase())) {
          currentPlatform = platformKey;
          console.log(`[AutoCard] 检测到平台: ${config.name}`);
          return platformKey;
        }
      }
    }
    
    currentPlatform = null;
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
      return;
    }
    
    const button = document.createElement('div');
    button.id = 'autocard-float-btn';
    button.innerHTML = `
      <div class="autocard-icon">📝</div>
      <div class="autocard-tooltip">AutoCard 简历填写</div>
    `;
    button.style.cssText = `
      position: fixed;
      right: 20px;
      bottom: 20px;
      width: 56px;
      height: 56px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 50%;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
      cursor: pointer;
      z-index: 999999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      user-select: none;
    `;
    
    const icon = button.querySelector('.autocard-icon');
    icon.style.cssText = `
      font-size: 24px;
      transition: transform 0.3s ease;
    `;
    
    const tooltip = button.querySelector('.autocard-tooltip');
    tooltip.style.cssText = `
      position: absolute;
      right: 70px;
      background: #333;
      color: white;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 14px;
      white-space: nowrap;
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s ease;
      pointer-events: none;
    `;
    
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
      showFloatingPanel();
    });
    
    document.body.appendChild(button);
    console.log('[AutoCard] 浮动按钮已注入');
  }
  
  function showFloatingPanel() {
    const existingPanel = document.getElementById('autocard-float-panel');
    if (existingPanel) {
      existingPanel.style.display = 'flex';
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
            <div class="autocard-actions" style="margin-top: 12px;">
              <button class="autocard-btn autocard-btn-primary" id="autocard-btn-load">
                🔄 从插件加载
              </button>
              <button class="autocard-btn autocard-btn-secondary" id="autocard-btn-paste">
                📋 粘贴 JSON 数据
              </button>
            </div>
          </div>
        </div>
        
        <div class="autocard-section">
          <div class="autocard-section-title">🌐 当前平台</div>
          <div class="autocard-section-content">
            <div id="autocard-platform-info" style="padding: 12px; background: #f5f5f5; border-radius: 8px;">
              检测中...
            </div>
          </div>
        </div>
        
        <div class="autocard-section">
          <div class="autocard-section-title">⚡ 操作</div>
          <div class="autocard-section-content">
            <div class="autocard-actions" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
              <button class="autocard-btn autocard-btn-success" id="autocard-btn-fill-all">
                ✨ 智能填写全部
              </button>
              <button class="autocard-btn autocard-btn-info" id="autocard-btn-fill-personal">
                👤 个人信息
              </button>
              <button class="autocard-btn autocard-btn-info" id="autocard-btn-fill-education">
                🎓 教育经历
              </button>
              <button class="autocard-btn autocard-btn-info" id="autocard-btn-fill-work">
                💼 工作经历
              </button>
              <button class="autocard-btn autocard-btn-info" id="autocard-btn-fill-project">
                🚀 项目经历
              </button>
              <button class="autocard-btn autocard-btn-info" id="autocard-btn-fill-skills">
                🛠 技能填写
              </button>
            </div>
          </div>
        </div>
        
        <div class="autocard-section">
          <div class="autocard-section-title">📊 填写结果</div>
          <div class="autocard-section-content">
            <div id="autocard-results" style="max-height: 200px; overflow-y: auto; font-size: 13px;">
              <div style="color: #888; text-align: center; padding: 20px;">
                暂无填写记录
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    
    panel.style.cssText = `
      position: fixed;
      right: 20px;
      bottom: 90px;
      width: 400px;
      max-height: 80vh;
      background: white;
      border-radius: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
      z-index: 999998;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    `;
    
    document.body.appendChild(panel);
    
    injectPanelStyles();
    bindPanelEvents();
    updatePanelUI();
    
    console.log('[AutoCard] 浮动面板已显示');
  }
  
  function injectPanelStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .autocard-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }
      .autocard-panel-title {
        font-weight: 600;
        font-size: 16px;
      }
      .autocard-panel-close {
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
      .autocard-panel-close:hover {
        background: rgba(255, 255, 255, 0.2);
      }
      .autocard-panel-body {
        padding: 16px 20px;
        overflow-y: auto;
      }
      .autocard-section {
        margin-bottom: 16px;
      }
      .autocard-section:last-child {
        margin-bottom: 0;
      }
      .autocard-section-title {
        font-weight: 600;
        font-size: 14px;
        color: #333;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .autocard-section-content {
        background: #fafafa;
        border-radius: 12px;
        padding: 14px;
      }
      .autocard-status {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #666;
        font-size: 14px;
      }
      .autocard-status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #ccc;
      }
      .autocard-status-dot.ready {
        background: #52c41a;
      }
      .autocard-actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }
      .autocard-btn {
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
      .autocard-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }
      .autocard-btn:active {
        transform: translateY(0);
      }
      .autocard-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
      }
      .autocard-btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }
      .autocard-btn-secondary {
        background: #f0f0f0;
        color: #333;
      }
      .autocard-btn-success {
        background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
        color: white;
      }
      .autocard-btn-info {
        background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
        color: white;
      }
      .autocard-btn-warning {
        background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);
        color: white;
      }
      .autocard-result-item {
        padding: 8px 12px;
        margin-bottom: 6px;
        background: white;
        border-radius: 6px;
        border-left: 3px solid #ccc;
      }
      .autocard-result-item.success {
        border-left-color: #52c41a;
      }
      .autocard-result-item.fail {
        border-left-color: #ff4d4f;
      }
      .autocard-result-field {
        font-weight: 500;
        color: #333;
      }
      .autocard-result-value {
        color: #666;
        font-size: 12px;
        margin-top: 2px;
        word-break: break-all;
      }
      .autocard-result-error {
        color: #ff4d4f;
        font-size: 12px;
        margin-top: 2px;
      }
    `;
    document.head.appendChild(style);
  }
  
  function bindPanelEvents() {
    const panel = document.getElementById('autocard-float-panel');
    if (!panel) return;
    
    panel.querySelector('.autocard-panel-close').addEventListener('click', () => {
      panel.style.display = 'none';
    });
    
    document.getElementById('autocard-btn-load').addEventListener('click', async () => {
      await loadResumeData();
    });
    
    document.getElementById('autocard-btn-paste').addEventListener('click', () => {
      const jsonStr = prompt('请粘贴简历 JSON 数据：');
      if (jsonStr) {
        try {
          const data = JSON.parse(jsonStr);
          resumeData = data;
          console.log('[AutoCard] 简历数据已设置:', data);
          updatePanelUI();
        } catch (e) {
          alert('JSON 格式错误：' + e.message);
        }
      }
    });
    
    document.getElementById('autocard-btn-fill-all').addEventListener('click', async () => {
      await fillAllFields();
    });
    
    document.getElementById('autocard-btn-fill-personal').addEventListener('click', async () => {
      await fillSection('personal');
    });
    
    document.getElementById('autocard-btn-fill-education').addEventListener('click', async () => {
      await fillSection('education');
    });
    
    document.getElementById('autocard-btn-fill-work').addEventListener('click', async () => {
      await fillSection('work');
    });
    
    document.getElementById('autocard-btn-fill-project').addEventListener('click', async () => {
      await fillSection('project');
    });
    
    document.getElementById('autocard-btn-fill-skills').addEventListener('click', async () => {
      await fillSection('skills');
    });
    
    document.addEventListener('click', (e) => {
      const floatBtn = document.getElementById('autocard-float-btn');
      const panel = document.getElementById('autocard-float-panel');
      
      if (panel && panel.style.display === 'flex') {
        if (!floatBtn?.contains(e.target) && !panel.contains(e.target)) {
          panel.style.display = 'none';
        }
      }
    });
  }
  
  function updatePanelUI() {
    const statusDot = document.getElementById('autocard-data-status');
    const statusText = document.getElementById('autocard-data-status-text');
    const platformInfo = document.getElementById('autocard-platform-info');
    
    if (resumeData) {
      statusDot.classList.add('ready');
      const name = resumeData.personalInfo?.name || '未设置';
      const experiences = (resumeData.workExperiences?.length || 0) + 
                          (resumeData.educationExperiences?.length || 0);
      statusText.textContent = `已加载 (${name}, ${experiences} 条经历)`;
    } else {
      statusDot.classList.remove('ready');
      statusText.textContent = '未加载简历数据';
    }
    
    if (currentPlatform && PLATFORM_CONFIGS[currentPlatform]) {
      platformInfo.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 24px;">🌐</span>
          <div>
            <div style="font-weight: 600; color: #333;">${PLATFORM_CONFIGS[currentPlatform].name}</div>
            <div style="font-size: 12px; color: #888;">已加载平台特定选择器</div>
          </div>
        </div>
      `;
    } else {
      platformInfo.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 24px;">❓</span>
          <div>
            <div style="font-weight: 600; color: #333;">未识别平台</div>
            <div style="font-size: 12px; color: #888;">将使用通用字段定位策略</div>
          </div>
        </div>
      `;
    }
  }
  
  async function loadResumeData() {
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'getResumeData'
      });
      
      if (response && response.success && response.data) {
        resumeData = response.data;
        console.log('[AutoCard] 简历数据已加载:', resumeData);
        updatePanelUI();
        alert('简历数据加载成功！');
      } else {
        alert('未找到简历数据，请先在插件弹窗中设置。');
      }
    } catch (e) {
      console.error('[AutoCard] 加载简历数据失败:', e);
      alert('加载简历数据失败：' + e.message);
    }
  }
  
  async function fillAllFields() {
    if (!resumeData) {
      alert('请先加载简历数据！');
      return;
    }
    
    const platformSelectors = getPlatformSelectors();
    
    if (window.AutoCardFieldLocator) {
      window.AutoCardFieldLocator.setPlatformSelectors(platformSelectors);
    }
    
    if (window.AutoCardFormFiller) {
      window.AutoCardFormFiller.init(resumeData, platformSelectors);
      
      const results = await window.AutoCardFormFiller.fillAll();
      displayResults(results);
      
      await addFillHistory({
        action: 'fillAll',
        timestamp: new Date().toISOString(),
        results: results.map(r => ({
          fieldName: r.fieldName,
          success: r.success,
          value: r.value
        }))
      });
      
      const successCount = results.filter(r => r.success).length;
      const failCount = results.length - successCount;
      
      alert(`填写完成！\n成功: ${successCount} 个字段\n失败: ${failCount} 个字段`);
    }
  }
  
  async function fillSection(section) {
    if (!resumeData) {
      alert('请先加载简历数据！');
      return;
    }
    
    const platformSelectors = getPlatformSelectors();
    
    if (window.AutoCardFieldLocator) {
      window.AutoCardFieldLocator.setPlatformSelectors(platformSelectors);
    }
    
    if (window.AutoCardFormFiller) {
      window.AutoCardFormFiller.init(resumeData, platformSelectors);
      
      let results = [];
      
      switch (section) {
        case 'personal':
          results = await window.AutoCardFormFiller.fillPersonalInfo();
          break;
        case 'education':
          results = await window.AutoCardFormFiller.fillEducationExperiences();
          break;
        case 'work':
          results = await window.AutoCardFormFiller.fillWorkExperiences();
          break;
        case 'project':
          results = await window.AutoCardFormFiller.fillProjectExperiences();
          break;
        case 'skills':
          results = await window.AutoCardFormFiller.fillSkills();
          break;
      }
      
      displayResults(results);
      
      const successCount = results.filter(r => r.success).length;
      const failCount = results.length - successCount;
      
      alert(`填写完成！\n成功: ${successCount} 个字段\n失败: ${failCount} 个字段`);
    }
  }
  
  function displayResults(results) {
    const container = document.getElementById('autocard-results');
    if (!container) return;
    
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
          `<div class="autocard-result-value">${String(r.value).substring(0, 50)}${String(r.value).length > 50 ? '...' : ''}</div>`
        }
      </div>
    `).join('');
  }
  
  async function addFillHistory(item) {
    fillHistory.unshift(item);
    if (fillHistory.length > 100) {
      fillHistory = fillHistory.slice(0, 100);
    }
    
    try {
      await chrome.runtime.sendMessage({
        action: 'saveFillHistory',
        data: item
      });
    } catch (e) {
      console.error('[AutoCard] 保存历史记录失败:', e);
    }
  }
  
  function listenForMessages() {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      switch (request.action) {
        case 'setResumeData':
          resumeData = request.data;
          updatePanelUI();
          sendResponse({ success: true });
          break;
          
        case 'getResumeData':
          sendResponse({ success: true, data: resumeData });
          break;
          
        case 'fillAll':
          fillAllFields();
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
          
        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
      
      return true;
    });
  }
  
  init();
  
})();
