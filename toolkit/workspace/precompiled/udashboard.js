// API HELPER FUNCTION - get module exposed widgets
function moduleHelp(module) {
    const endpoint = `${module}/help/True`;
    console.log(`[API] Endpoint: ${endpoint}`);
    return restAPI(endpoint).then(({ result }) => {
        const parsedWidgets = result.map(item => JSON.parse(item.replace(/\\"/g, '"')));
        console.log(`Parsed ${module} help:`, parsedWidgets);
        return parsedWidgets;
    }).catch(error => {
        console.error(error);
        return [];
    });
}

// PAGE GENERATION

function containerAppendChild(elements, container) {
    // Append list of elements into the container aka draw elements :D
    if (!elements || !container) {
        console.error("Inputs array or container element is missing.");
        return;}
    elements.forEach(function(element) {
        container.appendChild(element);});
}

function generateElement(type, data, options={}) {
    // type: slider, button, box, h1, h2, p, li, etc.
    // data: rest command
    const container = document.getElementById('dynamicContent');
    if (type === 'slider') {
        // Create slider widget
        sliderWidget(container, data, options)
    } else if (type === 'button') {
        // Create button widget
        buttonWidget(container, data, options)
    } else if (type === 'textbox') {
        // Create textbox widget
        textBoxWidget(container, data, options)
    } else if (type === 'color') {
        // Create color palette widget
        colorPaletteWidget(container, data, options)
    } else {
        // Create other elements
        const paragraph = document.createElement('p');
        const element = document.createElement(type);
        element.textContent = data;
        containerAppendChild([paragraph, element], container);
    }
}

function autoTitleLen(widgets, lm_call) {
    try {
        const func = lm_call.split('/')[0].split(' ')[0];
        const count = widgets.reduce((accumulator, { lm_call }) => accumulator + (lm_call.split(' ')[0] === func ? 1 : 0), 0);
        return count > 1 ? 2 : 1;
    } catch (error) {
        console.error(error);
        return 1;
    }
}

function craftModuleWidgets(module, widgets) {
    if (!widgets.length) {
        console.log(`${module} no exposed widgets`);
        return;
    }
    console.log(`Craft widgets bind to ${module}`);
    generateElement('h2', `🧬 ${module}`);

    const widgetTypeOptions = {
        button: item => ({title_len: autoTitleLen(widgets, item.lm_call), options: item.options }),
        slider: item => ({title_len: autoTitleLen(widgets, item.lm_call), range: item.range }),
        color: item => ({title_len: autoTitleLen(widgets, item.lm_call), range: item.range }),
        textbox: item => ({title_len: autoTitleLen(widgets, item.lm_call), refresh: item.refresh })
    };

    widgets.forEach(item => {
        let { type, lm_call } = item;
        lm_call = lm_call.replace(/\s/g, '/');
        const type_options = widgetTypeOptions[type] ? widgetTypeOptions[type](item) : null;
        if (!type_options) {
            console.log(`Unsupported micrOS widget html_type: ${type}`);
            return;
        }

        try {
            generateElement(type, `${module}/${lm_call}`, type_options);
        } catch (error) {
            console.error(error);
        }
    });
}

function DynamicWidgetLoad() {
    restAPI('modules').then(data => {
        const app_list = data.result;
        app_list.forEach(module => {
            moduleHelp(module).then(widgets => {
                craftModuleWidgets(module, widgets);
            }).catch(error => {
                console.error(`Error processing module ${module}:`, error);
            });
        });
    }).catch(error => {
        console.error('Error loading modules:', error);
    });
}

// craftModuleWidgets
