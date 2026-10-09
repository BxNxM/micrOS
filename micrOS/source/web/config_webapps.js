// Loaded on demand by config.js when the Web menu opens.
// Keep Web-menu styles with its on-demand script.
(() => {
  if (document.getElementById('configWebAppsStyles')) return;
  const style = document.createElement('style');
  style.id = 'configWebAppsStyles';
  style.textContent = `
#configWebApps .config-hint {
  display: block;
  opacity: 0.75;
  margin: 8px 0 0;
}

#configWebApps .config-mount-access-row {
  justify-content: flex-start;
}

#configWebApps .config-mount-access-row > .config-field {
  flex: 0 1 160px;
  width: auto;
  margin-bottom: 0;
}
`;
  document.head.appendChild(style);
})();

Object.assign(configLabelMap, {
  'web.dashboard': 'Dashboard',
  'web.fileserver': 'Fileserver',
  'web.fs_explore': 'Show all dirs',
  'web.config': 'Config',
  'web.fs_write_access.modules': 'Module',
  'web.fs_write_access.data': 'Data',
  'web.fs_write_access.logs': 'Logs',
});

function renderWebAppsSection() {
  renderConfigFields(filterConfig('Web'), 'Web');
  const container = document.getElementById('configFields');
  const toggle = container.querySelector('[data-config-key="webui"]');
  const label = toggle && toggle.parentElement.querySelector('.config-label');
  if (label) label.style.visibility = 'hidden';
  updateWebAppsVisibility(container);
}

function storeWebAppsStatus(status) {
  Object.keys(configData).filter(key => key.startsWith('web.fs_write_access.'))
    .forEach(key => { delete configData[key]; });
  Object.entries(status).forEach(([key, value]) => {
    if (typeof value === 'boolean') configData['web.' + key] = value;
  });
  Object.entries(status.fs_write_access || {}).forEach(([mount, value]) => {
    const name = mount.replace(/^\$/, '');
    if (['modules', 'data', 'logs'].includes(name) && typeof value === 'boolean') {
      configData['web.fs_write_access.' + name] = value;
    }
  });
}

async function getWebAppsStatus() {
  const response = await restAPI('web/status/pwd=' + restQuote(configData.appwd || ''), false);
  if (!response || response.state !== true || !response.result ||
      typeof response.result !== 'object' || Array.isArray(response.result)) {
    throw new Error('Unable to load web app settings.');
  }
  return response.result;
}

let webAppUpdating = false;

async function updateWebApp(key, value) {
  if (webAppUpdating || configData[key] === value) return;
  const originalGroup = document.getElementById('configWebApps');
  const focusedButton = document.activeElement;
  const restoreFocus = originalGroup && originalGroup.contains(focusedButton);
  const focusedLabel = restoreFocus ? focusedButton.textContent : '';
  webAppUpdating = true;
  const refresh = message => {
    const group = document.getElementById('configWebApps');
    if (group && group.refreshWebApps) group.refreshWebApps(message);
  };
  if (originalGroup) originalGroup.setWebAppsPending();
  let errorMessage = '';
  try {
    const mountPrefix = 'web.fs_write_access.';
    const isMount = key.startsWith(mountPrefix);
    const argument = key.slice(isMount ? mountPrefix.length : 4);
    const route = isMount ? 'web/mounts_w_access/' : 'web/load/';
    const auth = isMount ? '/pwd=' + restQuote(configData.appwd || '') : '';
    const response = await restAPI(route + argument + '=' + (value ? 'True' : 'False') + auth, false);
    if (!response || response.state !== true) throw new Error('Unable to update web app settings.');
    const status = await getWebAppsStatus();
    storeWebAppsStatus(status);
    if (configData[key] !== value) throw new Error('Unable to confirm web app settings.');
  } catch (error) {
    errorMessage = error.message;
    // Reconcile with the device if the write succeeded but confirmation failed.
    try { storeWebAppsStatus(await getWebAppsStatus()); } catch (_) {}
  } finally {
    webAppUpdating = false;
    const group = document.getElementById('configWebApps');
    const focusStayedInGroup = group === originalGroup &&
      (group.contains(document.activeElement) || document.activeElement === document.body);
    refresh(errorMessage);
    if (restoreFocus && focusStayedInGroup) {
      const toggle = group.querySelector(`[data-config-key="${key}"]`);
      const button = toggle && Array.from(toggle.querySelectorAll('button'))
        .find(button => button.textContent === focusedLabel);
      (button || group).focus({preventScroll: true});
    }
  }
}

function renderWebAppField(container, key, value) {
  const field = document.createElement('div');
  field.className = 'config-field';
  field.appendChild(textElement('label', configLabel(key) + ': ', 'config-label'));
  const toggle = createBooleanToggle(key, value, nextValue => updateWebApp(key, nextValue));
  toggle.querySelectorAll('button').forEach(button => {
    button.disabled = webAppUpdating || key === 'web.config';
  });
  field.appendChild(toggle);
  container.appendChild(field);
}

function updateWebAppsVisibility(container) {
  const enabled = (changedValues.webui ?? configData.webui) === true;
  const toggle = container.querySelector('[data-config-key="webui"]');
  if (toggle) {
    let status = container.querySelector('#configWebUiStatus');
    if (!status) {
      status = textElement('small', '');
      status.id = 'configWebUiStatus';
      status.setAttribute('role', 'status');
      toggle.parentElement.appendChild(status);
    }
    status.textContent = enabled
      ? 'Web services enabled'
      : 'Web services disabled: web app and REST API will be unavailable.';
    status.className = enabled ? 'config-label config-alarm-ok' : 'config-error';
  }
  const group = container.querySelector('#configWebApps');
  if (group) group.hidden = !enabled;
  else if (enabled) renderWebApps(container);
}

function renderWebApps(container) {
  const group = createConfigFieldset('Web apps');
  group.id = 'configWebApps';
  group.tabIndex = -1;
  const fields = document.createElement('div');
  const message = textElement('p', 'Loading web apps...');
  message.setAttribute('role', 'status');
  group.appendChild(fields);
  group.appendChild(message);
  group.appendChild(textElement('small', 'Changes apply immediately. Disabling an app requires a reboot.', 'config-hint'));
  container.appendChild(group);

  function render(statusMessage = '') {
    fields.innerHTML = '';
    const current = configData;
    Object.entries(current)
      .filter(([key, value]) => key.startsWith('web.') && key !== 'web.fs_explore' && !key.startsWith('web.fs_write_access.') && typeof value === 'boolean')
      .sort(([a], [b]) => configLabel(a).localeCompare(configLabel(b), 'en'))
      .forEach(([key, value]) => {
        renderWebAppField(fields, key, value);
        if (key === 'web.fileserver' && current[key] === true && typeof current['web.fs_explore'] === 'boolean') {
          const options = createConfigFieldset('Fileserver options');
          renderWebAppField(options, 'web.fs_explore', current['web.fs_explore']);
          if (current['web.fileserver'] && current['web.fs_explore']) {
            const accessRow = document.createElement('div');
            accessRow.className = 'config-button-group config-mount-access-row';
            ['modules', 'data', 'logs'].forEach(mount => {
              const mountKey = 'web.fs_write_access.' + mount;
              if (typeof current[mountKey] === 'boolean') renderWebAppField(accessRow, mountKey, current[mountKey]);
            });
            if (Object.keys(current).some(key => key.startsWith('web.fs_write_access.'))) {
              options.appendChild(textElement('h4', 'Write access', 'config-table-title config-heading-top'));
              options.appendChild(accessRow);
              options.appendChild(textElement('small', 'Hint: Mount write access resets to read-only after reboot.', 'config-hint'));
              const command = textElement('code', '', 'config-hint');
              const updateCommand = () => {
                const values = configData;
                const args = ['modules', 'data', 'logs']
                  .filter(mount => typeof values['web.fs_write_access.' + mount] === 'boolean')
                  .map(mount => `${mount}=${values['web.fs_write_access.' + mount] ? 'True' : 'False'}`);
                command.textContent = 'web mounts_w_access ' + args.join(' ') + ' pwd="<password>"';
              };
              updateCommand();
              options.appendChild(command);
            }
          }
          fields.appendChild(options);
        }
      });
    message.textContent = statusMessage;
    group.setAttribute('aria-busy', String(webAppUpdating));
  }

  group.refreshWebApps = render;

  group.setWebAppsPending = () => {
    fields.querySelectorAll('button').forEach(button => { button.disabled = true; });
    message.textContent = 'Updating...';
    group.setAttribute('aria-busy', 'true');
  };

  // An in-flight update will confirm status and render the current group.
  if (webAppUpdating) {
    group.setWebAppsPending();
    return;
  }
  group.setAttribute('aria-busy', 'true');
  getWebAppsStatus()
    .then(status => {
      // A response from a previous menu visit must not overwrite newer state.
      if (!group.isConnected) return;
      storeWebAppsStatus(status);
      render();
    })
    .catch(error => {
      if (!group.isConnected) return;
      message.textContent = error.message;
      group.setAttribute('aria-busy', 'false');
    });
}
