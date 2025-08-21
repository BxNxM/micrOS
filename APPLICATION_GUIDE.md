# ![LOGO](./media/logo_mini.png?raw=true)

```
██       ██████   █████  ██████      ███    ███  ██████  ██████  ██    ██ ██      ███████ ███████ 
██      ██    ██ ██   ██ ██   ██     ████  ████ ██    ██ ██   ██ ██    ██ ██      ██      ██      
██      ██    ██ ███████ ██   ██     ██ ████ ██ ██    ██ ██   ██ ██    ██ ██      █████   ███████ 
██      ██    ██ ██   ██ ██   ██     ██  ██  ██ ██    ██ ██   ██ ██    ██ ██      ██           ██ 
███████  ██████  ██   ██ ██████      ██      ██  ██████  ██████   ██████  ███████ ███████ ███████ 
```

![microIO](https://img.shields.io/badge/microIO.py-blue) ![Types](https://img.shields.io/badge/Types.py-darkgreen) ![Common](https://img.shields.io/badge/Common.py-purple)

![MICROSVISUALIZATION](./media/micrOSToolkit.png?raw=true)

# Create your own application module


1. Create python file with the following naming convension: `LM_`your_app`.py`
2. You can create any function in this modul, these will be exposed by micrOS framework over IP so these can be accessable via phone client or web application (webui)
3. Drag-n-Drop LM file to micrOS devToolKit GUI
4. Select device
5. Press upload

**Youtube video series** Click on the picture:
[![Watch the playlist](https://img.youtube.com/vi/Oh5fffbreoU/0.jpg)](https://www.youtube.com/watch?v=Oh5fffbreoU&list=PL5rjiRvmUfU5bKbKkqs3KjbrJor1dlaIH&pp=gAQB)


```
██████  ███████  ██████  ██ ███    ██ ███    ██ ███████ ██████  
██   ██ ██      ██       ██ ████   ██ ████   ██ ██      ██   ██ 
██████  █████   ██   ███ ██ ██ ██  ██ ██ ██  ██ █████   ██████  
██   ██ ██      ██    ██ ██ ██  ██ ██ ██  ██ ██ ██      ██   ██ 
██████  ███████  ██████  ██ ██   ████ ██   ████ ███████ ██   ██ level
```

### LM\_basic.py

```python
"""
LM_basic.py is an example of a very basic Load Module.

This module demonstrates the micrOS function exposure feature.
This means that all defined functions can be accessed via
ShellCli (using a raw socket) and optionally via WebCli (http).
"""


def hello(name="Anonymous"):
    """Returns a greeting message for the given name."""
    return f"Hello {name}!"


def add_two_numbers(a, b):
    """Adds two numbers and returns the result in a formatted string."""
    return f"{a} + {b} = {a + b}"


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :param widgets: only a placeholder here - has no effect
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """

    return ("hello name='Anonymous'",
            "add_two_numbers a b")

```

### LM\_basic\_led.py

```python
"""
LM_basic_led.py is an example Load Module for controlling an LED.

This module demonstrates the micrOS function exposure feature
for hardware interaction. It allows the user to control an LED
connected to a specified pin through the following functions:
- load: Initialize and cache the LED pin instance.
- on: Turn the LED on.
- off: Turn the LED off.
- toggle: Toggle the LED state.

These functions can be accessed via ShellCli (using a raw socket)
and optionally via WebCli (http).
"""

from machine import Pin  	# Import MicroPython's Pin module for GPIO control

LED = None  				# Cache the Pin instance for the LED


def load(pin_number=26):
    """
    Initialize the specified pin as an output for the LED and cache the instance.

    Args:
        pin_number (int): The GPIO pin number to which the LED is connected. Default is 26.

    Returns:
        Pin: The initialized Pin instance.
    """
    global LED
    if LED is None:
        LED = Pin(pin_number, Pin.OUT)  # Initialize the pin as output and store in global variable
    return LED


def on():
    """
    Turn the LED on by setting the pin output to high.

    Returns:
        str: Status message indicating the LED is on.
    """
    pin = load()
    pin.value(1)  # Set pin high - LED ON
    return "LED ON"


def off():
    """
    Turn the LED off by setting the pin output to low.

    Returns:
        str: Status message indicating the LED is off.
    """
    pin = load()
    pin.value(0)  # Set pin low - LED OFF
    return "LED OFF"


def toggle():
    """
    Toggle the LED state.

    Returns:
        str: Status message indicating the new LED state.
    """
    pin = load()
    pin.value(not pin.value())  # Toggle pin state
    return "LED ON" if pin.value() else "LED OFF"


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :param widgets: only a placeholder here - has no effect
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'load', 'on', 'off', 'toggle'

```

For more info: Micropython official [Pins](https://docs.micropython.org/en/latest/library/machine.Pin.html)

[Official micropython site](https://docs.micropython.org/en/latest/esp32/quickref.html#pins-and-gpio)

-------------------------------------------------------------------------------


### micrOS LM\_template.py

Function naming convesions for Load Modules.

```python
"""
LM_template.py is a Load Module template for micrOS.

This template demonstrates the recommended function naming conventions,
pin registration, and hardware interaction practices in micrOS. The module
provides functions to control an LED connected to a specified pin and
examples of optional state management and pin mapping.

Functions available in this module:
- load: Initialize and cache the LED pin instance.
- on: Turn the LED on.
- off: Turn the LED off.
- toggle: Toggle the LED state.
- pinmap: Retrieve the logical pinmap (optional).
- status: Report the current state of the LED (optional).
- help: Provide a list of available functions.

These functions can be accessed via ShellCli (using a raw socket) and
optionally via WebCli.
"""

from machine import Pin
from microIO import bind_pin, pinmap_search

LED = None  # Cache the Pin instance for the LED


def load(pin_number=26):
    """
    [Naming convention]
    Initialize the specified pin as an output for the LED and cache the instance.
    This function follows the micrOS recommended naming convention for module load/init.

    Args:
        pin_number (int): The GPIO pin number to which the LED is connected. Default is 26.

    Returns:
        Pin: The initialized Pin instance.
    """
    global LED
    if LED is None:
        pin = bind_pin('led', pin_number)  # Reserve the pin as "led"
        LED = Pin(pin, Pin.OUT)  # Initialize the pin as output and store in global variable
    return LED


def on():
    """
    Turn the LED on by setting the pin output to high.

    Returns:
        str: Status message indicating the LED is on.
    """
    pin = load()
    pin.value(1)  # Set pin high - LED ON
    return "LED ON"


def off():
    """
    Turn the LED off by setting the pin output to low.

    Returns:
        str: Status message indicating the LED is off.
    """
    pin = load()
    pin.value(0)  # Set pin low - LED OFF
    return "LED OFF"


def toggle():
    """
    Toggle the LED state.

    Returns:
        str: Status message indicating the new LED state.
    """
    pin = load()
    pin.value(not pin.value())  # Toggle pin state
    return "LED ON" if pin.value() else "LED OFF"


def pinmap():
    """
    [Naming convention]
    Retrieve the logical pinmap for the application.

    This function uses `pinmap_search` to resolve pin mappings based on the
    IO_<device_tag>.py configuration and any custom pin definitions.

    Returns:
        dict: A dictionary of pin mappings (e.g., {pin_key: pin_value, ...}).
    """
    return pinmap_search(['led'])


def status(lmf=None):
    """
    [Naming convention]
    Report the current state of the LED.

    This function follows the micrOS naming convention for state-machine returns.
    It provides the state of the module as a dictionary with keys like {S, R, G, B, etc.}.

    Args:
        lmf (None): Placeholder for future enhancements.

    Returns:
        dict: A dictionary containing the state of the LED. Example: {'S': 0/1}.
    """
    return {'S': LED.value()}


def help(widgets=False):
    """
    [Naming convention]
    [i] micrOS LM naming convention - built-in help message
    :param widgets: only a placeholder here - has no effect
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'load', 'on', 'off', 'toggle', 'pinmap', 'status', 'help'

```

#### microIO.py

```python
def bind_pin(tag, number=None):
    """
    Universal pin handler - assign+lock pin for a tag -> application
    :param tag: tag for application pin booking with built-in tag detection from IO_<device>.py
    :param number: optional parameter to overwrite default tag:pin relation
    """
```

> Note: Simple micrOS pin allocation method

```python
def pinmap_info():
    """
    Debug info function to get active pinmap and booked IO-s
    return: {'map': "platform", 'booked': {}, 'custom': {}}
    """
```

```python
def pinmap_search(keys):
    """
    :param keys: one or list of pin names (like: switch_1) to resolve physical pin number
    Gives information where to connect the selected periphery to control WITHOUT PIN BOOKING
    """
```

> Note: Used for multi-device pin support (advanced)  


```
██ ███    ██ ████████ ███████ ██████  ███    ███ ███████ ██████  ██  █████  ████████ ███████ 
██ ████   ██    ██    ██      ██   ██ ████  ████ ██      ██   ██ ██ ██   ██    ██    ██      
██ ██ ██  ██    ██    █████   ██████  ██ ████ ██ █████   ██   ██ ██ ███████    ██    █████   
██ ██  ██ ██    ██    ██      ██   ██ ██  ██  ██ ██      ██   ██ ██ ██   ██    ██    ██      
██ ██   ████    ██    ███████ ██   ██ ██      ██ ███████ ██████  ██ ██   ██    ██    ███████ level
```

## ![dashboard](./media/web_dashboard.png?raw=true) micrOS Types.py module

> Advanced help messages with widget type assignment

Normally in help function you can return a tuple of strings, this can be
queried as help message from ShellCli and WebCli.

With `Types.resolve` integration you can easily extend normal human readable help messages,
and enable machine readable output for frontend element generation.

Main steps:

1. Create `help` function with `widgets` parameter <br>
2. Wrap help tuple into `resolve` function
3. Use predefined widget types (tags)
4. Check the following example:

Tags:

* `BUTTON`, requires[0]: no param
* `COLOR`, requires[3]: r, g, b function parameters
* `SLIDER`, requires[1]: br function parameters (or any other single param)
* `TEXTBOX`, requires[0]: no param
* `JOYSTICK`, requires[1]: x and y function parameters
* Implementation of [TYPES](./micrOS/source/Types.py)


### micrOS LM\_types\_demo.py

```python
"""
LM_types_demo.py is a Load Module for micrOS showcasing type-based function resolutions.

This module demonstrates the recommended function naming conventions,
pin registration, and hardware interaction practices in micrOS. It also
highlights the use of `Types.resolve` to dynamically generate function
lists and UI widgets for micrOS interfaces.

Functions available in this module:
- load: Initialize and cache the LED pin instance.
- on: Turn the LED on.
- off: Turn the LED off.
- toggle: Toggle the LED state.
- pinmap: Retrieve the logical pinmap (optional).
- status: Report the current state of the LED (optional).
- help: Provide a list of available functions, with optional widget generation.

These functions can be accessed via ShellCli (using a raw socket) and
optionally via WebCli.
"""

from machine import Pin
from microIO import bind_pin, pinmap_search
from Types import resolve

LED = None  # Cache the Pin instance for the LED


def load(pin_number=26):
    """
    [Naming convention]
    Initialize the specified pin as an output for the LED and cache the instance.
    This function follows the micrOS recommended naming convention for module load/init.

    Args:
        pin_number (int): The GPIO pin number to which the LED is connected. Default is 26.

    Returns:
        Pin: The initialized Pin instance.
    """
    global LED
    if LED is None:
        pin = bind_pin('led', pin_number)  # Reserve the pin as "led"
        LED = Pin(pin, Pin.OUT)  # Initialize the pin as output and store in global variable
    return LED


def on():
    """
    Turn the LED on by setting the pin output to high.

    Returns:
        str: Status message indicating the LED is on.
    """
    pin = load()
    pin.value(1)  # Set pin high - LED ON
    return "LED ON"


def off():
    """
    Turn the LED off by setting the pin output to low.

    Returns:
        str: Status message indicating the LED is off.
    """
    pin = load()
    pin.value(0)  # Set pin low - LED OFF
    return "LED OFF"


def toggle():
    """
    Toggle the LED state.

    Returns:
        str: Status message indicating the new LED state.
    """
    pin = load()
    pin.value(not pin.value())  # Toggle pin state
    return "LED ON" if pin.value() else "LED OFF"


def pinmap():
    """
    [Naming convention]
    Retrieve the logical pinmap for the application.

    This function uses `pinmap_search` to resolve pin mappings based on the
    IO_<device_tag>.py configuration and any custom pin definitions.

    Returns:
        dict: A dictionary of pin mappings (e.g., {pin_key: pin_value, ...}).
    """
    return pinmap_search(['led'])


def status(lmf=None):
    """
    [Naming convention]
    Report the current state of the LED.

    This function follows the micrOS naming convention for state-machine returns.
    It provides the state of the module as a dictionary with keys like {S, R, G, B, etc.}.

    Args:
        lmf (None): Placeholder for future enhancements.

    Returns:
        dict: A dictionary containing the state of the LED. Example: {'S': 0/1}.
    """
    return {'S': LED.value()}


def help(widgets=False):
    """
    [Naming convention]
    [i] micrOS LM naming convention - built-in help message
    :param widgets: only a placeholder here - has no effect
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('load',
                    'BUTTON on',
                    'BUTTON off',
                    'BUTTON toggle',
                    'pinmap',
                    'status',
                    'help'), widgets)

```

Output:

```
simulator $ types_demo help
 load,
 on,
 off,
 toggle,
 pinmap,
 status,
 help,

simulator $ types_demo help True
 {"type": "button", "lm_call": "on ", "options": ["None"]},
 {"type": "button", "lm_call": "off ", "options": ["None"]},
 {"type": "button", "lm_call": "toggle ", "options": ["None"]},
```

Usage(s): [LM_neopixel](./micrOS/source/LM_neopixel.py), etc. in most of the modules :)

TYPE Example sytax:

```python
    return resolve(('COLOR color r=<0-255> g b',                 # range syntax: <min-max-step> step is optional
                    'SLIDER brightness br=<0-1000-10>',          # range syntax: <min-max-step> step is optional
                    'BUTTON action',
                    'BUTTON conntrol cmd=<Hello,Bello>',         # options syntax: <opt1,opt2,...> list of parameters
                    'other_function num'), widgets=widgets)
```

-------------------------------------------------------------------------------

```
 █████  ██████  ██    ██  █████  ███    ██  ██████ ███████ ██████  
██   ██ ██   ██ ██    ██ ██   ██ ████   ██ ██      ██      ██   ██ 
███████ ██   ██ ██    ██ ███████ ██ ██  ██ ██      █████   ██   ██ 
██   ██ ██   ██  ██  ██  ██   ██ ██  ██ ██ ██      ██      ██   ██ 
██   ██ ██████    ████   ██   ██ ██   ████  ██████ ███████ ██████  level
                                                                    
```

## micrOS Common.py module

#### Common module with additinal features for LoadModule-s

Module responsible for collecting additional feature definitions dedicated to the micrOS framework and LoadModules. Code: [micrOS/source/Common.py](./micrOS/source/Common.py)

------------------------------------

### console

**Example:** LM\_my\_module.py

```python
from Common import console

def write_and_light(msg="Hello world!"):
    console(msg)       # Use console write + built-in LED effect 
                       #     When dbg=True in node_config
```

Usage(s): [LM_sound_event](./micrOS/source/LM_sound_event.py) [LM_demo](./micrOS/source/LM_demo.py) 

------------------------------------

### transition(from\_val, to\_val, step\_ms, interval_sec)

Generator for color transitions.

Parameters:

* from\_val: Starting value
* to\_val: Target value
* step\_ms: Step to reach to\_val
* interval\_sec: Full intervals

Returns:

* A generator that yields the intermediate values between from_val and to_val in steps of step_ms.

Usage(s): [LM_rgb](./micrOS/source/LM_rgb.py) [LM_cct](./micrOS/source/LM_cct.py) [LM_servo](./micrOS/source/LM_servo.py)

------------------------------------

### transition\_gen(*args, interval\_sec=1.0)

Create multiple transition generators.

Parameters:

* args: Pairs of from_val and to_val values for each channel
* interval\_sec: Interval in seconds to calculate the optimal fade/transition effect

Returns:

* If only one transition generator is created, it returns the generator and the step size in milliseconds (gen, step_ms). If multiple transition generators are created, it returns a list of generators and the step size in milliseconds ([gen1, gen2, ...], step_ms).

Usage(s): [LM_rgb](./micrOS/source/LM_rgb.py) [LM_cct](./micrOS/source/LM_cct.py) [LM_servo](./micrOS/source/LM_servo.py)

------------------------------------

### class SmartADC

ADC wrapper class for reading analog values.

Methods:

* \_\_init\_\_(self, pin): Initializes the ADC object with the specified pin.
* get(self): Reads the analog value from the ADC and returns a dictionary with the raw value, percentage, and voltage.
* get\_instance(pin): Returns a singleton SmartADC object for the specified pin.

------------------------------------

### micro\_task(tag, task=None, \_wrap=False)

Async task creation from LoadModules.

```python
def micro_task(tag: str, task=None, _wrap=False):
    """
    [LM] Async task manager.
    Modes:
      A) GET:
         micro_task("tag") -> existing task object or None
      B) CREATE:
         micro_task("tag", task=...) -> True | None | False
         Creates a new async task with the given tag if not already running.
      C) CREATE AS DECORATOR (shortcut):
         @micro_task("main", _wrap=True)
         async def mytask(tag, ...): ...
         # Calling mytask(...) will create/start a new task under "main._mytask"

    :param tag: Task tag string
    :param task: Coroutine (or list of command arguments) to contract a task with
                 the given async task callback
    :param _wrap: When True, return a decorator factory (for use as @micro_task(...))
    :return: Task object (GET), bool|None|False (CREATE), or decorator (DECORATOR)
    """
```

#### Example: LM\_task\_example.py

```python
from Common import micro_task

async def __task(tag, period_ms):
    counter = 0
    with micro_task(tag=tag) as my_task:
        while True:
            # DO something here in the async loop...
            counter += 1

            # Store data in task cache (task show mytask)
            my_task.out = f'MyTask Counter: {counter}'

            # Async sleep - feed event loop
            await my_task.feed(sleep_ms=period_ms)
            # [i] feed same as "await asyncio.sleep_ms(period_ms)" with micrOS features (WDT)

def create_task():
    """
    Legacy way of task creation (with exact task tagging)
    """
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    task_tag = "microtask.run"
    state = micro_task(tag=task_tag, task=__task(tag=task_tag, period_ms=5))
    return "Starting" if state else "Already running"
```

> Than you can call `task_example create_task` function.

**New Decorator way - shorter more efficient**

```python
from Common import micro_task

@micro_task("microtask", _wrap=True)
async def mytask(tag, period_ms=30):
    """
    New shorter way of task creation
     with decorator function
    """
    counter = 0
    with micro_task(tag=tag) as my_task:
        while True:
            # DO something here in the async loop...
            counter += 1

            # Store data in task cache (task show mytask)
            my_task.out = f'MyTask Counter: {counter}'

            # Async sleep - feed event loop
            await my_task.feed(sleep_ms=period_ms)
            # [i] feed same as "await asyncio.sleep_ms(period_ms)" with micrOS features (WDT)
```

> Than you can call `task_example mytask` function.

Usage(s): [LM_presence](./micrOS/source/LM_presence.py) [LM_buzzer](./micrOS/source/LM_buzzer.py) [LM_cct](./micrOS/source/LM_cct.py) [LM_dimmer](./micrOS/source/LM_dimmer.py) [LM_neopixel](./micrOS/source/LM_neopixel.py) [LM_neopixel](./micrOS/source/LM_neopixel.py) [LM_rgb](./micrOS/source/LM_rgb.py) [LM_roboarm](./micrOS/source/LM_roboarm.py) [LM_robustness](./micrOS/source/LM_robustness.py) etc.

------------------------------------

### manage\_task(tag, operation)

Async task management from LoadModules.: `show` , `isbusy` , `kill`

Parameters:

- `tag`: Task string identifier. Used for task creation, or can be get as `task list` command output.
- `operation`: Opeartion `show` , `isbusy` , `kill` on `tag`-ed task.

```python
def manage_task(tag, operation):
    """
    [LM] Async task management - user interface
    :param tag: task tag
    :param operation: kill / show / isbusy
    """
```

Usage(s): [LM\_oled\_ui](./micrOS/source/LM_oled_ui.py) [LM\_i2s\_mic](./micrOS/source/LM_i2s_mic.py)

------------------------------------

### exec_cmd(cmd)

Run sync task from LoadModules by string list.

Parameters:

- `cmd`: String list for Load Module execution

Example:

```
cmd = ["system", "info"]
state, output = exec_cmd(cmd)
``` 

Where `"system"` is the module name and `"info"` is the function name, and it not requires any paramater.


> Note: `cmd` can contain only one command with its optional paramater. So this method not supports multi command execution.

```python
def exec_cmd(cmd):
    """
    Single (sync) LM execution - user interface
    :param cmd: command string list
    return state, output
    """
```

Usage(s): [LM\_oled_ui](./micrOS/source/LM_oled_ui.py)

------------------------------------

### data\_logger(f\_name, data=None, limit=12, msgobj=None)

micrOS Common Data logger solution.

Parameters:

* f\_name: Log name (without extension, automatically appends .dat)
* data: Data to append to the log. If None, reads the log and returns it as a message stream.
* limit: Line limit for the log (default: 12)
* msgobj: Socket stream object (automatically set)

Returns:

* If data is None, returns the log as a message stream. If data is provided, returns True if the write operation was successful, False otherwise.


**Example:** LM\_my\_logger.py

```python
from Common import data_logger


def log_data(data):
	if not data_logger(f_name="mylog", data=data, limit=20):
		return "data_logger, error... check system alarms"
	return "data saved."

	
def get_data():
	return data_logger(f_name="mylog")
	

def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
	return 'log_data data="value"', 'get_data'
```

Usage(s): [LM_dht22](./micrOS/source/LM_dht22.py)

------------------------------------

### socket_stream decorator

Adds an extra `msgobj` to the wrapped function's argument list. The `msgobj` provides a socket message interface for the open connection.

**Example:** LM\_my\_module.py

```python
from Common import socket_stream

@socket_stream
def function_name(arg1, arg2, ..., msgobj=None):
    # function body
    msgobj("Reply from Load Module to shellCli :)")
```

Usage(s): [LM_system](./micrOS/source/LM_system.py) 

------------------------------------

### notify(text)

micrOS common notification handler (Telegram).

**Prerequisite**
> Set Telegram API KEY in node config: telegram key

```
conf
 telegram <API KEY>
noconf
my_notification "hello"
 notify, msg was sent.
```

Parameters:

* text: Notification text

Returns:

* True if the notification was sent successfully, False otherwise.

**Example:** LM\_my\_notification.py

```python
from Common import notify

def send_notification(msg="Hello from micrOS board"):
	if not notify(msg):
		return "notify, error... check system alarms"
	return "notify, msg was sent."
```

Usage(s): [LM_presence](./micrOS/source/LM_presence.py)


------------------------------------

### web\_endpoint(endpoint, function):

Custom endpoint creation in order to receive GET requests. `<localhost.local>/endpoint` from Load Modules to WebCli web server.

**Prerequisite**
> Enable `webui True` in node config.

Parameters:

* **endpoint**: name of the http endpoint after the main address, like `localhost.local/my_endpoint`, in this case the `my_endpoint` is the input paramater here.

* Simple **function** return: callback function, this will be called when endpoint is called, it must return 2 values: html type and data for example `html/text, data` data for example: `hello world`. Supported data types: `text/html`, `text/plain`, `image/jpeg`. In short:

```python
return "image/jpeg" | "text/html" | "text/plain", <data>
	
# <data>: binary | string
```
> select one from between | signs

* Stream function return:

```python
return "multipart/x-mixed-replace" | "multipart/form-data", <data>
	
# <data>: {'callback':<func>, 'content-type': 'image/jpeg' | 'audio/l16;...'}
```
> select one from between | signs

Returns:

* True if function successfuly registered on the endpoint

**Example:** LM\_my\_endpoint.py

```python
from Common import web_endpoint

def load():
	...
	web_endpoint('my_endpoint', _response)
	return "Endpoint was created: http://localhost/my_endpoint"

def _response():
	reply = "hello world"
	return 'text/plain', reply
```

Usage(s): [LM_OV2640](./micrOS/source/LM_OV2640.py)

--------------------------

### AnimationPlayer(animation:callable=None, tag:str=None, batch\_draw:bool=False, batch\_size:int=None)

Base class for asyncronous animation playing. `animation` must be a generator.

```python3

class AnimationPlayer:
    """
    Generic async animation (generator) player.
    """

    def __init__(self, animation:callable=None, tag:str=None, batch_draw:bool=False, batch_size:int=None, loop:bool=True):
        """
        Initialize the AnimationPlayer with an optional animation.
        :param animation: Function to GENERATE animation data
        :param tag: Optional task tag for micro_task management.
        :param batch_draw: If True - draw in batches
        :param batch_size: Number of pixels per batch when drawing
        :param loop: If True - loop the animation (default)
        """

    def control(self, play_speed_ms:int, bt_draw:bool=None, bt_size:int=None, loop=True):
        """
        Set/Get current play speed of the animation.
        :param play_speed_ms: player loop speed in milliseconds.
        :param bt_draw: batch drawing flag.
        :param bt_size: batch drawing size.
        :param loop: loop flag.
        return: {"realtime": not self.batch_draw, "batched": self.batch_draw,
                "size": self.__batch_size, "speed_ms": self._player_speed_ms}
        """

    def play(self, animation=None, speed_ms=None, bt_draw=False, bt_size=None, loop=True):
        """
        Play animation via generator function.
        :param animation: Animation generator function.
        :param speed_ms: Speed of the animation in milliseconds. (min.: 3ms)
        :param bt_draw: batch drawing flag.
        :param bt_size: batch drawing size.
        :param loop: Loop the animation.
        return: verdict str/bool
        """

    def stop(self):
        """
        Stop the animation.
        """

    def update(self, *arg, **kwargs):
        """
        Child class must implement this method to handle data update logic.
        """
        raise NotImplementedError("Child class must implement update method.")

    def draw(self):
        """
        Child class must implement this method to handle drawing logic.
        """
        raise NotImplementedError("Child class must implement draw method.")

    def clear(self):
        """
        Clear the display logic.
        """
        raise NotImplementedError("Child class must implement clear method.")
```

#### Generator example:

```python
def generator():
    while True:
        yield 10, 0, 0
        yield 5, 5, 0
        yield 0, 10, 0
        yield 0, 5, 5
        yield 0, 0, 10
        yield 5, 0, 5
```

Usage(s): [LM_neomatrix](./micrOS/source/LM_neomatrix.py) [LM_neoeffects.](./micrOS/source/LM_neoeffects.py)

--------------------------

### data_dir(f\_name=None)

Get data working directory path. If f_name is given returns a the full data path with file name.

```python
def data_dir(f_name=None):
    """
    Access for data dir path
    :param f_name: if given, returns full path, otherwise returns data dir root path
    """
```

### web_dir(f\_name=None)

Get web working directory path. If f_name is given returns a the full web path with file name.

```python
def web_dir(f_name=None):
    """
    Access for web dir path
    :param f_name: if given, returns full path, otherwise returns web dir root path
    """
```

