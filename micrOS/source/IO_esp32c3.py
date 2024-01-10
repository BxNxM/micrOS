from micropython import const

# BUILTIN LED
builtin = const(-8)     # BUILT IN LED - progress_led,  (-) means inverted output

# ANALOG RGB + WW + CW
redgb = const(4)      # - rgb red channel [PWM]
rgreenb = const(3)    # - rgb green channel [PWM]
rgbue = const(2)      # - rgb blue channel [PWM]

wwhite = const(1)	   # - warm white [PWM]
cwhite = const(0)	   # - cold white [PWM]


# DIGITAL LED
neop = const(5)        # - neopixel OneWire bus [PWM]


# ACTUATORS
servo_1 = const(6)    # - servo(1) [PWM]
servo_2 = const(7)    # - servo(2) [PWM]

switch_1 = const(8)   # - switch(1) [simple]
switch_2 = const(9)   # - switch(2) [simple]
switch_3 = const(10)    # - switch(3) [simple]
switch_4 = const(20)    # - switch(4) [simple]

dim_1 = const(21)      # - dimmer(1) [PWM]
