# Trad Rack Configuration reference

This document is modeled after Klipper's
[Config Reference](https://www.klipper3d.org/Config_Reference.html)
document but only contains items pertaining to Trad Rack.
## Main configuration

### [trad_rack]

Main configuration section for Trad Rack.
```
[trad_rack]
selector_max_velocity:
#   Maximum velocity (in mm/s) of the selector. 
#   This parameter must be specified.
selector_max_accel:
#   Maximum acceleration (in mm/s^2) of the selector. 
#   This parameter must be specified.
#filament_max_velocity:
#   Maximum velocity (in mm/s) for filament movement. 
#   Defaults to buffer_pull_speed.
#filament_max_accel:
#   Maximum acceleration (in mm/s^2) for filament movement.
#   Defaults to max_extrude_only_accel from the [extruder] section.
toolhead_fil_sensor_pin:
#   The pin on which the toolhead filament sensor is connected.
#   If a pin is not specified, no toolhead filament sensor will 
#   be used.
lane_count:
#   The number of filament lanes. This parameter must be specified.
lane_spacing:
#   Spacing (in mm) between filament lanes. 
#   This parameter must be specified.
#lane_offsets:
#   Comma-separated list of offsets (in mm) to apply to each 
#   lane position. After a lane position is calculated from the
#   lane's index and lane_spacing, the offset for that lane is added.
#   For example, if lane_spacing is 17.0 and the 2nd number in
#   lane_offsets is 0.1, the position of the selector at lane 1 will
#   be 1 * 17.0 + 0.1 = 17.1. The default is 0.0 for each lane.
servo_down_angle:
#   The angle (in degrees) for the servo's down position.
#   This parameter must be specified.
servo_up_angle:
#   The angle (in degrees) for the servo's up position.
#   This parameter must be specified.
#servo_wait_ms: 500
#   Time (in milliseconds) to wait for the servo to complete moves
#   between the up and down angles. The default is 500.
selector_unload_length:
#   Length (in mm) to retract a piece of filament out of the selector
#   and back into the module after the selector sensor has been
#   triggered or untriggered. This parameter must be specified.
bowden_length:
#   Length (in mm) to quickly move filament through the bowden tube
#   between Trad Rack and the toolhead during loads and unloads.
#   This parameter must be specified.
extruder_load_length:
#   Length (in mm) to move filament into the extruder when loading the
#   toolhead. See Tuning.md for details.
#   This parameter must be specified.
hotend_load_length:
#   Length (im mm) to move filament into the hotend when loading the
#   toolhead. See Tuning.md for details.
#   This parameter must be specified.
toolhead_unload_length:
#   Length (in mm) to move filament out of the toolhead during an
#   unload. See Tuning.md for details. If toolhead_fil_sensor_pin is
#   specified, this parameter must be specified.
#   If toolhead_fil_sensor_pin is not specified, the default is
#   extruder_load_length + hotend_load_length.
#bowden_unload_modifier: 0.0
#   Length modifier (in mm) for moving filament through the bowden
#   tube between Trad Rack and the toolhead during unloads.
#   See Tuning.md for details. The default is 0.0.
#selector_sense_speed: 40.0
#   Speed (in mm/s) when moving filament until the selector
#   sensor is triggered or untriggered. See Tuning.md for details
#   on when this speed is applied. The default is 40.0.
#selector_unload_speed: 60.0
#   Speed (in mm/s) to move filament when unloading the selector.
#   The default is 60.0.
#spool_pull_speed: 100.0
#   Speed (in mm/s) to move filament through the bowden tube when
#   loading from a spool. See Tuning.md for details. 
#   The default is 100.0.
#buffer_pull_speed:
#   Speed (in mm/s) to move filament through the bowden tube when
#   unloading or loading from a buffer. See Tuning.md for details.
#   Defaults to spool_pull_speed.
#toolhead_sense_speed:
#   Speed (in mm/s) when moving filament until the toolhead
#   sensor is triggered or untriggered. See Tuning.md for details on
#   when this speed is applied. Defaults to selector_sense_speed.
#extruder_load_speed:
#   Speed (in mm/s) to move filament into the extruder when loading
#   the toolhead. See Tuning.md for details. The default is 60.0.
#hotend_load_speed:
#   Speed (in mm/s) to move filament into the hotend when loading the
#   toolhead. See Tuning.md for details. The default is 7.0.
#toolhead_unload_speed:
#   Speed (in mm/s) to move filament when unloading the toolhead.
#   See Tuning.md for details. Defaults to extruder_load_speed.
#load_with_toolhead_sensor: True
#   Whether to use the toolhead sensor when loading the toolhead.
#   See Tuning.md for details. Defaults to True but is ignored if
#   toolhead_fil_sensor_pin is not specified. 
#unload_with_toolhead_sensor: True
#   Whether to use the toolhead sensor when unloading the toolhead.
#   See Tuning.md for details. Defaults to True but is ignored if
#   toolhead_fil_sensor_pin is not specified.
#pre_unload_gcode:
#   Gcode command template that is run before the toolhead is
#   unloaded. The default is to run no extra commands.
#post_toolchange_gcode:
#   Gcode command template that is run after the toolhead is
#   loaded. The default is to run no extra commands.
#pause_gcode:
#   Gcode command template that is run whenever Trad Rack needs to
#   pause the print due to a failed load or unload. The default is to
#   run the PAUSE gcode command.
#resume_gcode:
#   Gcode command template that is run whenever the TR_RESUME command
#   needs to resume the print. The default is to run the RESUME
#   gcode command.
```

## Additional sections

### [stepper_tr_selector]

Section for the stepper that moves the selector between lanes.

```
[stepper_tr_selector]
step_pin:
dir_pin:
enable_pin:
rotation_distance:
microsteps:
full_steps_per_rotation:
endstop_pin:
position_min:
position_endstop:
position_max:
#   This should be set to (lane_count - 1) * lane_spacing.
homing_speed:
#   See the "stepper" section in Klipper's Config_Reference.md
#   document for a description of the above parameters.
```

### [stepper_tr_fil_driver]

Section for the stepper that moves filament.

```
[stepper_tr_fil_driver]
step_pin:
dir_pin:
enable_pin:
rotation_distance:
gear_ratio:
microsteps:
full_steps_per_rotation:
endstop_pin:
position_min:
#   This should be set to a large negative number with an absolute
#   value greater than the length of the bowden tube between Trad Rack
#   and the toolhead.
position_endstop: 0
position_max:
#   This should be set to a large positive number greater than the
#   length of the bowden tube between Trad Rack and the toolhead.
homing_positive_dir: False
#   See the "[stepper]" section in Klipper's Config_Reference.md
#   document for a description of the above parameters.
```

### [tmc2209 stepper_tr_selector]

Stepper driver section for stepper_tr_selector.

```
[tmc2209 stepper_tr_selector]
uart_pin:
run_current:
sense_resistor:
#   See the "[tmc_2209]" section in Klipper's Config_Reference.md
#   document for a description of the above parameters. You may have
#   to use a different section name if you use a different driver.
```

### [tmc2209 stepper_tr_fil_driver]

Stepper driver section for stepper_tr_fil_driver.

```
[tmc2209 stepper_tr_selector]
uart_pin:
run_current:
sense_resistor:
#   See the "[tmc_2209]" section in Klipper's Config_Reference.md
#   document for a description of the above parameters. You may have
#   to use a different section name if you use a different driver.
```

### [servo tr_servo]

Section for the servo that moves the drive gear up and down.

```
[servo tr_servo]
pin:
maximum_servo_angle:
minimum_pulse_width:
maximum_pulse_width:
#   See the "[servo]" section in Klipper's Config_Reference.md
#   document for a description of the above parameters.
```
