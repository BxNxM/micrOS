
function getMatchingElements(targetList, whitelist) {
    let matchingElementsSet = new Set();
    whitelist.forEach(whitelistedItem => {
        targetList.forEach(targetItem => {
            if (targetItem.startsWith(whitelistedItem)) {
                matchingElementsSet.add(whitelistedItem);
            }
        });
    });
    // Convert the Set back to an array
    let matchingElements = Array.from(matchingElementsSet);
    return matchingElements;
}

function containerAppendChild(elements, container) {
    // Append list of elements into the container aka draw elements :D
    if (!elements || !container) {
        console.error("Inputs array or container element is missing.");
        return;}
    elements.forEach(function(element) {
        container.appendChild(element);});
}

function generateElement(type, data) {
    // type: slider, button, box, h1, h2, p, li, etc.
    // data: rest command
    var container = document.getElementById('dynamicContent');
    var element;
    paragraph = document.createElement('p');
    if (type.toLowerCase() === 'slider') {
        paragraph.textContent = data.split('/').slice(1).join('-').replace(/=/g, '');
        // Create a slider
        element = document.createElement('input');
        element.type = 'range';
        element.min = 0;
        element.max = 100;
        element.step = 5;
        element.value = 50;

        // Create a span to display the slider value
        var valueDisplay = document.createElement('span');
        valueDisplay.textContent = element.value;
        element.addEventListener('input', function () {
            valueDisplay.textContent = this.value;
        });
        // Add an event listener for API CALL
        element.addEventListener('change', function () {
            console.log(`Slider value: ${data}/${this.value}`);
            if (data.endsWith("=")) {
                restAPI(`${data}${this.value}`);
            } else {
                restAPI(`${data}/${this.value}`);
            }
        });
        containerAppendChild([paragraph, element, valueDisplay], container);
    } else if (type.toLowerCase() === 'button') {
        // Create a button
        element = document.createElement('button');
        element.textContent = 'toggle';
        // Add an event listener for API CALL
        element.addEventListener('click', function () {
            console.log(`Button clicked: ${data}`);
            restAPI(data);
        });
        containerAppendChild([paragraph, element], container);
    } else if (type.toLowerCase() === 'box') {
        paragraph.textContent = 'measure';
        // Create a small box (div)
        element = document.createElement('div');
        element.style.width = '30%';
        element.style.height = '60px';
        element.style.paddingTop = '10px';
        element.style.paddingLeft = '10px';
        element.style.border = '2px solid #e7e7e7';
        element.style.borderRadius = '4px';
        console.log(`Box update: ${data}`);
        restAPI(data).then(resp => {
            console.log(resp.result);
            element.textContent = JSON.stringify(resp.result, null, 4);});
        containerAppendChild([paragraph, element], container);
    } else {
        // Create other elements
        element = document.createElement(type);
        element.textContent = data;
        containerAppendChild([paragraph, element], container);
    }
}

function genPage(module, functions) {
    generateElement(type='h2', data=`🧬 ${module}`);
    for (const func of functions) {
        let html_type='p';
        if (func === 'brightness') {
            html_type='slider';
        }
        if (func === 'toggle') {
            html_type='button';
        }
        if (func === 'measure') {
            html_type = 'box'
        }
        generateElement(type=html_type, data=`${module}/${func}`);
    }
}


function DynamicWidgetLoad() {
    // CONFIGURE known FE functions
    const conf_func_fe_list = ['brightness', 'toggle', 'measure'];

    // INIT DASHBOARD (load active modules -> build page)
    restAPI('modules').then(data => {
        console.log(data);
        let app_list = data['result'];
        // Handle the app_list data here
        for (const module of app_list) {
            //console.log(module);
            restAPI(`${module}/help`, debug=false).then(data => {
                let module_help = data.result;
                let matchingElements = getMatchingElements(module_help, conf_func_fe_list);
                //console.log(matchingElements)
                if (matchingElements.length > 0) {
                    genPage(module, matchingElements);
                }
            });
        }
    }).catch(error => {
        console.error(error);
    });
}


function CustomWidgetLoad(endpoint) {
    // INIT DASHBOARD (load custom widget commands -> build page)
    // endpoint: 'dashboard_be/widget_list' returns special dict
    restAPI(endpoint).then(commands => {
        console.log(commands.result)
        const widget_dict=commands.result;
        for (const module in widget_dict) {
            if (Object.hasOwnProperty.call(widget_dict, module)) {
                const innerObject = widget_dict[module];
                generateElement(type='h2', data=`🧬 ${module}`);
                // Iterate through the inner object
                for (const func in innerObject) {
                    if (Object.hasOwnProperty.call(innerObject, func)) {
                        const api_type = innerObject[func];
                        const api_cmd = `${module}/${func}`;
                        console.log(`Gen. Type: ${api_type} Cmd: ${api_cmd}`);
                        generateElement(type=api_type, data=api_cmd);
        };};};}
    }).catch(error => {
        console.error(error);
    });
}



// genPage
