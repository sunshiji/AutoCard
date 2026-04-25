(function() {
  'use strict';
  
  const CONFIG = {
    enabled: true,
    randomUserAgent: true,
    mouseMovementSimulation: true,
    inputDelayMin: 100,
    inputDelayMax: 300,
    clickDelayMin: 200,
    clickDelayMax: 500,
    typingDelayMin: 50,
    typingDelayMax: 150
  };
  
  let lastInteractionTime = 0;
  
  function randomPauseBetweenActions() {
    if (!CONFIG.enabled) return;
    
    const now = Date.now();
    const timeSinceLastAction = now - lastInteractionTime;
    
    if (timeSinceLastAction < 500) {
      const delay = Math.random() * 200 + 100;
      return sleep(delay);
    }
    
    lastInteractionTime = now;
    return Promise.resolve();
  }
  
  function randomDelay(min, max) {
    const delay = Math.random() * (max - min) + min;
    return sleep(delay);
  }
  
  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  function simulateHumanMouseMovement(element) {
    if (!CONFIG.mouseMovementSimulation || !element) return Promise.resolve();
    
    return new Promise(resolve => {
      const rect = element.getBoundingClientRect();
      const startX = window.innerWidth / 2 + (Math.random() - 0.5) * 200;
      const startY = window.innerHeight / 2 + (Math.random() - 0.5) * 200;
      const endX = rect.left + rect.width / 2;
      const endY = rect.top + rect.height / 2;
      
      const steps = Math.floor(Math.random() * 20) + 10;
      let currentStep = 0;
      
      function moveNext() {
        if (currentStep > steps) {
          resolve();
          return;
        }
        
        const progress = currentStep / steps;
        const easing = 1 - Math.pow(1 - progress, 3);
        
        const x = startX + (endX - startX) * easing + (Math.random() - 0.5) * 5;
        const y = startY + (endY - startY) * easing + (Math.random() - 0.5) * 5;
        
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
  
  function simulateHumanTyping(element, text) {
    if (!CONFIG.enabled) {
      element.value = text;
      triggerInputEvents(element);
      return Promise.resolve();
    }
    
    return new Promise(async (resolve) => {
      const chars = text.split('');
      
      for (let i = 0; i < chars.length; i++) {
        const char = chars[i];
        
        const keydownEvent = new KeyboardEvent('keydown', {
          bubbles: true,
          cancelable: true,
          key: char
        });
        element.dispatchEvent(keydownEvent);
        
        element.value = text.substring(0, i + 1);
        
        const inputEvent = new InputEvent('input', {
          bubbles: true,
          inputType: 'insertText',
          data: char
        });
        element.dispatchEvent(inputEvent);
        
        const keyupEvent = new KeyboardEvent('keyup', {
          bubbles: true,
          cancelable: true,
          key: char
        });
        element.dispatchEvent(keyupEvent);
        
        await sleep(Math.random() * (CONFIG.typingDelayMax - CONFIG.typingDelayMin) + CONFIG.typingDelayMin);
        
        if (Math.random() < 0.05 && i > 0 && i < chars.length - 1) {
          const wrongChar = String.fromCharCode(97 + Math.floor(Math.random() * 26));
          element.value = text.substring(0, i + 1) + wrongChar;
          triggerInputEvents(element);
          await sleep(100);
          
          element.value = text.substring(0, i + 1);
          triggerInputEvents(element);
          await sleep(50);
        }
      }
      
      const changeEvent = new Event('change', { bubbles: true });
      element.dispatchEvent(changeEvent);
      
      resolve();
    });
  }
  
  function triggerInputEvents(element) {
    const inputEvent = new InputEvent('input', {
      bubbles: true,
      inputType: 'insertText'
    });
    element.dispatchEvent(inputEvent);
    
    const changeEvent = new Event('change', { bubbles: true });
    element.dispatchEvent(changeEvent);
  }
  
  async function safeClick(element, fieldName) {
    const strategies = [
      playwrightClick,
      jsClick,
      jsDispatchClick,
      focusOnly
    ];
    
    for (const strategy of strategies) {
      try {
        const success = await strategy(element);
        if (success) {
          return true;
        }
        await randomDelay(50, 100);
      } catch (e) {
        console.log(`[AutoCard] 点击策略失败: ${e}`);
        continue;
      }
    }
    
    return false;
  }
  
  async function playwrightClick(element) {
    try {
      await randomPauseBetweenActions();
      await simulateHumanMouseMovement(element);
      
      element.focus();
      await randomDelay(50, 100);
      
      const mouseDownEvent = new MouseEvent('mousedown', {
        bubbles: true,
        cancelable: true,
        view: window,
        bubbles: true
      });
      element.dispatchEvent(mouseDownEvent);
      
      await randomDelay(50, 100);
      
      const mouseUpEvent = new MouseEvent('mouseup', {
        bubbles: true,
        cancelable: true,
        view: window
      });
      element.dispatchEvent(mouseUpEvent);
      
      const clickEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window
      });
      element.dispatchEvent(clickEvent);
      
      return true;
    } catch (e) {
      return false;
    }
  }
  
  async function jsClick(element) {
    try {
      element.click();
      return true;
    } catch (e) {
      return false;
    }
  }
  
  async function jsDispatchClick(element) {
    try {
      const events = ['mousedown', 'mouseup', 'click', 'focus'];
      
      for (const eventName of events) {
        const event = new MouseEvent(eventName, {
          bubbles: true,
          cancelable: true,
          view: window
        });
        element.dispatchEvent(event);
        await randomDelay(20, 50);
      }
      
      return true;
    } catch (e) {
      return false;
    }
  }
  
  async function focusOnly(element) {
    try {
      element.focus();
      return true;
    } catch (e) {
      return false;
    }
  }
  
  function removeOverlays() {
    try {
      const selectors = [
        '.loading', '.spinner', '.overlay', '.modal-backdrop', '.mask',
        '[class*="loading"]', '[class*="spinner"]', '[class*="overlay"]',
        '.el-loading-mask', '.ant-spin-container',
        '#loading', '.fade-enter-active', '.fade-leave-active'
      ];
      
      let removedCount = 0;
      
      selectors.forEach(sel => {
        const elements = document.querySelectorAll(sel);
        elements.forEach(el => {
          const style = window.getComputedStyle(el);
          const pointerEvents = style.pointerEvents;
          const zIndex = style.zIndex;
          const opacity = style.opacity;
          const display = style.display;
          const visibility = style.visibility;
          
          if (pointerEvents === 'auto' && 
              (zIndex !== 'auto' || opacity !== '0') &&
              display !== 'none' && 
              visibility !== 'hidden') {
            el.style.display = 'none';
            el.style.pointerEvents = 'none';
            el.style.opacity = '0';
            el.style.visibility = 'hidden';
            removedCount++;
          }
        });
      });
      
      const allElements = document.querySelectorAll('*');
      allElements.forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.pointerEvents === 'auto' && 
            style.zIndex !== 'auto' &&
            parseInt(style.zIndex) > 1000) {
          const rect = el.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            el.style.pointerEvents = 'none';
            removedCount++;
          }
        }
      });
      
      if (removedCount > 0) {
        console.log(`[AutoCard] 移除了 ${removedCount} 个潜在的遮罩元素`);
      }
      
      return removedCount;
    } catch (e) {
      console.log(`[AutoCard] 移除遮罩失败: ${e}`);
      return 0;
    }
  }
  
  function aggressiveRemoveOverlays() {
    try {
      const removed = document.evaluate(`
        (() => {
          let removed = 0;
          
          const selectors = [
            '.loading', '.spinner', '.overlay', '.modal-backdrop', '.mask',
            '[class*="loading"]', '[class*="spinner"]', '[class*="overlay"]',
            '.el-loading-mask', '.ant-spin-container',
            '#loading', '.fade-enter-active', '.fade-leave-active'
          ];
          
          selectors.forEach(sel => {
            const elements = document.querySelectorAll(sel);
            elements.forEach(el => {
              const style = window.getComputedStyle(el);
              const pointerEvents = style.pointerEvents;
              const zIndex = style.zIndex;
              const opacity = style.opacity;
              const display = style.display;
              const visibility = style.visibility;
              
              if (pointerEvents === 'auto' && 
                  (zIndex !== 'auto' || opacity !== '0') &&
                  display !== 'none' && 
                  visibility !== 'hidden') {
                el.style.display = 'none';
                el.style.pointerEvents = 'none';
                el.style.opacity = '0';
                el.style.visibility = 'hidden';
                removed++;
              }
            });
          });
          
          const allElements = document.querySelectorAll('*');
          allElements.forEach(el => {
            const style = window.getComputedStyle(el);
            if (style.pointerEvents === 'auto' && 
                style.zIndex !== 'auto' &&
                parseInt(style.zIndex) > 1000) {
              const rect = el.getBoundingClientRect();
              if (rect.width > 0 && rect.height > 0) {
                el.style.pointerEvents = 'none';
                removed++;
              }
            }
          });
          
          return removed;
        })()
      `, document, null, XPathResult.NUMBER_TYPE, null);
      
      if (removed.numberValue > 0) {
        console.log(`[AutoCard] 移除了 ${removed.numberValue} 个潜在的遮罩元素`);
      }
      
      return removed.numberValue;
    } catch (e) {
      return removeOverlays();
    }
  }
  
  function tryActivateField(element, fieldName) {
    try {
      element.style.pointerEvents = 'auto';
      element.readOnly = false;
      element.disabled = false;
      
      if (element.parentElement) {
        element.parentElement.style.pointerEvents = 'auto';
      }
      
      const focusEvent = new FocusEvent('focus', { bubbles: true });
      const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
      
      element.dispatchEvent(focusEvent);
      element.dispatchEvent(clickEvent);
      
      console.log(`[AutoCard] 尝试激活字段: ${fieldName}`);
      return true;
    } catch (e) {
      console.log(`[AutoCard] 激活字段失败: ${e}`);
      return false;
    }
  }
  
  function checkElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
  }
  
  function forceScrollIntoView(element) {
    try {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'center'
      });
      return true;
    } catch (e) {
      try {
        const rect = element.getBoundingClientRect();
        window.scrollTo({
          top: rect.top + window.pageYOffset - 100,
          left: 0,
          behavior: 'smooth'
        });
        return true;
      } catch (e2) {
        return false;
      }
    }
  }
  
  async function waitForOverlay(element, timeout = 5000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const isBlocked = checkElementBlocked(element);
      if (!isBlocked) {
        return;
      }
      
      await sleep(100);
    }
    
    aggressiveRemoveOverlays();
  }
  
  function checkElementBlocked(element) {
    try {
      const rect = element.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const topElement = document.elementFromPoint(centerX, centerY);
      
      if (topElement && !element.contains(topElement) && topElement !== element) {
        const computedStyle = window.getComputedStyle(topElement);
        const pointerEvents = computedStyle.pointerEvents;
        const zIndex = computedStyle.zIndex;
        const opacity = computedStyle.opacity;
        const display = computedStyle.display;
        const visibility = computedStyle.visibility;
        
        if (pointerEvents === 'none' || opacity === '0' || 
            display === 'none' || visibility === 'hidden') {
          return false;
        }
        
        if (zIndex && zIndex !== 'auto') {
          const elZIndex = window.getComputedStyle(element).zIndex;
          if (parseInt(zIndex) > parseInt(elZIndex || '0')) {
            return true;
          }
        }
        
        return topElement !== element;
      }
      
      return false;
    } catch (e) {
      return false;
    }
  }
  
  console.log('[AutoCard] anti-detection.js 已加载');
  
  window.AutoCardAntiDetection = {
    CONFIG,
    randomPauseBetweenActions,
    randomDelay,
    sleep,
    simulateHumanMouseMovement,
    simulateHumanTyping,
    triggerInputEvents,
    safeClick,
    playwrightClick,
    jsClick,
    jsDispatchClick,
    focusOnly,
    removeOverlays,
    aggressiveRemoveOverlays,
    tryActivateField,
    checkElementInViewport,
    forceScrollIntoView,
    waitForOverlay,
    checkElementBlocked
  };
  
})();
