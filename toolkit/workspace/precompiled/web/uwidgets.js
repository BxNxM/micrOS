// WIDGETS ELEMENTS

const widget_indent = '40px';
const windowWidth = window.innerWidth;
const widgetColors = ['#00d1ff', '#ffca3a', '#7bd88f', '#ff6b6b', '#c77dff', '#f4a261'];

function createElement(tag, styles={}, props={}) {
    const element = document.createElement(tag);
    Object.assign(element, props);
    Object.assign(element.style, styles);
    return element;
}

function appendChildren(container, elements) {
    elements.forEach(element => container.appendChild(element));
    return container;
}

function createTitle(command, title_len) {
    return command.split('/').slice(1, title_len + 1).join('-').replace(/=|:range:|:options:/g, '');
}

function createWidgetTitle(command, title_len, text=null) {
    return createElement('p', { textIndent: widget_indent }, { textContent: text || createTitle(command, title_len) });
}

function widgetWidth(ratio, max) {
    return `${Math.min(windowWidth * ratio, max)}px`;
}

function paramPythonify(opt) {
    if (opt === "None" || opt === "True" || opt === "False") {return opt;}
    if (!isNaN(parseInt(opt, 10)) && String(parseInt(opt, 10)) === opt) {return opt;}
    if (!isNaN(parseFloat(opt)) && String(parseFloat(opt)) === opt) {return opt;}
    return `"${opt}"`;
}

function rangeInput(range, value=(range[1] - range[0]) / 2, styles={}) {
    const [min, max, step] = range;
    return createElement('input', styles, { type: 'range', min, max, step, value });
}

function bindRangeDisplay(input, display) {
    display.textContent = input.value;
    input.addEventListener('input', () => display.textContent = input.value);
}

function scheduleWidgetRefresh(container, refresh, update) {
    update();
    if (refresh > 0) {
        const intervalId = setInterval(update, refresh);
        container.addEventListener('DOMNodeRemovedFromDocument', () => clearInterval(intervalId));
    }
}

function numericValues(result, keys=null) {
    const values = {};
    for (const key in (result || {})) {
        const value = result[key];
        if (typeof value === 'number' && isFinite(value)) {
            values[key] = value;
            if (keys && keys.indexOf(key) < 0) {keys.push(key);}
        }
    }
    return values;
}

function sliderWidget(container, command, params={}) {
    const { title_len = 1, range = [0, 100, 5] } = params;
    const element = rangeInput(range, (range[1] - range[0]) / 2, {
        marginLeft: widget_indent,
        width: widgetWidth(0.6, 300)
    });
    const valueDisplay = createElement('span');

    bindRangeDisplay(element, valueDisplay);
    element.addEventListener('change', () => {
        const call_cmd = command.includes(':range:') ? command.replace(':range:', element.value) :
                         command.endsWith('=') ? `${command}${element.value}` :
                         `${command}/${element.value}`;
        console.log(`[API] Slider exec: ${call_cmd}`);
        restAPI(call_cmd);
    });

    appendChildren(container, [createWidgetTitle(command, title_len), element, valueDisplay]);
}

function buttonWidget(container, command, params={}) {
    const { title_len = 1, options = ['None'] } = params;
    const text = createTitle(command, title_len);
    const optionLabels = { 'True': 'ON', 'False': 'OFF', 'None': 'Default' };
    const paragraph = createElement('p', { textIndent: widget_indent });

    if (options.length > 1) {
        container.appendChild(createWidgetTitle(command, title_len, text));
    }
    options.forEach(opt => {
        const element = createElement('button', { marginRight: '10px', height: '30px' }, {
            textContent: options.length === 1 ? text : optionLabels[opt] || opt
        });
        element.addEventListener('click', () => {
            const call_cmd = command.replace(':options:', paramPythonify(opt));
            console.log(`[API] Button clicked: ${call_cmd}`);
            restAPI(call_cmd);
        });
        paragraph.appendChild(element);
    });
    appendChildren(container, [paragraph]);
}

function textBoxWidget(container, command, params={}) {
    const { title_len = 1, refresh = 5000 } = params;
    const uniqueId = `textbox-${command}-${Date.now()}`;
    const element = createElement('div', {
        marginLeft: widget_indent,
        width: widgetWidth(0.6, 300),
        padding: '10px',
        boxSizing: 'border-box',
        border: '2px solid #e7e7e7',
        borderRadius: '4px'
    }, { id: uniqueId });
    const updateTextbox = () => {
        const call_cmd = command.replace(':range:', 'None');
        restAPI(call_cmd, false).then(resp => {
            console.log(`[API] textBox[${uniqueId}] call: ${call_cmd}`);
            element.innerHTML = JSON.stringify(resp.result, null, 4).replace(/,\s*"/g, ',<br>"');
        }).catch(error => {
            console.error('[API] Textbox error:', error);
            element.textContent = 'Error loading data';
        });
    };

    appendChildren(container, [createWidgetTitle(command, title_len), element]);
    scheduleWidgetRefresh(container, refresh, updateTextbox);
}

function colorPaletteWidget(container, command, params = {}) {
    const { title_len = 1, range = [0, 255] } = params;
    const colors = ['#542040', '#2b2155', '#4c1e44', '#56213f', '#853366', '#493984', '#6f3487'];
    const colorPicker = createElement('input', { width: '60px', height: '40px', marginLeft: widget_indent }, {
        type: 'color',
        value: colors[Math.floor(Math.random() * colors.length)]
    });
    const hexToRgb = (hex, max = 255) => {
        const rgb = parseInt(hex.replace(/^#/, ''), 16);
        const ratio = max > 255 ? max / 255 : 1;
        return {
            r: Math.round(((rgb >> 16) & 255) * ratio),
            g: Math.round(((rgb >> 8) & 255) * ratio),
            b: Math.round((rgb & 255) * ratio)
        };
    };

    colorPicker.classList.add('custom-color-picker');
    colorPicker.addEventListener('change', () => {
        const { r, g, b } = hexToRgb(colorPicker.value, range[1]);
        const call_cmd = command.replace('r=:range:', `r=${r}`)
                                .replace('g=:range:', `g=${g}`)
                                .replace('b=:range:', `b=${b}`);
        console.log(`[API] colorPalette exec: ${call_cmd}`);
        restAPI(call_cmd);
    });

    appendChildren(container, [createWidgetTitle(command, title_len), colorPicker, createElement('span')]);
}

function graphWidget(container, command, params={}) {
    const { title_len = 1, refresh = 3000, limit = 30 } = params;
    const width = Math.round(Math.min(windowWidth * 0.6, 320));
    const height = 180;
    const pad = 28;
    const samples = [];
    const keys = [];
    const canvas = createElement('canvas', {
        marginLeft: widget_indent,
        width: `${width}px`,
        border: '2px solid #e7e7e7',
        borderRadius: '8px',
        backgroundColor: 'rgba(16, 20, 24, 0.72)'
    }, { width, height });
    const legend = createElement('div', { marginLeft: widget_indent, width: `${width}px`, fontSize: '11px' });
    const ctx = canvas.getContext('2d');
    const timeText = stamp => new Date(stamp).toLocaleTimeString();
    const bounds = () => {
        let min = Infinity;
        let max = -Infinity;
        samples.forEach(sample => keys.forEach(key => {
            if (key in sample.values) {
                min = Math.min(min, sample.values[key]);
                max = Math.max(max, sample.values[key]);
            }
        }));
        if (!isFinite(min)) {return null;}
        const highest = max;
        const span = min === max ? 1 : max - min;
        return { min: min - span * (min === max ? 1 : 0.12), max: max + span * 0.15, highest };
    };

    const draw = () => {
        const limits = bounds();
        if (!limits) {return;}
        const first = samples[0];
        const latest = samples[samples.length - 1];
        const last = latest.values;
        const scaleX = Math.max(latest.time - first.time, 1);
        const xOf = time => pad + ((time - first.time) / scaleX) * (width - pad - 12);
        const yOf = value => height - pad - ((value - limits.min) / (limits.max - limits.min)) * (height - pad - 14);

        ctx.clearRect(0, 0, width, height);
        Object.assign(ctx, { lineWidth: 1, strokeStyle: '#64707c', fillStyle: '#b7c0c8', font: '10px sans-serif' });
        ctx.beginPath();
        ctx.moveTo(pad, 10);
        ctx.lineTo(pad, height - pad);
        ctx.lineTo(width - 10, height - pad);
        ctx.stroke();
        ctx.fillText(timeText(first.time), pad, height - 4);
        ctx.textAlign = 'right';
        ctx.fillText(timeText(latest.time), width - 10, height - 4);
        ctx.textAlign = 'left';

        keys.forEach((key, i) => {
            const color = widgetColors[i % widgetColors.length];
            Object.assign(ctx, { lineWidth: 2, strokeStyle: color, fillStyle: color });
            ctx.beginPath();
            let started = false;
            samples.forEach(sample => {
                if (!(key in sample.values)) {return;}
                const x = xOf(sample.time);
                const y = yOf(sample.values[key]);
                started ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
                started = true;
                ctx.fillRect(x - 2, y - 2, 4, 4);
            });
            ctx.stroke();
        });

        Object.assign(ctx, { lineWidth: 1, textAlign: 'right', fillStyle: '#fff' });
        ctx.fillText(limits.highest, pad - 4, yOf(limits.highest) + 3);
        legend.textContent = '';
        keys.forEach((key, i) => {
            const value = key in last ? last[key] : '-';
            const color = widgetColors[i % widgetColors.length];
            if (value !== '-') {
                ctx.fillStyle = color;
                ctx.fillText(value, pad - 4, yOf(value) + 3);
            }
            legend.appendChild(createElement('span', { color }, { textContent: `${key}: ${value}  ` }));
        });
        ctx.textAlign = 'left';
    };

    const update = () => restAPI(command, false).then(({ result }) => {
        const values = numericValues(result, keys);
        if (!Object.keys(values).length) {return;}
        samples.push({ time: Date.now(), values });
        if (samples.length > limit) {samples.splice(0, samples.length - limit);}
        draw();
    });

    appendChildren(container, [createWidgetTitle(command, title_len), canvas, legend]);
    scheduleWidgetRefresh(container, refresh, update);
}
