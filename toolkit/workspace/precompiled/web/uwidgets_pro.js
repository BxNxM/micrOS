// PRO WIDGETS ELEMENTS

function joystickWidget(container, command, params={}) {
    const { title_len = 1, range = [0, 100, 5] } = params;
    const [min, max, step] = range;
    const paragraph = document.createElement('p');
    const joystickContainer = document.createElement('div');
    const joystick = document.createElement('div');
    const valueDisplay = document.createElement('span');

    paragraph.style.textIndent = widget_indent;
    paragraph.textContent = createTitle(command, title_len);

    joystickContainer.style.position = 'relative';
    joystickContainer.style.width = '200px';
    joystickContainer.style.height = '200px';
    joystickContainer.style.border = '1px solid #fff';
    joystickContainer.style.marginLeft = widget_indent;
    joystickContainer.style.backgroundColor = 'transparent';

    joystick.style.position = 'absolute';
    joystick.style.width = '30px';
    joystick.style.height = '30px';
    joystick.style.background = '#fff';
    joystick.style.borderRadius = '50%';
    joystick.style.left = '50%';
    joystick.style.top = '50%';
    joystick.style.transform = 'translate(-50%, -50%)';
    joystick.style.cursor = 'pointer';

    valueDisplay.style.textIndent = widget_indent;
    valueDisplay.style.display = 'block';

    let isDragging = false;

    const updateValueDisplay = (x, y) => {
        valueDisplay.textContent = `x: ${x}, y: ${y}`;
    };

    const constrain = (value, min, max) => {
        if (value < min) return min;
        if (value > max) return max;
        return value;
    };

    const startDragging = (event) => {
        isDragging = true;
        event.preventDefault();
    };

    const stopDragging = () => {
        if (isDragging) {
            const rect = joystickContainer.getBoundingClientRect();
            const x = Math.round((parseFloat(joystick.style.left) / rect.width) * (max - min) + min);
            const y = Math.round((parseFloat(joystick.style.top) / rect.height) * (max - min) + min);

            const call_cmd = command.includes('x=:range:') && command.includes('y=:range:') ?
                command.replace('x=:range:', `x=${x}`).replace('y=:range:', `y=${y}`) :
                `${command}`;

            console.log(`[API] Joystick exec: ${call_cmd}`);
            restAPI(call_cmd);
        }
        isDragging = false;
    };

    const drag = (event) => {
        if (isDragging) {
            const rect = joystickContainer.getBoundingClientRect();
            const offsetX = event.touches ? event.touches[0].clientX - rect.left : event.clientX - rect.left;
            const offsetY = event.touches ? event.touches[0].clientY - rect.top : event.clientY - rect.top;
            const x = constrain(offsetX, 0, rect.width);
            const y = constrain(offsetY, 0, rect.height);

            joystick.style.left = `${x}px`;
            joystick.style.top = `${y}px`;

            const xValue = Math.round((x / rect.width) * (max - min) + min);
            const yValue = Math.round((y / rect.height) * (max - min) + min);
            updateValueDisplay(xValue, yValue);
        }
    };

    joystick.addEventListener('mousedown', startDragging);
    joystick.addEventListener('touchstart', startDragging);

    document.addEventListener('mouseup', stopDragging);
    document.addEventListener('touchend', stopDragging);

    document.addEventListener('mousemove', drag);
    document.addEventListener('touchmove', drag);

    joystickContainer.appendChild(joystick);
    containerAppendChild([paragraph, joystickContainer, valueDisplay], container);
    updateValueDisplay((max - min) / 2, (max - min) / 2);
}

function embedWidget(container, command, params={}) {
    const { title_len = 1, callback = '', image = false, title = null } = params;
    const embedUrl = toAbsoluteEndpoint(callback);
    const label = title || (command ? createTitle(command, title_len) : 'embedded content');
    const paragraph = document.createElement('p');
    const wrapper = document.createElement('div');
    const content = document.createElement(image ? 'img' : 'iframe');
    const widgetWidth = `${Math.min(windowWidth * 0.8, 480)}px`;

    paragraph.style.textIndent = widget_indent;
    paragraph.textContent = label;
    Object.assign(wrapper.style, { marginLeft: widget_indent, width: widgetWidth });
    Object.assign(content.style, {
        width: '100%',
        border: '2px solid #e7e7e7',
        borderRadius: '8px',
        backgroundColor: '#101418'
    });

    if (!image) {
        content.src = embedUrl;
        content.title = label;
        content.loading = 'lazy';
        content.style.height = '320px';
        wrapper.appendChild(content);
        containerAppendChild([paragraph, wrapper], container);
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
        requestAnimationFrame(() => {
            content.src = embedUrl;
        });
    };

    content.addEventListener('click', connect);
    wrapper.appendChild(content);
    containerAppendChild([paragraph, wrapper], container);
    connect();
}

function graphWidget(container, command, params={}) {
    const { title_len = 1, refresh = 3000, limit = 30 } = params;
    const paragraph = document.createElement('p');
    const canvas = document.createElement('canvas');
    const legend = document.createElement('div');
    const width = Math.round(Math.min(windowWidth * 0.6, 320));
    const height = 180;
    const pad = 28;
    const samples = [];
    const keys = [];
    const colors = ['#00d1ff', '#ffca3a', '#7bd88f', '#ff6b6b', '#c77dff', '#f4a261'];
    const ctx = canvas.getContext('2d');
    const timeText = stamp => new Date(stamp).toLocaleTimeString();

    paragraph.style.textIndent = widget_indent;
    paragraph.textContent = createTitle(command, title_len);
    Object.assign(canvas, { width, height });
    Object.assign(canvas.style, {
        marginLeft: widget_indent,
        width: `${width}px`,
        border: '2px solid #e7e7e7',
        borderRadius: '8px',
        backgroundColor: 'rgba(16, 20, 24, 0.72)'
    });
    Object.assign(legend.style, { marginLeft: widget_indent, width: `${width}px`, fontSize: '11px' });

    const draw = () => {
        let min = Infinity;
        let max = -Infinity;
        samples.forEach(sample => keys.forEach(key => {
            if (key in sample.values) {
                min = Math.min(min, sample.values[key]);
                max = Math.max(max, sample.values[key]);
            }
        }));
        if (!isFinite(min)) {return;}
        const highest = max;
        const span = min === max ? 1 : max - min;
        min -= span * (min === max ? 1 : 0.12);
        max += span * 0.15;
        const first = samples[0];
        const latest = samples[samples.length - 1];
        const last = latest.values;
        const scaleX = Math.max(latest.time - first.time, 1);
        const xOf = time => pad + ((time - first.time) / scaleX) * (width - pad - 12);
        const yOf = value => height - pad - ((value - min) / (max - min)) * (height - pad - 14);

        ctx.clearRect(0, 0, width, height);
        ctx.lineWidth = 1;
        ctx.strokeStyle = '#64707c';
        ctx.fillStyle = '#b7c0c8';
        ctx.font = '10px sans-serif';
        ctx.beginPath();
        ctx.moveTo(pad, 10);
        ctx.lineTo(pad, height - pad);
        ctx.lineTo(width - 10, height - pad);
        ctx.stroke();
        ctx.fillText(timeText(first.time), pad, height - 4);
        ctx.textAlign = 'right';
        ctx.fillText(timeText(latest.time), width - 10, height - 4);
        ctx.textAlign = 'left';
        ctx.lineWidth = 2;

        keys.forEach((key, i) => {
            const color = colors[i % colors.length];
            ctx.strokeStyle = color;
            ctx.fillStyle = color;
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
        ctx.lineWidth = 1;
        ctx.textAlign = 'right';
        ctx.fillStyle = '#fff';
        ctx.fillText(highest, pad - 4, yOf(highest) + 3);
        legend.textContent = '';
        keys.forEach((key, i) => {
            const value = key in last ? last[key] : '-';
            const color = colors[i % colors.length];
            if (value !== '-') {
                ctx.fillStyle = color;
                ctx.fillText(value, pad - 4, yOf(value) + 3);
            }
            const item = document.createElement('span');
            item.style.color = color;
            item.textContent = `${key}: ${value}  `;
            legend.appendChild(item);
        });
        ctx.textAlign = 'left';
    };

    const update = () => restAPI(command, false).then(({ result }) => {
        const values = {};
        const resultData = result || {};
        let hasData = false;
        for (const key in resultData) {
            const value = resultData[key];
            if (typeof value === 'number' && isFinite(value)) {
                values[key] = value;
                hasData = true;
                if (keys.indexOf(key) < 0) {keys.push(key);}
            }
        }
        if (!hasData) {return;}
        samples.push({ time: Date.now(), values });
        if (samples.length > limit) {samples.splice(0, samples.length - limit);}
        draw();
    });

    containerAppendChild([paragraph, canvas, legend], container);
    update();
    if (refresh > 0) {
        const intervalId = setInterval(update, refresh);
        container.addEventListener('DOMNodeRemovedFromDocument', () => clearInterval(intervalId));
    }
}
