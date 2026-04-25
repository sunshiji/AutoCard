(function() {
  'use strict';
  
  let resumeData = null;
  let fillHistory = [];
  let currentTabId = null;
  
  const DEFAULT_RESUME_DATA = {
    personalInfo: {
      name: null,
      phone: null,
      email: null,
      gender: null,
      birthday: null,
      currentAddress: null,
      workYears: null,
      currentSalary: null,
      expectedSalary: null,
      jobStatus: null,
      selfIntroduction: null
    },
    educationExperiences: [],
    workExperiences: [],
    projectExperiences: [],
    skills: []
  };
  
  document.addEventListener('DOMContentLoaded', init);
  
  function init() {
    loadStoredData();
    loadCurrentTab();
    bindEvents();
    updateUI();
  }
  
  async function loadStoredData() {
    try {
      const result = await chrome.storage.local.get(['resumeData', 'fillHistory']);
      
      if (result.resumeData) {
        resumeData = result.resumeData;
      }
      
      if (result.fillHistory) {
        fillHistory = result.fillHistory;
      }
      
      updateUI();
    } catch (e) {
      console.error('[AutoCard] 加载存储数据失败:', e);
    }
  }
  
  async function loadCurrentTab() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) {
        currentTabId = tab.id;
        updatePlatformInfo(tab.url);
      }
    } catch (e) {
      console.error('[AutoCard] 获取当前标签页失败:', e);
    }
  }
  
  function bindEvents() {
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        switchTab(tabName);
      });
    });
    
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
      fileInput.addEventListener('change', handleFileUpload);
    }
    
    const btnPasteJson = document.getElementById('btn-paste-json');
    if (btnPasteJson) {
      btnPasteJson.addEventListener('click', handlePasteJson);
    }
    
    const btnManualInput = document.getElementById('btn-manual-input');
    if (btnManualInput) {
      btnManualInput.addEventListener('click', showManualInputModal);
    }
    
    const btnEditData = document.getElementById('btn-edit-data');
    if (btnEditData) {
      btnEditData.addEventListener('click', showManualInputModal);
    }
    
    const btnClearData = document.getElementById('btn-clear-data');
    if (btnClearData) {
      btnClearData.addEventListener('click', handleClearData);
    }
    
    const btnFillAll = document.getElementById('btn-fill-all');
    if (btnFillAll) {
      btnFillAll.addEventListener('click', () => executeFillAction('fillAll'));
    }
    
    const btnFillPersonal = document.getElementById('btn-fill-personal');
    if (btnFillPersonal) {
      btnFillPersonal.addEventListener('click', () => executeFillAction('personal'));
    }
    
    const btnFillEducation = document.getElementById('btn-fill-education');
    if (btnFillEducation) {
      btnFillEducation.addEventListener('click', () => executeFillAction('education'));
    }
    
    const btnFillWork = document.getElementById('btn-fill-work');
    if (btnFillWork) {
      btnFillWork.addEventListener('click', () => executeFillAction('work'));
    }
    
    const btnFillProject = document.getElementById('btn-fill-project');
    if (btnFillProject) {
      btnFillProject.addEventListener('click', () => executeFillAction('project'));
    }
    
    const btnFillSkills = document.getElementById('btn-fill-skills');
    if (btnFillSkills) {
      btnFillSkills.addEventListener('click', () => executeFillAction('skills'));
    }
    
    const btnShowPanel = document.getElementById('btn-show-panel');
    if (btnShowPanel) {
      btnShowPanel.addEventListener('click', showFloatingPanel);
    }
    
    const btnClearHistory = document.getElementById('btn-clear-history');
    if (btnClearHistory) {
      btnClearHistory.addEventListener('click', handleClearHistory);
    }
    
    const inputDelay = document.getElementById('input-delay');
    if (inputDelay) {
      inputDelay.addEventListener('change', saveSettings);
    }
    
    const clickDelay = document.getElementById('click-delay');
    if (clickDelay) {
      clickDelay.addEventListener('change', saveSettings);
    }
    
    const antiDetection = document.getElementById('anti-detection');
    if (antiDetection) {
      antiDetection.addEventListener('change', saveSettings);
    }
  }
  
  function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => {
      tab.classList.remove('active');
      if (tab.dataset.tab === tabName) {
        tab.classList.add('active');
      }
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.remove('active');
    });
    
    const content = document.getElementById(`tab-${tabName}`);
    if (content) {
      content.classList.add('active');
    }
  }
  
  function updateUI() {
    updateDataStatus();
    updateDataSummary();
    updateHistoryList();
  }
  
  function updateDataStatus() {
    const statusBadge = document.querySelector('#data-status .status-badge');
    const statusText = document.getElementById('status-text');
    
    if (resumeData && resumeData.personalInfo) {
      statusBadge.classList.add('ready');
      const name = resumeData.personalInfo.name || '未设置';
      statusText.textContent = `已加载 (${name})`;
    } else {
      statusBadge.classList.remove('ready');
      statusText.textContent = '未加载简历数据';
    }
  }
  
  function updateDataSummary() {
    const summarySection = document.getElementById('data-summary-section');
    const summary = document.getElementById('data-summary');
    
    if (!resumeData || !resumeData.personalInfo) {
      summarySection.style.display = 'none';
      return;
    }
    
    summarySection.style.display = 'block';
    
    const pi = resumeData.personalInfo;
    
    summary.innerHTML = `
      <div class="data-summary-item">
        <span class="data-summary-label">姓名</span>
        <span class="data-summary-value">${pi.name || '未填写'}</span>
      </div>
      <div class="data-summary-item">
        <span class="data-summary-label">手机</span>
        <span class="data-summary-value">${pi.phone || '未填写'}</span>
      </div>
      <div class="data-summary-item">
        <span class="data-summary-label">邮箱</span>
        <span class="data-summary-value">${pi.email || '未填写'}</span>
      </div>
      <div class="data-summary-item">
        <span class="data-summary-label">性别</span>
        <span class="data-summary-value">${pi.gender || '未填写'}</span>
      </div>
      <div class="data-summary-item">
        <span class="data-summary-label">教育经历</span>
        <span class="data-summary-value">${(resumeData.educationExperiences?.length || 0)} 条</span>
      </div>
      <div class="data-summary-item">
        <span class="data-summary-label">工作经历</span>
        <span class="data-summary-value">${(resumeData.workExperiences?.length || 0)} 条</span>
      </div>
      <div class="data-summary-item">
        <span class="data-summary-label">项目经历</span>
        <span class="data-summary-value">${(resumeData.projectExperiences?.length || 0)} 条</span>
      </div>
      <div class="data-summary-item">
        <span class="data-summary-label">技能</span>
        <span class="data-summary-value">${(resumeData.skills?.length || 0)} 个</span>
      </div>
    `;
  }
  
  function updatePlatformInfo(url) {
    const platformInfo = document.getElementById('platform-info');
    if (!url) {
      platformInfo.innerHTML = `
        <div class="icon">🔍</div>
        <div>请在求职网站页面使用</div>
      `;
      return;
    }
    
    const PLATFORM_CONFIGS = {
      liepin: { name: '猎聘', patterns: ['liepin.com', 'liepin'], icon: '🎯' },
      boss: { name: 'BOSS直聘', patterns: ['zhipin.com', 'boss'], icon: '💼' },
      beisen: { name: '北森招聘', patterns: ['zhiye.com', 'beisen', '北森'], icon: '🏢' }
    };
    
    let detectedPlatform = null;
    const urlLower = url.toLowerCase();
    
    for (const [key, config] of Object.entries(PLATFORM_CONFIGS)) {
      for (const pattern of config.patterns) {
        if (urlLower.includes(pattern.toLowerCase())) {
          detectedPlatform = { key, ...config };
          break;
        }
      }
      if (detectedPlatform) break;
    }
    
    if (detectedPlatform) {
      platformInfo.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; padding: 8px 0;">
          <span style="font-size: 32px;">${detectedPlatform.icon}</span>
          <div>
            <div style="font-weight: 600; color: #333;">${detectedPlatform.name}</div>
            <div style="font-size: 11px; color: #52c41a;">✓ 已识别平台</div>
          </div>
        </div>
      `;
    } else {
      platformInfo.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; padding: 8px 0;">
          <span style="font-size: 32px;">🌐</span>
          <div>
            <div style="font-weight: 600; color: #333;">通用模式</div>
            <div style="font-size: 11px; color: #666;">将使用通用字段定位策略</div>
          </div>
        </div>
      `;
    }
  }
  
  function updateHistoryList() {
    const historyList = document.getElementById('history-list');
    
    if (!fillHistory || fillHistory.length === 0) {
      historyList.innerHTML = `
        <div class="empty-state">
          <div class="icon">📭</div>
          <div>暂无填写记录</div>
        </div>
      `;
      return;
    }
    
    historyList.innerHTML = fillHistory.slice(0, 20).map(item => {
      const date = new Date(item.timestamp);
      const timeStr = date.toLocaleString('zh-CN');
      const actionNames = {
        fillAll: '填写全部',
        personal: '填写个人信息',
        education: '填写教育经历',
        work: '填写工作经历',
        project: '填写项目经历',
        skills: '填写技能'
      };
      
      const successCount = item.results?.filter(r => r.success).length || 0;
      const totalCount = item.results?.length || 0;
      
      return `
        <div class="history-item">
          <div class="history-time">${timeStr}</div>
          <div class="history-action">${actionNames[item.action] || item.action}</div>
          <div class="history-stats">成功: ${successCount}/${totalCount}</div>
        </div>
      `;
    }).join('');
  }
  
  async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
      const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      
      if (ext === '.json') {
        const text = await readFileAsText(file);
        const data = JSON.parse(text);
        setResumeData(data);
        alert('JSON 文件加载成功！');
      } else if (ext === '.pdf' || ext === '.docx') {
        alert('简历文件解析功能需要配合解析库使用。\n\n请将简历转换为 JSON 格式，或使用手动输入功能。');
      } else {
        alert('不支持的文件格式');
      }
    } catch (e) {
      console.error('[AutoCard] 文件处理失败:', e);
      alert('文件处理失败：' + e.message);
    }
  }
  
  function readFileAsText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = e => resolve(e.target.result);
      reader.onerror = e => reject(e);
      reader.readAsText(file);
    });
  }
  
  function handlePasteJson() {
    const jsonStr = prompt('请粘贴简历 JSON 数据：');
    if (jsonStr) {
      try {
        const data = JSON.parse(jsonStr);
        setResumeData(data);
        alert('JSON 数据加载成功！');
      } catch (e) {
        alert('JSON 格式错误：' + e.message);
      }
    }
  }
  
  function showManualInputModal() {
    const existingData = resumeData || JSON.parse(JSON.stringify(DEFAULT_RESUME_DATA));
    
    const modal = document.createElement('div');
    modal.id = 'autocard-modal';
    modal.innerHTML = `
      <div class="modal-overlay">
        <div class="modal-content">
          <div class="modal-header">
            <h3>📝 简历数据录入</h3>
            <button class="modal-close">&times;</button>
          </div>
          <div class="modal-body" style="max-height: 500px; overflow-y: auto;">
            <div class="form-section">
              <div class="form-section-title">👤 基本信息</div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">姓名 *</label>
                  <input type="text" class="form-input" id="mi-name" value="${existingData.personalInfo?.name || ''}" placeholder="请输入姓名">
                </div>
                <div class="form-group">
                  <label class="form-label">性别</label>
                  <select class="form-input" id="mi-gender">
                    <option value="">请选择</option>
                    <option value="男" ${existingData.personalInfo?.gender === '男' ? 'selected' : ''}>男</option>
                    <option value="女" ${existingData.personalInfo?.gender === '女' ? 'selected' : ''}>女</option>
                  </select>
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">手机号 *</label>
                  <input type="text" class="form-input" id="mi-phone" value="${existingData.personalInfo?.phone || ''}" placeholder="请输入手机号">
                </div>
                <div class="form-group">
                  <label class="form-label">邮箱 *</label>
                  <input type="email" class="form-input" id="mi-email" value="${existingData.personalInfo?.email || ''}" placeholder="请输入邮箱">
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">自我介绍</label>
                <textarea class="form-input form-textarea" id="mi-intro" placeholder="请输入自我介绍">${existingData.personalInfo?.selfIntroduction || ''}</textarea>
              </div>
            </div>
            
            <div class="form-section">
              <div class="form-section-title">🛠 技能</div>
              <div class="form-group">
                <label class="form-label">技能标签（用逗号分隔）</label>
                <input type="text" class="form-input" id="mi-skills" value="${(existingData.skills || []).join('、')}" placeholder="例如：Java, Python, React">
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" id="modal-cancel">取消</button>
            <button class="btn btn-primary" id="modal-save">保存</button>
          </div>
        </div>
      </div>
    `;
    
    const style = document.createElement('style');
    style.textContent = `
      .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        padding: 16px;
      }
      .modal-content {
        background: white;
        border-radius: 12px;
        width: 100%;
        max-width: 500px;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
      }
      .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        border-bottom: 1px solid #e8e8e8;
      }
      .modal-header h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
      .modal-close {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #666;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background 0.2s;
      }
      .modal-close:hover {
        background: #f0f0f0;
      }
      .modal-body {
        padding: 16px 20px;
        overflow-y: auto;
      }
      .modal-footer {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        padding: 16px 20px;
        border-top: 1px solid #e8e8e8;
      }
      .modal-footer .btn {
        width: auto;
        padding: 10px 24px;
      }
      .form-section {
        margin-bottom: 20px;
      }
      .form-section:last-child {
        margin-bottom: 0;
      }
      .form-section-title {
        font-weight: 600;
        font-size: 14px;
        color: #333;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #e8e8e8;
      }
      .form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
    
    const closeBtn = modal.querySelector('.modal-close');
    const cancelBtn = modal.querySelector('#modal-cancel');
    const saveBtn = modal.querySelector('#modal-save');
    
    closeBtn.addEventListener('click', () => modal.remove());
    cancelBtn.addEventListener('click', () => modal.remove());
    
    saveBtn.addEventListener('click', () => {
      const name = document.getElementById('mi-name').value.trim();
      const phone = document.getElementById('mi-phone').value.trim();
      const email = document.getElementById('mi-email').value.trim();
      
      if (!name) {
        alert('请输入姓名');
        return;
      }
      if (!phone) {
        alert('请输入手机号');
        return;
      }
      if (!email) {
        alert('请输入邮箱');
        return;
      }
      
      const newData = {
        personalInfo: {
          name: name,
          phone: phone,
          email: email,
          gender: document.getElementById('mi-gender').value || null,
          selfIntroduction: document.getElementById('mi-intro').value.trim() || null
        },
        educationExperiences: existingData.educationExperiences || [],
        workExperiences: existingData.workExperiences || [],
        projectExperiences: existingData.projectExperiences || [],
        skills: document.getElementById('mi-skills').value
          .split(/[,，、\s]+/)
          .filter(s => s.trim())
      };
      
      setResumeData(newData);
      modal.remove();
      alert('数据保存成功！');
    });
  }
  
  function setResumeData(data) {
    resumeData = data;
    saveResumeData();
    updateUI();
    sendDataToContentScript();
  }
  
  async function saveResumeData() {
    try {
      await chrome.storage.local.set({ resumeData: resumeData });
      console.log('[AutoCard] 简历数据已保存');
    } catch (e) {
      console.error('[AutoCard] 保存简历数据失败:', e);
    }
  }
  
  async function sendDataToContentScript() {
    if (!currentTabId) return;
    
    try {
      await chrome.tabs.sendMessage(currentTabId, {
        action: 'setResumeData',
        data: resumeData
      });
    } catch (e) {
      console.log('[AutoCard] 无法发送数据到内容脚本:', e);
    }
  }
  
  async function handleClearData() {
    if (confirm('确定要清除所有简历数据吗？')) {
      resumeData = null;
      try {
        await chrome.storage.local.remove('resumeData');
        updateUI();
        alert('数据已清除');
      } catch (e) {
        alert('清除失败：' + e.message);
      }
    }
  }
  
  async function handleClearHistory() {
    if (confirm('确定要清除所有填写历史吗？')) {
      fillHistory = [];
      try {
        await chrome.storage.local.remove('fillHistory');
        updateUI();
        alert('历史已清除');
      } catch (e) {
        alert('清除失败：' + e.message);
      }
    }
  }
  
  async function executeFillAction(action) {
    if (!resumeData) {
      alert('请先加载简历数据！');
      return;
    }
    
    if (!currentTabId) {
      alert('无法获取当前标签页！');
      return;
    }
    
    try {
      await chrome.tabs.sendMessage(currentTabId, {
        action: action === 'fillAll' ? 'fillAll' : 'fillSection',
        section: action === 'fillAll' ? null : action
      });
    } catch (e) {
      console.error('[AutoCard] 执行填写操作失败:', e);
      alert('执行失败：' + e.message + '\n\n请确保当前页面已加载 AutoCard 内容脚本。');
    }
  }
  
  async function showFloatingPanel() {
    if (!currentTabId) {
      alert('无法获取当前标签页！');
      return;
    }
    
    try {
      await chrome.tabs.sendMessage(currentTabId, {
        action: 'showPanel'
      });
      window.close();
    } catch (e) {
      console.error('[AutoCard] 显示面板失败:', e);
      alert('操作失败：' + e.message);
    }
  }
  
  async function saveSettings() {
    const inputDelay = document.getElementById('input-delay')?.value || 150;
    const clickDelay = document.getElementById('click-delay')?.value || 300;
    const antiDetection = document.getElementById('anti-detection')?.checked ?? true;
    
    try {
      await chrome.storage.local.set({
        settings: {
          inputDelay: parseInt(inputDelay),
          clickDelay: parseInt(clickDelay),
          antiDetection: antiDetection
        }
      });
    } catch (e) {
      console.error('[AutoCard] 保存设置失败:', e);
    }
  }
  
})();
