# G-Codes

This document is modeled after Klipper's
[G-Codes document](https://www.klipper3d.org/G-Codes.html) but only
contains items pertaining to Trad Rack.

**Table of Contents**
- [General commands](#general-commands)
  - [TR\_HOME](#tr_home)
  - [TR\_GO\_TO\_LANE](#tr_go_to_lane)
  - [TR\_LOAD\_LANE](#tr_load_lane)
  - [TR\_LOAD\_TOOLHEAD](#tr_load_toolhead)
  - [T0, T1, T2, etc.](#t0-t1-t2-etc)
  - [TR\_UNLOAD\_TOOLHEAD](#tr_unload_toolhead)
  - [TR\_SERVO\_DOWN](#tr_servo_down)
  - [TR\_SERVO\_UP](#tr_servo_up)
  - [TR\_SET\_ACTIVE\_LANE](#tr_set_active_lane)
  - [TR\_RESET\_ACTIVE\_LANE](#tr_reset_active_lane)
  - [TR\_RESUME](#tr_resume)
  - [TR\_LOCATE\_SELECTOR](#tr_locate_selector)
  - [TR\_NEXT](#tr_next)
  - [TR\_SYNC\_TO\_EXTRUDER](#tr_sync_to_extruder)
  - [TR\_UNSYNC\_FROM\_EXTRUDER](#tr_unsync_from_extruder)
- [Calibration and testing](#calibration-and-testing)
  - [TR\_SERVO\_TEST](#tr_servo_test)
  - [TR\_CALIBRATE\_SELECTOR](#tr_calibrate_selector)
  - [TR\_SET\_HOTEND\_LOAD\_LENGTH](#tr_set_hotend_load_length)
- [Tool mapping](#tool-mapping)
  - [TR\_ASSIGN\_LANE](#tr_assign_lane)
  - [TR\_SET\_DEFAULT\_LANE](#tr_set_default_lane)
  - [TR\_RESET\_TOOL\_MAP](#tr_reset_tool_map)
  - [TR\_PRINT\_TOOL\_MAP](#tr_print_tool_map)
  - [TR\_PRINT\_TOOL\_GROUPS](#tr_print_tool_groups)
- [Macros](#macros)

## General commands

### TR_HOME
`TR_HOME`: Homes the selector.

### TR_GO_TO_LANE
`TR_GO_TO_LANE LANE=<lane index>`: Moves the selector to the specified
lane.

### TR_LOAD_LANE
`TR_LOAD_LANE LANE=<lane index> [RESET_SPEED=<0|1>]`: Ensures filament
is loaded into the module for the specified lane by prompting the user
to insert filament, loading filament from the module into the
selector, and retracting the filament back into the module.
If RESET_SPEED is 1, the bowden move speed used for the
specified LANE will be reset to `spool_pull_speed`
(see [bowden speeds](/docs/Tuning.md#bowden-speeds) for details).
If not specified, RESET_SPEED defaults to 1.

### TR_LOAD_TOOLHEAD
`TR_LOAD_TOOLHEAD LANE=<lane index>|TOOL=<tool index>
[MIN_TEMP=<temperature>] [EXACT_TEMP=<temperature>]
[BOWDEN_LENGTH=<mm>] [EXTRUDER_LOAD_LENGTH=<mm>]
[HOTEND_LOAD_LENGTH=<mm>]`: Loads filament from the specified lane or
tool into the toolhead*. Either LANE or TOOL must be specified. If
both are specified, then LANE takes precedence. If there is already an
"active lane" because the toolhead has been loaded beforehand, it will
be unloaded before loading the new filament. If `MIN_TEMP` is
specified and it is higher than the extruder's current temperature,
then the extruder will be heated to at least `MIN_TEMP` before
unloading/loading; the current extruder temperature target may be used
instead if it is higher than `MIN_TEMP`, and if not then
[tr_last_heater_target](Save_Variables.md) may be used. If
`EXACT_TEMP` is specified, the extruder will be heated to `EXACT_TEMP`
before unloading/loading, regardless of any other temperature setting.
If any of the optional length parameters are specified, they override
the corresponding settings in the
[trad_rack config section](Config_Reference.md#trad_rack).

\* see the [Tool Mapping document](/docs/Tool_Mapping.md) for
details on the difference between lanes and tools and how they relate
to each other.

### T0, T1, T2, etc.
`T<tool index>`: Equivalent to calling 
`TR_LOAD_TOOLHEAD TOOL=<tool index>`. All of the optional parameters
accepted by the TR_LOAD_TOOLHEAD command can also be used with these
commands.

### TR_UNLOAD_TOOLHEAD
`TR_UNLOAD_TOOLHEAD [MIN_TEMP=<temperature>]
[EXACT_TEMP=<temperature>]`: Unloads filament from the toolhead and
back into its module. If `MIN_TEMP` is specified and it is higher than
the extruder's current temperature, then the extruder will be heated
to at least `MIN_TEMP` before unloading; the current extruder
temperature target may be used instead if it is higher than
`MIN_TEMP`, and if not then [tr_last_heater_target](Save_Variables.md)
may be used. If `EXACT_TEMP` is specified, the extruder will be heated
to `EXACT_TEMP` before unloading/loading, regardless of any other
temperature setting.

### TR_SERVO_DOWN
`TR_SERVO_DOWN [FORCE=<0|1>]`: Moves the servo to bring the drive gear down. The
selector must be moved to a valid lane before using this command, unless FORCE
is 1. If not specified, FORCE defaults to 0. The FORCE parameter is unsafe for
normal use and should only be used when the servo is not attached to Trad Rack's
carriage.

### TR_SERVO_UP
`TR_SERVO_UP`: Moves the servo to bring the drive gear up.

### TR_SET_ACTIVE_LANE
`TR_SET_ACTIVE_LANE LANE=<lane index>`: Tells Trad Rack to assume the
toolhead has been loaded with filament from the specified lane. The
selector's position will also be inferred from this lane, and the
selector motor will be enabled if it isn't already.

### TR_RESET_ACTIVE_LANE
`TR_RESET_ACTIVE_LANE`: Tells Trad Rack to assume the toolhead has
not been loaded.

### TR_RESUME
`TR_RESUME`: Retries loading the last lane, loads the next filament
into the toolhead, and resumes the print. The user will be prompted
to use this command if Trad Rack has paused the print due to a failed
load or unload.

### TR_LOCATE_SELECTOR
`TR_LOCATE_SELECTOR`: Ensures the position of Trad Rack's selector is
known so that it is ready for a print. If the user needs to take an
action, they will be prompted to do so and the print will be paused
(for example if the selector sensor is triggered but no active lane is
set). The user_wait_time config option from the
[trad_rack config section](Config_Reference.md#trad_rack) determines
how long Trad Rack will wait for user action before automatically
unloading the toolhead and resuming. In addition, the save_active_lane
config option determines whether this command can infer the "active
lane" from a value saved before the last restart if the selector
filament sensor is triggered but no active lane is currently set.
It is recommended to call this command in the print start gcode.

### TR_NEXT
`TR_NEXT`: You will be prompted to use this command if Trad Rack
requires user confirmation before continuing an action.

### TR_SYNC_TO_EXTRUDER
`TR_SYNC_TO_EXTRUDER`: Syncs Trad Rack's filament driver to the
extruder during printing, as well as during any extrusion moves within
toolhead loading or unloading that would normally involve only the
extruder. This is an experimental feature and is not recommended
unless you have the rotation_distance for the extruder and filament
driver very closely matched. Even with a small error, the
filament driver and extruder may gradually drift out of sync during a
long print with no toolchanges, leading to slipping or grinding of the
filament. If you want the filament driver to be synced to the extruder
on every startup without having to call this command, you can set
sync_to_extruder to True in the
[trad_rack config section](Config_Reference.md#trad_rack).

### TR_UNSYNC_FROM_EXTRUDER
`TR_UNSYNC_FROM_EXTRUDER`: Unsyncs Trad Rack's filament driver from
the extruder during printing, as well as during any extrusion moves
within toolhead loading or unloading that normally involve only the
extruder. This is the default behavior unless you have set
sync_to_extruder to True in the
[trad_rack config section](Config_Reference.md#trad_rack).

## Calibration and testing

The following commands are used either for calibration or for testing
settings without having to restart Klipper to reload the config.
Calibration procedures that should be run before using Trad Rack are
covered by the [Quick Start document](/docs/Quick_Start.md):

### TR_SERVO_TEST
`TR_SERVO_TEST [ANGLE=<degrees>]`: Moves the servo to the specified
ANGLE relative to the down position. If ANGLE is not specified, the
servo will be moved to the up position defined by servo_up_angle from
the [trad_rack config section](Config_Reference.md#trad_rack).
This command is meant for testing different servo angles in order
to find the correct value for servo_up_angle.

### TR_CALIBRATE_SELECTOR
`TR_CALIBRATE_SELECTOR`: Initiates the process of calibrating
lane_spacing, as well as the min, endstop, and max positions of the
selector motor. You will be guided through the selector calibration
process via messages in the console.

### TR_SET_HOTEND_LOAD_LENGTH
`TR_SET_HOTEND_LOAD_LENGTH VALUE=<value>|ADJUST=<adjust>`: Sets the
value of hotend_load_length, overriding its value from the
[trad_rack config section](Config_Reference.md#trad_rack). Does not
persist across restarts. If the VALUE parameter is used,
hotend_load_length will be set to the value passed in. If the ADJUST
parameter is used, the adjustment will be added to the current value
of hotend_load_length.

## Tool mapping

The following gcode commands are used for viewing or manipulating the
tool mapping/lane groups. See the
[Tool Mapping document](/docs/Tool_Mapping.md) for more details:

### TR_ASSIGN_LANE
`TR_ASSIGN_LANE LANE=<lane index> TOOL=<tool index>
[SET_DEFAULT=<0|1>]`:
Assigns the specified LANE to the specified TOOL. If SET_DEFAULT is 1,
LANE will become the default lane for the tool. If not specified,
SET_DEFAULT defaults to 0.

### TR_SET_DEFAULT_LANE
`TR_SET_DEFAULT_LANE LANE=<lane index> [TOOL=<tool index>]`: If TOOL
is specified, LANE will be set as the default lane for the tool. If
TOOL is not specified, LANE will be set as the default lane for its
currently-assigned tool.

### TR_RESET_TOOL_MAP
`TR_RESET_TOOL_MAP`: Resets lane/tool mapping. Each tool will be
mapped to a lane group consisting of a single lane with the same index
as the tool.

### TR_PRINT_TOOL_MAP
`TR_PRINT_TOOL_MAP`: Prints a table of the lane/tool mapping to the
console, with rows corresponding to tools and columns corresponding to
lanes.

### TR_PRINT_TOOL_GROUPS
`TR_PRINT_TOOL_GROUPS`: Prints a list of lanes assigned to each tool
to the console. If a tool has multiple lanes assigned to it, the
default lane will be indicated.

## Macros

In addition to the above gcode commands, the
[trad_rack_optional config file](/Klipper_Stuff/klipper_config/trad_rack_optional.cfg)
adds several gcode macros (if you choose to include it). See the
[Customization document](Customization.md#macros) for details.
