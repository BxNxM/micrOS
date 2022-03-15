# Profile configs schemas

## Idea

Profiles contains subset of node_config.json.
That config subset can contains 2 types of values:

- Value to inject, for example `int / float / string /bool`
  - These kind of values will be injected automatically to the newly generated config file. 
- null values (None in python)
  - Indicates user input query - auto deployment script will ask the parameter values from the user (command line)
  
## Value types

- The default config key's values are the responsible for the right config argument types.


## Available profiles

**`default_profile-node_config.json`**

> The most lightweight option, only runs the Socket Shell interface.
> 
> - Interrupts: OFF (no memory allocation)
> - Preloaded modules: OFF
> - Network up and running + communication interface ONLY.

Example commands: `default_profile_command_examples.txt`

**`heartbeat_profile-node_config.json`**

> Beep function - flashing light feedback, minimal setup also.
> 
> - Interrupts:
>  - Timer interrupt: ON
>  - External/Event interrupt: OFF 
> - Preloaded modules: OFF
> - Network up and running + communication interface active.

Example commands: `heartbeat_profile_command_examples.txt`

**`lamp_profile-node_config.json`**

> Smart RGB Lamp app with button. 
> 
> - Interrupts:
>  - Timer interrupt: ON - heartbeat feedback led
>  - External/Event interrupt: Button - push detection - toggle led state 
> - Preloaded modules: RGB LED (gpio) setup
> - Network up and running + communication interface active.

Example commands: `lamp_profile_command_examples.txt`

**`catgame_profile-node_config.json`**

> Servo based interactive cat toy
> 
> - Interrupts:
>  - Timer interrupt: ON
>  - External/Event interrupt: OFF
> - Preloaded modules: OFF
> - Network up and running + communication interface active.

Example commands: `catgame_profile_command_examples.txt`
