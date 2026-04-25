(function() {
  'use strict';
  
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
  
  const PLATFORM_SELECTORS = {};
  
  const LABEL_INPUT_STRATEGIES = [
    { name: 'platform_selector', description: '平台特定选择器（优先）' },
    { name: 'label_by_text', description: '通过label文本匹配' },
    { name: 'label_for_attribute', description: '通过label的for属性匹配' },
    { name: 'aria_labelledby', description: '通过aria-labelledby匹配' },
    { name: 'placeholder', description: '通过placeholder匹配' },
    { name: 'name_attribute', description: '通过name属性匹配' },
    { name: 'id_attribute', description: '通过id属性匹配' },
    { name: 'preceding_sibling', description: '通过前兄弟节点文本匹配' },
    { name: 'parent_sibling', description: '通过父节点的兄弟文本匹配' }
  ];
  
  const INPUT_TYPES = {
    text: ["input[type='text']", "input:not([type])", "textarea"],
    email: ["input[type='email']"],
    phone: ["input[type='tel']"],
    password: ["input[type='password']"],
    number: ["input[type='number']"],
    date: ["input[type='date']"],
    select: ["select"],
    checkbox: ["input[type='checkbox']"],
    radio: ["input[type='radio']"],
    textarea: ["textarea"]
  };
  
  let cache = {};
  let platformSelectors = {};
  
  function setPlatformSelectors(selectors) {
    platformSelectors = selectors || {};
    cache = {};
  }
  
  function locateField(fieldName, labelTexts, context = document) {
    if (!labelTexts) {
      labelTexts = FIELD_MAPPINGS[fieldName] || [fieldName];
    }
    
    const cacheKey = `${fieldName}_${labelTexts.join('_')}`;
    if (cache[cacheKey]) {
      return cache[cacheKey];
    }
    
    const contexts = getAllContexts(context);
    
    for (const ctx of contexts) {
      for (const strategy of LABEL_INPUT_STRATEGIES) {
        const located = tryLocateWithStrategy(ctx, fieldName, labelTexts, strategy.name);
        if (located) {
          cache[cacheKey] = located;
          return located;
        }
      }
    }
    
    return null;
  }
  
  function getAllContexts(context) {
    const contexts = [context];
    
    function collectFrames(frameList) {
      for (const frame of frameList) {
        try {
          if (frame.document) {
            contexts.push(frame.document);
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
    return contexts;
  }
  
  function tryLocateWithStrategy(context, fieldName, labelTexts, strategy) {
    const strategies = {
      platform_selector: locateByPlatformSelector,
      label_by_text: locateByLabelText,
      label_for_attribute: locateByLabelFor,
      aria_labelledby: locateByAriaLabelledby,
      placeholder: locateByPlaceholder,
      name_attribute: locateByName,
      id_attribute: locateById,
      preceding_sibling: locateByPrecedingSibling,
      parent_sibling: locateByParentSibling
    };
    
    if (strategies[strategy]) {
      return strategies[strategy](context, fieldName, labelTexts);
    }
    
    return null;
  }
  
  function locateByPlatformSelector(context, fieldName, labelTexts) {
    if (!platformSelectors || Object.keys(platformSelectors).length === 0) {
      return null;
    }
    
    const selectors = platformSelectors[fieldName] || [];
    if (selectors.length === 0) {
      return null;
    }
    
    for (const selector of selectors) {
      try {
        const elements = context.querySelectorAll(selector);
        for (const element of elements) {
          if (isInteractiveElement(element)) {
            return {
              fieldName: fieldName,
              selector: selector,
              labelText: labelTexts[0] || null,
              inputType: getInputType(element),
              element: element,
              isRequired: checkRequired(element)
            };
          }
        }
      } catch (e) {
        continue;
      }
    }
    
    return null;
  }
  
  function locateByLabelText(context, fieldName, labelTexts) {
    for (const labelText of labelTexts) {
      const xpathVariants = [
        `.//label[contains(normalize-space(.), ${escapeXpathText(labelText)})]`,
        `.//label[normalize-space(.) = ${escapeXpathText(labelText)}]`,
        `.//*[self::label or self::span or self::div][contains(normalize-space(.), ${escapeXpathText(labelText)})]`
      ];
      
      for (const xpath of xpathVariants) {
        const labels = evaluateXpath(xpath, context);
        for (const label of labels) {
          const labelFor = label.getAttribute('for');
          if (labelFor) {
            const inputElem = context.querySelector(`#${labelFor}`);
            if (inputElem && isInteractiveElement(inputElem)) {
              return {
                fieldName: fieldName,
                selector: `#${labelFor}`,
                labelText: labelText,
                inputType: getInputType(inputElem),
                element: inputElem,
                isRequired: checkRequired(inputElem)
              };
            }
          }
          
          const parent = label.parentElement;
          if (parent) {
            const inputs = parent.querySelectorAll('input, textarea, select');
            for (const inp of inputs) {
              if (isInteractiveElement(inp)) {
                return {
                  fieldName: fieldName,
                  selector: generateSelector(inp),
                  labelText: labelText,
                  inputType: getInputType(inp),
                  element: inp,
                  isRequired: checkRequired(inp)
                };
              }
            }
          }
          
          const following = getFollowingInput(label);
          if (following) {
            return {
              fieldName: fieldName,
              selector: generateSelector(following),
              labelText: labelText,
              inputType: getInputType(following),
              element: following,
              isRequired: checkRequired(following)
            };
          }
        }
      }
    }
    
    return null;
  }
  
  function locateByLabelFor(context, fieldName, labelTexts) {
    for (const labelText of labelTexts) {
      const labels = evaluateXpath(
        `.//label[contains(normalize-space(.), ${escapeXpathText(labelText)})]`,
        context
      );
      
      for (const label of labels) {
        const labelFor = label.getAttribute('for');
        if (labelFor) {
          const inputElem = context.querySelector(`[id="${labelFor}"]`);
          if (inputElem && isInteractiveElement(inputElem)) {
            return {
              fieldName: fieldName,
              selector: `[id="${labelFor}"]`,
              labelText: labelText,
              inputType: getInputType(inputElem),
              element: inputElem,
              isRequired: checkRequired(inputElem)
            };
          }
        }
      }
    }
    
    return null;
  }
  
  function locateByAriaLabelledby(context, fieldName, labelTexts) {
    const inputs = context.querySelectorAll('input[aria-labelledby], textarea[aria-labelledby], select[aria-labelledby]');
    
    for (const inp of inputs) {
      const labelledby = inp.getAttribute('aria-labelledby');
      if (labelledby) {
        const labelElem = context.querySelector(`#${labelledby}`);
        if (labelElem) {
          const labelText = (labelElem.textContent || '').trim();
          
          for (const targetText of labelTexts) {
            if (textMatches(labelText, targetText)) {
              return {
                fieldName: fieldName,
                selector: generateSelector(inp),
                labelText: labelText,
                inputType: getInputType(inp),
                element: inp,
                isRequired: checkRequired(inp)
              };
            }
          }
        }
      }
    }
    
    return null;
  }
  
  function locateByPlaceholder(context, fieldName, labelTexts) {
    const inputs = context.querySelectorAll('input[placeholder], textarea[placeholder]');
    
    for (const inp of inputs) {
      const placeholder = (inp.getAttribute('placeholder') || '').trim();
      
      for (const targetText of labelTexts) {
        if (textMatches(placeholder, targetText)) {
          return {
            fieldName: fieldName,
            selector: generateSelector(inp),
            labelText: placeholder,
            inputType: getInputType(inp),
            element: inp,
            isRequired: checkRequired(inp)
          };
        }
      }
    }
    
    return null;
  }
  
  function locateByName(context, fieldName, labelTexts) {
    const namePatterns = [
      fieldName.toLowerCase(),
      fieldName.replace('_', ''),
      fieldName.replace('_', '-')
    ];
    
    namePatterns.push(...labelTexts.map(t => t.toLowerCase()));
    
    for (const pattern of namePatterns) {
      const inputs = context.querySelectorAll(`input[name*="${pattern}"], textarea[name*="${pattern}"], select[name*="${pattern}"]`);
      for (const inp of inputs) {
        const name = (inp.getAttribute('name') || '').toLowerCase();
        if (name.includes(pattern)) {
          return {
            fieldName: fieldName,
            selector: generateSelector(inp),
            inputType: getInputType(inp),
            element: inp,
            isRequired: checkRequired(inp)
          };
        }
      }
    }
    
    return null;
  }
  
  function locateById(context, fieldName, labelTexts) {
    const idPatterns = [
      fieldName.toLowerCase(),
      fieldName.replace('_', ''),
      fieldName.replace('_', '-')
    ];
    
    idPatterns.push(...labelTexts.map(t => t.toLowerCase()));
    
    for (const pattern of idPatterns) {
      const inputs = context.querySelectorAll(`input[id*="${pattern}"], textarea[id*="${pattern}"], select[id*="${pattern}"]`);
      for (const inp of inputs) {
        const elemId = (inp.getAttribute('id') || '').toLowerCase();
        if (elemId.includes(pattern)) {
          return {
            fieldName: fieldName,
            selector: generateSelector(inp),
            inputType: getInputType(inp),
            element: inp,
            isRequired: checkRequired(inp)
          };
        }
      }
    }
    
    return null;
  }
  
  function locateByPrecedingSibling(context, fieldName, labelTexts) {
    const inputs = context.querySelectorAll('input, textarea, select');
    
    for (const inp of inputs) {
      const precedingText = getPrecedingSiblingText(inp);
      
      if (precedingText) {
        for (const targetText of labelTexts) {
          if (textMatches(precedingText, targetText)) {
            return {
              fieldName: fieldName,
              selector: generateSelector(inp),
              labelText: precedingText.substring(0, 50),
              inputType: getInputType(inp),
              element: inp,
              isRequired: checkRequired(inp)
            };
          }
        }
      }
    }
    
    return null;
  }
  
  function locateByParentSibling(context, fieldName, labelTexts) {
    const inputs = context.querySelectorAll('input, textarea, select');
    
    for (const inp of inputs) {
      const parentLabel = getParentSiblingText(inp);
      
      if (parentLabel) {
        for (const targetText of labelTexts) {
          if (textMatches(parentLabel, targetText)) {
            return {
              fieldName: fieldName,
              selector: generateSelector(inp),
              labelText: parentLabel.substring(0, 50),
              inputType: getInputType(inp),
              element: inp,
              isRequired: checkRequired(inp)
            };
          }
        }
      }
    }
    
    return null;
  }
  
  function getFollowingInput(element) {
    let next = element.nextElementSibling;
    while (next) {
      if (/^(INPUT|TEXTAREA|SELECT)$/i.test(next.tagName)) {
        return next;
      }
      const input = next.querySelector('input, textarea, select');
      if (input) return input;
      next = next.nextElementSibling;
    }
    return null;
  }
  
  function getPrecedingSiblingText(element) {
    const texts = [];
    let prev = element.previousElementSibling;
    while (prev) {
      if (prev.textContent) {
        texts.push(prev.textContent.trim());
      }
      prev = prev.previousElementSibling;
    }
    return texts.join(' ');
  }
  
  function getParentSiblingText(element) {
    const texts = [];
    let parent = element.parentElement;
    
    while (parent) {
      let prev = parent.previousElementSibling;
      while (prev) {
        if (prev.textContent) {
          texts.push(prev.textContent.trim());
        }
        prev = prev.previousElementSibling;
      }
      
      const children = parent.querySelectorAll(':scope > label, :scope > span, :scope > div');
      for (const child of children) {
        if (child.textContent) {
          texts.push(child.textContent.trim());
        }
      }
      
      parent = parent.parentElement;
    }
    
    return texts.join(' ');
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
  
  function isInteractiveElement(element) {
    const tagName = element.tagName.toLowerCase();
    const interactiveTags = ['input', 'textarea', 'select'];
    
    if (interactiveTags.includes(tagName)) {
      const inputType = (element.getAttribute('type') || '').toLowerCase();
      const hiddenTypes = ['hidden', 'submit', 'reset', 'button'];
      
      if (hiddenTypes.includes(inputType)) {
        return false;
      }
      
      return true;
    }
    
    return false;
  }
  
  function getInputType(element) {
    const tagName = element.tagName.toLowerCase();
    
    if (tagName === 'textarea') {
      return 'textarea';
    } else if (tagName === 'select') {
      return 'select';
    } else if (tagName === 'input') {
      const inputType = (element.getAttribute('type') || 'text').toLowerCase();
      
      if (['text', 'email', 'tel', 'password', 'number', 'date', 'checkbox', 'radio'].includes(inputType)) {
        return inputType;
      }
      
      return 'text';
    }
    
    return 'text';
  }
  
  function checkRequired(element) {
    const required = element.getAttribute('required');
    if (required !== null) {
      return true;
    }
    
    const ariaRequired = element.getAttribute('aria-required');
    if (ariaRequired && ariaRequired.toLowerCase() === 'true') {
      return true;
    }
    
    const parentClass = element.parentElement?.className || '';
    if (parentClass.toLowerCase().includes('required')) {
      return true;
    }
    
    return false;
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
  
  function evaluateXpath(xpath, context) {
    const results = [];
    const iterator = document.evaluate(
      xpath,
      context,
      null,
      XPathResult.ORDERED_NODE_ITERATOR_TYPE,
      null
    );
    
    let node;
    while ((node = iterator.iterateNext())) {
      results.push(node);
    }
    
    return results;
  }
  
  function locateAllFields(fieldNames, context = document) {
    const results = {};
    
    for (const fieldName of fieldNames) {
      const located = locateField(fieldName, null, context);
      if (located) {
        results[fieldName] = located;
      }
    }
    
    return results;
  }
  
  function clearCache() {
    cache = {};
  }
  
  console.log('[AutoCard] field-locator.js 已加载');
  
  window.AutoCardFieldLocator = {
    FIELD_MAPPINGS,
    PLATFORM_SELECTORS,
    LABEL_INPUT_STRATEGIES,
    INPUT_TYPES,
    setPlatformSelectors,
    locateField,
    locateAllFields,
    clearCache,
    getInputType,
    checkRequired,
    generateSelector,
    isInteractiveElement,
    textMatches
  };
  
})();
