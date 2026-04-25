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

let resumeData = null;
let fillHistory = [];

async function init() {
  console.log('[AutoCard] Background Service Worker 启动');
  await loadDataFromStorage();
  setupMessageListeners();
}

async function loadDataFromStorage() {
  try {
    const result = await chrome.storage.local.get(['resumeData', 'fillHistory']);
    
    if (result.resumeData) {
      resumeData = deepMerge(DEFAULT_RESUME_DATA, result.resumeData);
      console.log('[AutoCard] 已加载简历数据:', resumeData.personalInfo?.name || '空');
    } else {
      resumeData = JSON.parse(JSON.stringify(DEFAULT_RESUME_DATA));
    }
    
    if (result.fillHistory) {
      fillHistory = result.fillHistory;
      console.log('[AutoCard] 已加载历史记录:', fillHistory.length, '条');
    }
  } catch (error) {
    console.error('[AutoCard] 加载数据失败:', error);
    resumeData = JSON.parse(JSON.stringify(DEFAULT_RESUME_DATA));
    fillHistory = [];
  }
}

function setupMessageListeners() {
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('[AutoCard] Background 收到消息:', request.action, '来自:', sender.id);
    
    switch (request.action) {
      case 'getResumeData':
        handleGetResumeData(sendResponse);
        break;
        
      case 'setResumeData':
        handleSetResumeData(request.data, sendResponse);
        break;
        
      case 'saveFillHistory':
        handleSaveFillHistory(request.data, sendResponse);
        break;
        
      case 'getFillHistory':
        handleGetFillHistory(sendResponse);
        break;
        
      case 'getPlatformConfigs':
        handleGetPlatformConfigs(sendResponse);
        break;
        
      case 'detectPlatform':
        handleDetectPlatform(request.url, sendResponse);
        break;
        
      default:
        console.log('[AutoCard] 未知消息类型:', request.action);
        sendResponse({ success: false, error: 'Unknown action: ' + request.action });
    }
    
    return true;
  });
}

async function handleGetResumeData(sendResponse) {
  console.log('[AutoCard] 返回简历数据:', resumeData?.personalInfo?.name);
  sendResponse({ 
    success: true, 
    data: resumeData,
    hasData: resumeData && resumeData.personalInfo && resumeData.personalInfo.name !== null
  });
}

async function handleSetResumeData(data, sendResponse) {
  try {
    console.log('[AutoCard] 保存简历数据:', data?.personalInfo?.name);
    
    resumeData = deepMerge(DEFAULT_RESUME_DATA, data);
    
    await chrome.storage.local.set({ resumeData: resumeData });
    
    sendResponse({ success: true });
    
    await broadcastToContentScripts({
      action: 'resumeDataUpdated',
      data: resumeData
    });
    
  } catch (error) {
    console.error('[AutoCard] 保存简历数据失败:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleSaveFillHistory(item, sendResponse) {
  try {
    console.log('[AutoCard] 保存历史记录');
    
    fillHistory.unshift(item);
    if (fillHistory.length > 100) {
      fillHistory = fillHistory.slice(0, 100);
    }
    
    await chrome.storage.local.set({ fillHistory: fillHistory });
    
    sendResponse({ success: true });
    
  } catch (error) {
    console.error('[AutoCard] 保存历史记录失败:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleGetFillHistory(sendResponse) {
  sendResponse({ success: true, data: fillHistory });
}

async function handleGetPlatformConfigs(sendResponse) {
  sendResponse({ success: true, data: PLATFORM_CONFIGS });
}

async function handleDetectPlatform(url, sendResponse) {
  let detectedPlatform = null;
  const urlLower = (url || '').toLowerCase();
  
  for (const [platformKey, config] of Object.entries(PLATFORM_CONFIGS)) {
    for (const pattern of config.patterns) {
      if (urlLower.includes(pattern.toLowerCase())) {
        detectedPlatform = { key: platformKey, ...config };
        console.log('[AutoCard] 检测到平台:', config.name);
        break;
      }
    }
    if (detectedPlatform) break;
  }
  
  sendResponse({ success: true, platform: detectedPlatform });
}

async function broadcastToContentScripts(message) {
  try {
    const tabs = await chrome.tabs.query({});
    
    for (const tab of tabs) {
      try {
        await chrome.tabs.sendMessage(tab.id, message);
      } catch (e) {
      }
    }
  } catch (e) {
    console.log('[AutoCard] 广播消息时部分标签页未响应');
  }
}

function deepMerge(target, source) {
  if (!source) return { ...target };
  if (!target) return { ...source };
  
  const result = { ...target };
  
  for (const key in source) {
    if (source[key] !== undefined && source[key] !== null) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = deepMerge(target[key] || {}, source[key]);
      } else if (Array.isArray(source[key])) {
        result[key] = [...source[key]];
      } else {
        result[key] = source[key];
      }
    }
  }
  
  return result;
}

chrome.runtime.onInstalled.addListener((details) => {
  console.log('[AutoCard] 插件已安装/更新:', details.reason);
  init();
});

chrome.runtime.onStartup.addListener(() => {
  console.log('[AutoCard] 浏览器启动');
  init();
});

init();

console.log('[AutoCard] Background Service Worker 已初始化');
