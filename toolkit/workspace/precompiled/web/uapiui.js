// OPTIONAL MICROS REST UI WIDGETS FOR UAPI.JS

function restWidget(container='restWidget', opts={}) {
    const root = byId(container);
    if (!root) {return null;}

    const styled = (el, css) => {el.style.cssText = css; return el;};
    const prefix = opts.prefix ? `${opts.prefix}-` : '';
    const inputId = opts.inputId || `${prefix}restCmdInput`;
    const historyKey = opts.historyKey || 'micros.rest.commands';
    let history = [];
    try {history = JSON.parse(sessionStorage.getItem(historyKey) || '[]').filter(x => typeof x === 'string');} catch (_) {}

    const label = makeEl('label', {htmlFor: inputId, textContent: opts.label || '⚙️ Enter micrOS command: '});
    const input = styled(makeEl('input', {type: 'text', id: inputId, value: opts.value || ''}), 'background:transparent;max-width:none;min-width:0;padding-right:34px;position:relative;width:100%;z-index:1;');
    const ghost = styled(makeEl('span'), 'box-sizing:border-box;color:rgba(0,0,0,.35);font:14px/1.4 Verdana,sans-serif;inset:2px;overflow:hidden;padding:6px 34px 6px 12px;pointer-events:none;position:absolute;white-space:pre;');
    const accept = styled(makeEl('button', {type: 'button', textContent: '↦', title: 'Accept suggestion'}), 'bottom:2px;display:none;min-height:0;padding:0 8px;position:absolute;right:2px;top:2px;z-index:3;');
    const send = makeEl('button', {type: 'submit', textContent: opts.button || 'Send'});
    const inputWrap = styled(makeEl('span', {}, [input, ghost, accept]), 'background:white;border-radius:6px;flex:1;max-width:350px;min-width:200px;position:relative;');
    const form = makeEl('form', {}, [inputWrap, send]);
    const url = makeEl('p', {id: opts.urlId || `${prefix}restConsoleUrl`});
    const responseBox = makeEl('pre', {id: opts.responseId || `${prefix}restConsoleResponse`});
    const time = makeEl('p', {id: opts.timeId || `${prefix}restConsoleTime`});
    const updateHint = () => {
        ghost.textContent = input.value && history.find(x => x.startsWith(input.value) && x !== input.value) || '';
        accept.style.display = ghost.textContent ? '' : 'none';
    };
    const acceptHint = () => {
        if (!ghost.textContent) {return;}
        input.value = ghost.textContent;
        input.setSelectionRange(input.value.length, input.value.length);
        updateHint();
        input.focus();
    };

    input.oninput = updateHint;
    input.onkeydown = e => {
        if (e.key === 'Tab' && ghost.textContent) {
            e.preventDefault();
            acceptHint();
        }
    };
    accept.onclick = acceptHint;
    form.onsubmit = () => {
        const cmd = input.value.trim();
        if (cmd) {
            history = [cmd, ...history.filter(x => x !== cmd)].slice(0, opts.historyLimit || 20);
            try {sessionStorage.setItem(historyKey, JSON.stringify(history));} catch (_) {}
        }
        updateHint();
        restAPICore(cmd, opts.timeout || 5000)
            .then(({ response, delta, query }) => restConsole(query, response, delta, {url, response: responseBox, time}))
            .catch(error => restConsole('restAPI error', {error: error.message}, 0, {url, response: responseBox, time}));
        return false;
    };

    root.textContent = '';
    root.append(makeEl('h3', {}, [label]), form, url, responseBox, time);
    updateHint();
    return {root, input, form, url, response: responseBox, time};
}

function renderEndpointGroups(endpoints) {
    const container = byId('endpointGroups');
    if (!container) {return;}
    container.textContent = '';
    if (!Array.isArray(endpoints) || !endpoints.length) {return;}

    const groups = {};
    const button = (label, entry) => makeEl('button', {textContent: label, onclick: () => window.open(`/${entry}`, '_blank')});
    endpoints.forEach(endpoint => {
        const entry = endpoint.replace(/^\/+/, '');
        const group = entry.split('/')[0];
        if (group) {(groups[group] = groups[group] || []).push(entry);}
    });

    Object.keys(groups).sort().forEach(group => {
        const entries = groups[group].sort();
        if (entries.length === 1 && entries[0] === group) {
            container.appendChild(button(group, group));
            return;
        }
        const groupEl = makeEl('div', {className: 'endpoint-group'}, [makeEl('span', {className: 'endpoint-group-title', textContent: group})]);
        entries.forEach(entry => groupEl.appendChild(button(entry === group ? group : entry.replace(`${group}/`, ''), entry)));
        container.appendChild(groupEl);
    });
}
