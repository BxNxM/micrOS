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

// Fields with semicolon-separated parameters
const multiParamFields = new Set(['boothook', 'timirqcbf', 'staessid', 'stapwd']);

// Regex to detect irq callback fields (irq<n>_cbf)
const irqCallbackRegex = /^irq\d+_cbf$/;

let configData = {};
let changedValues = {};

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

function updateConfig(key, value) {
  return fetch('/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ [key]: value })
  })
  .then(r => r.json())
  .then(data => {
    console.log('Update response:', data);
  })
  .catch(e => show('Update failed: ' + e.message));
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
    changedValues = {};
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
  button.textContent = '💾 Save';
  button.style.margin = '0';
  button.style.padding = '8px 16px';
  button.style.alignSelf = 'center';
  button.onclick = () => handleUpdateConfig();
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

  // Check if this is the Interrupts section
  if (Object.keys(data).some(key => key.startsWith('irq'))) {
    renderInterruptFields(data, container);
  } else {
    renderDefaultFields(data, container);
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
  const section = document.createElement('section');
  section.style.marginBottom = '24px';

  const titleEl = document.createElement('h3');
  titleEl.textContent = `${title} (${tasks.length})`;
  titleEl.style.marginBottom = '12px';
  section.appendChild(titleEl);

  if (tasks.length === 0) {
    const empty = document.createElement('div');
    empty.textContent = 'None';
    section.appendChild(empty);
    container.appendChild(section);
    return;
  }

  const list = document.createElement('div');
  list.style.display = 'grid';
  list.style.gap = '8px';

  tasks.forEach(tag => {
    const row = document.createElement('div');
    row.style.display = 'flex';
    row.style.alignItems = 'center';
    row.style.justifyContent = 'space-between';
    row.style.padding = '10px';
    row.style.border = '1px solid #4B376C';
    row.style.borderRadius = '6px';
    row.style.backgroundColor = '#1F1433';

    const label = document.createElement('span');
    label.textContent = tag;
    label.style.flex = '1';
    row.appendChild(label);

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.alignItems = 'center';
    actions.style.gap = '8px';

    if (showActionButtons) {
      const killButton = document.createElement('button');
      killButton.textContent = 'Kill';
      killButton.onclick = () => handleTaskKill(tag, row);
      actions.appendChild(killButton);
    }

    const detailsButton = document.createElement('button');
    detailsButton.textContent = 'Details';
    detailsButton.onclick = () => handleTaskDetails(tag, row);
    actions.appendChild(detailsButton);

    row.appendChild(actions);
    list.appendChild(row);
  });

  section.appendChild(list);
  container.appendChild(section);
}

function handleTaskKill(tag, rowElement) {
  const statusEl = getOrCreateTaskStatus(rowElement);
  statusEl.textContent = 'Killing...';
  restAPI(`task/kill/${encodeURIComponent(tag)}`, false)
    .then(response => {
      if (response && response.state) {
        statusEl.textContent = `Killed: ${JSON.stringify(response.result)}`;
      } else {
        statusEl.textContent = `Kill failed: ${JSON.stringify(response)}`;
      }
    })
    .catch(error => {
      statusEl.textContent = 'Kill error: ' + error.message;
    });
}

function handleTaskDetails(tag, rowElement) {
  const statusEl = getOrCreateTaskStatus(rowElement);
  statusEl.textContent = 'Loading details...';
  restAPI(`task/show/${encodeURIComponent(tag)}`, false)
    .then(response => {
      if (response && response.hasOwnProperty('result')) {
        statusEl.textContent = `${response.result} (${response.state === false ? 'state=false' : 'state=true'})`;
      } else {
        statusEl.textContent = `No detail response: ${JSON.stringify(response)}`;
      }
    })
    .catch(error => {
      statusEl.textContent = 'Details error: ' + error.message;
    });
}

function getOrCreateTaskStatus(rowElement) {
  let statusEl = rowElement.querySelector('.task-status');
  if (!statusEl) {
    statusEl = document.createElement('div');
    statusEl.className = 'task-status';
    statusEl.style.marginLeft = '12px';
    statusEl.style.fontSize = '0.9rem';
    statusEl.style.opacity = '0.9';
    rowElement.appendChild(statusEl);
  }
  return statusEl;
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
  pkgHeader.style.justifyContent = 'space-between';
  pkgHeader.style.alignItems = 'center';
  const title = document.createElement('h3');
  title.textContent = 'Packages';
  title.style.margin = '0';
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
  list.innerHTML = 'Loading...';
  restAPI('pacman/inspect', false)
    .then(resp => {
      list.innerHTML = '';
      if (!resp || !resp.hasOwnProperty('result')) {
        list.textContent = 'No packages';
        return;
      }
      const items = resp.result || [];
      if (Array.isArray(items) && items.length === 0) {
        list.textContent = 'No packages installed.';
        return;
      }
      if (Array.isArray(items)) {
        items.forEach(pkg => {
          const row = document.createElement('div');
          row.style.padding = '8px';
          row.style.border = '1px solid #4B376C';
          row.style.borderRadius = '6px';
          row.style.marginBottom = '6px';
          row.textContent = typeof pkg === 'string' ? pkg : JSON.stringify(pkg);
          list.appendChild(row);
        });
        return;
      }
      if (typeof items === 'object') {
        Object.keys(items).forEach(k => {
          const row = document.createElement('div');
          row.style.padding = '8px';
          row.style.border = '1px solid #4B376C';
          row.style.borderRadius = '6px';
          row.style.marginBottom = '6px';
          row.textContent = `${k}: ${JSON.stringify(items[k])}`;
          list.appendChild(row);
        });
        return;
      }
      list.textContent = JSON.stringify(items);
    })
    .catch(err => {
      list.innerHTML = 'Failed to load packages: ' + err.message;
    });
}

function renderDefaultFields(data, container) {
  Object.entries(data).forEach(([key, value]) => {
    renderField(container, key, value);
  });
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
    input = document.createElement('input');
    input.type = 'checkbox';
    input.checked = value;
    input.onchange = () => trackChange(key, input.checked);
  } else if (typeof value === 'number') {
    input = document.createElement('input');
    input.type = 'number';
    input.value = value;
    input.onchange = () => trackChange(key, Number(input.value));
  } else if (typeof value === 'string') {
    input = document.createElement('input');
    input.type = 'text';
    input.value = value;
    input.onchange = () => trackChange(key, input.value);
  } else {
    input = document.createElement('pre');
    input.textContent = JSON.stringify(value, null, 2);
  }

  wrapper.appendChild(label);
  wrapper.appendChild(input);
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
    createParamInput(inputContainer, key, '', inputContainer.querySelectorAll('input[type="text"]').length, -1, addButton);
    updateMultiParamTrack(inputContainer, key);
  };

  const values = parseSemicolonValues(value);
  if (values.length === 0) {
    values.push('');
  }
  values.forEach((val, idx) => {
    createParamInput(inputContainer, key, val, idx, values.length, addButton);
  });

  updateRowAddButtonState(inputContainer, addButton, 'input[type="text"]');
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
  input.type = 'text';
  input.value = value;
  input.style.flex = '1';
  input.style.boxSizing = 'border-box';
  input.placeholder = `Parameter ${idx + 1}`;
  input.onchange = () => updateMultiParamTrack(container.closest('[data-type="multi-param"]') || container, key);
  input.oninput = () => updateMultiParamTrack(container.closest('[data-type="multi-param"]') || container, key);

  inputWrapper.appendChild(input);

  // Add delete button if more than one field exists
  const currentInputs = container.querySelectorAll('input[type="text"]');
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
  updateRowAddButtonState(container, addButton, 'input[type="text"]');
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
  const inputs = container.querySelectorAll('input[type="text"]');
  const values = Array.from(inputs).map(input => input.value.trim()).filter(v => v.length > 0);
  const result = joinSemicolonValues(values);
  trackChange(key, result);
  const addButton = container.querySelector('.multi-param-add');
  if (addButton) {
    updateRowAddButtonState(container, addButton, 'input[type="text"]');
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
  const blockWrapper = document.createElement('div');
  blockWrapper.style.border = '1px solid #4B376C';
  blockWrapper.style.borderRadius = '6px';
  blockWrapper.style.padding = '20px';
  blockWrapper.style.backgroundColor = '#1F1433';
  blockWrapper.dataset.blockIndex = blockIdx;

  const blockHeader = document.createElement('div');
  blockHeader.style.display = 'flex';
  blockHeader.style.justifyContent = 'space-between';
  blockHeader.style.alignItems = 'center';
  blockHeader.style.marginBottom = '12px';

  const blockTitle = document.createElement('span');
  blockTitle.textContent = `Schedule ${blockIdx + 1}`;
  blockTitle.style.fontWeight = 'bold';
  blockHeader.appendChild(blockTitle);

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
  const addBlockButton = container.querySelector('button:last-child');
  if (addBlockButton && addBlockButton.textContent.includes('Add Schedule')) {
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
  groupWrapper.style.padding = '12px';
  groupWrapper.style.border = '1px solid #4B376C';
  groupWrapper.style.borderRadius = '4px';

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
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.checked = groupData['timirq'];
    input.onchange = () => trackChange('timirq', input.checked);
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
  groupWrapper.style.padding = '12px';
  groupWrapper.style.border = '1px solid #4B376C';
  groupWrapper.style.borderRadius = '4px';

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
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.checked = groupData[enableKey];
    input.onchange = () => trackChange(enableKey, input.checked);
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
    const select = document.createElement('select');
    select.value = groupData[trigKey];
    ['up', 'down', 'both'].forEach(option => {
      const opt = document.createElement('option');
      opt.value = option;
      opt.textContent = option.charAt(0).toUpperCase() + option.slice(1);
      select.appendChild(opt);
    });
    select.style.width = '100%';
    select.style.boxSizing = 'border-box';
    select.onchange = () => trackChange(trigKey, select.value);
    wrapper.appendChild(label);
    wrapper.appendChild(select);
    groupWrapper.appendChild(wrapper);
  }

  container.appendChild(groupWrapper);
}

function trackChange(key, value) {
  changedValues[key] = value;
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
    // Optionally, show the first section by default
    const firstMenuItem = document.querySelector('#configMenu p');
    if (firstMenuItem) {
      firstMenuItem.click();
    }
  });
});
