// CORE MICROS BACKEND INTERFACE

const BASE_URL = `http://${window.location.hostname}${window.location.port ? `:${window.location.port}` : ""}`;

function restAPICore(cmd, timeout=5000) {
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
    if (cmd === '') {cmd = document.getElementById('restCmdInput').value;}
    return restAPICore(cmd, timeout).then(({ response, delta, query }) => {
            if (consoleOut) {restConsole(query, response, delta);}
            return response;
        }).catch(error => {
            if (error.name === 'AbortError') {console.error(`Timeout (${timeout}ms) - restAPICore: ${cmd}`);
            } else {console.error('Error in restAPI:', error);}
            return { response: null, delta: 0, query: 'restAPI error' };
        });
}

function restConsole(apiUrl, data, delta) {
    // UPDATES: restConsoleUrl, restConsoleResponse, restConsoleTime
    document.getElementById('restConsoleUrl').innerHTML = `<strong>Generated URL:</strong><br> <a href="${apiUrl}" target="_blank" style="color: white;">${apiUrl}</a>`;
    document.getElementById('restConsoleResponse').innerHTML = JSON.stringify(data, null, 4).replace(/\\n/g, "<br/>" + "&nbsp;".repeat(15));
    document.getElementById('restConsoleTime').innerHTML = `⏱ Response time: ${delta} ms`;
}

function renderEndpointGroups(endpoints) {
    const container = document.getElementById('endpointGroups');
    if (!container) {return;}
    container.innerHTML = '';
    if (!Array.isArray(endpoints) || endpoints.length === 0) {return;}
    const groups = endpoints.reduce((acc, endpoint) => {
        const trimmed = endpoint.replace(/^\/+/, '');
        if (!trimmed) {return acc;}
        const root = trimmed.split('/')[0];
        acc[root] = acc[root] || [];
        acc[root].push(trimmed);
        return acc;
    }, {});
    Object.keys(groups).sort().forEach(group => {
        const entries = groups[group].sort();
        const isSingle = entries.length === 1 && entries[0] === group;
        if (isSingle) {
            const button = document.createElement('button');
            button.textContent = group;
            button.onclick = () => window.open(`/${group}`, '_blank');
            container.appendChild(button);
            return;
        }
        const groupEl = document.createElement('div');
        groupEl.className = 'endpoint-group';
        const title = document.createElement('span');
        title.className = 'endpoint-group-title';
        title.textContent = group;
        groupEl.appendChild(title);
        entries.forEach(entry => {
            const label = entry === group ? group : entry.replace(`${group}/`, '');
            const button = document.createElement('button');
            button.textContent = label;
            button.onclick = () => window.open(`/${entry}`, '_blank');
            groupEl.appendChild(button);
        });
        container.appendChild(groupEl);
    });
}

function restInfo(showPages=true) {
    // UPDATES: 'restInfo' and restConsole(...)
    restAPICore(cmd = '').then(({ response, delta, query }) => {
        // Update API Console
        restConsole(query, response, delta)
        // Update 'restInfo' tag
        const result = response['result'];
        const auth = result.auth ? "🔑" : "";
        let infoHeader = `micrOS: ${result.micrOS} ❖ node: ${result.node}${auth}`;
        if (showPages) {
            const endpoints = result['usr_endpoints'] ? Array.from(result['usr_endpoints']) : [];
            renderEndpointGroups(endpoints);
        }
        document.getElementById('restInfoHeader').innerHTML = infoHeader;
    }).catch(error => {
        console.error('Error in restAPI:', error);
    });
}

// Designed by BxNxM |/|/|/|/
