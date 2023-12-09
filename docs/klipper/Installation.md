# Installation

This document lists the steps to get Trad Rack set up to work with
Klipper.

**Table of Contents**
- [Klippy module](#klippy-module)
- [Config files](#config-files)
  - [Preliminary changes](#preliminary-changes)
    - [\[idle\_timeout\]](#idle_timeout)
    - [\[save\_variables\]](#save_variables)
  - [Using provided config files](#using-provided-config-files)
  - [Modifying provided config files for a different board](#modifying-provided-config-files-for-a-different-board)
  - [Building a config from scratch](#building-a-config-from-scratch)

## Klippy module

Place [trad_rack.py](/Klipper_Stuff/klippy_module/trad_rack.py)
in `~/klipper/klippy/extras` and restart the Klipper service to load
the module.

Note: if you are using an older version of Klipper before
[commit bafb126](https://github.com/Klipper3d/klipper/commit/bafb126abd77edd0cb2e5ae3b5d99ff83272594c), you will need to use
[this older version of trad_rack.py](https://github.com/Annex-Engineering-Trad-Rack-Test/TradRack_Beta/blob/cd5385d536fbfd0bd46d850f5da289858e9c73f8/Klipper_Stuff/klippy_module/trad_rack.py)
instead due to changes to the Toolhead class.

## Config files

Complete the following changes/additions to your Klipper config:

### Preliminary changes

The following preliminary changes should be made to your existing
config file(s):

#### [idle_timeout]

It is recommended to modify the [idle_timeout] section to prevent
the printer from disabling the heaters and motors if the printer is
paused. Add the following to your config file or modify `gcode` if the
[idle_timeout] section is already there:

```ini
[idle_timeout]
# only turn off heaters and motors if the printer is not paused
gcode:
    {% if not printer.pause_resume.is_paused %}
        TURN_OFF_HEATERS
        M84
    {% endif %}
```

#### [save_variables]

The [save_variables] config section is required. 
See the [Klipper config reference document](https://www.klipper3d.org/Config_Reference.html#save_variables) for details on how to add this section.

### Using provided config files

Copy the following files into your Klipper config folder and
[include them](https://www.klipper3d.org/Config_Reference.html#include)
in your main printer config file:

- One of the files from the
  [base_config_options folder](/Klipper_Stuff/klipper_config/base_config_options/):
  base config file. Several options are provided for different boards
  or stepper drivers. This file is required. Make sure to complete the
  following changes:
  - [mcu tr] section
    - Replace `serial` with the serial for your board.
      See Klipper's 
      [Installation document](https://www.klipper3d.org/Installation.html)
      if you need help finding this value.
  - [trad_rack] section
    - Change `toolhead_fil_sensor_pin` to match the pin you are using
    for your toolhead filament sensor.
    - Change `lane_count` to match your Trad Rack.
    - Change the following values to suit your setup. See the 
      [Tuning document](/docs/Tuning.md) for more details:
        - `bowden_length`
        - `extruder_load_length`
        - `hotend_load_length`
        - `toolhead_unload_length`
  - [stepper_tr_selector] section
    - Change `position_max` accordingly depending on your 
      `lane_count`, using the formula in the config file.
  - [tmc2209 stepper_tr_selector] or [tmc5160 stepper_tr_selector]
    section
    - Change `run_current` to match your selector motor.
  - [tmc2209 stepper_tr_fil_driver] or [tmc5160 stepper_tr_fil_driver]
    section
    - Change `run_current` to match your filament driver motor.
- [trad_rack_optional.cfg](/Klipper_Stuff/klipper_config/trad_rack_optional.cfg):
  optional config file. It is highly recommended to include this file
  (see the [Customization document](Customization.md) for more
  details).

### Modifying provided config files for a different board

Follow the instructions in
[using provided config files](#using-provided-config-files). In
addition, modify every "pin" or "uart_address" setting in
the base config file to match your board: copy each of these settings
from a corresponding section in the
[example Klipper config for your board](https://github.com/Klipper3d/klipper/tree/master/config). Some settings such as `tx_pin` or `uart_address` might
not be needed.

### Building a config from scratch

See the [Config Reference document](Config_Reference.md) for the
required configuration sections and parameters for Trad Rack.
