# Slicing

This document explains how to get your slicer set up for multimaterial
printing with Trad Rack. These instructions are mainly geared towards
PrusaSlicer and SuperSlicer, but some notes on custom gcode may be
applicable to other slicers too.

## Provided slicer profiles

Example slicer profiles for SuperSlicer can be found in the
[Slicer_Config](/Slicer_Config/) folder. To use these profiles, copy
the files into the corresponding `filament`, `print`, and `printer`
folders located in:

- Windows: `C:\users\<username>\AppData\Roaming\SuperSlicer`
- Mac: `/Users/<username>/Library/Application Support/SuperSlicer`

These profiles assume you have included
[trad_rack_optional.cfg](/Klipper_Stuff/klipper_config/trad_rack_optional.cfg)
in your Klipper config and that you have a `Print_Start` g-code macro
that takes the following parameters:

- `EXTRUDER`: hotend temperature
- `BED`: bed temperature

Note: the purge volumes used in these profiles are for a mosquito
magnum, but I have not done much experimentation or optimization.
I would recommend doing your own tuning on purge volumes, try
different wipe advanced algorithms (or use the purge volume tables),
etc.

## Changes to make to existing profiles

This section explains changes to make to an existing single-tool
slicing profile. Setting names used here follow the "parameter names"
that are used in the slicer config files; you can use the search
function to see which settings these refer to in the GUI.

### Printer Settings

The following changes should be made to the printer config file in the
Printer Settings tab.

- `extruders_count`: set this to the number of lanes.
- `single_extruder_multi_material`: set to `true` (`1` in the config).
- `start_gcode`:
  - Add the following lines to the beginning of the Start G-code section:
    
    ```
    TR_CHECK_READY
    TR_Print_Start EXTRUDER=[first_layer_temperature] LANE=[initial_tool]
    ```

    And the following to the end:
    
    ```
    Save_Pressure_Advance
    ```
    
    Explanation:
    - `TR_CHECK_READY`: see the 
      [G-Codes](/docs/klipper/G-Codes.md/#tr_check_ready)
      document for more details
    - `TR_Print_Start`: loads the first filament into the toolhead
    - `Save_Pressure_Advance`: saves the current pressure advance
      value so that it can be restored after ramming. The pressure
      advance value you want to use for the print should be set before
      this line. Alternatively you can set the pressure advance in
      the `end_filament_gcode`, but you would have more values to
      change if you want to change the pressure advance for the entire
      print.
 - `cooling_tube_retraction`: see the tooltip for details.
 - `cooling_tube_length`: see the tooltip for details.
 - `parking_pos_retract`: set this to 
   `cooling_tube_retraction + cooling_tube_length / 2`.
 - `extra_loading_move`: set this to a negative number with an
   absolute value slightly less than that of `parking_pos_retract`.
   For example, if `parking_pos_retract` is `37`, set this to `-36.99`.
 - Advanced wipe tower purge volume calculs:
   - One of the options for purge volume calculations is to have the
     slicer calculate volumes based on each filament's pigment
     percentage. See the tooltips for more details on these settings:
     - `wipe_advanced`
     - `wipe_advanced_nozzle_melted_volume`
     - `wipe_advanced_multiplier`
     - `wipe_advanced_algo`

### Print Settings

The following changes should be made to the print config file in the
Print Settings tab.

- `wipe_tower`: set to `true` (`1` in the config) unless you are using
  an alternative way of purging material.
- `only_retract_when_crossing_perimeters`: set to `false` (`0` in the
  config) to avoid colors bleeding into each other when the nozzle
  moves over the print.

### Filament Settings

The following changes should be made to each filament config file in
the Filament Settings tab.

(this section is not done yet; everything you might need to change
that is specific to multimaterial or Trad Rack should be located
in Multimaterial > Toolchange parameters with single extruder MM
printers. I recommend looking at the provided example
filament config files.)
