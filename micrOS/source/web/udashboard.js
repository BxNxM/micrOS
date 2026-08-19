// API HELPER FUNCTION - get module exposed widgets
const OPTIONAL_WIDGET_TYPES = {
    joystick: { src: 'uwidgets_pro.js', ready: () => typeof joystickWidget === 'function' },
    embed: { src: 'uwidgets_pro.js', ready: () => typeof embedWidget === 'function' },
    white: { src: 'uwidgets_pro.js', ready: () => typeof whiteWidget === 'function' }
};
const WIDGET_RENDERERS = {
    button: 'buttonWidget',
    color: 'colorPaletteWidget',
    embed: 'embedWidget',
    graph: 'graphWidget',
    joystick: 'joystickWidget',
    slider: 'sliderWidget',
    textbox: 'textBoxWidget',
    white: 'whiteWidget'
};
const optionalWidgetLoaders = {};
const normalizeCallback = callback => String(callback || '').trim().replace(/\s+/g, '/').replace(/^\/+/, '').replace(/\/+$/, '');
const FEATURE_DISCOVERY_TIMEOUT = 20000;
const moduleStatusSyncs = {};

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
    return restAPI(endpoint, false, FEATURE_DISCOVERY_TIMEOUT).then(({ result }) => {
        const parsedWidgets = result.map(item => JSON.parse(item.replace(/\\"/g, '"')));
        console.log(`Parsed ${module} help:`, parsedWidgets);
        return parsedWidgets;
    }).catch(error => {
        console.error(error);
        return [];
    });
}

// PAGE GENERATION

function generateElement(type, module, callback="", options={}) {
    const data = `${module}/${callback}`;
    const container = document.getElementById(`container-${module}`);
    if (!container) {
        console.error("No container");
        return;
    }

    const rendererName = WIDGET_RENDERERS[type];
    if (rendererName) {
        const renderer = window[rendererName];
        if (typeof renderer !== 'function') {
            console.error(`Widget not loaded: ${type}`);
            return;
        }
        renderer(container, data, options);
        return;
    }

    const element = document.createElement(type);
    element.textContent = `🧬 ${module}`;
    container.appendChild(element);
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

function createModuleStatusSync(module, widgets) {
    const statusMeta = widgets.find(({ type }) => type === 'status');
    if (!statusMeta) {
        return null;
    }
    const handlers = [];
    const callback = normalizeCallback(statusMeta.callback || 'status');
    const endpoint = `${module}/${callback}`;
    let inFlight = null, pending = false;
    const fetchStatus = () => {
        console.log(`[API] Widget status sync: ${endpoint}`);
        inFlight = restAPI(endpoint, false).then(({ result }) => {
            if (result && typeof result === 'object') {
                handlers.forEach(handler => {
                    try {
                        handler(result);
                    } catch (error) {
                        console.error(`[API] Widget status apply failed: ${endpoint}`, error);
                    }
                });
                return result;
            }
            return null;
        }).catch(error => {
            console.error(`[API] Widget status sync failed: ${endpoint}`, error);
            return null;
        }).then(result => {
            inFlight = null;
            if (pending) {
                pending = false;
                return fetchStatus();
            }
            return result;
        });
        return inFlight;
    };
    const sync = {
        register: handler => {
            if (typeof handler === 'function') { handlers.push(handler); }
        },
        refresh: () => {
            if (inFlight) {
                pending = true;
                return inFlight;
            }
            return fetchStatus();
        }
    };
    moduleStatusSyncs[module] = sync;
    return sync;
}

function refreshModuleStatus(module) {
    const sync = moduleStatusSyncs[module];
    return sync ? sync.refresh() : Promise.resolve(null);
}

function refreshDashboardStatuses() {
    return Promise.all(Object.keys(moduleStatusSyncs).map(refreshModuleStatus));
}

async function craftModuleWidgets(module, widgets, order = 0) {
    if (!widgets.length) {
        console.log(`${module} no exposed widgets`);
        return;
    }
    const controls = widgets.filter(({ type }) => type !== 'status');
    const statusSync = createModuleStatusSync(module, widgets);
    try {
        await ensureOptionalWidgetsLoaded(controls);
    } catch (error) {
        console.error(`Error loading optional widgets for ${module}:`, error);
    }

    console.log(`Craft widget to ${module}`);
    // Create HTML elements for widgets
    const widgets_section = document.getElementById('widgets-section');
    const widget_container = document.createElement('ol');
    widget_container.id = `container-${module}`;
    widget_container.className = "widget";
    widget_container.style.order = order;
    widgets_section.appendChild(widget_container);
    // Create widget title
    generateElement('h2', module);

    const titleOptions = item => ({ title_len: autoTitleLen(widgets, item.callback) });
    const baseOptions = item => ({ ...titleOptions(item), sync: statusSync });
    const rangedOptions = item => ({ ...baseOptions(item), range: item.range });
    const widgetTypeOptions = {
        button: item => ({ ...baseOptions(item), options: item.options, result: item.result }),
        slider: rangedOptions,
        color: rangedOptions,
        white: rangedOptions,
        joystick: rangedOptions,
        textbox: item => ({ ...titleOptions(item), refresh: item.refresh }),
        graph: item => ({ ...titleOptions(item), refresh: item.refresh, limit: item.limit }),
        embed: item => ({
            title_len: item.callback ? Math.max(autoTitleLen(widgets, item.callback), 2) : 1,
            callback: normalizeCallback(item.callback || ''),
            image: item.image,
            title: item.title
        })
    };

    // Create control elements for widget
    controls.forEach(item => {
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
    if (statusSync) { statusSync.refresh(); }
}

function DynamicWidgetLoad() {
    restAPI('modules', true, FEATURE_DISCOVERY_TIMEOUT).then(data => {
        const widgets_section = document.getElementById('widgets-section');
        if (widgets_section) {
            widgets_section.textContent = '';
        }
        Object.keys(moduleStatusSyncs).forEach(module => delete moduleStatusSyncs[module]);
        const app_list = (data.result || []).slice().sort();
        app_list.forEach((module, order) => {
            moduleHelp(module).then(widgets => craftModuleWidgets(module, widgets, order)).catch(error => {
                console.error(`Error processing module ${module}:`, error);
            });
        });
    }).catch(error => {
        console.error('Error loading modules:', error);
    });
}
