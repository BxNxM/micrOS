// WIDGETS ELEMENTS

function sliderWidget(container, command, options={}) {
        var title_len = options.title_len || 1;
        paragraph = document.createElement('p');
        paragraph.textContent = command.split('/').slice(1, title_len+1).join('-').replace(/=/g, '').replace(':range:', '');
        // Create a slider
        element = document.createElement('input');
        element.type = 'range';
        element.min = options.range[0] || 0;
        element.max = options.range[1] || 100;
        element.step = options.range[2] || 5;
        element.value = Math.round((element.max-element.min)/2);

        // Create a span to display the slider value
        var valueDisplay = document.createElement('span');
        valueDisplay.textContent = element.value;
        element.addEventListener('input', function () {
            valueDisplay.textContent = this.value;
        });
        // Add an event listener for API CALL
        element.addEventListener('change', function () {
            var call_cmd;
            if (options.hasOwnProperty('range')) {
                // NEW
                call_cmd = command.replace(':range:', this.value);
            } else {
                // LEGACY
                if (command.endsWith("=")) {
                    call_cmd = `${command}${this.value}`
                } else {
                    call_cmd = `${command}/${this.value}`;
                }
            }
            console.log(`[API] Slider exec: ${call_cmd}`);
            restAPI(call_cmd);
        });
        containerAppendChild([paragraph, element, valueDisplay], container);
}

function buttonWidget(container, command, options={}) {
        var title_len = options.title_len || 1;
        paragraph = document.createElement('p');
        // Create a button
        element = document.createElement('button');
        element.textContent = command.split('/').slice(1, title_len+1).join('-');
        // Add an event listener for API CALL
        element.addEventListener('click', function () {
            var call_cmd;
            if (options.hasOwnProperty('range')) {
                // NEW
                call_cmd = command.replace(':range:', 'None');
            } else {
                // LEGACY
                call_cmd = command;
            }
            console.log(`[API] Button clicked: ${call_cmd}`);
            restAPI(call_cmd);
        });
        containerAppendChild([paragraph, element], container);
}

function textBoxWidget(container, command, options={}) {
        var title_len = options.title_len || 1;
        paragraph = document.createElement('p');
        paragraph.textContent = command.split('/').slice(1, title_len+1).join('-');
        // Create a small box (div)
        element = document.createElement('div');
        element.style.width = '30%';
        element.style.height = '60px';
        element.style.paddingTop = '10px';
        element.style.paddingLeft = '10px';
        element.style.border = '2px solid #e7e7e7';
        element.style.borderRadius = '4px';
        console.log(`Box update: ${data}`);
        var call_cmd;
        if (options.hasOwnProperty('range')) {
            // NEW
            call_cmd = command.replace(':range:', 'None');
        } else {
            // LEGACY
            call_cmd = command;
        }
        console.log(`[API] textBox exec: ${call_cmd}`);
        restAPI(call_cmd).then(resp => {
            console.log(resp.result);
            element.textContent = JSON.stringify(resp.result, null, 4);});
        containerAppendChild([paragraph, element], container);
}

function colorPaletteWidget(container, command, options) {
    // TODO
    console.log(`Dummy color widget: ${command}`)
}

// sliderWidget
