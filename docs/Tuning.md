# Tuning

This document provides an overview of the loading and unloading
processes and how to tune them.

## Loading process

The following table shows which actions are taken when loading
filament to the toolhead from Trad Rack, going from the top of the
table to the bottom, as well as some details about each action:
distance of each move, speed of the move, whether Trad Rack's filament
driver motor is involved, and whether the main extruder is involved.

| Description               | Distance (mm)         | Speed (mm\s)                        | Trad Rack filament driver | Main extruder |
| ---                       | ---                   | ---                                 | ---                       | ---           |
| move through bowden tube  | `bowden_length`       | see [bowden speeds](#bowden-speeds) | y                         | n             |
| toolhead sensor homing*   | until sensor triggers | `toolhead_sense_speed`              | y                         | y             |
| load extruder             | `extruder_load_length`| `extruder_load_speed`               | y                         | y             |
| load hotend               | `hotend_load_length`  | `hotend_load_speed`                 | y**                       | y             |

\* this move only occurs if `toolhead_fil_sensor_pin` is specified
and `load_with_toolhead_sensor` is True.

\** the servo will start disengaging Trad Rack's drive gear 
`servo_wait_ms` before the move ends.

## Unloading process

The following table shows which actions are taken when unloading
filament from the toolhead back into Trad Rack.

| Description               | Distance (mm)                               | Speed (mm/s)            | Trad Rack filament driver | Main extruder |
| ---                       | ---                                         | ---                     | ---                       | ---           |
| toolhead sensor homing*** | until sensor is untriggered                 | `toolhead_sense_speed`  | y                         | y             |
| unload toolhead           | `toolhead_unload_length`                    | `toolhead_unload_speed` | y                         | y             |
| move through bowden tube  | `bowden_length` + `bowden_unload_length_mod`| `buffer_pull_speed`     | y                         | n             |

\*** this move only occurs if `toolhead_fil_sensor_pin` is specified
and `unload_with_toolhead_sensor` is True.

## Tuning lengths

The following lengths must be tuned to match your bowden tube,
extruder, toolhead, and toolhead sensor setup. The values in the
provided config file have been tuned for an Annex K3 toolhead running
a Sherpa Micro extruder (with a sensor detecting its idler arm
movement) and a Mosquito Magnum hotend.

- `bowden_length` (mm): this value should be slightly smaller than the
  length of the bowden tube between Trad Rack and your toolhead.
  This length should be tuned to bring the filament tip almost all
  the way to the extruder drive gears, starting from the point where
  Trad Rack's selector filament sensor is triggered. Make sure there
  is some distance between the filament tip and the drive gears for
  safety.
- `extruder_load_length` (mm): this length should be tuned to bring the
  filament tip slightly above the start of the meltzone, starting from
  the point where the toolhead sensor is triggered. You can base this
  length off of measurements of your toolhead from CAD. If you are not
  using a toolhead sensor, then the position of the filament tip after
  moving through the bowden tube would be your starting point.
- `hotend_load_length` (mm): this length is meant to bring the filament tip
  into the meltzone so it is ready for printing. You may have to tune
  this parameter through trial and error to avoid extra oozing during
  loading or gaps in your prime tower.
- `toolhead_unload_length` (mm): this length is meant to retract the
  filament tip from the toolhead so the extruder gears are not
  touching it, starting from the point where the toolhead sensor is
  untriggered. If you have `bowden_unload_length_mod` set to zero, the
  filament tip should end up roughly at the same place after this move
  as it does during loading before the toolhead sensor homing starts.
- `bowden_unload_length_mod` (mm): this length is added to `bowden_length`
  when moving the filament through the bowden tube during unloads.
  Its purpose is to let you use different bowden tube lengths during
  loading and unloading. For example, you can use a negative number
  (and increase `toolhead_unload_length` by the same absolute value)
  in order to pull the filament farther out of the toolhead before the
  main extruder disengages for extra safety.

## Bowden speeds

There is more force required and more inertia when loading filament
when the buffer is empty than when the buffer is full: in the former
case the drive gears must rotate the spool, but in the latter case the
spool can stay stationary since all the loaded filament comes out of
the buffer. To take advantage of this, we have two separate speeds
that are used when moving filament through the bowden tube:

- `spool_pull_speed` (mm/s): this speed is used when loading from a lane
  whose buffer is assumed to be empty (usually because the lane's
  filament has not been unloaded from the toolhead previously).
- `buffer_pull_speed` (mm/s): this speed is used when unloading or when
  loading from a lane whose buffer is assumed to be full (because
  the lane's filament has been unloaded from the toolhead previously).
