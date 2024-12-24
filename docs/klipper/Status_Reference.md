# Status Reference

This document is modeled after Klipper's
[Status Reference document](https://www.klipper3d.org/Status_Reference.html)
but only contains items pertaining to Trad Rack.

## trad_rack

The following information is available in the `trad_rack` object:
- `curr_lane`: The lane the selector is currently positioned at.
- `active_lane`: The lane currently loaded in the toolhead.
- `next_lane`: The next lane to load to the toolhead if a toolchange
  is in progress.
- `next_tool`: The next tool to load to the toolhead if a toolchange
  is in progress (if a tool number was specified for the toolchange).
- `tool_map`: An array of integers listing the assigned tool for each
  lane. The tool number for a specified lane can be accessed with
  `tool_map[<lane index>]`.
- `selector_homed`: Whether or not the selector axis is homed.

## save_variables

Trad Rack uses the `save_variables` object to save variables to disk
so that they can be used across restarts. See the
[Save Variables document](Save_Variables.md) for more details
on how Trad Rack uses save_variables, and Klipper's
[Command Templates document](https://www.klipper3d.org/Command_Templates.html#save-variables-to-disk)
for details on how to access all saved variables.
