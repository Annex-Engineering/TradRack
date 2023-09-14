# Installation

This document lists the steps to get Trad Rack set up to work with
Klipper.

## Klippy module

Place [trad_rack.py](/Klipper_Stuff/klippy_module/trad_rack.py)
in `~/klipper/klippy/extras` and restart the Klipper service to load
the module.

## Config files

### Preliminary changes

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


The [save_variables] config section is required. 
See the [Klipper config reference document](https://www.klipper3d.org/Config_Reference.html#save_variables) for details on how to add this section.

### Using provided config files

Place the following files inside your Klipper config folder and
[include them](https://www.klipper3d.org/Config_Reference.html#include)
in your main printer config file:

- Either
  [trad_rack_nebula_2209.cfg](/Klipper_Stuff/klipper_config/trad_rack_nebula_2209.cfg),
  [trad_rack_nebula_5160.cfg](/Klipper_Stuff/klipper_config/trad_rack_nebula_5160.cfg),
  or [trad_rack_skr_pico.cfg](/Klipper_Stuff/klipper_config/trad_rack_skr_pico.cfg):
  base config file. This file is required. Make sure to complete the
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
  optional config file. This file is recommended but may be more or
  less useful depending on your slicer setup.

### Modifying provided config files for a different board

Follow the instructions in
[using provided config files](#using-provided-config-files). In
addition, modify every "pin" or "uart_address" setting in
[trad_rack_skr_pico.cfg](/Klipper_Stuff/klipper_config/trad_rack_skr_pico.cfg)
to match your board; copy each of these settings from a corresponding
section in the
[example Klipper config for your board](https://github.com/Klipper3d/klipper/tree/master/config). Some settings such as `tx_pin` or `uart_address` might
not be needed.

### Building a config from scratch

See the [Config Reference document](Config_Reference.md) for the
required configuration sections and parameters for Trad Rack.
