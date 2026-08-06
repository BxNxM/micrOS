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

// Fields with semicolon-separated parameters
const multiParamFields = new Set(['boothook', 'timirqcbf', 'staessid', 'stapwd']);

// Regex to detect irq callback fields (irq<n>_cbf)
const irqCallbackRegex = /^irq\d+_cbf$/;

let configData = {};
let changedValues = {};
const selectedCategoryKey = 'micros.config.selectedCategory';

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

function createPasswordToggle(input) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = 'Show';
  button.style.width = '56px';
  button.style.height = '32px';
  button.style.padding = '0';
  button.style.cursor = 'pointer';
  button.style.flexShrink = '0';
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
  row.style.display = 'flex';
  row.style.alignItems = 'center';
  row.style.gap = '8px';
  row.style.width = '100%';
  row.style.maxWidth = '350px';
  input.style.flex = '1';
  input.style.boxSizing = 'border-box';
  input.style.minWidth = '0';
  input.style.maxWidth = 'none';
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
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'config-toggle-option ' + className;
    button.textContent = label;
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
    const opt = document.createElement('option');
    opt.value = option;
    opt.textContent = option.charAt(0).toUpperCase() + option.slice(1);
    select.appendChild(opt);
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

// Helper: Parse crontasks (double semicolon for blocks, single for functions)
function parseCrontasks(value) {
  if (!value || typeof value !== 'string') return [];
  return value.split(';;').map(block => block.trim()).filter(b => b.length > 0);
}

// Helper: Join semicolon values
function joinSemicolonValues(values) {
  return values.filter(v => v && v.trim().length > 0).join('; ');
}

// Helper: Join crontask blocks
function joinCrontasks(blocks) {
  return blocks.filter(b => b && b.trim().length > 0).join('; ');
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
      console.log('Clicked menu item:', item.textContent);
      setSelectedMenuItem(item);
      closeMobileMenu();
      const key = item.textContent;
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
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'config-save-button';
  button.textContent = '💾 Save';
  button.onclick = () => handleUpdateConfig();
  button.disabled = !hasUnsavedChanges();
  return button;
}

function renderConfigFields(data, sectionKey = '') {
  const container = document.getElementById('configFields');
  container.innerHTML = ''; // Clear previous content

  if (isEditableConfigSection(sectionKey)) {
    const headerRow = document.createElement('div');
    headerRow.style.display = 'flex';
    headerRow.style.flexDirection = 'row';
    headerRow.style.alignItems = 'center';
    headerRow.style.justifyContent = 'flex-start';
    headerRow.style.gap = '12px';
    headerRow.style.marginBottom = '8px';

    const heading = document.createElement('h2');
    heading.textContent = sectionKey;
    heading.style.margin = '0';
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
  const heading = document.createElement('h2');
  heading.textContent = 'Tasks';
  heading.style.marginTop = '0';
  container.appendChild(heading);

  const loading = document.createElement('div');
  loading.textContent = 'Loading task list...';
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
    actions.unshift({label: 'Kill', handler: handleTaskKill});
  }
  renderActionList(container, title, tasks, actions);
}

function renderActionList(container, title, items, actions) {
  const section = document.createElement('section');
  section.style.marginBottom = '24px';

  if (title) {
    const titleEl = document.createElement('h3');
    titleEl.textContent = `${title} (${items.length})`;
    titleEl.style.marginBottom = '12px';
    section.appendChild(titleEl);
  }

  if (items.length === 0) {
    section.appendChild(document.createTextNode('None'));
    container.appendChild(section);
    return;
  }

  const list = document.createElement('div');
  list.style.display = 'grid';
  list.style.gap = '8px';
  items.forEach(item => renderActionRow(list, item, actions));
  section.appendChild(list);
  container.appendChild(section);
}

function renderActionRow(container, labelText, actions) {
  const row = document.createElement('div');
  row.style.padding = '10px';
  row.style.border = '1px solid #4B376C';
  row.style.borderRadius = '6px';
  row.style.backgroundColor = '#1F1433';

  const header = document.createElement('div');
  header.style.display = 'flex';
  header.style.alignItems = 'center';
  header.style.justifyContent = 'space-between';
  header.style.gap = '8px';

  const label = document.createElement('span');
  label.textContent = labelText;
  label.style.flex = '1';
  header.appendChild(label);

  const details = document.createElement('pre');
  details.style.display = 'none';
  details.style.marginTop = '8px';

  actions.forEach(action => {
    const button = document.createElement('button');
    button.textContent = action.label;
    button.onclick = () => action.handler(labelText, details, button);
    header.appendChild(button);
  });

  row.appendChild(header);
  row.appendChild(details);
  container.appendChild(row);
}

function setInlineDetails(details, text) {
  details.textContent = text;
  details.style.display = 'block';
}

function styleGroupBox(element, padding = '12px') {
  element.style.border = '1px solid #4B376C';
  element.style.borderRadius = '6px';
  element.style.padding = padding;
  element.style.backgroundColor = '#1F1433';
}

function handleTaskKill(tag, details) {
  setInlineDetails(details, 'Killing...');
  restAPI(`task/kill/${encodeURIComponent(tag)}`, false)
    .then(response => {
      if (response && response.state) {
        setInlineDetails(details, `Killed: ${JSON.stringify(response.result)}`);
      } else {
        setInlineDetails(details, `Kill failed: ${JSON.stringify(response)}`);
      }
    })
    .catch(error => {
      setInlineDetails(details, 'Kill error: ' + error.message);
    });
}

function handleTaskDetails(tag, details) {
  if (details.textContent && details.textContent !== 'Loading details...') {
    details.style.display = details.style.display === 'none' ? 'block' : 'none';
    return;
  }
  setInlineDetails(details, 'Loading details...');
  restAPI(`task/show/${encodeURIComponent(tag)}`, false)
    .then(response => {
      if (response && response.hasOwnProperty('result')) {
        setInlineDetails(details, `${response.result} (${response.state === false ? 'state=false' : 'state=true'})`);
      } else {
        setInlineDetails(details, `No detail response: ${JSON.stringify(response)}`);
      }
    })
    .catch(error => {
      setInlineDetails(details, 'Details error: ' + error.message);
    });
}

function makeError(message) {
  const err = document.createElement('div');
  err.style.color = '#ff8b8b';
  err.style.fontWeight = 'bold';
  err.textContent = message;
  return err;
}

// Packages UI: install and inspect
function renderPackagesSection() {
  const container = document.getElementById('configFields');
  container.innerHTML = '';
  const heading = document.createElement('h2');
  heading.textContent = 'Packages';
  heading.style.marginTop = '0';
  container.appendChild(heading);

  // Install block
  const installSection = document.createElement('section');
  installSection.style.marginBottom = '16px';
  const installLabel = document.createElement('label');
  installLabel.textContent = 'Install Package (URL or name):';
  installLabel.style.fontWeight = 'bold';
  installSection.appendChild(installLabel);

  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = 'e.g. umqtt.simple or https://...';
  input.id = 'packageUrlInput';
  input.style.width = '100%';
  input.style.boxSizing = 'border-box';
  input.style.margin = '8px 0';
  installSection.appendChild(input);

  const installBtn = document.createElement('button');
  installBtn.textContent = 'Install';
  installBtn.onclick = () => {
    const url = input.value.trim();
    if (!url) {
      alert('Enter package URL or name');
      return;
    }
    installBtn.disabled = true;
    installBtn.textContent = 'Installing...';
    // encode the URL so slashes and other characters are preserved
    restAPI('pacman/install/"' + url + '"', false)
      .then(resp => {
        alert('Install response: ' + JSON.stringify(resp));
        installBtn.disabled = false;
        installBtn.textContent = 'Install';
        refreshPackagesList();
      })
      .catch(err => {
        alert('Install failed: ' + err.message);
        installBtn.disabled = false;
        installBtn.textContent = 'Install';
      });
  };
  installSection.appendChild(installBtn);
  container.appendChild(installSection);

  // Packages list block
  const pkgSection = document.createElement('section');
  const pkgHeader = document.createElement('div');
  pkgHeader.style.display = 'flex';
  pkgHeader.style.alignItems = 'center';
  pkgHeader.style.gap = '8px';
  pkgHeader.style.padding = '0 10px';
  pkgHeader.style.boxSizing = 'border-box';
  const title = document.createElement('h3');
  title.textContent = 'Packages';
  title.style.margin = '0';
  title.style.flex = '1';
  pkgHeader.appendChild(title);
  const refreshBtn = document.createElement('button');
  refreshBtn.textContent = 'Refresh';
  refreshBtn.onclick = () => {
    refreshPackagesList();
  };
  pkgHeader.appendChild(refreshBtn);
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
        renderActionList(list, '', items.map(pkg => typeof pkg === 'string' ? pkg : JSON.stringify(pkg)), [
          {label: 'Details', handler: loadPackageDetails}
        ]);
        return;
      }
      if (typeof items === 'object') {
        renderActionList(list, '', Object.keys(items), [
          {label: 'Details', handler: loadPackageDetails}
        ]);
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

function loadPackageDetails(packageName, details, button) {
  if (details.textContent) {
    details.style.display = details.style.display === 'none' ? 'block' : 'none';
    return;
  }
  button.disabled = true;
  button.textContent = 'Loading...';
  restAPI('pacman/inspect/"' + packageName + '"', false, 10000)
    .then(resp => {
      setInlineDetails(details, formatPackageDetails(resp && resp.result));
    })
    .catch(err => {
      setInlineDetails(details, 'Failed to load details: ' + err.message);
    })
    .finally(() => {
      button.disabled = false;
      button.textContent = 'Details';
    });
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
  renderDefaultFields(data, container);
  const input = container.querySelector('input[type="text"]');
  const select = document.createElement('select');
  select.disabled = true;
  select.appendChild(new Option('Loading known maps...', ''));
  if (input) {
    input.parentNode.appendChild(select);
  }

  const infoSection = document.createElement('section');
  infoSection.style.marginTop = '20px';

  const title = document.createElement('h3');
  title.textContent = 'Runtime Pin Map';
  title.style.marginBottom = '8px';
  infoSection.appendChild(title);

  const status = document.createElement('div');
  status.textContent = 'Loading pin map...';
  infoSection.appendChild(status);
  container.appendChild(infoSection);

  restAPI('system/pinmap', false, 10000)
    .then(response => {
      status.remove();
      if (!response || !response.result || response.state === false) {
        infoSection.appendChild(makeError('Unable to load pin map.'));
        return;
      }
      populatePinMapSelector(select, input, response.result.known_maps || []);
      renderPinMapInfo(infoSection, response.result);
    })
    .catch(error => {
      status.remove();
      infoSection.appendChild(makeError('Failed to load pin map: ' + error.message));
    });
}

function populatePinMapSelector(select, input, knownMaps) {
  if (!select || !input) return;
  select.innerHTML = '';
  select.appendChild(new Option('Select known map...', ''));
  knownMaps.forEach(mapName => {
    select.appendChild(new Option(mapName, mapName));
  });
  select.disabled = knownMaps.length === 0;
  const selectedMap = getPinMapName(input.value);
  select.value = knownMaps.includes(selectedMap) ? selectedMap : '';
  select.onchange = () => {
    if (!select.value) return;
    input.value = mergePinMapName(input.value, select.value);
    trackChange('cstmpmap', input.value);
  };
}

function getPinMapName(value) {
  const firstPart = (value || '').split(';')[0].trim();
  return firstPart && !firstPart.includes(':') ? firstPart : '';
}

function mergePinMapName(value, mapName) {
  const parts = (value || '').split(';').map(part => part.trim()).filter(part => part);
  const customPins = parts[0] && !parts[0].includes(':') ? parts.slice(1) : parts;
  return [mapName].concat(customPins).join('; ');
}

function renderPinMapInfo(container, pinmap) {
  renderKeyValueTable(container, 'Active Map', {'map': pinmap.map || 'n/a'});
  renderKeyValueTable(container, 'Custom Pins', pinmap.custom || {});
  renderKeyValueTable(container, 'Booked Pins', pinmap.booked || {});
}

function renderKeyValueTable(container, titleText, data) {
  const section = document.createElement('section');
  section.style.marginBottom = '16px';
  const title = document.createElement('h4');
  title.textContent = titleText;
  title.style.marginBottom = '6px';
  section.appendChild(title);
  container.appendChild(section);
  const entries = Object.entries(data);
  if (entries.length === 0) {
    section.appendChild(document.createTextNode('None'));
    return;
  }
  const table = document.createElement('table');
  table.style.borderCollapse = 'collapse';
  table.style.width = '100%';
  table.style.maxWidth = '720px';
  entries.forEach(([key, value]) => {
    const row = document.createElement('tr');
    [key, String(value)].forEach(text => {
      const cell = document.createElement('td');
      cell.textContent = text;
      cell.style.border = '1px solid #4B376C';
      cell.style.padding = '6px 8px';
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
  wrapper.style.marginBottom = '12px';

  const label = document.createElement('label');
  label.textContent = 'WiFi Networks: ';
  label.style.fontWeight = 'bold';
  label.style.display = 'block';
  label.style.marginBottom = '8px';
  wrapper.appendChild(label);

  const pairContainer = document.createElement('div');
  pairContainer.style.display = 'flex';
  pairContainer.style.flexDirection = 'column';
  pairContainer.style.gap = '8px';

  const addButton = document.createElement('button');
  addButton.textContent = '+';
  addButton.style.width = '40px';
  addButton.style.height = '32px';
  addButton.style.padding = '0';
  addButton.style.cursor = 'pointer';
  addButton.onclick = () => {
    if (addButton.disabled) return;
    createWifiCredentialPair(pairContainer, '', '', addButton, -1);
    updateWifiCredentialTrack(pairContainer, addButton);
  };

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
  row.style.display = 'flex';
  row.style.alignItems = 'flex-end';
  row.style.gap = '8px';
  row.style.flexWrap = 'wrap';

  const ssidWrap = document.createElement('div');
  ssidWrap.style.display = 'flex';
  ssidWrap.style.flexDirection = 'column';
  ssidWrap.style.width = '100%';
  ssidWrap.style.maxWidth = '350px';
  const ssidLabel = document.createElement('label');
  ssidLabel.textContent = 'WiFi SSID:';
  const ssidInput = document.createElement('input');
  ssidInput.type = 'text';
  ssidInput.value = ssid;
  ssidInput.dataset.wifiSsid = 'true';
  ssidInput.oninput = () => updateWifiCredentialTrack(container, addButton);
  ssidWrap.appendChild(ssidLabel);
  ssidWrap.appendChild(ssidInput);
  row.appendChild(ssidWrap);

  const pwdWrap = document.createElement('div');
  pwdWrap.style.display = 'flex';
  pwdWrap.style.flexDirection = 'column';
  pwdWrap.style.width = '100%';
  pwdWrap.style.maxWidth = '350px';
  const pwdLabel = document.createElement('label');
  pwdLabel.textContent = 'WiFi Password:';
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
    const delButton = document.createElement('button');
    delButton.textContent = '−';
    delButton.style.width = '40px';
    delButton.style.height = '32px';
    delButton.style.cursor = 'pointer';
    delButton.style.color = '#ff8b8b';
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
  wrapper.style.marginBottom = '12px';
  wrapper.style.display = 'flex';
  wrapper.style.flexDirection = 'column';

  const label = document.createElement('label');
  label.textContent = (configLabelMap[key] || key) + ': ';
  label.style.fontWeight = 'bold';

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
  wrapper.style.marginBottom = '12px';

  const label = document.createElement('label');
  label.textContent = (configLabelMap[key] || key) + ': ';
  label.style.fontWeight = 'bold';
  label.style.display = 'block';
  label.style.marginBottom = '8px';
  wrapper.appendChild(label);

  const inputContainer = document.createElement('div');
  inputContainer.style.display = 'flex';
  inputContainer.style.flexDirection = 'column';
  inputContainer.style.gap = '8px';
  inputContainer.dataset.key = key;
  inputContainer.dataset.type = 'multi-param';

  const addButton = document.createElement('button');
  addButton.textContent = '+';
  addButton.className = 'multi-param-add';
  addButton.style.width = '40px';
  addButton.style.height = '32px';
  addButton.style.padding = '0';
  addButton.style.cursor = 'pointer';
  addButton.onclick = () => {
    if (addButton.disabled) return;
    createParamInput(inputContainer, key, '', inputContainer.querySelectorAll('input[data-param-input]').length, -1, addButton);
    updateMultiParamTrack(inputContainer, key);
  };

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
  inputWrapper.style.display = 'flex';
  inputWrapper.style.alignItems = 'center';
  inputWrapper.style.gap = '8px';
  inputWrapper.className = 'param-row';

  const input = document.createElement('input');
  input.type = isPasswordField(key) ? 'password' : 'text';
  input.value = value;
  input.style.flex = '1';
  input.style.boxSizing = 'border-box';
  input.placeholder = `Parameter ${idx + 1}`;
  input.dataset.paramInput = 'true';
  input.onchange = () => updateMultiParamTrack(container.closest('[data-type="multi-param"]') || container, key);
  input.oninput = () => updateMultiParamTrack(container.closest('[data-type="multi-param"]') || container, key);

  appendInputWithPasswordToggle(inputWrapper, input, key);

  // Add delete button if more than one field exists
  const currentInputs = container.querySelectorAll('input[data-param-input]');
  if (currentInputs.length > 0 || totalCount > 1 || totalCount === -1) {
    const delButton = document.createElement('button');
    delButton.textContent = '−';
    delButton.style.width = '40px';
    delButton.style.height = '32px';
    delButton.style.cursor = 'pointer';
    delButton.style.color = '#ff8b8b';
    delButton.onclick = () => {
      inputWrapper.remove();
      moveAddButtonToLastRow(container, addButton);
      updateMultiParamTrack(container.closest('[data-type="multi-param"]') || container, key);
    };
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
  wrapper.style.marginBottom = '12px';

  const label = document.createElement('label');
  label.textContent = (configLabelMap[key] || key) + ': ';
  label.style.fontWeight = 'bold';
  label.style.display = 'block';
  label.style.marginBottom = '8px';
  wrapper.appendChild(label);

  const blockContainer = document.createElement('div');
  blockContainer.style.display = 'flex';
  blockContainer.style.flexDirection = 'column';
  blockContainer.style.gap = '16px';
  blockContainer.dataset.key = key;
  blockContainer.dataset.type = 'crontask';

  const blocks = parseCrontasks(value);
  blocks.forEach((block, idx) => {
    createCrontaskBlock(blockContainer, key, block, idx, blocks.length);
  });

  // Add button for new block
  const addBlockButton = document.createElement('button');
  addBlockButton.textContent = '+ Add Schedule';
  addBlockButton.className = 'schedule-add';
  addBlockButton.style.width = '100%';
  addBlockButton.style.padding = '8px';
  addBlockButton.style.cursor = 'pointer';
  addBlockButton.onclick = () => {
    createCrontaskBlock(blockContainer, key, '', blockContainer.querySelectorAll('[data-block-index]').length, -1);
    updateCrontaskTrack(blockContainer, key);
  };
  blockContainer.appendChild(addBlockButton);

  wrapper.appendChild(blockContainer);
  container.appendChild(wrapper);
}

function createCrontaskBlock(container, key, block, blockIdx, totalBlocks) {
  const blockWrapper = document.createElement('fieldset');
  styleGroupBox(blockWrapper, '20px');
  blockWrapper.dataset.blockIndex = blockIdx;

  const legend = document.createElement('legend');
  legend.textContent = `Schedule ${blockIdx + 1}`;
  legend.style.fontWeight = 'bold';
  legend.style.fontSize = '1.1rem';
  blockWrapper.appendChild(legend);

  const blockHeader = document.createElement('div');
  blockHeader.style.display = 'flex';
  blockHeader.style.justifyContent = 'flex-end';
  blockHeader.style.alignItems = 'center';
  blockHeader.style.marginBottom = '12px';

  if (totalBlocks > 1 || totalBlocks === -1) {
    const delBlockButton = document.createElement('button');
    delBlockButton.textContent = 'Remove';
    delBlockButton.style.cursor = 'pointer';
    delBlockButton.style.color = '#ff8b8b';
    delBlockButton.onclick = () => {
      blockWrapper.remove();
      updateCrontaskTrack(container.closest('[data-type="crontask"]') || container, key);
    };
    blockHeader.appendChild(delBlockButton);
  }
  blockWrapper.appendChild(blockHeader);

  // Timestamp field
  const tsWrapper = document.createElement('div');
  tsWrapper.style.marginBottom = '12px';
  const tsLabel = document.createElement('label');
  tsLabel.textContent = 'Time (WD:H:M:S or sunset/sunrise +/- offset): ';
  tsLabel.style.fontWeight = 'bold';
  tsLabel.style.display = 'block';
  tsLabel.style.marginBottom = '4px';
  const tsInput = document.createElement('input');
  tsInput.type = 'text';
  tsInput.style.width = '100%';
  tsInput.style.boxSizing = 'border-box';
  tsInput.dataset.field = 'timestamp';

  const blockParts = block.split('!');
  const timestamp = blockParts[0] || '';
  const functionsStr = blockParts.slice(1).join('!');

  tsInput.value = timestamp;
  tsInput.onchange = () => updateCrontaskTrack(container.closest('[data-type="crontask"]') || container, key);
  tsInput.oninput = () => updateCrontaskTrack(container.closest('[data-type="crontask"]') || container, key);
  tsWrapper.appendChild(tsLabel);
  tsWrapper.appendChild(tsInput);
  blockWrapper.appendChild(tsWrapper);

  // Functions field
  const fnWrapper = document.createElement('div');
  fnWrapper.style.marginBottom = '8px';
  const fnLabel = document.createElement('label');
  fnLabel.textContent = 'Functions: ';
  fnLabel.style.fontWeight = 'bold';
  fnLabel.style.display = 'block';
  fnLabel.style.marginBottom = '4px';
  fnWrapper.appendChild(fnLabel);

  const fnContainer = document.createElement('div');
  fnContainer.style.display = 'flex';
  fnContainer.style.flexDirection = 'column';
  fnContainer.style.gap = '8px';
  fnContainer.dataset.type = 'function-list';

  const addFnButton = document.createElement('button');
  addFnButton.textContent = '+';
  addFnButton.style.width = '40px';
  addFnButton.style.height = '40px';
  addFnButton.style.padding = '0';
  addFnButton.style.cursor = 'pointer';
  addFnButton.onclick = () => {
    if (addFnButton.disabled) return;
    createFunctionRow(fnContainer, key, blockWrapper, '', fnContainer.querySelectorAll('input[data-function-input]').length, -1, addFnButton);
    updateCrontaskTrack(container.closest('[data-type="crontask"]') || container, key);
  };

  const functionValues = parseSemicolonValues(functionsStr);
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
  row.style.display = 'flex';
  row.style.alignItems = 'center';
  row.style.gap = '8px';
  row.className = 'function-row';

  const input = document.createElement('input');
  input.type = 'text';
  input.value = value;
  input.style.flex = '1';
  input.style.boxSizing = 'border-box';
  input.placeholder = `Function ${idx + 1}`;
  input.dataset.functionInput = 'true';
  input.onchange = () => {
    updateCrontaskTrack(blockWrapper.closest('[data-type="crontask"]') || blockWrapper, key);
    updateRowAddButtonState(container, addButton, 'input[data-function-input]');
  };
  input.oninput = () => {
    updateCrontaskTrack(blockWrapper.closest('[data-type="crontask"]') || blockWrapper, key);
    updateRowAddButtonState(container, addButton, 'input[data-function-input]');
  };
  row.appendChild(input);

  const fnInputs = container.querySelectorAll('input[data-function-input]');
  if (fnInputs.length > 0 || totalCount > 1 || totalCount === -1) {
    const delButton = document.createElement('button');
    delButton.textContent = '−';
    delButton.style.width = '40px';
    delButton.style.height = '32px';
    delButton.style.cursor = 'pointer';
    delButton.style.color = '#ff8b8b';
    delButton.onclick = () => {
      row.remove();
      moveFunctionAddButtonToLastRow(container, addButton);
      updateRowAddButtonState(container, addButton, 'input[data-function-input]');
      updateCrontaskTrack(blockWrapper.closest('[data-type="crontask"]') || blockWrapper, key);
    };
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
    placeholder.style.display = 'flex';
    placeholder.style.alignItems = 'center';
    placeholder.style.gap = '8px';
    placeholder.className = 'function-row';
    container.appendChild(placeholder);
    placeholder.appendChild(addButton);
    return;
  }
  rows[rows.length - 1].appendChild(addButton);
}

function updateCrontaskTrack(container, key) {
  const blocks = container.querySelectorAll('[data-block-index]');
  const blockStrings = Array.from(blocks).map(block => {
    const tsInput = block.querySelector('input[data-field="timestamp"]');
    const fnInputs = block.querySelectorAll('input[data-function-input]');
    const timestamp = tsInput ? tsInput.value.trim() : '';
    const functions = Array.from(fnInputs).map(input => input.value.trim()).filter(v => v.length > 0).join('; ');

    if (!timestamp) return '';
    if (!functions) return timestamp;
    return `${timestamp}!${functions}`;
  }).filter(b => b.length > 0);

  const result = blockStrings.join(';;');
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
  groupWrapper.style.marginBottom = '20px';
  styleGroupBox(groupWrapper);

  const legend = document.createElement('legend');
  legend.textContent = 'Timer Interrupt';
  legend.style.fontWeight = 'bold';
  legend.style.fontSize = '1.1rem';
  groupWrapper.appendChild(legend);

  // Enable checkbox
  if ('timirq' in groupData) {
    const wrapper = document.createElement('div');
    wrapper.style.marginBottom = '12px';
    const label = document.createElement('label');
    label.textContent = 'Enable: ';
    label.style.fontWeight = 'bold';
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
    wrapper.style.marginBottom = '12px';
    const label = document.createElement('label');
    label.textContent = 'Interval: ';
    label.style.fontWeight = 'bold';
    label.style.display = 'block';
    const inputWrapper = document.createElement('div');
    inputWrapper.style.display = 'flex';
    inputWrapper.style.alignItems = 'center';
    inputWrapper.style.gap = '6px';
    const input = document.createElement('input');
    input.type = 'number';
    input.value = groupData['timirqseq'];
    input.style.flex = '1';
    input.onchange = () => trackChange('timirqseq', Number(input.value));
    const unit = document.createElement('span');
    unit.textContent = 'ms';
    unit.style.fontWeight = 'bold';
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
  groupWrapper.style.marginBottom = '20px';
  styleGroupBox(groupWrapper);

  const legend = document.createElement('legend');
  legend.textContent = `Interrupt ${irqNum}`;
  legend.style.fontWeight = 'bold';
  legend.style.fontSize = '1.1rem';
  groupWrapper.appendChild(legend);

  // Render the three fields for this interrupt
  const enableKey = `irq${irqNum}`;
  const cbfKey = `irq${irqNum}_cbf`;
  const trigKey = `irq${irqNum}_trig`;

  // Enable checkbox
  if (enableKey in groupData) {
    const wrapper = document.createElement('div');
    wrapper.style.marginBottom = '12px';
    const label = document.createElement('label');
    label.textContent = 'Enable: ';
    label.style.fontWeight = 'bold';
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
    wrapper.style.marginBottom = '12px';
    const label = document.createElement('label');
    label.textContent = 'Trigger Mode: ';
    label.style.fontWeight = 'bold';
    label.style.display = 'block';
    const select = createSelectInput(trigKey, groupData[trigKey]);
    select.style.width = '100%';
    select.style.boxSizing = 'border-box';
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

document.addEventListener('DOMContentLoaded', () => {
  loadConfig().then(() => {
    addMenuListeners();
    const toggle = document.getElementById('menuToggle');
    if (toggle) {
      toggle.addEventListener('click', toggleMenu);
    }
    const selectedCategory = loadSelectedCategory();
    const menuItems = Array.from(document.querySelectorAll('#configMenu p'));
    const menuItem = menuItems.find(item => item.textContent === selectedCategory) || menuItems[0];
    if (menuItem) {
      menuItem.click();
    }
  });
});
