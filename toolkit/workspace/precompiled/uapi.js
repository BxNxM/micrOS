// Get the current hostname and create the REST API URL
const currentHostname = window.location.hostname;
const port = window.location.port ? `:${window.location.port}` : "";

function restAPI(cmd = '') {
    if (cmd == '') {
        cmd = document.getElementById('inputApiCmd').value;
    }
    cmd = cmd.trim().replace(/\s+/g, '/');
    let apiUrl = `http://${currentHostname}${port}/rest/${cmd}`;
    const startTime = performance.now();
    let endTime;

    // Call rest api with command parameter
    fetch(apiUrl).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.status);
        }
        endTime = performance.now();
        return response.json();
    }).then(data => {
        // Display the generated URL on the webpage
        document.getElementById('usrApiCallUrl').innerHTML = `<strong>Generated URL:</strong><br> <a href="${apiUrl}" target="_blank" style="color: white;">${apiUrl}</a>`;
        // Handle the data received from the server
        document.getElementById('usrApiCallResponse').innerHTML = JSON.stringify(data, null, 4).replace(/\\n/g, "<br/>" + "&nbsp;".repeat(15));
        const delta = (endTime - startTime).toFixed(0);
        document.getElementById('restResponseTime').innerHTML = `⏱ Response time: ${delta} ms`;
        // Update sys info /rest default
        if (cmd == '') {
            document.getElementById('SysApiCall').innerHTML = Object.entries(data['result'])
                .filter(([key]) => key !== 'usr_endpoints') // Exclude usr_endpoints
                .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
                .join('  ❖  ').replace(/"/g, '') +
                (data['result']['usr_endpoints'] ? "<br><br>📎 " + Object.entries(data['result']['usr_endpoints'])
                    .map(([key, value]) => `<a href="${value}" target="_blank" style="color: white;">${value}</a>`)
                    .join(' | ') : '');
        }
    }).catch(error => {
        console.error('Fetch error:', error);
    });
}

// Init basic info from board
// restAPI();
