# Customization

This document contains info on how code is divided between the
[trad_rack Klipper module](/Klipper_Stuff/klippy_module/trad_rack.py)
and the config, how to customize Trad Rack's behavior through gcode
templates, and what the
[trad_rack_optional config file](/Klipper_Stuff/klipper_config/trad_rack_optional.cfg)
does.

**Table of Contents**
- [Klipper module and config files](#klipper-module-and-config-files)
- [The trad\_rack\_optional config file](#the-trad_rack_optional-config-file)
  - [Main settings](#main-settings)
  - [Tip shaping](#tip-shaping)
    - [When Shape\_Tip is used](#when-shape_tip-is-used)
    - [Contents of the Shape\_Tip macro](#contents-of-the-shape_tip-macro)
  - [Macros](#macros)

## Klipper module and config files

Most of Trad Rack's functionality is handled through the
[trad_rack Klipper module](/Klipper_Stuff/klippy_module/trad_rack.py).
This functionality includes any behaviors that are considered
"universal" enough that they should require no customization besides
simple config value changes, but (hopefully) no more than that. All
other behaviors that may require more extensive customization, such as
filament tip-shaping or cutting procedures, are handled through gcode
templates to allow for more user customization. The following gcode
templates are currently available:

- `pre_unload_gcode`: Gcode command template that is run before the
  toolhead is unloaded. The default is to run no extra commands.
- `post_load_gcode`: Gcode command template that is run after the
  toolhead is loaded. The default is to run no extra commands.
- `pause_gcode`: Gcode command template that is run whenever Trad Rack
  needs to pause the print (usually due to a failed load or unload).
  The default is to run the PAUSE gcode command.
- `resume_gcode`: Gcode command template that is run whenever the
  TR_RESUME command needs to resume the print. The default is to run
  the RESUME gcode command.

## The trad_rack_optional config file

[trad_rack_optional.cfg](/Klipper_Stuff/klipper_config/trad_rack_optional.cfg)
provides a recommended example implementation of `pre_unload_gcode`
and `post_load_gcode`.[^1] It is highly recommended to include this file
when getting starting with Trad Rack; it provides several useful
features, and the [provided slicer profiles](/Slicer_Config/) (as well
as the suggested
[changes to make to existing slicer profiles](/docs/slicing/Slicing.md#changes-to-make-to-existing-profiles))
were made with the assumption that this file is being used. However,
you are encouraged to modify or replace this file to fit your needs.

### Main settings

`[gcode_macro TR_Variables]` contains several variables that allow for
quick customization. This includes adjusting positions as well as
enabling or disabling features. See the comments next to these
variables for more details.

### Tip shaping

`[gcode_macro Shape_Tip]` is used for shaping the tip of the filament
before unloading. This can include mimicing ramming and unload
behavior from the slicer, filament cutting, etc. 

#### When Shape_Tip is used

By default, the `Shape_Tip` macro is called in `pre_unload_gcode`
before unloading *only if a print is not in progress* (since it is
assumed that your print gcode file will contain tip-shaping gcode of
its own). It is also possible to use the `Shape_Tip` macro during a
print; see the
[Slicing document](/docs/slicing/Slicing.md#experimental-options) for
more details.

#### Contents of the Shape_Tip macro

By default, the `Shape_Tip` macro will call `Slicer_Unload`. This is
another macro defined in
[trad_rack_optional.cfg](/Klipper_Stuff/klipper_config/trad_rack_optional.cfg)
that mimics ramming and/or unload behavior from PrusaSlicer or
SuperSlicer. If you want the `Shape_Tip` macro to do something else
instead (for example if you are using a filament cutter and don't need
the typical tip-shaping procedure), you can replace the call to
`Slicer_Unload` with something else.

### Macros

[trad_rack_optional.cfg](/Klipper_Stuff/klipper_config/trad_rack_optional.cfg)
adds the following macros. See the comments in the file for
information on how these macros are meant to be used and what
parameters they expect:

- `TR_Variables`: Contains variables for quick customization of
  `pre_unload_gcode` and `post_load_gcode`. See
  [main settings](#main-settings).

- `Shape_Tip`: Macro that gets called in `pre_unload_gcode` whenever
  Trad Rack inserts its own gcode for tip-shaping. See
  [tip shaping](#tip-shaping).

- `Set_Slicer_Unload_Preset`: Applies setting presets for
  the `Slicer_Unload` macro. Presets can be defined by creating new
  variables in `[gcode_macro Set_Slicer_Unload_Preset]`.

- `Slicer_Unload`: Mimics the ramming and/or unload
  behavior of PrusaSlicer or SuperSlicer. Settings can be adjusted
  by directly adjusting the macro's variables or by using
  `Set_Slicer_Unload_Preset`. Variable names match the "parameter
  names" used in the slicer.

- `_Wait_for_Toolchange_Temp`: Helper macro for `Slicer_Unload`.

- `Home_and_Wipe_Nozzle`: Used in `pre_unload_gcode` (if
  `variable_use_wiper` is set to `True` in
  `[gcode_macro TR_Variables]`). See the comment in
  `[gcode_macro TR_Variables]` for more details.

- `Save_Pressure_Advance`: Saves the current pressure advance value so
  it can be restored after tip-shaping. See the [Slicing document](/docs/slicing/Slicing.md#print-settings) for how this macro is meant to be used.
  This macro may be useful if you set pressure advance only at the
  start of a print.

- `Restore_Pressure_Advance`: Used by `post_load_gcode` to restore the
  pressure advance value saved by `Save_Pressure_Advance` after a
  toolchange.

[^1]: `pause_gcode` and `resume_gcode` are left at their default
values of `PAUSE` and `RESUME` respectively.
