# G-Codes

This document is modeled after Klipper's
[G-Codes](https://www.klipper3d.org/G-Codes.html)
document but only contains items pertaining to Trad Rack.

### TR_HOME
`TR_HOME`: Homes the selector.

### TR_GO_TO_LANE
`TR_GO_TO_LANE LANE=<lane index>`: Moves the selector to the specified
lane.

### TR_LOAD_LANE
`TR_LOAD_LANE LANE=<lane index>`: Ensures filament is loaded into
the module for the specified lane by prompting the user to insert
filament, loading filament from the module into the selector, and
retracting the filament back into the module.

### TR_LOAD_TOOLHEAD
`TR_LOAD_TOOLHEAD LANE=<lane index> [BOWDEN_LENGTH=<mm>]
[EXTRUDER_LOAD_LENGTH=<mm>] [HOTEND_LOAD_LENGTH=<mm]`: Loads filament
from the specified lane into the toolhead. If there is already an
"active lane" because the toolhead has been loaded beforehand, it will
be unloaded before loading the new filament. If any of the optional
length parameters are specified, they override the corresponding
settings in the
[trad_rack config section](Config_Reference.md#trad_rack).

### T0, T1, T2, etc.
`T<lane index>`: Equivalent to calling 
`TR_LOAD_TOOLHEAD LANE=<lane index>`. All of the optional parameters
accepted by the TR_LOAD_TOOLHEAD command can also be used with these
commands.

### TR_UNLOAD_TOOLHEAD
`TR_UNLOAD_TOOLHEAD`: Unloads filament from the toolhead and back into
its module.

### TR_SERVO_DOWN
`TR_SERVO_DOWN`: Moves the servo to bring the drive gear down. The
selector must be moved to a valid lane before using this command.

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
set). It is recommended to call this command in the print start gcode.
