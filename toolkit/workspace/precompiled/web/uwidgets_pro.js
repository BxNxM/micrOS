// PRO WIDGETS ELEMENTS

function joystickWidget(container, command, params={}) {
    const { title_len = 1, range = [0, 100, 5] } = params;
    const [min, max] = range;
    const joystickContainer = createElement('div', {
        position: 'relative',
        width: '200px',
        height: '200px',
        border: '1px solid #fff',
        marginLeft: widget_indent,
        backgroundColor: 'transparent'
    });
    const joystick = createElement('div', {
        position: 'absolute',
        width: '30px',
        height: '30px',
        background: '#fff',
        borderRadius: '50%',
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)',
        cursor: 'pointer'
    });
    const valueDisplay = createElement('span', { textIndent: widget_indent, display: 'block' });
    const constrain = (value, low, high) => Math.max(low, Math.min(value, high));
    const scaled = (value, size) => Math.round((value / size) * (max - min) + min);
    let isDragging = false;

    const updateValueDisplay = (x, y) => {
        valueDisplay.textContent = `x: ${x}, y: ${y}`;
    };
    const stopDragging = () => {
        if (!isDragging) {return;}
        const rect = joystickContainer.getBoundingClientRect();
        const x = scaled(parseFloat(joystick.style.left), rect.width);
        const y = scaled(parseFloat(joystick.style.top), rect.height);
        const call_cmd = command.includes('x=:range:') && command.includes('y=:range:') ?
            command.replace('x=:range:', `x=${x}`).replace('y=:range:', `y=${y}`) :
            `${command}`;

        console.log(`[API] Joystick exec: ${call_cmd}`);
        restAPI(call_cmd);
        isDragging = false;
    };
    const drag = event => {
        if (!isDragging) {return;}
        const touch = event.touches ? event.touches[0] : event;
        const rect = joystickContainer.getBoundingClientRect();
        const x = constrain(touch.clientX - rect.left, 0, rect.width);
        const y = constrain(touch.clientY - rect.top, 0, rect.height);

        joystick.style.left = `${x}px`;
        joystick.style.top = `${y}px`;
        updateValueDisplay(scaled(x, rect.width), scaled(y, rect.height));
    };

    joystick.addEventListener('mousedown', event => {
        isDragging = true;
        event.preventDefault();
    });
    joystick.addEventListener('touchstart', event => {
        isDragging = true;
        event.preventDefault();
    });
    document.addEventListener('mouseup', stopDragging);
    document.addEventListener('touchend', stopDragging);
    document.addEventListener('mousemove', drag);
    document.addEventListener('touchmove', drag);

    joystickContainer.appendChild(joystick);
    appendChildren(container, [createWidgetTitle(command, title_len), joystickContainer, valueDisplay]);
    updateValueDisplay((max - min) / 2, (max - min) / 2);
}

function toAbsoluteEndpoint(endpoint) {
    if (!endpoint) {return '';}
    if (/^https?:\/\//i.test(endpoint)) {return endpoint;}
    return `${BASE_URL}/${endpoint.replace(/^\/+/, '')}`;
}

function embedWidget(container, command, params={}) {
    const { title_len = 1, callback = '', image = false, title = null } = params;
    const embedUrl = toAbsoluteEndpoint(callback);
    const label = title || (command ? createTitle(command, title_len) : 'embedded content');
    const wrapper = createElement('div', { marginLeft: widget_indent, width: widgetWidth(0.8, 480) });
    const content = createElement(image ? 'img' : 'iframe', {
        width: '100%',
        border: '2px solid #e7e7e7',
        borderRadius: '8px',
        backgroundColor: '#101418'
    });

    if (!image) {
        Object.assign(content, { src: embedUrl, title: label, loading: 'lazy' });
        content.style.height = '320px';
        wrapper.appendChild(content);
        appendChildren(container, [createWidgetTitle(command, title_len, label), wrapper]);
        return;
    }

    Object.assign(content.style, {
        minHeight: '180px',
        display: 'block',
        objectFit: 'contain',
        cursor: 'pointer'
    });
    content.alt = label;
    const connect = () => {
        if (!embedUrl) {return;}
        console.log(`[API] Embed connect: ${embedUrl}`);
        content.removeAttribute('src');
        requestAnimationFrame(() => content.src = embedUrl);
    };

    content.addEventListener('click', connect);
    wrapper.appendChild(content);
    appendChildren(container, [createWidgetTitle(command, title_len, label), wrapper]);
    connect();
}

function whiteWidget(container, command, params={}) {
    const { title_len = 1, range = [0, 1000, 5] } = params;
    const initialValue = Math.round((range[0] + range[1]) / 2);
    const wrapper = createElement('div', {
        marginLeft: widget_indent,
        width: widgetWidth(0.7, 360),
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
    });
    const createSlider = labelText => {
        const row = createElement('label', {
            display: 'grid',
            gridTemplateColumns: '88px 1fr 52px',
            alignItems: 'center',
            gap: '8px'
        });
        const slider = rangeInput(range, initialValue, { width: '100%' });
        const valueDisplay = createElement('span', { textAlign: 'right' });

        bindRangeDisplay(slider, valueDisplay);
        appendChildren(row, [createElement('span', {}, { textContent: labelText }), slider, valueDisplay]);
        return { row, slider };
    };
    const cold = createSlider('Cold white');
    const warm = createSlider('Warm white');
    const execute = () => {
        const call_cmd = command.replace('cw=:range:', `cw=${cold.slider.value}`)
                                .replace('ww=:range:', `ww=${warm.slider.value}`);
        console.log(`[API] White exec: ${call_cmd}`);
        restAPI(call_cmd);
    };

    cold.slider.addEventListener('change', execute);
    warm.slider.addEventListener('change', execute);
    appendChildren(wrapper, [cold.row, warm.row]);
    appendChildren(container, [createWidgetTitle(command, title_len), wrapper]);
}
