# Trad Rack Configuration reference

This document is modeled after Klipper's
[Config Reference document](https://www.klipper3d.org/Config_Reference.html)
but only contains items pertaining to Trad Rack.

**Table of Contents**
- [Main configuration](#main-configuration)
  - [\[trad\_rack\]](#trad_rack)
- [Additional sections](#additional-sections)
  - [\[stepper\_tr\_selector\]](#stepper_tr_selector)
  - [\[stepper\_tr\_fil\_driver\]](#stepper_tr_fil_driver)
  - [\[tmc2209 stepper\_tr\_selector\]](#tmc2209-stepper_tr_selector)
  - [\[tmc2209 stepper\_tr\_fil\_driver\]](#tmc2209-stepper_tr_fil_driver)
  - [\[servo tr\_servo\]](#servo-tr_servo)

## Main configuration

### [trad_rack]

Main configuration section for Trad Rack. Some config options
reference [Tuning.md](/docs/Tuning.md) for more details.
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
#filament_max_accel: 1500.0
#   Maximum acceleration (in mm/s^2) for filament movement.
#   The default is 1500.0.
toolhead_fil_sensor_pin:
#   The pin on which the toolhead filament sensor is connected.
#   If a pin is not specified, no toolhead filament sensor will 
#   be used.
lane_count:
#   The number of filament lanes. This parameter must be specified.
lane_spacing:
#   Spacing (in mm) between filament lanes. 
#   This parameter must be specified.
#lane_offset_<lane index>:
#   Options with a "lane_offset_" prefix may be specified for any of
#   the lanes (from 0 to lane_count - 1). The option will apply an
#   offset (in mm) to the corresponding lane's position. Lane offsets
#   do not affect the position of any lanes besides the one specified
#   in the option name. This option is intended for fine adjustment
#   of each lane's position to ensure that the filament paths in the
#   lane module and selector line up with each other.
#   The default is 0.0 for each lane.
#lane_spacing_mod_<lane index>:
#   Options with a "lane_spacing_mod_" prefix may be specified for any
#   of the lanes (from 0 to lane_count - 1). The option will apply an
#   offset (in mm) to the corresponding lane's position, as well as
#   any lane with a higher index. For example, if lane_spacing_mod_2
#   is 4.0, any lane with an index of 2 or above will have its
#   position increased by 4.0. This option is intended to account for
#   variations in a lane module that will affect its position as well
#   as the positions of any subsequent modules with a higher index.
#   The default is 0.0 for each lane.
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
#   and back into the lane module after the selector sensor has been
#   triggered or untriggered. This parameter must be specified.
#selector_unload_length_extra: 0.0
#   Extra length (in mm) that is added to selector_unload_length when
#   retracting a piece of filament out of the selector and back into
#   the lane module. After the retraction, the filament is moved
#   forward by this length as well (so this option's value has no
#   effect on the final position of the filament). This option may be
#   useful when using Trad Rack with a motorized spool rewinder that
#   senses tension or compression in the filament between the spool
#   and Trad Rack in order to determine when to rotate the spool. The
#   extra forward movement of the filament after retracting is
#   intended to force the rewinder's sensor to detect tension in the
#   filament, causing rewinding to cease immediately so the filament
#   tip is not moved out of position by excess spool movement. The
#   default is 0.0.
#eject_length: 10.0
#   Length (in mm) to eject the filament into the lane module past the
#   length defined by selector_unload_length. The filament is ejected
#   whenever unloading a depleted spool after a runout to make sure
#   that filament segment is not loaded again until it has been
#   replaced.
bowden_length:
#   Length (in mm) to quickly move filament through the bowden tube
#   between Trad Rack and the toolhead during loads and unloads.
#   See Tuning.md for details. This parameter must be specified.
extruder_load_length:
#   Length (in mm) to move filament into the extruder when loading the
#   toolhead. See Tuning.md for details.
#   This parameter must be specified.
hotend_load_length:
#   Length (in mm) to move filament into the hotend when loading the
#   toolhead. See Tuning.md for details.
#   This parameter must be specified.
toolhead_unload_length:
#   Length (in mm) to move filament out of the toolhead during an
#   unload. See Tuning.md for details. If toolhead_fil_sensor_pin is
#   specified, this parameter must be specified.
#   If toolhead_fil_sensor_pin is not specified, the default is
#   extruder_load_length + hotend_load_length.
#selector_sense_speed: 40.0
#   Speed (in mm/s) when moving filament until the selector
#   sensor is triggered or untriggered. See Tuning.md for details
#   on when this speed is applied. The default is 40.0.
#selector_unload_speed: 60.0
#   Speed (in mm/s) to move filament when unloading the selector.
#   The default is 60.0.
#eject_speed: 80.0
#   Speed (in mm/s) to move the filament when ejecting a filament
#   segment into the lane module.
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
#fil_homing_retract_dist: 20.0
#   Distance (in mm) to retract filament away from a filament sensor
#   before moving on to the next move. This retraction occurs whenever
#   a filament sensor is triggered early during a fast move through
#   the bowden tube. See Tuning.md for details. The default is 20.0.
#target_toolhead_homing_dist:
#   Target filament travel distance (in mm) when homing to the
#   toolhead filament sensor during a load. See Tuning.md for details.
#   Defaults to either 10.0 or toolhead_unload_length, whichever is
#   greater.
#target_selector_homing_dist:
#   Target filament travel distance (in mm) when homing to the
#   selector filament sensor during an unload. See Tuning.md for
#   details. The default is 10.0.
#bowden_length_samples: 10
#   Maximum number of samples that are averaged to set bowden lengths
#   for loading and unloading. See Tuning.md for details. The default
#   is 10.
#load_lane_time: 15
#   Approximate maximum time (in seconds) to wait for filament to
#   reach the selector filament sensor when loading a lane with the
#   TR_LOAD_LANE gcode command. This time starts when the user is
#   prompted to insert filament and determines when the command will
#   be halted early if no filament is detected. The default is 15.
#load_selector_homing_dist:
#   Maximum distance to try to move filament when loading from a lane
#   module to the selector filament sensor before halting the homing
#   move. This value is not used by the TR_LOAD_LANE command but is
#   used in similar scenarios that do not involve user interaction.
#   Defaults to selector_unload_length * 2.
#bowden_load_homing_dist:
#   Maximum distance to try to move filament near the end of a
#   toolhead load (during the slow homing move to the toolhead sensor)
#   before halting the homing move. Defaults to bowden_length.
#bowden_unload_homing_dist:
#   Maximum distance to try to move filament near the end of a
#   toolhead unload (during the slow homing move to the selector
#   sensor) before halting the homing move. Defaults to bowden_length.
#unload_toolhead_homing_dist:
#   Maximum distance to try to move filament near the beginning of a
#   toolhead unload (during the homing move to the toolhead sensor)
#   before halting the homing move.
#   Defaults to (extruder_load_length + hotend_load_length) * 2.
#sync_to_extruder: False
#   Syncs Trad Rack's filament driver to the extruder during printing,
#   as well as during any extrusion moves within toolhead loading or
#   unloading that would normally involve only the extruder.
#   The default is False.
#user_wait_time: 15
#   Time (in seconds) to wait for the user to take an action
#   before continuing automatically. If set to -1, Trad Rack will wait
#   for the user indefinitely. This value is currently used by the
#   TR_LOCATE_SELECTOR gcode command. The default is 15.
#register_toolchange_commands: True
#   Whether to register gcode commands T0, T1, T2, etc. so that they
#   can be used to initiate toolchanges with Trad Rack. If set to
#   False, the TR_LOAD_TOOLHEAD command can still be used as a
#   substitute to initiate toolchanges. The default is True.
#save_active_lane: True
#   Whether to save the active lane to disk whenever it is set using
#   save_variables. If set to True, the TR_LOCATE_SELECTOR gcode
#   command will infer the active lane if the selector filament sensor
#   is triggered and an active lane was saved previously.
#   The default is True.
#log_bowden_lengths: False
#   Whether to log bowden load length data and bowden unload length
#   data (to ~/bowden_load_lengths.csv and ~/bowden_unload_lengths.csv
#   respectively). The default is False.
#pre_unload_gcode:
#   Gcode command template that is run before the toolhead is
#   unloaded. The default is to run no extra commands.
#post_unload_gcode:
#   Gcode command template that is run after the toolhead is
#   unloaded. The default is to run no extra commands.
#pre_load_gcode:
#   Gcode command template that is run before the toolhead is
#   loaded. The default is to run no extra commands.
#post_load_gcode:
#   Gcode command template that is run after the toolhead is
#   loaded. The default is to run no extra commands.
#pause_gcode:
#   Gcode command template that is run whenever Trad Rack needs to
#   pause the print (usually due to a failed load or unload). The
#   default is to run the PAUSE gcode command.
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
