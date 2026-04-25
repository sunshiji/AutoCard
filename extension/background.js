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
    loginIndicators: ['登录', '扫码登录', '微信登录', 'input[type="password"]'],
    fieldSelectors: {}
  },
  boss: {
    name: 'BOSS直聘',
    patterns: ['zhipin.com', 'boss'],
    loginIndicators: ['登录', '扫码登录', '微信登录'],
    fieldSelectors: {}
  },
  beisen: {
    name: '北森招聘',
    patterns: ['zhiye.com', 'beisen', '北森'],
    loginIndicators: ['登录', '扫码登录'],
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

const FIELD_MAPPINGS = {
  name: ['姓名', '名字', '真实姓名', 'name', 'fullName', 'realName'],
  phone: ['手机号', '手机号码', '电话', '联系电话', '手机', 'phone', 'mobile', 'telephone'],
  email: ['邮箱', '电子邮箱', 'email', 'mail'],
  gender: ['性别', 'gender', 'sex'],
  birthday: ['生日', '出生日期', '出生年月', 'birthday', 'birthDate'],
  education: ['学历', '教育程度', 'education', 'degree'],
  school: ['学校', '毕业院校', '院校', 'school', 'university', 'college'],
  major: ['专业', '所学专业', 'major'],
  startDate: ['开始时间', '起始时间', '入学时间', 'startDate', 'beginDate'],
  endDate: ['结束时间', '终止时间', '毕业时间', 'endDate', 'finishDate'],
  company: ['公司', '公司名称', '企业', 'company', 'enterprise', 'corporation'],
  position: ['职位', '岗位', '职务', 'position', 'post', 'jobTitle'],
  workDescription: ['工作描述', '工作内容', '职责描述', 'workDescription', 'jobDescription'],
  projectName: ['项目名称', '项目名', 'projectName', 'project'],
  projectRole: ['项目角色', '担任角色', 'projectRole', 'role'],
  projectDescription: ['项目描述', '项目介绍', 'projectDescription'],
  skill: ['技能', '专业技能', 'skill', 'ability', 'expertise'],
  selfIntroduction: ['自我介绍', '个人简介', '自我评价', 'selfIntroduction', 'introduction', 'evaluation']
};

const CONFIG = {
  inputDelayMin: 100,
  inputDelayMax: 300,
  clickDelayMin: 200,
  clickDelayMax: 500,
  elementWaitTimeout: 10000,
  antiDetectionEnabled: true,
  mouseMovementSimulation: true
};

let resumeData = null;
let currentPlatform = null;
let fillHistory = [];

async function loadResumeData() {
  try {
    const result = await chrome.storage.local.get('resumeData');
    if (result.resumeData) {
      resumeData = { ...DEFAULT_RESUME_DATA, ...result.resumeData };
    } else {
      resumeData = JSON.parse(JSON.stringify(DEFAULT_RESUME_DATA));
    }
    return resumeData;
  } catch (error) {
    console.error('[AutoCard] 加载简历数据失败:', error);
    resumeData = JSON.parse(JSON.stringify(DEFAULT_RESUME_DATA));
    return resumeData;
  }
}

async function saveResumeData(data) {
  try {
    resumeData = data;
    await chrome.storage.local.set({ resumeData: data });
    return true;
  } catch (error) {
    console.error('[AutoCard] 保存简历数据失败:', error);
    return false;
  }
}

function detectPlatform(url) {
  const urlLower = url.toLowerCase();
  
  for (const [platformKey, config] of Object.entries(PLATFORM_CONFIGS)) {
    for (const pattern of config.patterns) {
      if (urlLower.includes(pattern.toLowerCase())) {
        currentPlatform = platformKey;
        return platformKey;
      }
    }
  }
  
  currentPlatform = null;
  return null;
}

function getPlatformSelectors(platform) {
  if (platform && PLATFORM_CONFIGS[platform]) {
    return PLATFORM_CONFIGS[platform].fieldSelectors || {};
  }
  return {};
}

function getFieldMappings(fieldName) {
  return FIELD_MAPPINGS[fieldName] || [fieldName];
}

async function addFillHistory(action) {
  const historyItem = {
    id: Date.now(),
    timestamp: new Date().toISOString(),
    ...action
  };
  
  fillHistory.unshift(historyItem);
  
  if (fillHistory.length > 100) {
    fillHistory = fillHistory.slice(0, 100);
  }
  
  try {
    await chrome.storage.local.set({ fillHistory: fillHistory });
  } catch (error) {
    console.error('[AutoCard] 保存历史记录失败:', error);
  }
  
  return historyItem;
}

async function getFillHistory() {
  if (fillHistory.length > 0) {
    return fillHistory;
  }
  
  try {
    const result = await chrome.storage.local.get('fillHistory');
    fillHistory = result.fillHistory || [];
    return fillHistory;
  } catch (error) {
    console.error('[AutoCard] 加载历史记录失败:', error);
    return [];
  }
}

async function clearFillHistory() {
  fillHistory = [];
  try {
    await chrome.storage.local.remove('fillHistory');
    return true;
  } catch (error) {
    console.error('[AutoCard] 清除历史记录失败:', error);
    return false;
  }
}

function randomDelay(min, max) {
  return new Promise(resolve => {
    const delay = Math.random() * (max - min) + min;
    setTimeout(resolve, delay);
  });
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

function isObjectEmpty(obj) {
  if (!obj) return true;
  return Object.keys(obj).every(key => {
    const value = obj[key];
    if (value === null || value === undefined || value === '') return true;
    if (Array.isArray(value) && value.length === 0) return true;
    if (typeof value === 'object' && !Array.isArray(value)) {
      return isObjectEmpty(value);
    }
    return false;
  });
}

export {
  DEFAULT_RESUME_DATA,
  PLATFORM_CONFIGS,
  FIELD_MAPPINGS,
  CONFIG,
  resumeData,
  currentPlatform,
  fillHistory,
  loadResumeData,
  saveResumeData,
  detectPlatform,
  getPlatformSelectors,
  getFieldMappings,
  addFillHistory,
  getFillHistory,
  clearFillHistory,
  randomDelay,
  deepMerge,
  isObjectEmpty
};
