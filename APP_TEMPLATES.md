# How to write Load Modules

1. Create python file with the following naming convension: `LM_`your_app`.py`
2. You can create any function in this modul, these will be exposed by micrOS framework over tcp/ip so these can be accessable via phone client.
3. drag-n-drop LM file to micrOS devToolKit GUI
4. Select device
5. Press upload

### LM\_simple.py

```python
def hello(name="Anonymous"):
	return f"Hello {name}!"


def add_two_numbers(a, b):
	return f"{a}+{b} = {a+b}"
```

### LM\_simple\_led.py

```python
from machine import Pin					# Import micropython Pin module

PIN = None								# Cache created Pin instance

def load_n_init():
	global PIN
	if PIN is None:
		PIN = Pin(4, Pin.OUT)			# Init PIN 4 as OUTPUT and store (cache) in global var.
	return PIN


def on():
	pin = load_n_init()
	pin.value(1)							# Set pin high - LED ON
	return "LED ON"


def off():
	pin = load_n_init()
	pin.value(0)							# Set pin low - LED OFF
	return "LED OFF"


def toggle():
	pin = load_n_init()
	pin.value(not pin.value())
	return "LED ON" if pin.value() else "LED OFF"
	
def help():
	return 'load_n_init', 'on', 'off', 'toggle'
```

For more info: Micropython official [Pins](https://docs.micropython.org/en/latest/library/machine.Pin.html)


### LM_template.py

Function naming convesions for Load Modules.

```python

from LogicalPins import physical_pin, pinmap_dump
from machine import Pin

def load_n_init():
	"""
	[RECOMMENDED]
	Function naming convension to create IO (Pin) objects
	- function to initialize IO peripheries

	physical_pin - to resolve pin on board by logical name (tag)
	"""
	
	pin_number = physical_pin('redgb')	# select pin number from platfrom lookup table
	red = Pin(pin_number)
	return red


def lmdep():
   """
   [OPTIONAL] [IN CASE OF LM DEPENDENCY]
   Function to return Load Module dependencies (tuple)
   - example: if this module uses LM_rgb.py, you should
   				 return 'rgb'
   """
	return '<module_name>'


def pinmap():
	"""
	[OPTIONAL]
	Return list of pins
	Example:
		RoboArm $  rgb pinmap >json
		{"rgbue": 15, "rgreenb": 12, "redgb": 14}
	return: dict {pinkey: pinvalue}
	
	pinmap_dump - logical pinmap resolver based on IO_<device_tag>.py
	
	Example:
	return pinmap_dump(['redgb', 'rgreenb', 'rgbue'])
	"""
	return pinmap_dump(['redgb'])


def status(lmf=None):
	"""
	[OPTIONAL]
	Function naming convension for
	module state-machine return
	return: dict
	
	Example in case of RGB color state return
	return {'R': data[0], 'G': data[1], 'B': data[2], 'S': data[3]}
	"""
	return {'key': 'value'}


def help():
	"""
	[OPTIONAL]
	Return help message tuple
	"""
	return 'load_n_init', 'pinmap', 'status', 'lmdep'
```


## micrOS Common module

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
	

def help():
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

### rest\_endpoint(endpoint, function):

Add custom endpint `<localhost.local>/endpoint` from Load Modules to WebCli html server.

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
from Common import rest_endpoint

def load_n_init():
	...
	rest_endpoint('my_endpoint', _response)
	return "Endpoint was created: http://localhost/my_endpoint"

def _response():
	reply = "hello world"
	return 'text/plain', reply
```

Usage(s): [LM_OV2640](./micrOS/source/LM_OV2640.py)

