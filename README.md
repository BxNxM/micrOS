# MicrOS - IOT

![esp8266pinout](https://github.com/BxNxM/MicrOs/blob/master/media/ESP8266-NodeMCU-kit-12-E-pinout-gpio-pin.png?raw=true)

Esp8266 Micropython based - APPlication Core - with -
User function injection over LM_<userapp>.py 

- [ **DONE** ] Main block “thread” - rest api socket server
	- [ **DONE** ] command "shell" terminal - config handling - LoadModule ->command invocation
- [ **DONE** ] Configuration management - json based
	- split / subconfig handling ? - load optimization
- [ **DONE** ] Network autoconfiguration - STA - AP fallback
	- [ **DONE** ] AP mode add WPA encription
- [ **DONE** ] PM modul import optimization
- [ **DONE** ] Timer interrupts - async program execution - display refresh / heartbeat led / etc.? 
	- https://docs.micropython.org/en/latest/library/machine.Timer.html
- [ **DONE** ] Button (GPIO) interrupt - event handling
- [ **DONE** ] Precompile py -> mpy modules - mpy-cross compiler
	- [ **DONE** ] precompile flow automatization

> Note:
To remove ^M after get source files from nodemcu in vim:
:%s/ <press^V^M> //g

## Quick guide

#### Dependences

- **Deploy** dependences
	- esptool.py
	- ampy 

- **Connection** dependences
	- screen
	- telnet

#### Source devenv (bash)

```
source setup
```

#### Deploy micropython

```
nodemcu_erase; nodemcu deploy
```

#### Put resorces to nodemcu

```
nodemcu_put_all
```

## Socket terminal example

### Connect device

```
╰─➤  telnet <deviceIP> <devicePORT>
Trying <deviceIP>...
Connected to <deviceIP>.
Escape character is '^]'.
```

### Identify device

```
>>>  hello
hello:slim01:0x600x10x940x1f0x7e0xfa
```

### Get help

```
slim01 $  help
hello - default hello msg - identify device (SocketServer)
exit  - exit from shell socket prompt (SocketServer)
Configure mode:
   configure|conf     - Enter conf mode
         Key          - Get value
         Key:Value    - Set value
         dump         - Dump all data
   noconfigure|noconf - Exit conf mod
Command mode:
   oled_128x64i2c
                 invert
                 text
                 poweroff
                 poweron
                 show_debug_page
                 wakeup_oled_debug_page_execute
                 clean
                 draw_line
                 draw_rect
   commands
           listdir
           time
           memfree
           gccollect
           reboot
           wifirssi
           addnumbs
```
 
### Embedded config handler
 
```  
slim01 $  conf                        
[configure] slim01 $  dump
{'stapwd': '<your_wifi_password>', 'gmttime': 1, 'nwmd': 'STA', 'soctout': 100, 'timirq': True, 'appwd': 'ADmin123', 'devfid': 'slim01', 'extirq': True, 'dbg': True, 'devip': '10.0.1.6', 'hwuid': '0x600x10x940x1f0x7e0xfa', 'staessid': '<your_wifi_name>', 'socport': 9008, 'pled': True}
[configure] slim01 $  noconf
```

### Load Modules - User defined functions

```
slim01 $  commands memfree
CPU[Hz]: 160000000
GC MemFree[byte]: 6080
slim01 $  commands addnumbs(1,2,3,4)
1+2+3+4 = 10
slim01 $  exit
Bye!
exit and close connection from ('10.0.1.7', 53069)
Connection closed by foreign host.
```

## Node Configuration

| Parameters | Description |
| :----------: | ----------- |
| staessid   | 	Wifi station name 
| stapwd		| Wifi station password
| devfid		| Device friendly name / AP name - access point mode
| appwd		| AP password - access point mode
| pled			| Progress led - heart beat
| dbg	       |    	Debug mode - enable printouts and debug activities (oled)		
| soctout		| Socket / Web server connection timeout (because single user | handling)
| socport		| Socket / Web server service port
| timirg		| Timer interrupt enable - "subprocess" - function callback
| extirq     | External event interrupt - "subprocess" - function callback
| gmttime    | NTP - RTC - timezone setup 
| nwmd 		| STATE STORAGE - system saves nw mode here - AP / STA
| hwuid		| STATE STORAGE - hardwer address - dev uid
| devip		| STATE STORAGE - system stores device ip here


git push -u origin master
