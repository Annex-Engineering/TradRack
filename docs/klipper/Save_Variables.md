# Save Variables

Trad Rack uses
[save_variables](https://www.klipper3d.org/Config_Reference.html#save_variables)
to save variables to disk so that they can be used across restarts.
This document lists all of the variables that Trad Rack saves to disk.

## Bowden lengths

The following variables are used for storing bowden length data,
which is used to set "bowden_load_length" and "bowden_unload_length"
after a restart. See the
[Tuning document](/docs/Tuning.md) for details on how
"bowden_load_length" and "bowden_unload_length" are used.

- `calib_bowden_load_length`: Dict containing the following bowden
  load length data. This variable is saved each time the toolhead is
  loaded*:
  - `new_set_length`: The last calibrated "bowden_load_length".
  - `sample_count`: The number of samples that were averaged to
    determine `new_set_length`.
- `calib_bowden_unload_length`: Dict containing the following bowden
  unload length data. This variable is saved each time the toolhead is
  unloaded:
  - `new_set_length`: The last calibrated "bowden_unload_length".
  - `sample_count`: The number of samples that were averaged to
    determine `new_set_length`.
- `config_bowden_length`: The value of `bowden_length` at the time
  that bowden length data was last saved. On a restart, the saved
  bowden length data will be ignored if `bowden_length` does not match `config_bowden_length`. This variable is saved each time Klipper
  starts.

\* if `toolhead_fil_sensor_pin` is not specified or
`load_with_toolhead_sensor` is False, `calib_bowden_load_length` will
not be saved.

## Other variables

The following miscellaneous variables are saved.

- `tr_last_heater_target`: Extruder target temperature from the last
time the toolhead was loaded. This variable may be used by the
[TR_LOAD_TOOLHEAD or TR_UNLOAD_TOOLHEAD gcode commands](G-Codes.md)
for setting the extruder temperature before unloading/loading. This
variable is saved each time the toolhead is loaded.