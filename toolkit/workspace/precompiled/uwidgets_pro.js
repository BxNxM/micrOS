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
    joystickContainer.style.width = '150px';
    joystickContainer.style.height = '150px';
    joystickContainer.style.border = '1px solid #fff';
    joystickContainer.style.marginLeft = widget_indent;
    joystickContainer.style.backgroundColor = 'transparent'; // Transparent background

    joystick.style.position = 'absolute';
    joystick.style.width = '20px';
    joystick.style.height = '20px';
    joystick.style.background = '#fff';
    joystick.style.borderRadius = '50%';
    joystick.style.left = '50%';
    joystick.style.top = '50%';
    joystick.style.transform = 'translate(-50%, -50%)';
    joystick.style.cursor = 'pointer';

    valueDisplay.style.textIndent = widget_indent; // Indenting the value display line
    valueDisplay.style.display = 'block'; // Ensuring it behaves like a block element

    let isDragging = false;

    const updateValueDisplay = (x, y) => {
        valueDisplay.textContent = `x: ${x}, y: ${y}`;
    };

    const constrain = (value, min, max) => {
        if (value < min) return min;
        if (value > max) return max;
        return value;
    };

    joystick.addEventListener('mousedown', (event) => {
        isDragging = true;
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });

    document.addEventListener('mousemove', (event) => {
        if (isDragging) {
            const rect = joystickContainer.getBoundingClientRect();
            const offsetX = event.clientX - rect.left;
            const offsetY = event.clientY - rect.top;
            const x = constrain(offsetX, 0, rect.width);
            const y = constrain(offsetY, 0, rect.height);

            joystick.style.left = `${x}px`;
            joystick.style.top = `${y}px`;

            const xValue = Math.round((x / rect.width) * (max - min) + min);
            const yValue = Math.round((y / rect.height) * (max - min) + min);
            updateValueDisplay(xValue, yValue);
        }
    });

    joystick.addEventListener('mouseup', () => {
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
    });

    joystickContainer.appendChild(joystick);
    containerAppendChild([paragraph, joystickContainer, valueDisplay], container);
    updateValueDisplay((max - min) / 2, (max - min) / 2);
}


