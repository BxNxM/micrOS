// CORE MICROS BACKEND INTERFACE

let BASE_URL = '';
let REST_CONSOLE_CACHE;

function initializeBaseURL() {
    if (!BASE_URL && typeof window !== 'undefined') {
        BASE_URL = window.location.origin;
    }
}

function restAPICore(cmd, timeout=5000) {
    initializeBaseURL();
    console.log('BASE_URL:', BASE_URL);
    const query = `${BASE_URL}/rest/${cmd.trim().replace(/\s+/g, '/')}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    const startTime = performance.now();

    return fetch(query, { signal: controller.signal })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {throw new Error(`restAPICore code NOK: ${response.status}`);}
            return response.json().then(data => ({response: data,
                delta: (performance.now() - startTime).toFixed(0), query
            }));
        }).catch(error => {
            clearTimeout(timeoutId);
            console.error('Error in restAPICore:', error);
            throw error;
        });
}

function restAPI(cmd='', consoleOut=true, timeout=5000) {
    if (cmd === '') {
        const input = document.getElementById('restCmdInput');
        cmd = input ? input.value : '';
    }
    return restAPICore(cmd, timeout).then(({ response, delta, query }) => {
            if (consoleOut) {restConsole(query, response, delta);}
            return response;
        }).catch(error => {
            if (error.name === 'AbortError') {console.error(`Timeout (${timeout}ms) - restAPICore: ${cmd}`);
            } else {console.error('Error in restAPI:', error);}
            return { response: null, delta: 0, query: 'restAPI error' };
        });
}

function byId(id, root=document) {
    if (typeof id !== 'string') {return id;}
    root = root || document;
    if (root.getElementById) {return root.getElementById(id);}
    return root.querySelector ? root.querySelector(`#${id}`) : document.getElementById(id);
}

function makeEl(tag, props={}, children=[]) {
    const el = Object.assign(document.createElement(tag), props);
    el.append(...children);
    return el;
}

function apiConsoleStyle() {
    if (byId('apiConsoleStyle')) {return;}
    const c = '.api-console';
    document.head.appendChild(makeEl('style', {id: 'apiConsoleStyle', textContent:
        c + ',' + c + ' *{box-sizing:border-box}' +
        c + '{margin-top:18px;width:100%;overflow:hidden;border:1px solid rgba(255,255,255,.24);border-radius:8px;background:rgba(255,255,255,.14)}' +
        c + '[open]{border-color:rgba(255,255,255,.18);background:rgba(255,255,255,.06);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px)}' +
        c + ' summary{display:block;min-height:36px;padding:6px 12px;color:white;cursor:pointer}' +
        c + '[open] summary{background:rgba(255,255,255,.14)}' + c + ' summary:hover{background:rgba(255,255,255,.22)}' +
        c + '>div{padding:12px 10px 10px}' + c + ' h3{margin:0 0 8px}'
    }));
}

function restConsole(apiUrl, data, delta, root=document) {
    REST_CONSOLE_CACHE = [apiUrl, data, delta];
    const urlEl = root.url || byId('restConsoleUrl', root);
    const responseEl = root.response || byId('restConsoleResponse', root);
    const timeEl = root.time || byId('restConsoleTime', root);
    if (!urlEl || !responseEl || !timeEl) {return;}

    urlEl.textContent = '';
    urlEl.append(
        makeEl('strong', {textContent: 'Generated URL:'}),
        makeEl('br'),
        makeEl('a', {href: apiUrl, target: '_blank', textContent: apiUrl})
    );
    responseEl.textContent = JSON.stringify(data, null, 4);
    timeEl.textContent = `⏱ Response time: ${delta} ms`;
}

function restInfo(showPages=true) {
    // UPDATES: 'restInfo' and restConsole(...)
    restAPICore('').then(({ response, delta, query }) => {
        // Update API Console
        restConsole(query, response, delta)
        // Update 'restInfo' tag
        const result = response['result'];
        const auth = result.auth ? "🔑" : "";
        let infoHeader = `micrOS: ${result.micrOS} ❖ node: ${result.node}${auth}`;
        if (showPages && typeof renderEndpointGroups === 'function') {
            const endpoints = result['usr_endpoints'] ? Array.from(result['usr_endpoints']) : [];
            renderEndpointGroups(endpoints);
        }
        document.getElementById('restInfoHeader').textContent = infoHeader;
    }).catch(error => {
        console.error('Error in restAPI:', error);
    });
}
