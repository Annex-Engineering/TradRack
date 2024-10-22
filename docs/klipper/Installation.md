# Installation

This document lists the steps to get Trad Rack set up to work with
Klipper.

**Table of Contents**
- [Klippy module](#klippy-module)
  - [Klippy module installation](#klippy-module-installation)
  - [Enabling Moonraker updates](#enabling-moonraker-updates)
- [Config files](#config-files)
  - [Preliminary changes](#preliminary-changes)
    - [\[idle\_timeout\]](#idle_timeout)
    - [\[save\_variables\]](#save_variables)
  - [Using provided config files](#using-provided-config-files)
  - [Modifying provided config files for a different board](#modifying-provided-config-files-for-a-different-board)
  - [Building a config from scratch](#building-a-config-from-scratch)

## Klippy module

This section involves adding the Trad Rack Klippy module(s) to Klipper
and enabling updates through Moonraker.

If you are using
[Danger Klipper](https://github.com/DangerKlippers/danger-klipper),
you can skip to [setting up config files](#config-files) since
Danger Klipper already includes the trad_rack module.

The installation procedure differs slightly depending on whether
you are using a recent version of Klipper or an older version from
before
[commit bafb126](https://github.com/Klipper3d/klipper/commit/bafb126abd77edd0cb2e5ae3b5d99ff83272594c).

For parts of the installation procedure that differ depending on the
version of Klipper you are using, there will be an "Old" dropdown
below the commands/text that you would use with a recent
installation. In such cases, if you are using an old version of
Klipper from before commit bafb126, use the commands/text in the
dropdown instead of what is directly above.

### Klippy module installation

Run the following commands to download and install the Klippy
module(s):

```
cd ~
curl -LJO https://raw.githubusercontent.com/Annex-Engineering/TradRack/main/Klipper_Stuff/klippy_module/install.sh
chmod +x install.sh
./install.sh
```
<details>
  <summary>Old</summary>
  
  ```
  cd ~
  curl -LJO https://raw.githubusercontent.com/Annex-Engineering/TradRack/main/Klipper_Stuff/klippy_module/install.sh
  chmod +x install.sh
  ./install.sh pre_toolhead_changes
  ```
</details>

Then remove the install script with the following command:

```
rm install.sh
```

Finally, restart the klipper service using the following command:

```
sudo systemctl restart klipper
```

> [!TIP]
> If you ever need to run the install script again in the future (for
> example if additional Klippy modules get added), you can do so
> without recreating the `trad_rack_klippy_module` directory using the
> following commands:
> ```
> cd ~
> ./trad_rack_klippy_module/Klipper_Stuff/klippy_module/install.sh <branch_name>
> ```
> If unspecified, `branch_name` defaults to `main`.

### Enabling Moonraker updates

To enable updates of the Trad Rack Klippy module(s) through Moonraker,
add the following to your `moonraker.conf` file. This file is usually
located in `~/printer_data/config/`:

```
[update_manager trad_rack]
type: git_repo
path: ~/trad_rack_klippy_module
origin: https://github.com/Annex-Engineering/TradRack.git
primary_branch: main
managed_services: klipper
```
<details>
  <summary>Old</summary>

  ```
  [update_manager trad_rack]
  type: git_repo
  path: ~/trad_rack_klippy_module
  origin: https://github.com/Annex-Engineering/TradRack.git
  primary_branch: pre_toolhead_changes
  managed_services: klipper
  ```
</details>

Then restart the moonraker service using the following command:

```
sudo systemctl restart moonraker
```

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
