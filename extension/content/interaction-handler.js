(function() {
  'use strict';
  
  const CONFIG = {
    inputDelayMin: 100,
    inputDelayMax: 300,
    clickDelayMin: 200,
    clickDelayMax: 500
  };
  
  let lastInteractionTime = 0;
  
  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  function randomDelay(min, max) {
    const delay = Math.random() * (max - min) + min;
    return sleep(delay);
  }
  
  async function waitHumanLike(minDelay, maxDelay) {
    const min = minDelay || CONFIG.inputDelayMin;
    const max = maxDelay || CONFIG.inputDelayMax;
    return randomDelay(min, max);
  }
  
  function getIframe(iframeSelector, iframeUrlPattern) {
    if (iframeSelector) {
      const iframe = document.querySelector(iframeSelector);
      if (iframe) {
        return iframe.contentDocument || iframe.contentWindow?.document;
      }
    }
    
    if (iframeUrlPattern) {
      for (const frame of window.frames) {
        try {
          if (frame.location.href.includes(iframeUrlPattern)) {
            return frame.document;
          }
        } catch (e) {
          continue;
        }
      }
    }
    
    return null;
  }
  
  async function waitForDynamicContent(selector, timeout = 10000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const element = document.querySelector(selector);
      if (element && element.offsetParent !== null) {
        return element;
      }
      await sleep(100);
    }
    
    return null;
  }
  
  async function waitForDynamicContentToDisappear(selector, timeout = 10000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const element = document.querySelector(selector);
      if (!element || element.offsetParent === null) {
        return true;
      }
      await sleep(100);
    }
    
    return false;
  }
  
  async function scrollToLoadMore(direction = 'down', iterations = 3) {
    for (let i = 0; i < iterations; i++) {
      if (direction === 'down') {
        window.scrollTo(0, document.body.scrollHeight);
      } else {
        window.scrollTo(0, 0);
      }
      await randomDelay(500, 1000);
    }
  }
  
  async function handleSelectDropdown(element, value, label) {
    if (!element) return false;
    
    const tagName = element.tagName.toLowerCase();
    
    if (tagName === 'select') {
      try {
        if (value) {
          element.value = value;
          triggerSelectEvents(element);
          return true;
        } else if (label) {
          const options = element.querySelectorAll('option');
          for (const opt of options) {
            const optText = (opt.textContent || '').trim();
            if (textMatches(optText, label)) {
              opt.selected = true;
              triggerSelectEvents(element);
              return true;
            }
          }
        }
      } catch (e) {
        console.log(`[AutoCard] 原生 select 填充失败: ${e}`);
      }
    }
    
    return handleCustomDropdown(element, value, label);
  }
  
  async function handleCustomDropdown(triggerElement, value, label) {
    if (!triggerElement) return false;
    
    try {
      triggerElement.click();
      await randomDelay(300, 500);
      
      const optionSelectors = [
        'li',
        '.dropdown-item',
        '.option',
        "[role='option']",
        '.el-select-dropdown__item',
        '.ant-select-dropdown-menu-item',
        '.select-option',
        '.combobox-option'
      ];
      
      for (const sel of optionSelectors) {
        try {
          const options = document.querySelectorAll(sel);
          for (const option of options) {
            const optionText = (option.textContent || '').trim();
            
            if (value && option.getAttribute('value') === value) {
              option.click();
              await randomDelay(200, 300);
              return true;
            }
            
            if (label && textMatches(optionText, label)) {
              option.click();
              await randomDelay(200, 300);
              return true;
            }
          }
        } catch (e) {
          continue;
        }
      }
      
      return false;
    } catch (e) {
      console.log(`[AutoCard] 自定义下拉框处理失败: ${e}`);
      return false;
    }
  }
  
  async function handleDatePicker(element, dateValue, config) {
    if (!element) return false;
    
    const defaultConfig = {
      format: 'YYYY-MM-DD',
      useInputDirectly: true
    };
    
    const dateConfig = { ...defaultConfig, ...config };
    
    if (dateConfig.useInputDirectly) {
      try {
        let dateStr;
        if (dateValue instanceof Date) {
          dateStr = formatDate(dateValue, dateConfig.format);
        } else {
          dateStr = String(dateValue);
        }
        
        element.click();
        await randomDelay(100, 200);
        
        element.value = '';
        await randomDelay(50, 100);
        
        element.value = dateStr;
        element.setAttribute('value', dateStr);
        
        triggerInputEvents(element);
        
        await randomDelay(200, 300);
        
        if (element.value === dateStr || element.getAttribute('value') === dateStr) {
          return true;
        }
      } catch (e) {
        console.log(`[AutoCard] 日期直接输入失败: ${e}`);
      }
    }
    
    return handleCalendarDatePicker(element, dateValue, dateConfig);
  }
  
  async function handleCalendarDatePicker(element, dateValue, config) {
    if (!element) return false;
    
    let targetYear, targetMonth, targetDay;
    
    if (dateValue instanceof Date) {
      targetYear = dateValue.getFullYear();
      targetMonth = dateValue.getMonth() + 1;
      targetDay = dateValue.getDate();
    } else {
      const match = String(dateValue).match(/(\d{4})[-/年](\d{1,2})[-/月]?(\d{0,2})/);
      if (match) {
        targetYear = parseInt(match[1]);
        targetMonth = parseInt(match[2]);
        targetDay = parseInt(match[3] || '1');
      } else {
        return false;
      }
    }
    
    element.click();
    await randomDelay(200, 300);
    
    const calendarSelectors = [
      '.el-date-picker',
      '.ant-calendar',
      '.datepicker-dropdown',
      '.ui-datepicker',
      "[role='dialog']",
      '.mx-datepicker'
    ];
    
    let calendar = null;
    for (const sel of calendarSelectors) {
      calendar = document.querySelector(sel);
      if (calendar) break;
    }
    
    if (!calendar) {
      console.log('[AutoCard] 未找到日历控件');
      return false;
    }
    
    const maxAttempts = 24;
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      const currentYear = getCurrentCalendarYear(calendar);
      const currentMonth = getCurrentCalendarMonth(calendar);
      
      if (currentYear === targetYear && currentMonth === targetMonth) {
        break;
      }
      
      if (currentYear > targetYear || (currentYear === targetYear && currentMonth > targetMonth)) {
        clickPreviousMonth(calendar);
      } else {
        clickNextMonth(calendar);
      }
      
      await randomDelay(200, 400);
      attempts++;
    }
    
    const dayElement = findDayElement(calendar, targetDay);
    if (dayElement) {
      dayElement.click();
      await randomDelay(200, 300);
      return true;
    }
    
    return false;
  }
  
  function getCurrentCalendarYear(calendar) {
    const yearSelectors = [
      '.el-date-picker__header-label',
      '.ant-calendar-year-select',
      '.datepicker-years',
      '.ui-datepicker-year',
      '[data-year]',
      '.mx-calendar-header-year'
    ];
    
    for (const sel of yearSelectors) {
      const elem = calendar.querySelector(sel);
      if (elem) {
        const text = elem.textContent || '';
        const yearMatch = text.match(/(\d{4})/);
        if (yearMatch) {
          return parseInt(yearMatch[1]);
        }
        
        const dataYear = elem.getAttribute('data-year');
        if (dataYear) {
          return parseInt(dataYear);
        }
      }
    }
    
    return new Date().getFullYear();
  }
  
  function getCurrentCalendarMonth(calendar) {
    const monthMap = {
      '一月': 1, '二月': 2, '三月': 3, '四月': 4, '五月': 5, '六月': 6,
      '七月': 7, '八月': 8, '九月': 9, '十月': 10, '十一月': 11, '十二月': 12,
      '1月': 1, '2月': 2, '3月': 3, '4月': 4, '5月': 5, '6月': 6,
      '7月': 7, '8月': 8, '9月': 9, '10月': 10, '11月': 11, '12月': 12,
      'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
      'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12,
      'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
      'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    };
    
    const monthSelectors = [
      '.el-date-picker__header-label',
      '.ant-calendar-month-select',
      '.datepicker-months',
      '.ui-datepicker-month',
      '[data-month]',
      '.mx-calendar-header-month'
    ];
    
    for (const sel of monthSelectors) {
      const elem = calendar.querySelector(sel);
      if (elem) {
        const text = elem.textContent || '';
        
        for (const [monthName, monthNum] of Object.entries(monthMap)) {
          if (text.includes(monthName)) {
            return monthNum;
          }
        }
        
        const dataMonth = elem.getAttribute('data-month');
        if (dataMonth) {
          return parseInt(dataMonth) + 1;
        }
        
        const monthMatch = text.match(/(\d{1,2})月?/);
        if (monthMatch) {
          return parseInt(monthMatch[1]);
        }
      }
    }
    
    return new Date().getMonth() + 1;
  }
  
  function clickPreviousMonth(calendar) {
    const prevSelectors = [
      '.el-date-picker__prev-btn',
      '.ant-calendar-prev-month-btn',
      '.datepicker-prev',
      '.ui-datepicker-prev',
      "[aria-label='Previous month']",
      "button[class*='prev']",
      '.mx-btn-prev-year',
      '.mx-btn-prev-month'
    ];
    
    for (const sel of prevSelectors) {
      try {
        const btn = calendar.querySelector(sel);
        if (btn) {
          btn.click();
          return;
        }
      } catch (e) {
        continue;
      }
    }
  }
  
  function clickNextMonth(calendar) {
    const nextSelectors = [
      '.el-date-picker__next-btn',
      '.ant-calendar-next-month-btn',
      '.datepicker-next',
      '.ui-datepicker-next',
      "[aria-label='Next month']",
      "button[class*='next']",
      '.mx-btn-next-year',
      '.mx-btn-next-month'
    ];
    
    for (const sel of nextSelectors) {
      try {
        const btn = calendar.querySelector(sel);
        if (btn) {
          btn.click();
          return;
        }
      } catch (e) {
        continue;
      }
    }
  }
  
  function findDayElement(calendar, targetDay) {
    const daySelectors = [
      `td:not(.disabled):not(.not-current-month)`,
      `td[role='gridcell']:not([aria-disabled='true'])`,
      '.el-date-table td:not(.disabled):not(.is-disabled)',
      '.ant-calendar-date:not(.ant-calendar-disabled-cell)',
      '.mx-calendar-content .cell:not(.disabled)'
    ];
    
    for (const sel of daySelectors) {
      try {
        const cells = calendar.querySelectorAll(sel);
        for (const cell of cells) {
          const cellText = (cell.textContent || '').trim();
          if (cellText === String(targetDay)) {
            return cell;
          }
        }
      } catch (e) {
        continue;
      }
    }
    
    const allCells = calendar.querySelectorAll('td');
    for (const cell of allCells) {
      const cellText = (cell.textContent || '').trim();
      if (cellText === String(targetDay)) {
        const classList = cell.className || '';
        if (!classList.includes('disabled') && 
            !classList.includes('is-disabled') &&
            !classList.includes('not-current')) {
          return cell;
        }
      }
    }
    
    return null;
  }
  
  function formatDate(date, format) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return format
      .replace('YYYY', year)
      .replace('MM', month)
      .replace('DD', day);
  }
  
  async function clickAddMoreButton(buttonTexts) {
    if (!buttonTexts) {
      buttonTexts = [
        '添加', '新增', '增加', '添加更多', '新增一条',
        'Add', 'Add More', '+'
      ];
    }
    
    for (const text of buttonTexts) {
      const selectors = [
        `//button[contains(normalize-space(.), '${text}')]`,
        `//a[contains(normalize-space(.), '${text}')]`,
        `//span[contains(normalize-space(.), '${text}')]`,
        `//div[contains(normalize-space(.), '${text}') and @role='button']`
      ];
      
      for (const xpath of selectors) {
        try {
          const btn = document.evaluate(
            xpath,
            document,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
          ).singleNodeValue;
          
          if (btn && btn.offsetParent !== null) {
            btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
            await randomDelay(100, 200);
            btn.click();
            await randomDelay(500, 1000);
            return true;
          }
        } catch (e) {
          continue;
        }
      }
    }
    
    return false;
  }
  
  async function clickSaveButton(buttonTexts) {
    if (!buttonTexts) {
      buttonTexts = [
        '保存', '提交', '确认', '确定', '完成',
        'Save', 'Submit', 'Confirm', 'Done'
      ];
    }
    
    for (const text of buttonTexts) {
      const selectors = [
        `//button[contains(normalize-space(.), '${text}')]`,
        `//input[@type='submit' and @value='${text}']`,
        `//a[contains(normalize-space(.), '${text}')]`,
        `//div[contains(normalize-space(.), '${text}') and @role='button']`
      ];
      
      for (const xpath of selectors) {
        try {
          const btn = document.evaluate(
            xpath,
            document,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
          ).singleNodeValue;
          
          if (btn && btn.offsetParent !== null) {
            btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
            await randomDelay(100, 200);
            btn.click();
            await randomDelay(500, 1000);
            return true;
          }
        } catch (e) {
          continue;
        }
      }
    }
    
    return false;
  }
  
  async function handleRadioGroup(groupSelector, value, label) {
    const radios = document.querySelectorAll(`${groupSelector} input[type='radio']`);
    
    for (const radio of radios) {
      if (value) {
        const radioValue = radio.getAttribute('value');
        if (radioValue === value) {
          radio.click();
          await randomDelay(100, 200);
          return true;
        }
      }
      
      if (label) {
        const radioId = radio.getAttribute('id');
        if (radioId) {
          const labelElem = document.querySelector(`label[for='${radioId}']`);
          if (labelElem) {
            const labelText = (labelElem.textContent || '').trim();
            if (textMatches(labelText, label)) {
              radio.click();
              await randomDelay(100, 200);
              return true;
            }
          }
        }
        
        const parent = radio.parentElement;
        if (parent) {
          const parentText = (parent.textContent || '').trim();
          if (textMatches(parentText, label)) {
            radio.click();
            await randomDelay(100, 200);
            return true;
          }
        }
      }
    }
    
    return false;
  }
  
  async function handleCheckbox(selector, shouldCheck = true) {
    const checkbox = document.querySelector(selector);
    if (!checkbox) return false;
    
    const isChecked = checkbox.checked;
    
    if (shouldCheck !== isChecked) {
      checkbox.click();
      await randomDelay(100, 200);
    }
    
    return true;
  }
  
  async function handleTextarea(selector, value, charByChar = true) {
    const textarea = document.querySelector(selector);
    if (!textarea) return false;
    
    textarea.click();
    await randomDelay(100, 200);
    
    textarea.value = '';
    
    if (charByChar) {
      for (const char of value) {
        textarea.value += char;
        triggerInputEvents(textarea);
        await randomDelay(50, 150);
      }
    } else {
      textarea.value = value;
      triggerInputEvents(textarea);
    }
    
    await randomDelay(100, 200);
    return true;
  }
  
  async function handleFileUpload(selector, fileUrl) {
    const fileInput = document.querySelector(selector);
    if (!fileInput) return false;
    
    console.log('[AutoCard] 注意：浏览器插件无法直接操作本地文件上传');
    console.log('[AutoCard] 需要用户手动选择文件或使用其他方式');
    
    return false;
  }
  
  async function waitForSpinner(timeout = 10000) {
    const spinnerSelectors = [
      '.loading',
      '.spinner',
      '[class*="loading"]',
      '[class*="spinner"]',
      '.el-loading-mask',
      '.ant-spin'
    ];
    
    let spinner = null;
    for (const sel of spinnerSelectors) {
      spinner = document.querySelector(sel);
      if (spinner) break;
    }
    
    if (spinner) {
      return waitForDynamicContentToDisappear(spinner.tagName, timeout);
    }
    
    return true;
  }
  
  function simulateMouseMovement(startX, startY, endX, endY) {
    return new Promise(resolve => {
      const steps = Math.floor(Math.random() * 20) + 10;
      let currentStep = 0;
      
      function moveNext() {
        if (currentStep > steps) {
          resolve();
          return;
        }
        
        const progress = currentStep / steps;
        const x = startX + (endX - startX) * progress;
        const y = startY + (endY - startY) * progress;
        
        const mouseMoveEvent = new MouseEvent('mousemove', {
          bubbles: true,
          cancelable: true,
          view: window,
          clientX: x,
          clientY: y
        });
        
        document.dispatchEvent(mouseMoveEvent);
        
        currentStep++;
        setTimeout(moveNext, Math.random() * 30 + 10);
      }
      
      moveNext();
    });
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
  
  function triggerSelectEvents(element) {
    const inputEvent = new Event('input', { bubbles: true });
    const changeEvent = new Event('change', { bubbles: true });
    
    element.dispatchEvent(inputEvent);
    element.dispatchEvent(changeEvent);
  }
  
  function triggerInputEvents(element) {
    const inputEvent = new InputEvent('input', {
      bubbles: true,
      inputType: 'insertText'
    });
    
    const changeEvent = new Event('change', { bubbles: true });
    const blurEvent = new FocusEvent('blur', { bubbles: true });
    
    element.dispatchEvent(inputEvent);
    element.dispatchEvent(changeEvent);
    element.dispatchEvent(blurEvent);
  }
  
  console.log('[AutoCard] interaction-handler.js 已加载');
  
  window.AutoCardInteractionHandler = {
    CONFIG,
    sleep,
    randomDelay,
    waitHumanLike,
    getIframe,
    waitForDynamicContent,
    waitForDynamicContentToDisappear,
    scrollToLoadMore,
    handleSelectDropdown,
    handleCustomDropdown,
    handleDatePicker,
    handleCalendarDatePicker,
    clickAddMoreButton,
    clickSaveButton,
    handleRadioGroup,
    handleCheckbox,
    handleTextarea,
    handleFileUpload,
    waitForSpinner,
    simulateMouseMovement,
    textMatches,
    triggerSelectEvents,
    triggerInputEvents
  };
  
})();
