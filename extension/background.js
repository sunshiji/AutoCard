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

chrome.runtime.onInstalled.addListener(async () => {
  console.log('[AutoCard] 插件已安装');
  await loadResumeData();
  await loadFillHistory();
});

chrome.runtime.onStartup.addListener(async () => {
  console.log('[AutoCard] 浏览器启动');
  await loadResumeData();
  await loadFillHistory();
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[AutoCard] 收到消息:', request.action);
  
  switch (request.action) {
    case 'getResumeData':
      handleGetResumeData(sendResponse);
      break;
      
    case 'saveResumeData':
      handleSaveResumeData(request.data, sendResponse);
      break;
      
    case 'saveFillHistory':
      handleSaveFillHistory(request.data, sendResponse);
      break;
      
    default:
      sendResponse({ success: false, error: 'Unknown action' });
  }
  
  return true;
});

async function handleGetResumeData(sendResponse) {
  if (resumeData) {
    sendResponse({ success: true, data: resumeData });
  } else {
    const data = await loadResumeData();
    sendResponse({ success: true, data: data });
  }
}

async function handleSaveResumeData(data, sendResponse) {
  try {
    resumeData = data;
    await chrome.storage.local.set({ resumeData: data });
    console.log('[AutoCard] 简历数据已保存');
    sendResponse({ success: true });
  } catch (error) {
    console.error('[AutoCard] 保存简历数据失败:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleSaveFillHistory(item, sendResponse) {
  try {
    fillHistory.unshift(item);
    if (fillHistory.length > 100) {
      fillHistory = fillHistory.slice(0, 100);
    }
    await chrome.storage.local.set({ fillHistory: fillHistory });
    console.log('[AutoCard] 历史记录已保存');
    sendResponse({ success: true });
  } catch (error) {
    console.error('[AutoCard] 保存历史记录失败:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function loadResumeData() {
  try {
    const result = await chrome.storage.local.get('resumeData');
    if (result.resumeData) {
      resumeData = deepMerge(DEFAULT_RESUME_DATA, result.resumeData);
    } else {
      resumeData = JSON.parse(JSON.stringify(DEFAULT_RESUME_DATA));
    }
    console.log('[AutoCard] 简历数据已加载');
    return resumeData;
  } catch (error) {
    console.error('[AutoCard] 加载简历数据失败:', error);
    resumeData = JSON.parse(JSON.stringify(DEFAULT_RESUME_DATA));
    return resumeData;
  }
}

async function loadFillHistory() {
  try {
    const result = await chrome.storage.local.get('fillHistory');
    fillHistory = result.fillHistory || [];
    console.log('[AutoCard] 历史记录已加载:', fillHistory.length, '条');
    return fillHistory;
  } catch (error) {
    console.error('[AutoCard] 加载历史记录失败:', error);
    fillHistory = [];
    return fillHistory;
  }
}

function deepMerge(target, source) {
  const result = { ...target };
  
  for (const key in source) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      result[key] = deepMerge(target[key] || {}, source[key]);
    } else if (source[key] !== undefined && source[key] !== null) {
      result[key] = source[key];
    }
  }
  
  return result;
}

console.log('[AutoCard] background.js 已加载');
