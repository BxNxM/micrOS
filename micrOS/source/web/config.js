const menuStructure = {
  'Device': ['devfid', 'boothook', 'appwd', 'dbg', 'aioqueue', 'utc', 'boostmd'],
  'Network': ['devip', 'staessid', 'stapwd', 'nwmd', 'espnow', 'ha'],
  'Web': ['webui', 'webui_max_con'],
  'Scheduler': ['cron', 'crontasks'],
  'Interrupts': ['timirq', 'timirqcbf', 'timirqseq', 'irq1', 'irq1_cbf', 'irq1_trig', 'irq2', 'irq2_cbf', 'irq2_trig', 'irq3', 'irq3_cbf', 'irq3_trig', 'irq4', 'irq4_cbf', 'irq4_trig', 'irq_prell_ms'],
  'Pin-mapping': ['cstmpmap'],
};
const configLabelMap = {
  'devfid': 'Device name',
  'boothook': 'Startup Actions',
  'appwd': 'Admin Password',
  'dbg': 'Debug Mode',
  'aioqueue': 'Allowed Number of Tasks',
  'utc': 'UTC',
  'boostmd': 'Boost Mode',
  'devip': 'Device IP',
  'staessid': 'WiFi SSID',
  'stapwd': 'WiFi Password',
  'espnow': 'Enable ESPNOW',
  'nwmd': 'Network Mode',
  'ha': 'High Availability',
  'cron': 'Enable Scheduler',
  'crontasks': 'Scheduled Tasks',
  'webui': 'Enable',
  'webui_max_con': 'Allowed Number of Connections',
  'irq_prell_ms': 'Interrupt Debounce',
};
const configSelectOptions = {
  'nwmd': ['STA', 'AP'],
  'irq_trig': ['up', 'down', 'both'],
};
const categoryIconMap = {
  'Device': '📟',
  'Network': '📡',
  'Web': '🌐',
  'Scheduler': '⏰',
  'Interrupts': '⚡',
  'Pin-mapping': '📍',
  'Tasks': '✓',
  'Packages': '📦',
};

// Fields with semicolon-separated parameters
const multiParamFields = new Set(['boothook', 'timirqcbf', 'staessid', 'stapwd']);

// Regex to detect irq callback fields (irq<n>_cbf)
const irqCallbackRegex = /^irq\d+_cbf$/;

let configData = {};
let changedValues = {};
const selectedCategoryKey = 'micros.config.selectedCategory';
const restEncodeMap = {
  '"': '%5Cx22', "'": '%27', '#': '%23', '=': '%3D', '>': '%3E', '&': '%26',
  '/': '%2F', '\\': '%5C%5C', ' ': '%20', '?': '%3F', '%': '%25'
};

function loadSelectedCategory() {
  try {
    return sessionStorage.getItem(selectedCategoryKey);
  } catch (_) {
    return null;
  }
}

function saveSelectedCategory(category) {
  try {
    sessionStorage.setItem(selectedCategoryKey, category);
  } catch (_) {}
}

function isPasswordField(key) {
  return /pwd|password/i.test(key);
}

function textElement(tag, text, className = '') {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}

function makeButton(label, onClick = null, className = '') {
  const button = textElement('button', label, className);
  button.type = 'button';
  if (onClick) button.onclick = onClick;
  return button;
}

function makeInput(type, value = '', placeholder = '', dataset = {}, onInput = null) {
  const input = Object.assign(document.createElement('input'), {type, value, placeholder});
  Object.assign(input.dataset, dataset);
  if (onInput) input.oninput = onInput;
  return input;
}

function categoryTitle(category) {
  return (categoryIconMap[category] ? categoryIconMap[category] + ' ' : '') + category;
}

function categoryKeyFromMenuItem(item) {
  return item.dataset.category || item.textContent;
}

function decorateCategoryMenu() {
  document.querySelectorAll('#configMenu p').forEach(item => {
    const category = categoryKeyFromMenuItem(item);
    item.dataset.category = category;
    item.textContent = categoryTitle(category);
  });
}

function createPasswordToggle(input) {
  const button = makeButton('Show', null, 'config-password-toggle');
  button.onclick = () => {
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.textContent = show ? 'Hide' : 'Show';
  };
  return button;
}

function appendInputWithPasswordToggle(wrapper, input, key) {
  if (!isPasswordField(key)) {
    wrapper.appendChild(input);
    return;
  }
  const row = document.createElement('div');
  row.className = 'config-input-row';
  row.appendChild(input);
  row.appendChild(createPasswordToggle(input));
  wrapper.appendChild(row);
}

function createBooleanToggle(key, value, onChange) {
  const toggle = document.createElement('div');
  toggle.className = 'config-toggle';
  toggle.setAttribute('role', 'group');
  toggle.setAttribute('aria-label', configLabelMap[key] || key);

  const buttons = [];
  const setValue = nextValue => {
    buttons.forEach(([button, buttonValue]) => {
      const selected = buttonValue === !!nextValue;
      button.classList.toggle('selected', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
  };
  const addButton = (label, buttonValue, className) => {
    const button = makeButton(label, null, 'config-toggle-option ' + className);
    button.onclick = () => {
      setValue(buttonValue);
      onChange(buttonValue);
    };
    toggle.appendChild(button);
    buttons.push([button, buttonValue]);
  };

  addButton('Off', false, 'config-toggle-off');
  addButton('On', true, 'config-toggle-on');
  setValue(value);
  return toggle;
}

function createSelectInput(key, value) {
  const select = document.createElement('select');
  getSelectOptions(key).forEach(option => {
    select.appendChild(new Option(option.charAt(0).toUpperCase() + option.slice(1), option));
  });
  select.value = value;
  select.onchange = () => trackChange(key, select.value);
  return select;
}

function getSelectOptions(key) {
  return configSelectOptions[key] || (key.match(/^irq\d+_trig$/) ? configSelectOptions.irq_trig : null);
}

function hasUnsavedChanges() {
  return Object.keys(changedValues).length > 0;
}

function updateSaveButtonState() {
  document.querySelectorAll('.config-save-button').forEach(button => {
    button.disabled = !hasUnsavedChanges();
  });
}

// Helper: Check if field supports multi-parameters
function isMultiParamField(key) {
  return multiParamFields.has(key) || irqCallbackRegex.test(key) || key === 'crontasks';
}

// Helper: Parse semicolon-separated values
function parseSemicolonValues(value) {
  if (!value || typeof value !== 'string') return [];
  return value.split(';').map(v => v.trim()).filter(v => v.length > 0);
}

/** Select scheduler block separator using the same fallback as Scheduler.py. */
function crontaskSeparator(value) {
  return value && String(value).includes(';;') ? ';;' : ';';
}

/** Split scheduler config into timestamp blocks. */
function parseCrontasks(value) {
  if (!value || typeof value !== 'string') return [];
  if (crontaskSeparator(value) === ';;') {
    return value.split(';;').map(block => block.trim()).filter(b => b.length > 0);
  }
  return parseSemicolonValues(value).reduce((blocks, part) => {
    if (blocks.length && !part.includes('!')) {
      blocks[blocks.length - 1] += ';' + part;
    } else {
      blocks.push(part);
    }
    return blocks;
  }, []);
}

/** Split scheduler command list when multiple commands are present. */
function parseCrontaskFunctions(value, advancedMode) {
  if (!value || typeof value !== 'string') return [];
  if (advancedMode || value.includes(';')) {
    return parseSemicolonValues(value);
  }
  const singleCommand = value.trim();
  return singleCommand ? [singleCommand] : [];
}

// Helper: Join semicolon values
function joinSemicolonValues(values) {
  return values.filter(v => v && v.trim().length > 0).join('; ');
}

/** Serialize scheduler blocks with canonical double-semicolon separators. */
function joinCrontasks(blocks) {
  const cleanBlocks = blocks.filter(b => b && b.trim().length > 0);
  const cmdStart = cleanBlocks.length === 1 ? cleanBlocks[0].indexOf('!') : -1;
  return cleanBlocks.join(';;') + (cmdStart >= 0 && cleanBlocks[0].slice(cmdStart).includes(';') ? ';;' : '');
}

function loadConfig(report = true) {
  return fetch('/config')
    .then(r => r.json())
    .then(data => {
      configData = data;
    })
    .catch(e => show('Load failed: ' + e.message));
}

function handleUpdateConfig() {
  if (Object.keys(changedValues).length === 0) {
    alert('No changes to save');
    return;
  }
  return fetch('/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(changedValues)
  })
  .then(r => r.json())
  .then(data => {
    console.log('Update response:', data);
    if (!data || data.state !== true) {
      const detail = data && data.result ? data.result : 'Unknown error';
      const failed = data && Array.isArray(data.failed) ? ` (${data.failed.join(', ')})` : '';
      alert('Update failed: ' + detail + failed);
      return;
    }
    changedValues = {};
    updateSaveButtonState();
    alert('Configuration updated successfully');
  })
  .catch(e => {
    console.error('Update failed:', e);
    alert('Update failed: ' + e.message);
  });
}

function closeMobileMenu() {
  const menu = document.getElementById('configMenu');
  if (menu && window.innerWidth <= 768) {
    menu.classList.remove('open');
  }
}

function addMenuListeners() {
  const menuItems = document.querySelectorAll('#configMenu p');
  menuItems.forEach(item => {
    item.addEventListener('click', () => {
      const key = categoryKeyFromMenuItem(item);
      console.log('Clicked menu item:', key);
      setSelectedMenuItem(item);
      closeMobileMenu();
      saveSelectedCategory(key);
      if (key === 'Packages') {
        renderPackagesSection();
        return;
      }
      if (key === 'Tasks') {
        renderTaskSection();
        return;
      }
      const filteredConfig = filterConfig(key);
      console.log('Filtered config for', key, ':', filteredConfig);
      renderConfigFields(filteredConfig, key);
    });
  });
}

function setSelectedMenuItem(selectedItem) {
  const menuItems = document.querySelectorAll('#configMenu p');
  menuItems.forEach(item => {
    if (item === selectedItem) {
      item.classList.add('selected');
    } else {
      item.classList.remove('selected');
    }
  });
}

function filterConfig(key) {
  if (key === 'Other') {
    const allUsedKeys = Object.values(menuStructure).flat();
    return Object.fromEntries(Object.entries(configData).filter(([k]) => !allUsedKeys.includes(k)));
  }
  let configKeys = menuStructure[key] || [];
  let filteredConfig = {};
  configKeys.forEach(k => {
    if (configData.hasOwnProperty(k)) {
      filteredConfig[k] = configData[k];
    }
  });
  return filteredConfig;
}

function isEditableConfigSection(sectionKey) {
  return sectionKey in menuStructure;
}

function renderSaveButton(container) {
  const button = makeButton('💾 Save', () => handleUpdateConfig(), 'config-save-button primary-button');
  button.disabled = !hasUnsavedChanges();
  return button;
}

function renderConfigFields(data, sectionKey = '') {
  const container = document.getElementById('configFields');
  container.innerHTML = ''; // Clear previous content

  if (isEditableConfigSection(sectionKey)) {
    const headerRow = document.createElement('div');
    headerRow.className = 'config-header-row';

    const heading = textElement('h2', categoryTitle(sectionKey), 'config-heading');
    headerRow.appendChild(heading);

    headerRow.appendChild(renderSaveButton(container));
    container.appendChild(headerRow);
  }

  if (sectionKey === 'Pin-mapping') {
    renderPinMappingSection(data, container);
  } else if (Object.keys(data).some(key => key.startsWith('irq'))) {
    renderInterruptFields(data, container);
  } else {
    renderDefaultFields(data, container, sectionKey);
  }
}

function renderTaskSection() {
  const container = document.getElementById('configFields');
  container.innerHTML = '';
  const heading = textElement('h2', categoryTitle('Tasks'), 'config-heading-top');
  container.appendChild(heading);

  const loading = textElement('div', 'Loading task list...');
  container.appendChild(loading);

  restAPI('task/list', false)
    .then(response => {
      container.removeChild(loading);
      if (!response || !response.result) {
        container.appendChild(makeError('Unable to load task list.'));
        return;
      }

      const activeTasks = Array.isArray(response.result.active) ? response.result.active : [];
      const inactiveTasks = Array.isArray(response.result.inactive) ? response.result.inactive : [];

      renderTaskGroup(container, 'Active Tasks', activeTasks, true);
      renderTaskGroup(container, 'Inactive Tasks', inactiveTasks, false);
    })
    .catch(error => {
      container.removeChild(loading);
      container.appendChild(makeError('Failed to load task list: ' + error.message));
    });
}

function renderTaskGroup(container, title, tasks, showActionButtons) {
  const actions = [{label: 'Details', handler: handleTaskDetails}];
  if (showActionButtons) {
    actions.push({label: 'Kill', handler: handleTaskKill, className: 'danger-button', disabled: isProtectedTask});
  } else {
    actions.push({label: 'Del', handler: handleTaskKill, className: 'danger-button'});
  }
  renderActionList(container, title, tasks, actions);
}

function isProtectedTask(tag) {
  return ['server', 'idle'].includes(String(tag).split('.')[0]);
}

function renderActionList(container, title, items, actions) {
  const section = document.createElement('section');
  section.className = 'config-action-section config-section-gap-large';

  if (title) {
    const titleEl = textElement('h3', `${title} (${items.length})`);
    section.appendChild(titleEl);
  }

  if (items.length === 0) {
    section.appendChild(document.createTextNode('None'));
    container.appendChild(section);
    return;
  }

  const list = document.createElement('div');
  list.className = 'config-action-list';
  items.forEach(item => renderActionRow(list, item, actions));
  section.appendChild(list);
  container.appendChild(section);
}

function renderActionRow(container, labelText, actions) {
  const row = document.createElement('div');
  row.className = 'config-action-row';

  const header = document.createElement('div');
  header.className = 'config-action-header';

  const label = textElement('span', labelText, 'config-action-label');
  header.appendChild(label);

  const actionGroup = document.createElement('div');
  actionGroup.className = 'config-button-group';

  const actionPanels = document.createElement('div');

  actions.forEach(action => {
    const button = makeButton(action.label, null, action.className || '');
    if (action.disabled && action.disabled(labelText)) {
      button.disabled = true;
      button.title = 'System task cannot be killed';
    }
    const output = createInlineOutput();
    button.onclick = () => {
      if (button.disabled) return;
      action.handler(labelText, output, button);
    };
    actionGroup.appendChild(button);
    actionPanels.appendChild(output);
  });
  header.appendChild(actionGroup);

  row.appendChild(header);
  row.appendChild(actionPanels);
  container.appendChild(row);
}

function createInlineOutput() {
  const output = document.createElement('pre');
  output.className = 'config-inline-output';
  return output;
}

function setInlineDetails(details, text) {
  details.textContent = text;
  details.style.display = 'block';
}

function setTemporaryInlineDetails(details, text, timeout = 5000, onHide = null) {
  if (details.hideTimer) {
    clearTimeout(details.hideTimer);
  }
  setInlineDetails(details, text);
  details.hideTimer = setTimeout(() => {
    details.textContent = '';
    details.style.display = 'none';
    details.hideTimer = null;
    if (onHide) {
      onHide();
    }
  }, timeout);
}

function styleGroupBox(element, padding = '12px') {
  element.classList.add('config-box');
  element.style.padding = padding;
}

function handleTaskKill(tag, details, button) {
  runCommandAction(details, button, button.textContent, `task/kill/${encodeURIComponent(tag)}`, 'Task response', renderTaskSection);
}

function handleTaskDetails(tag, details) {
  if (details.style.display !== 'none' && details.textContent) {
    details.style.display = 'none';
    return;
  }
  setInlineDetails(details, 'Loading details...');
  restAPI(`task/show/${encodeURIComponent(tag)}`, false)
    .then(response => {
      if (response && response.hasOwnProperty('result')) {
        if (response.state === false) {
          setInlineDetails(details, `Details failed:\n${formatResponseBody(response)}`);
        } else {
          setInlineDetails(details, formatResponseBody(response.result));
        }
      } else {
        setInlineDetails(details, `No detail response: ${JSON.stringify(response)}`);
      }
    })
    .catch(error => {
      setInlineDetails(details, 'Details error: ' + error.message);
    });
}

function makeError(message) {
  return textElement('div', message, 'config-error');
}

function setButtonBusy(button, label) {
  button.disabled = true;
  button.textContent = label;
}

function resetButton(button, label) {
  button.disabled = false;
  button.textContent = label;
}

// Packages UI: install and inspect
function renderPackagesSection() {
  const container = document.getElementById('configFields');
  container.innerHTML = '';
  const heading = textElement('h2', categoryTitle('Packages'), 'config-heading-top');
  container.appendChild(heading);

  // Install block
  const installSection = document.createElement('section');
  installSection.className = 'config-section-gap';
  const installLabel = textElement('label', 'Install Package (URL or Package ref):', 'config-label-block');
  installSection.appendChild(installLabel);

  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = 'e.g. github:BxNxM/micrOSPackages/async_oledui';
  input.id = 'packageUrlInput';
  input.style.margin = '8px 0';
  installSection.appendChild(input);

  const installResult = createInlineOutput();

  const installBtn = makeButton('Install', () => {
    const url = input.value.trim();
    if (!url) {
      alert('Enter package URL or Package ref');
      return;
    }
    setButtonBusy(installBtn, 'Installing...');
    setInlineDetails(installResult, `Install Package (URL or Package ref): ${url}\n\nInstalling...`);
    restAPI('pacman/install/' + restQuote(url), false, 10000)
      .then(resp => {
        setInlineDetails(installResult, formatInstallResponse(url, resp));
        refreshPackagesList();
      })
      .catch(err => {
        setInlineDetails(installResult, `Install Package (URL or Package ref): ${url}\n\nInstall failed:\n${err.message}`);
      })
      .finally(() => {
        resetButton(installBtn, 'Install');
      });
  });
  installSection.appendChild(installBtn);

  const packageTools = document.createElement('div');
  packageTools.className = 'config-package-tools';

  const catalogBtn = makeButton('Catalog', () => {
    window.open('https://github.com/BxNxM/micrOSPackages/tree/main', '_blank', 'noopener,noreferrer');
  });
  packageTools.appendChild(catalogBtn);

  const refreshBtn = makeButton('Refresh', () => {
    refreshPackagesList();
  });
  packageTools.appendChild(refreshBtn);

  installSection.appendChild(packageTools);
  installSection.appendChild(installResult);
  container.appendChild(installSection);

  // Packages list block
  const pkgSection = document.createElement('section');
  const pkgHeader = document.createElement('div');
  pkgHeader.className = 'config-package-header';
  const title = textElement('h3', 'Packages', 'config-package-title');
  pkgHeader.appendChild(title);
  pkgSection.appendChild(pkgHeader);

  const list = document.createElement('div');
  list.id = 'packagesList';
  list.style.marginTop = '8px';
  pkgSection.appendChild(list);
  container.appendChild(pkgSection);

  refreshPackagesList();
}

function refreshPackagesList() {
  const list = document.getElementById('packagesList');
  if (!list) return;
  list.textContent = 'Loading...';
  restAPI('pacman/inspect', false)
    .then(resp => {
      list.textContent = '';
      if (!resp || !resp.hasOwnProperty('result')) {
        list.textContent = 'No packages';
        return;
      }
      const items = normalizePackageList(resp.result);
      if (Array.isArray(items) && items.length === 0) {
        list.textContent = 'No packages installed.';
        return;
      }
      if (Array.isArray(items)) {
        renderActionList(list, '', items.map(pkg => typeof pkg === 'string' ? pkg : JSON.stringify(pkg)), getPackageActions());
        return;
      }
      if (typeof items === 'object') {
        renderActionList(list, '', Object.keys(items), getPackageActions());
        return;
      }
      list.textContent = JSON.stringify(items);
    })
    .catch(err => {
      list.textContent = 'Failed to load packages: ' + err.message;
    });
}

function normalizePackageList(result) {
  if (Array.isArray(result)) return result;
  if (typeof result !== 'string') return result || [];
  try {
    const jsonList = JSON.parse(result.replace(/'/g, '"'));
    if (Array.isArray(jsonList)) return jsonList;
  } catch (_) {}
  return result.split('\n').map(item => item.trim()).filter(item => item);
}

function formatResponseBody(result) {
  return typeof result === 'string' ? result : JSON.stringify(result, null, 2);
}

function formatInstallResponse(packageRef, resp) {
  const header = `Install Package (URL or Package ref): ${packageRef}`;
  if (!resp || resp.state !== true) {
    const result = resp && resp.result !== undefined ? resp.result : 'No response';
    return `${header}\n\nInstall response (NOK):\n${formatResponseBody(result)}`;
  }
  const result = resp.result !== undefined ? resp.result : resp;
  return `${header}\n\nInstall response (OK):\n${formatResponseBody(result)}`;
}

function formatActionResponse(title, resp) {
  const result = resp.result !== undefined ? resp.result : resp;
  return `${title}:\n${formatResponseBody(result)}`;
}

function getPackageActions() {
  return [
    {label: 'Details', handler: loadPackageDetails},
    {label: 'Update', handler: updatePackage},
    {label: 'Delete', handler: deletePackage, className: 'danger-button'}
  ];
}

function getAdminPassword() {
  if (changedValues.hasOwnProperty('appwd')) {
    return changedValues.appwd;
  }
  return configData.appwd || '';
}

/** Encode a value as one quoted REST argument for micrOS execution. */
function restQuote(value) {
  return '"' + String(value).replace(/["'#=>&/\\ ?%]/g, char => restEncodeMap[char]) + '"';
}

function loadPackageDetails(packageName, details, button) {
  if (details.style.display !== 'none' && details.textContent) {
    details.style.display = 'none';
    return;
  }
  setButtonBusy(button, 'Loading...');
  setInlineDetails(details, 'Loading details...');
  restAPI('pacman/inspect/' + restQuote(packageName), false, 10000)
    .then(resp => {
      setInlineDetails(details, formatPackageDetails(resp && resp.result));
    })
    .catch(err => {
      setInlineDetails(details, 'Failed to load details: ' + err.message);
    })
    .finally(() => {
      resetButton(button, 'Details');
    });
}

function runCommandAction(details, button, actionName, command, doneTitle, onSuccessHide = null) {
  setButtonBusy(button, actionName + '...');
  setInlineDetails(details, actionName + '...');
  restAPI(command, false, 20000)
    .then(resp => {
      if (!resp || resp.state !== true) {
        setTemporaryInlineDetails(details, actionName + ' failed: ' + JSON.stringify(resp));
        return;
      }
      setTemporaryInlineDetails(
        details,
        formatActionResponse(doneTitle, resp),
        5000,
        onSuccessHide
      );
    })
    .catch(err => {
      setTemporaryInlineDetails(details, actionName + ' error: ' + err.message);
    })
    .finally(() => {
      resetButton(button, actionName);
    });
}

function updatePackage(packageName, details, button) {
  runCommandAction(details, button, 'Update', 'pacman/upgrade/' + restQuote(packageName), 'Update response');
}

function deletePackage(packageName, details, button) {
  if (!confirm('Delete package "' + packageName + '"?')) {
    return;
  }
  const appwd = getAdminPassword();
  if (!appwd) {
    setTemporaryInlineDetails(details, 'Delete failed: missing Admin Password / appwd');
    return;
  }
  runCommandAction(
    details,
    button,
    'Delete',
    'pacman/uninstall/' + restQuote(packageName) + '/pwd=' + restQuote(appwd),
    'Delete response',
    refreshPackagesList
  );
}

function formatPackageDetails(result) {
  if (typeof result !== 'string') {
    return JSON.stringify(result, null, 2);
  }
  try {
    return JSON.stringify(JSON.parse(result), null, 2);
  } catch (_) {
    return result;
  }
}

function renderPinMappingSection(data, container) {
  const pinmapUi = renderCustomPinMapField(container, data.cstmpmap || '');

  const select = document.createElement('select');
  select.disabled = true;
  select.appendChild(new Option('Loading known maps...', ''));
  pinmapUi.mapRow.appendChild(select);

  const infoSection = document.createElement('section');
  infoSection.className = 'config-pin-info';

  const title = textElement('h3', 'Runtime Pin Map', 'config-pin-title');
  infoSection.appendChild(title);

  const status = textElement('div', 'Loading pin map...');
  infoSection.appendChild(status);
  container.appendChild(infoSection);

  restAPI('system/pinmap', false, 10000)
    .then(response => {
      status.remove();
      if (!response || !response.result || response.state === false) {
        infoSection.appendChild(makeError('Unable to load pin map.'));
        return;
      }
      populatePinMapSelector(select, pinmapUi.mapInput, response.result.known_maps || []);
      renderPinMapInfo(infoSection, response.result);
    })
    .catch(error => {
      status.remove();
      infoSection.appendChild(makeError('Failed to load pin map: ' + error.message));
    });
}

function parsePinMapConfig(value) {
  const parts = parseSemicolonValues(value);
  const mapName = parts[0] && !parts[0].includes(':') ? parts.shift() : '';
  const pairs = parts.map(part => {
    const splitAt = part.indexOf(':');
    if (splitAt < 0) return null;
    return [part.slice(0, splitAt).trim(), part.slice(splitAt + 1).trim()];
  }).filter(pair => pair && pair[0] && pair[1]);
  return {mapName: mapName === 'n/a' ? '' : mapName, pairs};
}

function serializePinMapConfig(mapName, pairs) {
  const clean = (value, pattern = /[;:]/g) => (value || '').replace(pattern, '').trim();
  const cleanMap = clean(mapName);
  const serialized = (cleanMap && cleanMap !== 'n/a' ? [cleanMap] : []).concat(
    pairs.map(pair => [clean(pair[0]), clean(pair[1], /;/g)])
      .filter(([key, value]) => key && value)
      .map(([key, value]) => `${key}:${value}`)
  );
  return serialized.length ? serialized.join('; ') : 'n/a';
}

function renderCustomPinMapField(container, value) {
  const parsed = parsePinMapConfig(value);
  const wrapper = document.createElement('div');
  wrapper.className = 'config-field-group';

  const label = textElement('label', 'Pin Map: ', 'config-label-block');
  wrapper.appendChild(label);

  const editor = document.createElement('div');
  editor.className = 'config-stack';
  editor.dataset.type = 'pinmap-editor';

  const mapRow = document.createElement('div');
  mapRow.className = 'pinmap-map-row';

  const mapInput = makeInput('text', parsed.mapName, 'Automatic pin map', {pinmapName: 'true'}, () => updatePinMapTrack(editor));
  mapRow.appendChild(mapInput);
  editor.appendChild(mapRow);

  const pairsLabel = textElement('label', 'Pin Overrides:', 'config-label-tight');
  editor.appendChild(pairsLabel);

  const pairContainer = document.createElement('div');
  pairContainer.className = 'config-stack';
  pairContainer.dataset.pinmapPairs = 'true';
  editor.appendChild(pairContainer);

  const addButton = makeButton('+', () => {
    createPinMapPairRow(pairContainer);
    updatePinMapTrack(editor);
  }, 'pinmap-add config-icon-button config-add-button');

  const pairs = parsed.pairs.length ? parsed.pairs : [['', '']];
  pairs.forEach(pair => createPinMapPairRow(pairContainer, pair[0], pair[1]));

  editor.appendChild(addButton);
  wrapper.appendChild(editor);
  container.appendChild(wrapper);
  return {mapInput, mapRow};
}

function populatePinMapSelector(select, mapInput, knownMaps) {
  if (!select || !mapInput) return;
  select.innerHTML = '';
  select.appendChild(new Option('Known maps...', ''));
  knownMaps.forEach(mapName => {
    select.appendChild(new Option(mapName, mapName));
  });
  select.disabled = knownMaps.length === 0;
  select.value = knownMaps.includes(mapInput.value.trim()) ? mapInput.value.trim() : '';
  select.onchange = () => {
    if (!select.value) return;
    mapInput.value = select.value;
    updatePinMapTrack(mapInput.closest('[data-type="pinmap-editor"]'));
  };
}

function createPinMapPairRow(container, key = '', value = '') {
  const row = document.createElement('div');
  row.className = 'pinmap-pair-row';
  const editor = container.closest('[data-type="pinmap-editor"]');

  row.appendChild(makeInput('text', key, 'key', {pinmapKey: 'true'}, () => updatePinMapTrack(editor)));
  row.appendChild(makeInput('number', value, 'pin', {pinmapValue: 'true'}, () => updatePinMapTrack(editor)));

  row.appendChild(makeButton('−', () => {
    row.remove();
    if (!container.querySelector('.pinmap-pair-row')) createPinMapPairRow(container);
    updatePinMapTrack(editor);
  }, 'config-icon-button config-remove-button'));

  container.appendChild(row);
}

function updatePinMapTrack(editor) {
  if (!editor) return;
  const mapInput = editor.querySelector('input[data-pinmap-name]');
  const pairs = Array.from(editor.querySelectorAll('.pinmap-pair-row')).map(row => [
    row.querySelector('input[data-pinmap-key]').value,
    row.querySelector('input[data-pinmap-value]').value
  ]);
  trackChange('cstmpmap', serializePinMapConfig(mapInput ? mapInput.value : '', pairs));
}

function renderPinMapInfo(container, pinmap) {
  renderKeyValueTable(container, 'Active Map', {'map': pinmap.map || 'n/a'});
  renderKeyValueTable(container, 'Custom Pins', pinmap.custom || {});
  renderKeyValueTable(container, 'Booked Pins', pinmap.booked || {});
}

function renderKeyValueTable(container, titleText, data) {
  const section = document.createElement('section');
  section.className = 'config-action-section config-section-gap';
  const title = textElement('h4', titleText, 'config-table-title');
  section.appendChild(title);
  container.appendChild(section);
  const entries = Object.entries(data);
  if (entries.length === 0) {
    section.appendChild(document.createTextNode('None'));
    return;
  }
  const table = document.createElement('table');
  table.className = 'config-table';
  entries.forEach(([key, value]) => {
    const row = document.createElement('tr');
    [key, String(value)].forEach(text => {
      const cell = textElement('td', text);
      row.appendChild(cell);
    });
    table.appendChild(row);
  });
  section.appendChild(table);
}

function renderDefaultFields(data, container, sectionKey = '') {
  Object.entries(data).forEach(([key, value]) => {
    if (sectionKey === 'Network' && key === 'staessid' && data.hasOwnProperty('stapwd')) {
      renderWifiCredentialPairs(container, data.staessid, data.stapwd);
      return;
    }
    if (sectionKey === 'Network' && key === 'stapwd' && data.hasOwnProperty('staessid')) {
      return;
    }
    renderField(container, key, value);
  });
}

function renderWifiCredentialPairs(container, ssidValue, passwordValue) {
  const wrapper = document.createElement('div');
  wrapper.className = 'config-field-group';

  const label = textElement('label', 'WiFi Networks: ', 'config-label-block');
  wrapper.appendChild(label);

  const pairContainer = document.createElement('div');
  pairContainer.className = 'config-stack';

  const addButton = makeButton('+', () => {
    if (addButton.disabled) return;
    createWifiCredentialPair(pairContainer, '', '', addButton, -1);
    updateWifiCredentialTrack(pairContainer, addButton);
  }, 'config-icon-button config-add-button');

  const ssids = parseSemicolonValues(ssidValue);
  const passwords = parseSemicolonValues(passwordValue);
  const count = Math.max(ssids.length, passwords.length, 1);
  for (let idx = 0; idx < count; idx++) {
    createWifiCredentialPair(pairContainer, ssids[idx] || '', passwords[idx] || '', addButton, count);
  }

  updateWifiCredentialAddButton(pairContainer, addButton);
  wrapper.appendChild(pairContainer);
  container.appendChild(wrapper);
}

function createWifiCredentialPair(container, ssid, password, addButton, totalCount) {
  const row = document.createElement('div');
  row.className = 'wifi-pair-row';

  const ssidWrap = document.createElement('div');
  ssidWrap.className = 'wifi-field';
  const ssidLabel = textElement('label', 'WiFi SSID:');
  const ssidInput = document.createElement('input');
  ssidInput.type = 'text';
  ssidInput.value = ssid;
  ssidInput.dataset.wifiSsid = 'true';
  ssidInput.oninput = () => updateWifiCredentialTrack(container, addButton);
  ssidWrap.appendChild(ssidLabel);
  ssidWrap.appendChild(ssidInput);
  row.appendChild(ssidWrap);

  const pwdWrap = document.createElement('div');
  pwdWrap.className = 'wifi-field';
  const pwdLabel = textElement('label', 'WiFi Password:');
  const pwdInput = document.createElement('input');
  pwdInput.type = 'password';
  pwdInput.value = password;
  pwdInput.dataset.wifiPassword = 'true';
  pwdInput.oninput = () => updateWifiCredentialTrack(container, addButton);
  pwdWrap.appendChild(pwdLabel);
  appendInputWithPasswordToggle(pwdWrap, pwdInput, 'stapwd');
  row.appendChild(pwdWrap);

  const existingRows = container.querySelectorAll('.wifi-pair-row');
  if (existingRows.length > 0 || totalCount > 1 || totalCount === -1) {
    const delButton = makeButton('−', null, 'config-icon-button config-remove-button');
    delButton.onclick = () => {
      if (container.querySelectorAll('.wifi-pair-row').length <= 1) {
        ssidInput.value = '';
        pwdInput.value = '';
        updateWifiCredentialTrack(container, addButton);
        return;
      }
      row.remove();
      moveWifiAddButtonToLastRow(container, addButton);
      updateWifiCredentialTrack(container, addButton);
    };
    row.appendChild(delButton);
  }

  container.appendChild(row);
  moveWifiAddButtonToLastRow(container, addButton);
  updateWifiCredentialAddButton(container, addButton);
}

function moveWifiAddButtonToLastRow(container, addButton) {
  const rows = Array.from(container.querySelectorAll('.wifi-pair-row'));
  if (rows.length > 0) {
    rows[rows.length - 1].appendChild(addButton);
  }
}

function updateWifiCredentialAddButton(container, addButton) {
  const rows = Array.from(container.querySelectorAll('.wifi-pair-row'));
  const lastRow = rows[rows.length - 1];
  const ssidInput = lastRow ? lastRow.querySelector('input[data-wifi-ssid]') : null;
  const pwdInput = lastRow ? lastRow.querySelector('input[data-wifi-password]') : null;
  const enabled = !!(ssidInput && pwdInput && ssidInput.value.trim() && pwdInput.value.trim());
  addButton.disabled = !enabled;
  addButton.style.opacity = enabled ? '1' : '0.5';
}

function updateWifiCredentialTrack(container, addButton) {
  const pairs = Array.from(container.querySelectorAll('.wifi-pair-row')).map(row => ({
    ssid: row.querySelector('input[data-wifi-ssid]').value.trim(),
    password: row.querySelector('input[data-wifi-password]').value.trim()
  })).filter(pair => pair.ssid && pair.password);
  trackChange('staessid', joinSemicolonValues(pairs.map(pair => pair.ssid)));
  trackChange('stapwd', joinSemicolonValues(pairs.map(pair => pair.password)));
  updateWifiCredentialAddButton(container, addButton);
}

function renderField(container, key, value) {
  // Handle multi-parameter fields specially
  if (isMultiParamField(key)) {
    if (key === 'crontasks') {
      renderCrontaskField(container, key, value);
    } else {
      renderMultiParamField(container, key, value);
    }
    return;
  }

  const wrapper = document.createElement('div');
  wrapper.className = 'config-field';

  const label = textElement('label', (configLabelMap[key] || key) + ': ', 'config-label');

  let input;
  if (typeof value === 'boolean') {
    input = createBooleanToggle(key, value, nextValue => trackChange(key, nextValue));
  } else if (typeof value === 'number') {
    input = document.createElement('input');
    input.type = 'number';
    input.value = value;
    input.onchange = () => trackChange(key, Number(input.value));
  } else if (getSelectOptions(key)) {
    input = createSelectInput(key, value);
  } else if (typeof value === 'string') {
    input = document.createElement('input');
    input.type = isPasswordField(key) ? 'password' : 'text';
    input.value = value;
    input.onchange = () => trackChange(key, input.value);
  } else {
    input = document.createElement('pre');
    input.textContent = JSON.stringify(value, null, 2);
  }

  wrapper.appendChild(label);
  appendInputWithPasswordToggle(wrapper, input, key);
  container.appendChild(wrapper);
}

function renderMultiParamField(container, key, value) {
  const wrapper = document.createElement('div');
  wrapper.className = 'config-field-group';

  const label = textElement('label', (configLabelMap[key] || key) + ': ', 'config-label-block');
  wrapper.appendChild(label);

  const inputContainer = document.createElement('div');
  inputContainer.className = 'config-stack';
  inputContainer.dataset.key = key;
  inputContainer.dataset.type = 'multi-param';

  const addButton = makeButton('+', () => {
    if (addButton.disabled) return;
    createParamInput(inputContainer, key, '', inputContainer.querySelectorAll('input[data-param-input]').length, -1, addButton);
    updateMultiParamTrack(inputContainer, key);
  }, 'multi-param-add config-icon-button config-add-button');

  const values = parseSemicolonValues(value);
  if (values.length === 0) {
    values.push('');
  }
  values.forEach((val, idx) => {
    createParamInput(inputContainer, key, val, idx, values.length, addButton);
  });

  updateRowAddButtonState(inputContainer, addButton, 'input[data-param-input]');
  wrapper.appendChild(inputContainer);
  container.appendChild(wrapper);
}

function createParamInput(container, key, value, idx, totalCount, addButton) {
  const inputWrapper = document.createElement('div');
  inputWrapper.className = 'param-row';

  const input = document.createElement('input');
  input.type = isPasswordField(key) ? 'password' : 'text';
  input.value = value;
  input.placeholder = `Parameter ${idx + 1}`;
  input.dataset.paramInput = 'true';
  input.onchange = () => updateMultiParamTrack(container.closest('[data-type="multi-param"]') || container, key);
  input.oninput = () => updateMultiParamTrack(container.closest('[data-type="multi-param"]') || container, key);

  appendInputWithPasswordToggle(inputWrapper, input, key);

  // Add delete button if more than one field exists
  const currentInputs = container.querySelectorAll('input[data-param-input]');
  if (currentInputs.length > 0 || totalCount > 1 || totalCount === -1) {
    const delButton = makeButton('−', () => {
      inputWrapper.remove();
      moveAddButtonToLastRow(container, addButton);
      updateMultiParamTrack(container.closest('[data-type="multi-param"]') || container, key);
    }, 'config-icon-button config-remove-button');
    inputWrapper.appendChild(delButton);
  }

  container.appendChild(inputWrapper);
  moveAddButtonToLastRow(container, addButton);
  updateRowAddButtonState(container, addButton, 'input[data-param-input]');
}

function moveAddButtonToLastRow(container, addButton) {
  if (!addButton) return;
  const rows = Array.from(container.children).filter(child => child.classList && child.classList.contains('param-row'));
  if (rows.length === 0) {
    return;
  }
  rows[rows.length - 1].appendChild(addButton);
}

function updateRowAddButtonState(container, addButton, inputSelector) {
  if (!addButton) return;
  const inputs = Array.from(container.querySelectorAll(inputSelector));
  if (inputs.length === 0) {
    addButton.disabled = true;
    addButton.style.opacity = '0.5';
    return;
  }
  const lastInput = inputs[inputs.length - 1];
  const enabled = lastInput.value.trim().length > 0;
  addButton.disabled = !enabled;
  addButton.style.opacity = enabled ? '1' : '0.5';
}

function updateMultiParamTrack(container, key) {
  const inputs = container.querySelectorAll('input[data-param-input]');
  const values = Array.from(inputs).map(input => input.value.trim()).filter(v => v.length > 0);
  const result = joinSemicolonValues(values);
  trackChange(key, result);
  const addButton = container.querySelector('.multi-param-add');
  if (addButton) {
    updateRowAddButtonState(container, addButton, 'input[data-param-input]');
  }
}

function renderCrontaskField(container, key, value) {
  const wrapper = document.createElement('div');
  wrapper.className = 'config-field-group';

  const label = textElement('label', (configLabelMap[key] || key) + ': ', 'config-label-block');
  wrapper.appendChild(label);

  const blockContainer = document.createElement('div');
  blockContainer.className = 'config-stack config-stack-large';
  blockContainer.dataset.key = key;
  blockContainer.dataset.type = 'crontask';
  blockContainer.dataset.blockSeparator = crontaskSeparator(value);

  const blocks = parseCrontasks(value);
  blocks.forEach((block, idx) => {
    createCrontaskBlock(blockContainer, key, block, idx, blocks.length);
  });

  // Add button for new block
  const addBlockButton = makeButton('+ Add Schedule', () => {
    createCrontaskBlock(blockContainer, key, '', blockContainer.querySelectorAll('[data-block-index]').length, -1);
    updateCrontaskTrack(blockContainer, key);
  }, 'schedule-add config-add-button');
  blockContainer.appendChild(addBlockButton);

  wrapper.appendChild(blockContainer);
  container.appendChild(wrapper);
}

function crontaskRoot(element) {
  return element.closest('[data-type="crontask"]') || element;
}

function createCrontaskBlock(container, key, block, blockIdx, totalBlocks) {
  const blockWrapper = document.createElement('fieldset');
  styleGroupBox(blockWrapper, '20px');
  blockWrapper.dataset.blockIndex = blockIdx;

  const legend = textElement('legend', `Schedule ${blockIdx + 1}`, 'config-legend');
  blockWrapper.appendChild(legend);

  const blockHeader = document.createElement('div');
  blockHeader.className = 'config-block-header';

  if (totalBlocks > 1 || totalBlocks === -1) {
    const delBlockButton = makeButton('Remove', () => {
      blockWrapper.remove();
      updateCrontaskTrack(crontaskRoot(container), key);
    }, 'config-remove-button');
    blockHeader.appendChild(delBlockButton);
  }
  blockWrapper.appendChild(blockHeader);

  // Timestamp field
  const tsWrapper = document.createElement('div');
  tsWrapper.className = 'config-field-group';
  const tsLabel = textElement('label', '✨ Timestamp (WD:H:M:S or Tag +/-Offset): ', 'config-label-tight');
  const tsGroup = textElement('div', '', 'schedule-time-config');

  const blockParts = block.split('!');
  const timestamp = defaultScheduleTimestamp(blockParts[0]);
  const functionsStr = blockParts.slice(1).join('!');
  const tsInput = makeInput('text', timestamp, '', {field: 'timestamp'});

  tsWrapper.appendChild(tsLabel);
  renderScheduleTimeControls(tsGroup, tsInput, blockWrapper, key);
  tsWrapper.appendChild(tsGroup);
  blockWrapper.appendChild(tsWrapper);

  // Functions field
  const fnWrapper = document.createElement('div');
  const fnLabel = textElement('label', 'Functions: ', 'config-label-tight');
  fnWrapper.appendChild(fnLabel);

  const fnContainer = document.createElement('div');
  fnContainer.className = 'config-stack';
  fnContainer.dataset.type = 'function-list';

  const addFnButton = makeButton('+', null, 'config-icon-button config-add-button');
  addFnButton.style.height = '40px';
  addFnButton.onclick = () => {
    if (addFnButton.disabled) return;
    createFunctionRow(fnContainer, key, blockWrapper, '', fnContainer.querySelectorAll('input[data-function-input]').length, -1, addFnButton);
    updateCrontaskTrack(crontaskRoot(container), key);
  };

  const functionValues = parseCrontaskFunctions(functionsStr, container.dataset.blockSeparator === ';;');
  if (functionValues.length === 0) {
    functionValues.push('');
  }
  functionValues.forEach((fnValue, fnIdx) => {
    createFunctionRow(fnContainer, key, blockWrapper, fnValue, fnIdx, functionValues.length, addFnButton);
  });

  updateRowAddButtonState(fnContainer, addFnButton, 'input[data-function-input]');
  fnWrapper.appendChild(fnContainer);
  blockWrapper.appendChild(fnWrapper);

  // Insert before the add button
  const addBlockButton = container.querySelector('.schedule-add');
  if (addBlockButton) {
    container.insertBefore(blockWrapper, addBlockButton);
  } else {
    container.appendChild(blockWrapper);
  }
}

function createFunctionRow(container, key, blockWrapper, value, idx, totalCount, addButton) {
  const row = document.createElement('div');
  row.className = 'function-row';

  const input = document.createElement('input');
  input.type = 'text';
  input.value = value;
  input.placeholder = `Function ${idx + 1}`;
  input.dataset.functionInput = 'true';
  input.onchange = () => {
    updateCrontaskTrack(crontaskRoot(blockWrapper), key);
    updateRowAddButtonState(container, addButton, 'input[data-function-input]');
  };
  input.oninput = () => {
    updateCrontaskTrack(crontaskRoot(blockWrapper), key);
    updateRowAddButtonState(container, addButton, 'input[data-function-input]');
  };
  row.appendChild(input);

  const fnInputs = container.querySelectorAll('input[data-function-input]');
  if (fnInputs.length > 0 || totalCount > 1 || totalCount === -1) {
    const delButton = makeButton('−', () => {
      row.remove();
      moveFunctionAddButtonToLastRow(container, addButton);
      updateRowAddButtonState(container, addButton, 'input[data-function-input]');
      updateCrontaskTrack(crontaskRoot(blockWrapper), key);
    }, 'config-icon-button config-remove-button');
    row.appendChild(delButton);
  }

  container.appendChild(row);
  moveFunctionAddButtonToLastRow(container, addButton);
  updateRowAddButtonState(container, addButton, 'input[data-function-input]');
}

function moveFunctionAddButtonToLastRow(container, addButton) {
  if (!addButton) return;
  const rows = Array.from(container.children).filter(child => child.classList && child.classList.contains('function-row'));
  if (rows.length === 0) {
    const placeholder = document.createElement('div');
    placeholder.className = 'function-row';
    container.appendChild(placeholder);
    placeholder.appendChild(addButton);
    return;
  }
  rows[rows.length - 1].appendChild(addButton);
}

function defaultScheduleTimestamp(value) {
  return value && value !== 'n/a' && value !== '*:*:*:0' ? value : '*:9:10:0';
}

function renderScheduleTimeControls(wrapper, tsInput, blockWrapper, key) {
  const editor = document.createElement('div');
  editor.className = 'schedule-time-ui';
  const fixedGroup = textElement('div', '', 'schedule-time-section');
  editor.appendChild(fixedGroup);
  fixedGroup.appendChild(tsInput);

  const dayRow = textElement('div', '', 'schedule-time-row');
  ['M', 'Tu', 'W', 'Th', 'F', 'Sa', 'Su'].forEach((label, idx) => {
    const button = makeButton(label, () => {
      button.classList.toggle('selected');
      writeScheduleTime(editor, tsInput, blockWrapper, key, false);
    }, 'schedule-day-button');
    button.dataset.day = idx;
    dayRow.appendChild(button);
  });
  fixedGroup.appendChild(dayRow);

  const clockRow = textElement('div', '', 'schedule-time-row schedule-clock-row');
  ['h', 'm', 's'].forEach((part, idx) => {
    const input = makeInput('number', '', part.toUpperCase(), {timePart: part}, () => writeScheduleTime(editor, tsInput, blockWrapper, key, false));
    input.min = 0;
    input.max = idx === 0 ? 23 : 59;
    clockRow.appendChild(input);
  });
  fixedGroup.appendChild(clockRow);

  const sunRow = textElement('div', '', 'schedule-time-row schedule-sun-row');
  const sunSection = textElement('div', '', 'schedule-time-section schedule-time-alt');
  ['sunset', 'sunrise'].forEach(tag => {
    const button = makeButton(tag, () => {
      editor.dataset.sun = editor.dataset.sun === tag ? '' : tag;
      writeScheduleTime(editor, tsInput, blockWrapper, key, true);
    }, 'schedule-sun-button');
    button.dataset.sunButton = tag;
    sunRow.appendChild(button);
  });
  const offset = makeInput('text', '', '+/- min', {sunOffset: 'true'}, () => writeScheduleTime(editor, tsInput, blockWrapper, key, true));
  offset.inputMode = 'numeric';
  sunRow.appendChild(offset);
  sunSection.appendChild(sunRow);
  editor.appendChild(sunSection);

  tsInput.oninput = () => {
    syncScheduleTimeControls(editor, tsInput.value);
    updateCrontaskTrack(crontaskRoot(blockWrapper), key);
  };
  tsInput.onchange = tsInput.oninput;
  wrapper.appendChild(editor);
  syncScheduleTimeControls(editor, tsInput.value);
}

function syncScheduleTimeControls(editor, value) {
  const sunMatch = String(value || '').trim().match(/^(sunrise|sunset)([+-]\d+)?$/);
  editor.dataset.sun = sunMatch ? sunMatch[1] : '';
  editor.querySelectorAll('[data-sun-button]').forEach(button => {
    button.classList.toggle('selected', button.dataset.sunButton === editor.dataset.sun);
  });
  const offset = editor.querySelector('[data-sun-offset]');
  if (offset) offset.value = sunMatch && sunMatch[2] ? sunMatch[2].replace(/^\+/, '') : '';

  const parts = sunMatch ? [] : String(value || '').split(':');
  const selected = expandScheduleDays(parts.length === 4 ? parts[0].trim() : '*');
  editor.querySelectorAll('[data-day]').forEach(button => {
    button.classList.toggle('selected', selected.includes(Number(button.dataset.day)));
  });
  ['h', 'm', 's'].forEach((part, idx) => {
    const input = editor.querySelector(`[data-time-part="${part}"]`);
    if (input) input.value = parts.length === 4 ? parts[idx + 1].trim() : '';
  });
}

function expandScheduleDays(wd) {
  if (wd === '*') return [0, 1, 2, 3, 4, 5, 6];
  const range = String(wd).match(/^(\d)-(\d)$/);
  if (range) {
    const days = [];
    for (let day = Number(range[1]); ; day = (day + 1) % 7) {
      days.push(day);
      if (day === Number(range[2])) break;
    }
    return days;
  }
  return /^\d$/.test(wd) ? [Number(wd)] : [];
}

function compactScheduleDays(days) {
  days = days.sort((a, b) => a - b);
  if (days.length === 0 || days.length === 7) return '*';
  if (days.length === 1) return String(days[0]);
  const starts = days.filter(day => !days.includes((day + 6) % 7));
  const start = starts.length === 1 ? starts[0] : days[0];
  const ordered = [start];
  while (days.includes((ordered[ordered.length - 1] + 1) % 7)) {
    ordered.push((ordered[ordered.length - 1] + 1) % 7);
    if (ordered.length > 7) break;
  }
  return ordered.length === days.length ? `${ordered[0]}-${ordered[ordered.length - 1]}` : `${days[0]}-${days[days.length - 1]}`;
}

function writeScheduleTime(editor, tsInput, blockWrapper, key, preferSun) {
  const sun = editor.dataset.sun;
  const offset = (editor.querySelector('[data-sun-offset]').value || '').trim();
  if (preferSun && sun) {
    tsInput.value = sun + (/^[+-]?\d+$/.test(offset) && Number(offset) !== 0 ? (/^[+-]/.test(offset) ? offset : '+' + offset) : '');
    if (!['-', '+'].includes(offset)) syncScheduleTimeControls(editor, tsInput.value);
  } else {
    const days = Array.from(editor.querySelectorAll('[data-day].selected')).map(button => Number(button.dataset.day));
    const defaults = ['9', '10', '0'];
    const parts = ['h', 'm', 's'].map((part, idx) => {
      const input = editor.querySelector(`[data-time-part="${part}"]`);
      const max = idx === 0 ? 23 : 59;
      return input.value === '' ? defaults[idx] : String(Math.min(max, Math.max(0, Number(input.value))));
    });
    editor.dataset.sun = '';
    tsInput.value = compactScheduleDays(days) + ':' + parts.join(':');
    syncScheduleTimeControls(editor, tsInput.value);
  }
  updateCrontaskTrack(crontaskRoot(blockWrapper), key);
}

function updateCrontaskTrack(container, key) {
  const blocks = container.querySelectorAll('[data-block-index]');
  const blockStrings = Array.from(blocks).map(block => {
    const tsInput = block.querySelector('input[data-field="timestamp"]');
    const fnInputs = block.querySelectorAll('input[data-function-input]');
    const timestamp = tsInput ? defaultScheduleTimestamp(tsInput.value.trim()) : '';
    const functionValues = Array.from(fnInputs).map(input => input.value.trim()).filter(v => v.length > 0);
    const functions = functionValues.join(';');

    if (!timestamp || !functions) return '';
    return `${timestamp}!${functions}`;
  }).filter(b => b.length > 0);

  container.dataset.blockSeparator = ';;';
  const result = joinCrontasks(blockStrings);
  trackChange(key, result);
}

function renderInterruptFields(data, container) {
  // Separate timer interrupt config, individual interrupt configs, and other settings
  const timerKeys = ['timirq', 'timirqcbf', 'timirqseq'];
  const timerData = {};
  const irqData = {};
  const otherData = {};

  Object.entries(data).forEach(([key, value]) => {
    if (timerKeys.includes(key)) {
      timerData[key] = value;
    } else if (key.match(/^irq\d+/)) {
      irqData[key] = value;
    } else {
      otherData[key] = value;
    }
  });

  // Render timer interrupt block
  if (Object.keys(timerData).length > 0) {
    renderTimerInterruptGroup(container, timerData);
  }

  // Extract and group IRQ data by interrupt number
  const irqGroups = {};
  Object.entries(irqData).forEach(([key, value]) => {
    const match = key.match(/^irq(\d+)(_.+)?$/);
    if (match) {
      const irqNum = match[1];
      if (!irqGroups[irqNum]) {
        irqGroups[irqNum] = {};
      }
      irqGroups[irqNum][key] = value;
    }
  });

  // Render each interrupt group
  Object.keys(irqGroups)
    .sort((a, b) => parseInt(a) - parseInt(b))
    .forEach(irqNum => {
      renderInterruptGroup(container, irqNum, irqGroups[irqNum]);
    });

  // Render other settings (e.g., irq_prell_ms)
  Object.entries(otherData).forEach(([key, value]) => {
    renderField(container, key, value);
  });
}

function renderTimerInterruptGroup(container, groupData) {
  const groupWrapper = document.createElement('fieldset');
  groupWrapper.className = 'config-fieldset';
  styleGroupBox(groupWrapper);

  const legend = textElement('legend', 'Timer Interrupt', 'config-legend');
  groupWrapper.appendChild(legend);

  // Enable checkbox
  if ('timirq' in groupData) {
    const wrapper = document.createElement('div');
    wrapper.className = 'config-field-group';
    const label = textElement('label', 'Enable: ', 'config-label');
    const input = createBooleanToggle('timirq', groupData['timirq'], nextValue => trackChange('timirq', nextValue));
    wrapper.appendChild(label);
    wrapper.appendChild(input);
    groupWrapper.appendChild(wrapper);
  }

  // Callbacks input
  if ('timirqcbf' in groupData) {
    renderMultiParamField(groupWrapper, 'timirqcbf', groupData['timirqcbf']);
  }

  // Interval input with ms label
  if ('timirqseq' in groupData) {
    const wrapper = document.createElement('div');
    wrapper.className = 'config-field-group';
    const label = textElement('label', 'Interval: ', 'config-label-block');
    const inputWrapper = document.createElement('div');
    inputWrapper.className = 'config-input-row';
    const input = document.createElement('input');
    input.type = 'number';
    input.value = groupData['timirqseq'];
    input.onchange = () => trackChange('timirqseq', Number(input.value));
    const unit = textElement('span', 'ms', 'config-unit');
    inputWrapper.appendChild(input);
    inputWrapper.appendChild(unit);
    wrapper.appendChild(label);
    wrapper.appendChild(inputWrapper);
    groupWrapper.appendChild(wrapper);
  }

  container.appendChild(groupWrapper);
}

function renderInterruptGroup(container, irqNum, groupData) {
  const groupWrapper = document.createElement('fieldset');
  groupWrapper.className = 'config-fieldset';
  styleGroupBox(groupWrapper);

  const legend = textElement('legend', `Interrupt ${irqNum}`, 'config-legend');
  groupWrapper.appendChild(legend);

  // Render the three fields for this interrupt
  const enableKey = `irq${irqNum}`;
  const cbfKey = `irq${irqNum}_cbf`;
  const trigKey = `irq${irqNum}_trig`;

  // Enable checkbox
  if (enableKey in groupData) {
    const wrapper = document.createElement('div');
    wrapper.className = 'config-field-group';
    const label = textElement('label', 'Enable: ', 'config-label');
    const input = createBooleanToggle(enableKey, groupData[enableKey], nextValue => trackChange(enableKey, nextValue));
    wrapper.appendChild(label);
    wrapper.appendChild(input);
    groupWrapper.appendChild(wrapper);
  }

  // Callbacks input
  if (cbfKey in groupData) {
    renderMultiParamField(groupWrapper, cbfKey, groupData[cbfKey]);
  }

  // Trigger Mode dropdown
  if (trigKey in groupData) {
    const wrapper = document.createElement('div');
    wrapper.className = 'config-field-group';
    const label = textElement('label', 'Trigger Mode: ', 'config-label-block');
    const select = createSelectInput(trigKey, groupData[trigKey]);
    wrapper.appendChild(label);
    wrapper.appendChild(select);
    groupWrapper.appendChild(wrapper);
  }

  container.appendChild(groupWrapper);
}

function trackChange(key, value) {
  if (configData[key] === value) {
    delete changedValues[key];
  } else {
    changedValues[key] = value;
  }
  updateSaveButtonState();
  console.log('Tracked change:', key, '=', value);
  console.log('All changes:', changedValues);
}

function toggleMenu() {
  const menu = document.getElementById('configMenu');
  if (!menu) return;
  menu.classList.toggle('open');
}

function closeMenuOnOutsideClick(event) {
  const menu = document.getElementById('configMenu');
  const toggle = document.getElementById('menuToggle');
  if (!menu || !menu.classList.contains('open') || window.innerWidth > 768) return;
  if (menu.contains(event.target) || (toggle && toggle.contains(event.target))) return;
  closeMobileMenu();
}

document.addEventListener('DOMContentLoaded', () => {
  loadConfig().then(() => {
    decorateCategoryMenu();
    addMenuListeners();
    const toggle = document.getElementById('menuToggle');
    if (toggle) {
      toggle.addEventListener('click', toggleMenu);
    }
    document.addEventListener('pointerdown', closeMenuOnOutsideClick);
    const selectedCategory = loadSelectedCategory();
    const menuItems = Array.from(document.querySelectorAll('#configMenu p'));
    const menuItem = menuItems.find(item => categoryKeyFromMenuItem(item) === selectedCategory) || menuItems[0];
    if (menuItem) {
      menuItem.click();
    }
  });
});
