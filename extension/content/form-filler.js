(function() {
  'use strict';
  
  let resumeData = null;
  let platformSelectors = {};
  let fillResults = [];
  let progress = {
    totalFields: 0,
    filledFields: 0,
    failedFields: 0,
    currentSection: '',
    currentField: '',
    errors: []
  };
  
  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  function randomDelay(min, max) {
    const delay = Math.random() * (max - min) + min;
    return sleep(delay);
  }
  
  function getActualValue(element) {
    try {
      if (element.tagName === 'SELECT') {
        const selectedOpt = element.options[element.selectedIndex];
        return selectedOpt ? (selectedOpt.value || selectedOpt.textContent || '') : '';
      }
      if (element.tagName === 'INPUT' && (element.type === 'checkbox' || element.type === 'radio')) {
        return element.checked ? 'checked' : '';
      }
      return element.value || element.textContent || '';
    } catch (e) {
      return '';
    }
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
  
  function init(data, selectors) {
    resumeData = data;
    platformSelectors = selectors || {};
    fillResults = [];
    progress = {
      totalFields: 0,
      filledFields: 0,
      failedFields: 0,
      currentSection: '',
      currentField: '',
      errors: []
    };
  }
  
  async function fillPersonalInfo() {
    progress.currentSection = '个人信息';
    const results = [];
    
    if (!resumeData || !resumeData.personalInfo) {
      return results;
    }
    
    const personalInfo = resumeData.personalInfo;
    
    const fieldMappings = {
      name: personalInfo.name,
      phone: personalInfo.phone,
      email: personalInfo.email,
      gender: personalInfo.gender,
      selfIntroduction: personalInfo.selfIntroduction
    };
    
    for (const [fieldName, value] of Object.entries(fieldMappings)) {
      if (value === null || value === undefined || value === '') {
        continue;
      }
      
      progress.currentField = fieldName;
      
      const result = await fillSingleField(fieldName, value);
      results.push(result);
      fillResults.push(result);
      
      if (result.success) {
        progress.filledFields++;
      } else {
        progress.failedFields++;
        if (result.errorMessage) {
          progress.errors.push(`${fieldName}: ${result.errorMessage}`);
        }
      }
      
      await randomDelay(100, 300);
    }
    
    return results;
  }
  
  async function fillEducationExperiences() {
    progress.currentSection = '教育经历';
    const results = [];
    
    if (!resumeData || !resumeData.educationExperiences) {
      return results;
    }
    
    const experiences = resumeData.educationExperiences;
    
    for (let idx = 0; idx < experiences.length; idx++) {
      const exp = experiences[idx];
      
      if (idx > 0) {
        const added = await window.AutoCardInteractionHandler.clickAddMoreButton();
        if (added) {
          await randomDelay(500, 1000);
        }
      }
      
      const expResults = await fillEducationExperience(exp, idx);
      results.push(...expResults);
    }
    
    return results;
  }
  
  async function fillEducationExperience(exp, index) {
    const results = [];
    
    const fieldMappings = {
      school: exp.school,
      major: exp.major,
      education: exp.education,
      startDate: exp.startDate,
      endDate: exp.endDate
    };
    
    for (const [fieldName, value] of Object.entries(fieldMappings)) {
      if (value === null || value === undefined || value === '') {
        continue;
      }
      
      progress.currentField = `${fieldName}_${index}`;
      
      let result;
      if (fieldName === 'education') {
        result = await fillSelectField(fieldName, value);
      } else if (fieldName === 'startDate' || fieldName === 'endDate') {
        result = await fillDateField(fieldName, value);
      } else {
        result = await fillSingleField(fieldName, value);
      }
      
      results.push(result);
      fillResults.push(result);
      
      if (result.success) {
        progress.filledFields++;
      } else {
        progress.failedFields++;
      }
      
      await randomDelay(100, 300);
    }
    
    return results;
  }
  
  async function fillWorkExperiences() {
    progress.currentSection = '工作经历';
    const results = [];
    
    if (!resumeData || !resumeData.workExperiences) {
      return results;
    }
    
    const experiences = resumeData.workExperiences;
    
    for (let idx = 0; idx < experiences.length; idx++) {
      const exp = experiences[idx];
      
      if (idx > 0) {
        const added = await window.AutoCardInteractionHandler.clickAddMoreButton();
        if (added) {
          await randomDelay(500, 1000);
        }
      }
      
      const expResults = await fillWorkExperience(exp, idx);
      results.push(...expResults);
    }
    
    return results;
  }
  
  async function fillWorkExperience(exp, index) {
    const results = [];
    
    const fieldMappings = {
      company: exp.company,
      position: exp.position,
      industry: exp.industry,
      startDate: exp.startDate,
      endDate: exp.endDate,
      workDescription: exp.description
    };
    
    for (const [fieldName, value] of Object.entries(fieldMappings)) {
      if (value === null || value === undefined || value === '') {
        continue;
      }
      
      progress.currentField = `${fieldName}_${index}`;
      
      let result;
      if (fieldName === 'startDate' || fieldName === 'endDate') {
        result = await fillDateField(fieldName, value);
      } else if (fieldName === 'workDescription') {
        result = await fillTextareaField(fieldName, value);
      } else {
        result = await fillSingleField(fieldName, value);
      }
      
      results.push(result);
      fillResults.push(result);
      
      if (result.success) {
        progress.filledFields++;
      } else {
        progress.failedFields++;
      }
      
      await randomDelay(100, 300);
    }
    
    return results;
  }
  
  async function fillProjectExperiences() {
    progress.currentSection = '项目经历';
    const results = [];
    
    if (!resumeData || !resumeData.projectExperiences) {
      return results;
    }
    
    const experiences = resumeData.projectExperiences;
    
    for (let idx = 0; idx < experiences.length; idx++) {
      const exp = experiences[idx];
      
      if (idx > 0) {
        const added = await window.AutoCardInteractionHandler.clickAddMoreButton();
        if (added) {
          await randomDelay(500, 1000);
        }
      }
      
      const expResults = await fillProjectExperience(exp, idx);
      results.push(...expResults);
    }
    
    return results;
  }
  
  async function fillProjectExperience(exp, index) {
    const results = [];
    
    const fieldMappings = {
      projectName: exp.projectName,
      projectRole: exp.role,
      startDate: exp.startDate,
      endDate: exp.endDate,
      projectDescription: exp.description
    };
    
    for (const [fieldName, value] of Object.entries(fieldMappings)) {
      if (value === null || value === undefined || value === '') {
        continue;
      }
      
      progress.currentField = `${fieldName}_${index}`;
      
      let result;
      if (fieldName === 'startDate' || fieldName === 'endDate') {
        result = await fillDateField(fieldName, value);
      } else if (fieldName === 'projectDescription') {
        result = await fillTextareaField(fieldName, value);
      } else {
        result = await fillSingleField(fieldName, value);
      }
      
      results.push(result);
      fillResults.push(result);
      
      if (result.success) {
        progress.filledFields++;
      } else {
        progress.failedFields++;
      }
      
      await randomDelay(100, 300);
    }
    
    return results;
  }
  
  async function fillSkills() {
    progress.currentSection = '技能';
    const results = [];
    
    if (!resumeData || !resumeData.skills || resumeData.skills.length === 0) {
      return results;
    }
    
    const skillsText = resumeData.skills.join('、');
    
    const result = await fillSingleField('skill', skillsText);
    results.push(result);
    fillResults.push(result);
    
    if (result.success) {
      progress.filledFields++;
    } else {
      progress.failedFields++;
    }
    
    return results;
  }
  
  async function fillAll() {
    const allResults = [];
    
    allResults.push(...(await fillPersonalInfo()));
    allResults.push(...(await fillEducationExperiences()));
    allResults.push(...(await fillWorkExperiences()));
    allResults.push(...(await fillProjectExperiences()));
    allResults.push(...(await fillSkills()));
    
    return allResults;
  }
  
  async function fillSingleField(fieldName, value, labelTexts) {
    if (!value) {
      return createFillResult(false, fieldName, value, '值为空');
    }
    
    const located = window.AutoCardFieldLocator.locateField(fieldName, labelTexts);
    
    if (!located) {
      return createFillResult(false, fieldName, value, `无法定位字段: ${fieldName}`);
    }
    
    try {
      const element = located.element;
      const inputType = located.inputType;
      
      await window.AutoCardAntiDetection.randomPauseBetweenActions();
      
      const elementInfo = window.AutoCardUtils.getElementInfo(element);
      
      if (!elementInfo.isInteractable) {
        console.log(`[AutoCard] 元素可能不可交互，尝试激活: ${fieldName}`);
        window.AutoCardAntiDetection.tryActivateField(element, fieldName);
      }
      
      const isInViewport = window.AutoCardAntiDetection.checkElementInViewport(element);
      if (!isInViewport) {
        console.log(`[AutoCard] 字段不在视口内，尝试滚动: ${fieldName}`);
        window.AutoCardAntiDetection.forceScrollIntoView(element);
      }
      
      await randomDelay(100, 200);
      
      let fillSuccess = false;
      let actualValue = null;
      
      if (['text', 'email', 'tel', 'password', 'number', 'textarea'].includes(inputType)) {
        console.log(`[AutoCard] 使用文本输入策略: ${fieldName} (type=${inputType})`);
        [fillSuccess, actualValue] = await fillTextFieldWithVerify(element, value, fieldName);
      } else if (inputType === 'select') {
        console.log(`[AutoCard] 使用选择框策略: ${fieldName}`);
        [fillSuccess, actualValue] = await fillSelectWithVerify(element, value, fieldName);
      } else if (inputType === 'date') {
        console.log(`[AutoCard] 使用日期选择器策略: ${fieldName}`);
        [fillSuccess, actualValue] = await fillDateFieldWithVerify(element, value, fieldName);
      } else if (inputType === 'checkbox' || inputType === 'radio') {
        console.log(`[AutoCard] 使用选择器策略: ${fieldName} (type=${inputType})`);
        [fillSuccess, actualValue] = await fillChoiceFieldWithVerify(element, value, fieldName);
      } else {
        console.log(`[AutoCard] 使用通用策略: ${fieldName} (type=${inputType})`);
        [fillSuccess, actualValue] = await fillGenericWithVerify(element, value, fieldName);
      }
      
      if (fillSuccess) {
        console.log(`[AutoCard] ✓ 填充成功: ${fieldName} = '${actualValue}'`);
      } else {
        console.log(`[AutoCard] ✗ 填充失败: ${fieldName}`);
      }
      
      await randomDelay(100, 200);
      
      return createFillResult(
        fillSuccess,
        fieldName,
        value,
        fillSuccess ? null : '填充后验证失败',
        located.selector
      );
      
    } catch (e) {
      console.log(`[AutoCard] ✗ 异常: ${e}`);
      return createFillResult(
        false,
        fieldName,
        value,
        String(e),
        located.selector
      );
    }
  }
  
  async function fillTextFieldWithVerify(element, value, fieldName) {
    const strategies = [
      fillPlaywrightWithVerify,
      fillJsWithEventsAndVerify,
      fillTypeWithVerify
    ];
    
    for (const strategy of strategies) {
      try {
        window.AutoCardAntiDetection.aggressiveRemoveOverlays();
        await randomDelay(100, 200);
        
        const [success, actualVal] = await strategy(element, value);
        if (success) {
          return [true, actualVal];
        }
        
        await randomDelay(50, 100);
      } catch (e) {
        console.log(`[AutoCard] 策略失败: ${e}`);
        continue;
      }
    }
    
    const finalValue = getActualValue(element);
    return [valuesMatch(finalValue, value), finalValue];
  }
  
  async function fillPlaywrightWithVerify(element, value) {
    try {
      element.value = '';
      element.focus();
      await randomDelay(50, 100);
      
      element.value = value;
      window.AutoCardInteractionHandler.triggerInputEvents(element);
      
      await randomDelay(100, 200);
      
      const actual = getActualValue(element);
      return [valuesMatch(actual, value), actual];
    } catch (e) {
      console.log(`[AutoCard] playwright_fill 失败: ${e}`);
      return [false, getActualValue(element)];
    }
  }
  
  async function fillJsWithEventsAndVerify(element, value) {
    try {
      element.value = '';
      element.focus();
      
      const inputEvent1 = new Event('input', { bubbles: true });
      element.dispatchEvent(inputEvent1);
      
      element.value = value;
      element.setAttribute('value', value);
      
      const inputEvent2 = new Event('input', { bubbles: true });
      const changeEvent = new Event('change', { bubbles: true });
      const blurEvent = new FocusEvent('blur', { bubbles: true });
      
      element.dispatchEvent(inputEvent2);
      element.dispatchEvent(changeEvent);
      element.dispatchEvent(blurEvent);
      
      await randomDelay(100, 200);
      
      const actual = getActualValue(element);
      
      if (valuesMatch(actual, value)) {
        return [true, actual];
      }
      
      return [valuesMatch(actual, value), actual];
      
    } catch (e) {
      console.log(`[AutoCard] js_with_events 失败: ${e}`);
      return [false, getActualValue(element)];
    }
  }
  
  async function fillTypeWithVerify(element, value) {
    try {
      element.value = '';
      element.focus();
      await randomDelay(50, 100);
      
      await window.AutoCardAntiDetection.simulateHumanTyping(element, value);
      
      await randomDelay(100, 200);
      
      element.blur();
      
      const actual = getActualValue(element);
      return [valuesMatch(actual, value), actual];
    } catch (e) {
      console.log(`[AutoCard] playwright_type 失败: ${e}`);
      return [false, getActualValue(element)];
    }
  }
  
  async function fillSelectWithVerify(element, value, fieldName) {
    try {
      const isNativeSelect = element.tagName === 'SELECT';
      
      if (isNativeSelect) {
        const options = element.querySelectorAll('option');
        let found = false;
        
        for (const opt of options) {
          const optText = (opt.textContent || '').trim();
          const optValue = (opt.value || '').trim();
          
          if (valuesMatch(optValue, value) || 
              valuesMatch(optText, value) ||
              optText.includes(value) ||
              value.includes(optText)) {
            opt.selected = true;
            window.AutoCardInteractionHandler.triggerSelectEvents(element);
            found = true;
            break;
          }
        }
        
        if (found) {
          await randomDelay(100, 200);
          const actual = getActualValue(element);
          return [valuesMatch(actual, value), actual];
        }
      }
      
      console.log(`[AutoCard] 尝试自定义下拉框: ${fieldName}`);
      
      try {
        element.click();
        await randomDelay(300, 500);
        
        const optionSelectors = [
          'li', '.dropdown-item', '.option', "[role='option']",
          '.el-select-dropdown__item', '.ant-select-dropdown-menu-item',
          '.select-option', '.combobox-option'
        ];
        
        for (const sel of optionSelectors) {
          try {
            const options = document.querySelectorAll(sel);
            for (const opt of options) {
              const optText = (opt.textContent || '').trim();
              
              if (valuesMatch(optText, value)) {
                opt.click();
                await randomDelay(200, 300);
                
                const actual = getActualValue(element);
                if (valuesMatch(actual, value) || valuesMatch(optText, value)) {
                  return [true, actual || optText];
                }
              }
            }
          } catch (e) {
            continue;
          }
        }
        
      } catch (clickError) {
        if (String(clickError).toLowerCase().includes('intercept') || 
            String(clickError).toLowerCase().includes('pointer')) {
          console.log(`[AutoCard] 点击被拦截，尝试 JavaScript 点击...`);
          element.click();
          await randomDelay(300, 500);
        }
      }
      
      const actual = getActualValue(element);
      return [valuesMatch(actual, value), actual];
      
    } catch (e) {
      console.log(`[AutoCard] select 填充失败: ${e}`);
      return [false, getActualValue(element)];
    }
  }
  
  async function fillDateFieldWithVerify(element, value, fieldName) {
    try {
      let dateStr;
      if (value instanceof Date) {
        const year = value.getFullYear();
        const month = String(value.getMonth() + 1).padStart(2, '0');
        const day = String(value.getDate()).padStart(2, '0');
        dateStr = `${year}-${month}-${day}`;
      } else {
        dateStr = String(value);
      }
      
      const success = element.evaluate(() => {
        const dateStr = arguments[0];
        
        this.value = '';
        this.focus();
        
        this.value = dateStr;
        this.setAttribute('value', dateStr);
        
        const inputEvent = new Event('input', { bubbles: true });
        const changeEvent = new Event('change', { bubbles: true });
        this.dispatchEvent(inputEvent);
        this.dispatchEvent(changeEvent);
        
        return this.value === dateStr || this.getAttribute('value') === dateStr;
      }, dateStr);
      
      await randomDelay(200, 300);
      
      const actual = getActualValue(element);
      
      if (success && valuesMatch(actual, dateStr)) {
        return [true, actual];
      }
      
      try {
        element.value = dateStr;
        window.AutoCardInteractionHandler.triggerInputEvents(element);
        await randomDelay(200, 300);
        const actual2 = getActualValue(element);
        return [valuesMatch(actual2, dateStr), actual2];
      } catch (e) {
        // 继续
      }
      
      return [valuesMatch(actual, dateStr), actual];
      
    } catch (e) {
      console.log(`[AutoCard] 日期填充失败: ${e}`);
      return [false, getActualValue(element)];
    }
  }
  
  async function fillChoiceFieldWithVerify(element, value, fieldName) {
    try {
      const isRadio = element.type === 'radio';
      const isCheckbox = element.type === 'checkbox';
      
      if (isRadio) {
        element.checked = true;
        const changeEvent = new Event('change', { bubbles: true });
        element.dispatchEvent(changeEvent);
      } else if (isCheckbox) {
        const shouldCheck = String(value).toLowerCase().includes('true') || 
                          String(value).toLowerCase().includes('1') ||
                          String(value).toLowerCase().includes('yes') ||
                          String(value).toLowerCase().includes('checked') ||
                          String(value).toLowerCase().includes('是');
        element.checked = shouldCheck;
        const changeEvent = new Event('change', { bubbles: true });
        element.dispatchEvent(changeEvent);
      }
      
      await randomDelay(100, 200);
      
      const actual = getActualValue(element);
      return [true, actual];
      
    } catch (e) {
      console.log(`[AutoCard] 选择字段填充失败: ${e}`);
      return [false, getActualValue(element)];
    }
  }
  
  async function fillGenericWithVerify(element, value, fieldName) {
    try {
      await window.AutoCardAntiDetection.safeClick(element, fieldName);
      await randomDelay(100, 200);
      
      return fillTextFieldWithVerify(element, value, fieldName);
      
    } catch (e) {
      console.log(`[AutoCard] 通用填充失败: ${e}`);
      return [false, getActualValue(element)];
    }
  }
  
  async function fillSelectField(fieldName, value) {
    return fillSingleField(fieldName, value);
  }
  
  async function fillDateField(fieldName, value) {
    return fillSingleField(fieldName, value);
  }
  
  async function fillTextareaField(fieldName, value) {
    return fillSingleField(fieldName, value);
  }
  
  function createFillResult(success, fieldName, value, errorMessage, selector) {
    return {
      success: success,
      fieldName: fieldName,
      value: value,
      errorMessage: errorMessage,
      selectorUsed: selector
    };
  }
  
  function getProgress() {
    return { ...progress };
  }
  
  function getResults() {
    return [...fillResults];
  }
  
  console.log('[AutoCard] form-filler.js 已加载');
  
  window.AutoCardFormFiller = {
    init,
    fillPersonalInfo,
    fillEducationExperiences,
    fillWorkExperiences,
    fillProjectExperiences,
    fillSkills,
    fillAll,
    fillSingleField,
    fillSelectField,
    fillDateField,
    fillTextareaField,
    getProgress,
    getResults,
    getActualValue,
    valuesMatch
  };
  
})();
