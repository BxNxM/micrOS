// API HELPER FUNCTION - get module exposed widgets
const OPTIONAL_WIDGET_TYPES = {
    joystick: { src: 'uwidgets_pro.js', ready: () => typeof joystickWidget === 'function' },
    embed: { src: 'uwidgets_pro.js', ready: () => typeof embedWidget === 'function' },
    graph: { src: 'uwidgets_pro.js', ready: () => typeof graphWidget === 'function' }
};
const optionalWidgetLoaders = {};
const normalizeCallback = callback => String(callback || '').trim().replace(/\s+/g, '/').replace(/^\/+/, '').replace(/\/+$/, '');

function loadOptionalWidgetScript(src) {
    if (optionalWidgetLoaders[src]) {
        return optionalWidgetLoaders[src];
    }
    optionalWidgetLoaders[src] = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = () => reject(new Error(`Failed to load ${src}`));
        document.head.appendChild(script);
    });
    return optionalWidgetLoaders[src];
}

function ensureOptionalWidgetsLoaded(widgets) {
    const scripts = [...new Set(widgets
        .map(({ type }) => OPTIONAL_WIDGET_TYPES[type])
        .filter(Boolean)
        .filter(({ ready }) => !ready())
        .map(({ src }) => src))];
    return scripts.length ? Promise.all(scripts.map(loadOptionalWidgetScript)) : Promise.resolve();
}

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
        return;
    }
    elements.forEach(function(element) {
        container.appendChild(element);});
}

function generateElement(type, module, callback="", options={}) {
    // type: slider, button, box, h1, h2, p, li, etc.
    // data: rest command
    console.log(`type: ${type}`);
    const data = `${module}/${callback}`;
    console.log(`data: ${data}`);
    const container = document.getElementById(`container-${module}`);
    if(!container) {
        console.error("No container");
    }
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
    } else if (type === 'joystick') {
        // Create joystick widget
        if (typeof joystickWidget !== 'function') {
            console.error("Optional widget not loaded: joystick");
            return;
        }
        joystickWidget(container, data, options)
    } else if (type === 'embed') {
        // Create embedded image stream or webpage widget
        if (typeof embedWidget !== 'function') {
            console.error("Optional widget not loaded: embed");
            return;
        }
        embedWidget(container, data, options)
    } else if (type === 'graph') {
        // Create graph widget
        if (typeof graphWidget !== 'function') {
            console.error("Optional widget not loaded: graph");
            return;
        }
        graphWidget(container, data, options)
    } else {
        // Create other elements
        const element = document.createElement(type);
        element.textContent = `🧬 ${module}`;
        containerAppendChild([element], container);
    }
}

function autoTitleLen(widgets, callback) {
    try {
        const func = normalizeCallback(callback).split('/')[0];
        const count = widgets.reduce((accumulator, item) => accumulator + (normalizeCallback(item.callback).split('/')[0] === func ? 1 : 0), 0);
        return count > 1 ? 2 : 1;
    } catch (error) {
        console.error(error);
        return 1;
    }
}

async function craftModuleWidgets(module, widgets) {
    if (!widgets.length) {
        console.log(`${module} no exposed widgets`);
        return;
    }
    try {
        await ensureOptionalWidgetsLoaded(widgets);
    } catch (error) {
        console.error(`Error loading optional widgets for ${module}:`, error);
    }

    console.log(`Craft widget to ${module}`);
    // Create HTML elements for widgets
    const widgets_section = document.getElementById('widgets-section');
    const widget_container = document.createElement('ol');
    widget_container.id = `container-${module}`;
    widget_container.className = "widget";
    widgets_section.appendChild(widget_container);
    // Create widget title
    generateElement('h2', module);

    const widgetTypeOptions = {
        button: item => ({title_len: autoTitleLen(widgets, item.callback), options: item.options }),
        slider: item => ({title_len: autoTitleLen(widgets, item.callback), range: item.range }),
        color: item => ({title_len: autoTitleLen(widgets, item.callback), range: item.range }),
        textbox: item => ({title_len: autoTitleLen(widgets, item.callback), refresh: item.refresh }),
        graph: item => ({title_len: autoTitleLen(widgets, item.callback), refresh: item.refresh, limit: item.limit }),
        joystick: item => ({title_len: autoTitleLen(widgets, item.callback), range: item.range }),
        embed: item => ({
            title_len: item.callback ? Math.max(autoTitleLen(widgets, item.callback), 2) : 1,
            callback: normalizeCallback(item.callback || ''),
            image: item.image,
            retry: item.retry,
            title: item.title
        })
    };

    // Create control elements for widget
    widgets.forEach(item => {
        let { type, callback = '' } = item;
        callback = normalizeCallback(callback);
        const type_options = widgetTypeOptions[type] ? widgetTypeOptions[type](item) : null;
        if (!type_options) {
            console.log(`Unsupported micrOS widget html_type: ${type}`);
            return;
        }

        try {
            console.log("adding widget controls");
            generateElement(type, module, callback, type_options);
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
                return craftModuleWidgets(module, widgets);
            }).catch(error => {
                console.error(`Error processing module ${module}:`, error);
            });
        });
    }).catch(error => {
        console.error('Error loading modules:', error);
    });
}

// craftModuleWidgets
