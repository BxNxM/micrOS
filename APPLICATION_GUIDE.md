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

```
██████  ███████  ██████  ██ ███    ██ ███    ██ ███████ ██████  
██   ██ ██      ██       ██ ████   ██ ████   ██ ██      ██   ██ 
██████  █████   ██   ███ ██ ██ ██  ██ ██ ██  ██ █████   ██████  
██   ██ ██      ██    ██ ██ ██  ██ ██ ██  ██ ██ ██      ██   ██ 
██████  ███████  ██████  ██ ██   ████ ██   ████ ███████ ██   ██ level
```

### LM\_basic.py

```python
def hello(name="Anonymous"):
	return f"Hello {name}!"


def add_two_numbers(a, b):
	return f"{a}+{b} = {a+b}"


def help(widgets=False):
	return ("hello name='Anonymous'",
			  "add_two_numbers a b")
```

### LM\_basic\_led.py

```python
from machine import Pin	              # Import micropython Pin module

LED = None                            # Cache created Pin instance

def load(pin_number=4):
	global LED
	if LED is None:
		LED = Pin(pin_number, Pin.OUT) # Init PIN 4 as OUTPUT and store (cache) in global var.
	return LED


def on():
	pin = load()
	pin.value(1)                      # Set pin high - LED ON
	return "LED ON"


def off():
	pin = load()
	pin.value(0)                      # Set pin low - LED OFF
	return "LED OFF"


def toggle():
	pin = load()
	pin.value(not pin.value())
	return "LED ON" if pin.value() else "LED OFF"


def help():
	return 'load', 'on', 'off', 'toggle'
```

For more info: Micropython official [Pins](https://docs.micropython.org/en/latest/library/machine.Pin.html)

[Official micropython site](https://docs.micropython.org/en/latest/esp32/quickref.html#pins-and-gpio)

-------------------------------------------------------------------------------


### micrOS LM\_template.py

Function naming convesions for Load Modules.

```python

from machine import Pin	
from microIO import register_pin, pinmap_search

LED = None                            # Cache created Pin instance

def load(pin_number=4):
	"""
	[RECOMMENDED]
	Function Naming Convetion for module load/init
	"""
	global LED
	if LED is None:
		pin = register_pin('led', pin_number)            # Book pin 4 (as "led")
		LED = Pin(pin, Pin.OUT) # Init PIN 4 as OUTPUT and store (cache) in global var.
	return LED


def on():
	pin = load()
	pin.value(1)                      # Set pin high - LED ON
	return "LED ON"


def off():
	pin = load()
	pin.value(0)                      # Set pin low - LED OFF
	return "LED OFF"


def toggle():
	pin = load()
	pin.value(not pin.value())
	return "LED ON" if pin.value() else "LED OFF"


def pinmap():
	"""
	[OPTIONAL]
	pinmap_search - logical pinmap resolver based on IO_<device_tag>.py + Custom pins
	return: dict {pinkey: pinvalue, ...}
	"""
	return pinmap_search(['led'])


def status(lmf=None):
	"""
	[OPTIONAL]
	Function naming convension for
		module state-machine return
		return: dict
	
	Example:
		return {'S': 0/1}
	Supported keys: {S, R, G, B, BR, X, Y}
	"""
	return {'S': LED.value()}


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
	return 'load', 'on', 'off', 'toggle', 'pinmap', 'status', 'help'
```

#### microIO.py

``` python
def resolve_pin(tag):
    """
    Used in LoadModules
    tag - resolve pin name by logical name (like: switch_1)
    This function implements IO allocation/booking (with overload protection)
    return: integer (pin number)
    """
```

> Note: Used for multi-device pin support (advanced)  

```python
def register_pin(tag, number):
    """
    Book pin (with overload protection) without IO_platform.py file editing
    :param tag: associated pin name for pin number
    :param number: pin number as integer
    return: pin number
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


```
██ ███    ██ ████████ ███████ ██████  ███    ███ ███████ ██████  ██  █████  ████████ ███████ 
██ ████   ██    ██    ██      ██   ██ ████  ████ ██      ██   ██ ██ ██   ██    ██    ██      
██ ██ ██  ██    ██    █████   ██████  ██ ████ ██ █████   ██   ██ ██ ███████    ██    █████   
██ ██  ██ ██    ██    ██      ██   ██ ██  ██  ██ ██      ██   ██ ██ ██   ██    ██    ██      
██ ██   ████    ██    ███████ ██   ██ ██      ██ ███████ ██████  ██ ██   ██    ██    ███████ level
```

## micrOS Types.py module

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
from machine import Pin
from microIO import register_pin, pinmap_search
from Types import resolve

LED = None  # Cache created Pin instance


def load(pin_number=4):
    """
    [RECOMMENDED]
    Function Naming Convetion for module load/init
    """
    global LED
    if LED is None:
        pin = register_pin('led', pin_number)  # Book pin 4 (as "led")
        LED = Pin(pin, Pin.OUT)  # Init PIN 4 as OUTPUT and store (cache) in global var.
    return LED


def on():
    pin = load()
    pin.value(1)  # Set pin high - LED ON
    return "LED ON"


def off():
    pin = load()
    pin.value(0)  # Set pin low - LED OFF
    return "LED OFF"


def toggle():
    pin = load()
    pin.value(not pin.value())
    return "LED ON" if pin.value() else "LED OFF"


def pinmap():
    """
    [OPTIONAL]
    pinmap_search - logical pinmap resolver based on IO_<device_tag>.py + Custom pins
    return: dict {pinkey: pinvalue, ...}
    """
    return pinmap_search(['led'])


def status(lmf=None):
    """
    [OPTIONAL]
    Function naming convension for
        module state-machine return
        return: dict

    Example:
        return {'S': 0/1}
    Supported keys: {S, R, G, B, BR, X, Y}
    """
    return {'S': LED.value()}


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
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

### transition(from_val, to\_val, step\_ms, interval_sec)

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
* get\_singleton(pin): Returns a singleton SmartADC object for the specified pin.

------------------------------------

### micro\_task(tag, task=None)

Async task creation from LoadModules.

Parameters:

* tag: If None, returns the task generator object. If a taskID is provided, returns the existing task object by tag.
* task: Coroutine to execute.

Returns:

* If tag is None, returns the task generator object. If a taskID is provided, returns the existing task object by tag. If task is provided, returns the task creation state: True for success, False for failure.

**Example:** LM\_my\_task.py

```python
import uasyncio as asyncio
from Common import micro_task

async def __task(period_ms):
	counter = 0
	with micro_task(tag="mytask") as my_task:
		while True:
			
			# DO something here in the async loop...
			counter += 1

			# Store data in task cache (task show mytask)
			my_task.out = f'MyTask Counter: {counter}'
		
			# Async sleep - feed event loop
			await asyncio.sleep_ms(period_ms)


def create_task():
	# [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
	state = micro_task(tag="mytask", task=__task(period_ms=5))
	return "Starting" if state else "Already running"
```

Usage(s): [LM_presence](./micrOS/source/LM_presence.py) [LM_buzzer](./micrOS/source/LM_buzzer.py) [LM_cct](./micrOS/source/LM_cct.py) [LM_dimmer](./micrOS/source/LM_dimmer.py) [LM_neopixel](./micrOS/source/LM_neopixel.py) [LM_neopixel](./micrOS/source/LM_neopixel.py) [LM_rgb](./micrOS/source/LM_rgb.py) [LM_roboarm](./micrOS/source/LM_roboarm.py) etc.

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

Add custom endpint `<localhost.local>/endpoint` from Load Modules to WebCli web server.

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
