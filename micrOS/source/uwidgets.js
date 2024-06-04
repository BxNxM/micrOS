// WIDGETS ELEMENTS

const widget_indent = '40px';
const windowWidth = window.innerWidth;

function sliderWidget(container, command, options = {}) {
    const { title_len = 1, range = [0, 100, 5] } = options;
    const [min, max, step] = range;
    const paragraph = document.createElement('p');
    const element = document.createElement('input');
    const valueDisplay = document.createElement('span');

    paragraph.style.textIndent = widget_indent;
    paragraph.textContent = command.split('/').slice(1, title_len + 1).join('-').replace(/=|:range:/g, '');
    element.type = 'range';
    element.min = min;
    element.max = max;
    element.step = step;
    element.value = (max - min) / 2;
    element.style.marginLeft = widget_indent;
    element.style.width = `${Math.min(windowWidth * 0.6, 300)}px`;
    valueDisplay.textContent = element.value;

    element.addEventListener('input', () => valueDisplay.textContent = element.value);
    element.addEventListener('change', () => {
        const call_cmd = command.includes(':range:') ? command.replace(':range:', element.value) :
                         command.endsWith('=') ? `${command}${element.value}` :
                         `${command}/${element.value}`;
        console.log(`[API] Slider exec: ${call_cmd}`);
        restAPI(call_cmd);
    });

    containerAppendChild([paragraph, element, valueDisplay], container);
}

function buttonWidget(container, command, options = {}) {
    const { title_len = 1 } = options;
    const paragraph = document.createElement('p');
    const element = document.createElement('button');

    paragraph.style.textIndent = widget_indent;
    element.style.marginLeft = widget_indent;
    element.style.height = '30px';
    element.textContent = command.split('/').slice(1, title_len + 1).join('-');;

    element.addEventListener('click', () => {
        const call_cmd = options.hasOwnProperty('range') ? command.replace(':range:', 'None') : command;
        console.log(`[API] Button clicked: ${call_cmd}`);
        restAPI(call_cmd);
    });

    containerAppendChild([paragraph, element], container);
}

function textBoxWidget(container, command, options = {}) {
    const { title_len = 1, refresh = 5000 } = options;
    const paragraph = document.createElement('p');
    const uniqueId = `textbox-${command}-${Date.now()}`;
    const element = document.createElement('div');

    paragraph.style.textIndent = widget_indent;
    paragraph.textContent = command.split('/').slice(1, title_len + 1).join('-').replace(/=|:range:/g, '');

    element.id = uniqueId;
    Object.assign(element.style, {
        marginLeft: widget_indent,
        width: `${Math.min(windowWidth * 0.6, 300)}px`,
        padding: '10px',
        boxSizing: 'border-box',
        border: '2px solid #e7e7e7',
        borderRadius: '4px'
    });

    const updateTextbox = () => {
        const call_cmd = command.replace(':range:', 'None');
        restAPI(call_cmd).then(resp => {
            console.log(`[API] textBox[${uniqueId}] call: ${call_cmd}`);
            const content = JSON.stringify(resp.result, null, 4).replace(/,\s*"/g, ',<br>"');
            document.getElementById(uniqueId).innerHTML = content;
        }).catch(error => {
            console.error('[API] Textbox error:', error);
            document.getElementById(uniqueId).textContent = 'Error loading data';
        });
    };

    updateTextbox();
    if (refresh > 0) {
        const intervalId = setInterval(updateTextbox, refresh);
        container.addEventListener('DOMNodeRemovedFromDocument', () => clearInterval(intervalId));
    }

    containerAppendChild([paragraph, element], container);
}

function colorPaletteWidget(container, command, options = {}) {
    const hexToRgb = (hex, max = 255) => {
        hex = hex.replace(/^#/, '');
        let bigint = parseInt(hex, 16);
        let r = (bigint >> 16) & 255;
        let g = (bigint >> 8) & 255;
        let b = bigint & 255;
        if (max > 255) {
            const ratio = max / 255;
            r = Math.round(r * ratio);
            g = Math.round(g * ratio);
            b = Math.round(b * ratio);
        }
        return { r, g, b };
    };
    const getRandomColorFromList = () => {
        const colors = ['#542040', '#2b2155', '#4c1e44', '#56213f', '#853366', '#493984', '#6f3487'];
        return colors[Math.floor(Math.random() * colors.length)];
    };

    const { title_len = 1, range = [0, 255] } = options;
    const max_val = range[1];
    const paragraph = document.createElement('p');
    const colorPicker = document.createElement('input');
    const selectedColor = document.createElement('span');

    paragraph.style.textIndent = widget_indent;
    paragraph.textContent = command.split('/').slice(1, title_len + 1).join('-');
    colorPicker.type = 'color';
    colorPicker.value = getRandomColorFromList();
    colorPicker.classList.add('custom-color-picker');
    Object.assign(colorPicker.style, {
        width: '60px',
        height: '40px',
        marginLeft: '40px'
    });

    colorPicker.addEventListener('change', () => {
        const { r, g, b } = hexToRgb(colorPicker.value, max_val);
        const call_cmd = command.replace('r=:range:', `r=${r}`)
                                .replace('g=:range:', `g=${g}`)
                                .replace('b=:range:', `b=${b}`);
        console.log(`[API] colorPalette exec: ${call_cmd}`);
        restAPI(call_cmd);
    });

    containerAppendChild([paragraph, colorPicker, selectedColor], container);
}

// sliderWidget