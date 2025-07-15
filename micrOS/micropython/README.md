
# Micropython images - source

## Basic models

- esp32 [ESP32\_GENERIC](https://micropython.org/download/ESP32_GENERIC/)

- esp32c3 [ESP32\_GENERIC\_C3](https://micropython.org/download/ESP32_GENERIC_C3/)

- esp32s2 [ESP32\_GENERIC\_S2](https://micropython.org/download/ESP32_GENERIC_S2/)

- esp32s2-LOLIN_MINI [LOLIN\_S2\_MINI](https://micropython.org/download/LOLIN_S2_MINI/)

## Pro models

- esp32s3 [ESP32\_GENERIC\_S3](https://micropython.org/download/ESP32_GENERIC_S3/)

> esp32s3 default required flash size: 8Mb

- esp32s3\_spiram\_oct [ESP32\_GENERIC\_S3 - Octal-SPIRAM](https://micropython.org/download/ESP32_GENERIC_S3/) 

- tinypico [UM\_TINYPICO](https://micropython.org/download/UM_TINYPICO/)

- esp32cam [micropython-camera-driver
](https://github.com/lemariva/micropython-camera-driver/tree/master/firmware)

- esp32c6 [ESP32C6](https://micropython.org/download/ESP32_GENERIC_C6/)

## Experimental models

- rpi-pico-w [RPI\_PICO\_W](https://micropython.org/download/RPI_PICO_W/)

--------------------------------------------------------------------
--------------------------------------------------------------------

# Image manipulation - 4MB flash

> Support esp32s3 4Mb flash

> Default esp32s3 image flash memory (disk) requirement: 8Mb

## Issue: `ESP_ERR_FLASH_NOT_INITIALISED`

```bash
  File "inisetup.py", line 38, in setup
  File "inisetup.py", line 7, in check_bootsec
OSError: (-24579, 'ESP_ERR_FLASH_NOT_INITIALISED')
MicroPython v1.24.1 on 2024-11-29; Generic ESP32S3 module with ESP32S3
Type "help()" for more information.
```

### Fix:

```bash
pip install mp-image-tool-esp32

mp-image-tool-esp32 -f 4M --resize vfs=2M ESP32_GENERIC_S3.bin
```

| Parameter                 | Meaning                                                                            |
| ------------------------- | ---------------------------------------------------------------------------------- |
| `-f 4M`                   | Set the **total flash size** to **4 megabytes**.                                   |
| `--resize vfs=2M`         | Resize the **VFS (file system)** partition to **2 MB**.                            |
| `ESP32_GENERIC_S3-...bin` | Input file: a MicroPython binary image targeting ESP32-S3 (default for 8MB flash). |
