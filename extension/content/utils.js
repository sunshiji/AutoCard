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

function escapeXpathText(text) {
  if (text.includes("'") && text.includes('"')) {
    const parts = text.split("'");
    const escaped = parts.map(p => `'${p}'`).join(", \"'\", ");
    return `concat(${escaped})`;
  } else if (text.includes("'")) {
    return `"${text}"`;
  } else {
    return `'${text}'`;
  }
}

function textMatches(source, target) {
  if (!source || !target) return false;
  
  const sourceLower = source.toLowerCase();
  const targetLower = target.toLowerCase();
  
  if (sourceLower === targetLower) return true;
  if (targetLower.includes(sourceLower)) return true;
  if (sourceLower.includes(targetLower)) return true;
  
  return false;
}

function valuesMatch(actual, expected) {
  if (!actual && !expected) return true;
  
  const actualLower = String(actual).toLowerCase().trim();
  const expectedLower = String(expected).toLowerCase().trim();
  
  if (actualLower === expectedLower) return true;
  if (expectedLower.includes(actualLower)) return true;
  if (actualLower.includes(expectedLower)) return true;
  
  const actualClean = actualLower.replace(/[\s\-_./\u4e00-\u9fa5]/g, '');
  const expectedClean = expectedLower.replace(/[\s\-_./\u4e00-\u9fa5]/g, '');
  
  if (actualClean === expectedClean) return true;
  
  if (actualClean.length > 0 && expectedClean.length > 0) {
    if (actualClean.includes(expectedClean) || expectedClean.includes(actualClean)) {
      return true;
    }
  }
  
  return false;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getOrCreateShadowRoot(element) {
  if (!element) return null;
  
  if (element.shadowRoot) {
    return element.shadowRoot;
  }
  
  if (element.attachShadow) {
    try {
      return element.attachShadow({ mode: 'open' });
    } catch (e) {
      return null;
    }
  }
  
  return null;
}

function getAllFrameContexts() {
  const frames = [];
  
  function collectFrames(frameList) {
    for (const frame of frameList) {
      try {
        if (frame.document) {
          frames.push(frame.document);
        }
        if (frame.frames) {
          collectFrames(frame.frames);
        }
      } catch (e) {
        continue;
      }
    }
  }
  
  collectFrames(window.frames);
  return frames;
}

function getElementInfo(element) {
  if (!element) return null;
  
  const rect = element.getBoundingClientRect();
  const style = window.getComputedStyle(element);
  
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  const topElement = document.elementFromPoint(centerX, centerY);
  
  let isBlocked = false;
  let blockingElement = null;
  
  if (topElement && !element.contains(topElement) && topElement !== element) {
    const topStyle = window.getComputedStyle(topElement);
    const topPointerEvents = topStyle.pointerEvents;
    const topDisplay = topStyle.display;
    const topVisibility = topStyle.visibility;
    const topOpacity = topStyle.opacity;
    
    if (topPointerEvents === 'auto' && 
        topDisplay !== 'none' && 
        topVisibility !== 'hidden' &&
        topOpacity !== '0') {
      isBlocked = true;
      blockingElement = topElement.tagName + (topElement.className ? '.' + topElement.className.split(' ')[0] : '');
    }
  }
  
  return {
    tagName: element.tagName,
    type: element.type || null,
    name: element.name || null,
    id: element.id || null,
    value: element.value || '',
    isVisible: rect.width > 0 && rect.height > 0,
    isEnabled: !element.disabled,
    isReadOnly: element.readOnly,
    pointerEvents: style.pointerEvents,
    display: style.display,
    visibility: style.visibility,
    opacity: style.opacity,
    rect: {
      top: rect.top,
      left: rect.left,
      width: rect.width,
      height: rect.height
    },
    isInViewport: rect.top >= 0 && rect.left >= 0 && 
                 rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                 rect.right <= (window.innerWidth || document.documentElement.clientWidth),
    isBlocked: isBlocked,
    blockingElement: blockingElement,
    isInteractable: !element.disabled && 
                   !element.readOnly && 
                   rect.width > 0 && 
                   rect.height > 0 &&
                   style.display !== 'none' &&
                   style.visibility !== 'hidden' &&
                   style.opacity !== '0' &&
                   !isBlocked
  };
}

function generateSelector(element) {
  if (element.id && !element.id.startsWith('__')) {
    if (/^[a-zA-Z_-][a-zA-Z0-9_-]*$/.test(element.id)) {
      return `#${element.id}`;
    } else {
      const tagName = element.tagName.toLowerCase();
      return `${tagName}[id="${element.id}"]`;
    }
  }
  
  if (element.name) {
    const tagName = element.tagName.toLowerCase();
    return `${tagName}[name="${element.name}"]`;
  }
  
  if (element.placeholder) {
    const tagName = element.tagName.toLowerCase();
    return `${tagName}[placeholder="${element.placeholder}"]`;
  }
  
  const path = [];
  let current = element;
  
  while (current && current.nodeType === Node.ELEMENT_NODE) {
    let selector = current.tagName.toLowerCase();
    
    if (current.id) {
      const idStr = current.id;
      if (/^[a-zA-Z_-][a-zA-Z0-9_-]*$/.test(idStr)) {
        selector += '#' + idStr;
      } else {
        selector += `[id="${idStr}"]`;
      }
      path.unshift(selector);
      break;
    } else {
      let sibling = current;
      let nth = 1;
      while (sibling = sibling.previousElementSibling) {
        if (sibling.tagName.toLowerCase() === selector) nth++;
      }
      if (nth > 1) selector += `:nth-of-type(${nth})`;
    }
    
    path.unshift(selector);
    current = current.parentNode;
  }
  
  return path.join(' > ') || 'input';
}

console.log('[AutoCard] utils.js 已加载');

window.AutoCardUtils = {
  DEFAULT_RESUME_DATA,
  PLATFORM_CONFIGS,
  FIELD_MAPPINGS,
  CONFIG,
  resumeData,
  currentPlatform,
  fillHistory,
  randomDelay,
  deepMerge,
  isObjectEmpty,
  escapeXpathText,
  textMatches,
  valuesMatch,
  sleep,
  getOrCreateShadowRoot,
  getAllFrameContexts,
  getElementInfo,
  generateSelector
};
