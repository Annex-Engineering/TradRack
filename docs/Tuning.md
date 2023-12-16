# Tuning

This document provides an overview of the loading and unloading
processes and how to tune them.

**Table of Contents**
- [Loading process](#loading-process)
- [Unloading process](#unloading-process)
- [Tuning lengths](#tuning-lengths)
  - [Bowden length](#bowden-length)
  - [Toolhead-specific lengths](#toolhead-specific-lengths)
- [Bowden lengths](#bowden-lengths)
  - [Relevant config options](#relevant-config-options)
  - [How calibration works](#how-calibration-works)
  - [Saving and restoring bowden lengths](#saving-and-restoring-bowden-lengths)
- [Bowden speeds](#bowden-speeds)

## Loading process

The following table shows the actions taken in sequential order when
loading filament from Trad Rack into the toolhead, as well as some
details about each action: distance of each move, speed of the move,
whether Trad Rack's filament driver motor is involved, and whether the
printer's main extruder is involved.

| Description                 | Distance (mm)                           | Speed (mm\s)                        | Trad Rack filament driver | Main extruder       |
| ---                         | ---                                     | ---                                 | ---                       | ---                 |
| move through bowden tube    | ["bowden_load_length"](#bowden-lengths) | see [bowden speeds](#bowden-speeds) | :white_check_mark:        | :x:                 |
| toolhead sensor homing[^1]  | until sensor triggers[^2]               | `toolhead_sense_speed`              | :white_check_mark:        | :white_check_mark:  |
| load extruder               | `extruder_load_length`                  | `extruder_load_speed`               | :white_check_mark:        | :white_check_mark:  |
| load hotend                 | `hotend_load_length`                    | `hotend_load_speed`                 | :white_check_mark:[^3]    | :white_check_mark:  |

[^1]: This move only occurs if `toolhead_fil_sensor_pin` is specified
and `load_with_toolhead_sensor` is True.

[^2]: The maximum length of this move is defined by
`bowden_load_homing_dist`. If the sensor is still not triggered after
Trad Rack supposedly moved the filament this distance, the load will
be halted and the print will be paused.

[^3]: The servo will start disengaging Trad Rack's drive gear 
`servo_wait_ms` before the move ends, unless `sync_to_extruder` is
True (in which case the drive gear will stay engaged).

## Unloading process

The following table shows which actions are taken when unloading
filament from the toolhead back into Trad Rack.

| Description                 | Distance (mm)                             | Speed (mm/s)            | Trad Rack filament driver | Main extruder       |
| ---                         | ---                                       | ---                     | ---                       | ---                 |
| toolhead sensor homing[^4]  | until sensor is untriggered[^5]           | `toolhead_sense_speed`  | :white_check_mark:        | :white_check_mark:  |
| unload toolhead             | `toolhead_unload_length`                  | `toolhead_unload_speed` | :white_check_mark:        | :white_check_mark:  |
| move through bowden tube    | ["bowden_unload_length"](#bowden-lengths) | `buffer_pull_speed`     | :white_check_mark:        | :x:                 |
| selector sensor homing      | until sensor is untriggered               | `selector_sense_speed`  | :white_check_mark:        | :x:                 |

[^4]: This move only occurs if `toolhead_fil_sensor_pin` is specified
and `unload_with_toolhead_sensor` is True.

[^5]: The maximum length of this move is defined by
`bowden_unload_homing_dist`. If the sensor is still triggered after
Trad Rack supposedly moved the filament this distance, the unload will
be halted and the print will be paused.

## Tuning lengths

The following lengths must be tuned to match your bowden tube,
extruder, toolhead, and toolhead sensor setup. The values in the
provided config file have been tuned for an Annex K3 toolhead running
a Sherpa Micro extruder (with a sensor detecting its idler arm
movement) and a Mosquito Magnum hotend.

### Bowden length

- `bowden_length` (mm): 
  - If you are using a toolhead filament sensor
    (`toolhead_fil_sensor_pin` is specified and
    `load_with_toolhead_sensor` is True):
    - You can set this to any value that is greater than half the
      actual length of the bowden tube between Trad Rack and the
      toolhead but less than the full actual length. Knowing the
      actual length precisely is not necessary because the bowden load
      and unload lengths will be calibrated automatically (see
      [bowden lengths](#bowden-lengths) for details).
  - Else:
    - This value should be slightly smaller than the
      length of the bowden tube between Trad Rack and your toolhead.
      This length should be tuned to bring the filament tip almost all
      the way to the extruder drive gears, starting from the point where
      Trad Rack's selector filament sensor is triggered. Make sure there
      is some distance between the filament tip and the drive gears for
      safety.

### Toolhead-specific lengths

- `extruder_load_length` (mm): this length should be tuned to bring
  the filament tip from the point where the toolhead sensor is
  triggered to a point slightly above the heatbreak throat. You can
  base this length off of measurements of your toolhead from CAD. If
  you are not using a toolhead sensor, then the position of the
  filament tip after moving through the bowden tube would be your
  starting point.
- `hotend_load_length` (mm): this length is meant to bring the
  filament tip from the ending point of `extruder_load_length` to a
  point inside the meltzone so it is ready for printing. You may
  have to tune this parameter through trial and error to avoid extra
  oozing during loading or gaps in your wipe tower.
- `toolhead_unload_length` (mm): this length is meant to bring the
  filament tip from the point where the toolhead sensor is untriggered
  to a point above the extruder gears (where the extruder gears will
  not touch the filament). If your toolhead sensor is above the
  extruder gears and you are confident that the filament will not be
  touching the extruder gears at the point where it is untriggered,
  this length can be as low as 0. If you are not using a toolhead
  sensor, the starting point of this move would be wherever the
  filament is when the toolchange command gets executed.[^6]

[^6]: If following the instructions in the Slicing document, the
starting point of this move (if you are not using a toolhead sensor)
will be the top of the "cooling tube." See the Slicing document for
more details. It is also okay to leave `toolhead_unload_length` at its
default value if you are not using a toolhead sensor; the toolchange
will just take a little longer.

See the drawings below for a visualization of the toolhead-specific
lengths on toolheads with various sensor setups. Colorful labels are
length settings, and black labels in parentheses are references that
are used to determine the starting or ending points of the length
settings.

| Sensor location             | Drawing                                         |
| ---                         | ---                                             |
| Sensor above extruder gears | ![](images/toolhead_lengths/above.png?raw=true) |
| Sensing idler arm movement  | ![](images/toolhead_lengths/idler.png?raw=true) |
| Sensor below extruder gears | ![](images/toolhead_lengths/below.png?raw=true) |

Note: the bottom point of `hotend_load_length` is not drawn to scale
and will depend on your specific hotend, tip shaping procedure, etc.

## Bowden lengths

"bowden_load_length" and "bowden_unload_length" are both initially
set to `bowden_length`, but they are each updated automatically
on every load and unload respectively.

Note: if `toolhead_fil_sensor_pin` is not specified or
`load_with_toolhead_sensor` is False, "bowden_load_length" will not be
updated automatically and will remain equal to `bowden_length`.

### Relevant config options

The following config options are relevant to the calibration of moves
through the bowden tube. See
[how calibration works](#how-calibration-works) for an explanation of
how these values are used. It is not mandatory to set these config
options; they default to safe values but may be optimized further if
you wish:

- `fil_homing_retract_dist`
- `target_toolhead_homing_dist`
- `target_selector_homing_dist`
- `bowden_length_samples`

### How calibration works

During each sensor homing move, Trad Rack keeps track of how far its
drive gear rotates until the sensor triggers. As a result, the
distance from the start of the bowden tube move to the sensor's
trigger point can be estimated. For loading, the start of this
distance is the trigger point of the selector sensor, and the end is
the trigger point of the toolhead sensor. For unloading, the start is
the filament tip's location after the toolhead is unloaded, and the
end is the trigger point of the selector sensor.

The measured distance is the sum of the length of the fast move
through the bowden tube
and the length of the slower homing move that occurs afterwards.
`target_toolhead_homing_dist` or `target_selector_homing_dist` (for
loading or unloading respectively) is subtracted from the measured
distance to calculate a value for just the fast bowden move length.
These target distance values each represent
the target length of the slower sensor homing moves that occurs after
the fast bowden move; these slower moves should have
a nonzero length to account for any variance in the filament tip
position due to factors such as springiness or bending of the
filament. In addition, `target_toolhead_homing_dist` should be large
enough that the
fast bowden move that occurs during loading does not move the
filament far enough to hit the extruder's drive gears.
"bowden_load_length" and "bowden_unload_length" are set to try to
reach these target values.

At this point, an initial value for "bowden_load_length" or
"bowden_unload_length" has been determined based solely on the last
load or unload. A moving average is then used to determine the
value that will be set and used for the next load or unload.
`bowden_length_samples` determines the max number of measurements
that are averaged to determine this value.

The calibration process repeats on every load or unload.

In case the filament reaches the sensor early during the fast bowden
move, the move will be stopped and the filament will be retracted
away from the sensor by `fil_homing_retract_dist` (mm) before continuing
on to the slower sensor homing move. This retraction move is meant to
undo any extra displacement of the filament if the filament driver motor
skips when the fast bowden move is stopped.

### Saving and restoring bowden lengths

Bowden load and unload length data is saved to disk using
[save_variables](https://www.klipper3d.org/Config_Reference.html#save_variables)
so it can be restored across restarts. The `bowden_length` config
value is only used on the initial load and unload. However, if
`bowden_length` is set to a new value and Klipper is restarted, any
saved bowden load and unload length data will be ignored and
overwritten. Setting a new `bowden_length` allows you to discard old
saved values if you make a change to your hardware setup. See the
[Save Variables document](klipper/Save_Variables.md) for more details
on how Trad Rack uses save_variables.

## Bowden speeds

There is more force required and more inertia when loading filament
when the buffer is empty than when the buffer is full: in the former
case the drive gears must rotate the spool, but in the latter case the
spool can stay stationary since all the loaded filament comes out of
the buffer. To take advantage of this, we have two separate speeds
that are used when moving filament through the bowden tube:

- `spool_pull_speed` (mm/s): this speed is used when loading from a
  lane whose buffer is assumed to be empty (usually because the lane's
  filament has not been unloaded from the toolhead previously).
- `buffer_pull_speed` (mm/s): this speed is used when unloading or
  when loading from a lane whose buffer is assumed to be full (because
  the lane's filament has been unloaded from the toolhead previously).
