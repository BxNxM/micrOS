# MicrOS 
Esp8266 Micropython based - APPlication Core - with -
User function injection over LM_<userapp>.py 

- [ **DONE** ] Main block “thread” - rest api socket server
	- [ **DONE** ] command "shell" terminal - config handling - LoadModule ->command invocation
- [ **DONE** ] Configuration management - json based
	- split / subconfig handling ? - load optimization
- [ **DONE** ] Network autoconfiguration - STA - AP fallback
	- AP mode add WPA encription	
- [ **DONE** ] PM modul import optimization
- [ **DONE** ] Timer interrupts - async program execution - display refresh / heartbeat led / etc.? 
	- https://docs.micropython.org/en/latest/library/machine.Timer.html
- Button (GPIO) interrupt - event handling
- [ **DONE** ] Precompile py -> mpy modules - mpy-cross compiler
	- precompile flow automatization

> Note:
To remove ^M after get source files from nodemcu in vim:
:%s/ <press^V^M> //g

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
>>>  help
hello - default hello msg - identify device (WebServer)
exit  - exit from shell socket prompt (WebServer)
Configure mode:
   configure|conf     - Enter conf mode
         Key          - Get value
         Key:Value    - Set value
         dump         - Dump all data
   noconfigure|noconf - Exit conf mod
Command mode:
   LM_oled_128x64i2c
                    init
                    invert
                    text
                    show_debug_page
                    wakeup_oled_debug_page_execute
                    OLED
                    DEBUG_CNT
                    clean
                    draw_line
                    draw_rect
   LM_commands
              mem_free
              wifi_rssi
              reboot
              addnumbs
```
 
### Embedded config handler
 
```                          
>>>  conf
[configure] >>>  dump
{'stapwd': 'BNM3,1415', 'devfid': 'slim01', 'appwd': 'admin', 'timirq': True, 'soctout': 100, 'pled': True, 'hwuid': '0x600x10x940x1f0x7e0xfa', 'socport': 9008, 'dbg': True, 'nwmd': 'STA', 'devip': '10.0.1.77', 'staessid': 'elektroncsakpozitivan'}
[configure] >>>  devfid
slim01
[configure] >>>  noconf
```

### Load Modules - User defined functions

```
>>>  LM_commands wifi_rssi()
('elektroncsakpozitivan', -52, 11, ('VeryGood', 3))
>>>  LM_commands  mem_free()
CPU[Hz]: 160000000
GC MemFree[byte]: 5600
>>>  LM_commands addnumbs(2020, 2, 2)
2020+2+2 = 2024
>>>  exit
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
| nwmd 		| STATE STORAGE - system saves nw mode here - AP / STA
| hwuid		| STATE STORAGE - hardwer address - dev uid
| devip		| STATE STORAGE - system stores device ip here


git push -u origin master
