# Quick Start

This document provides an overview of how to get Trad Rack running.
Each section should be completed before moving on to the next.

**Table of Contents**
- [BOM/sourcing and other required hardware](#bomsourcing-and-other-required-hardware)
  - [Item Calculator](#item-calculator)
- [Printing required parts](#printing-required-parts)
- [Mechanical assembly](#mechanical-assembly)
- [Wiring](#wiring)
- [Kalico installation](#kalico-installation)
- [Servo calibration](#servo-calibration)
  - [Servo rotation direction](#servo-rotation-direction)
  - [Servo horn angle](#servo-horn-angle)
  - [Servo up angle](#servo-up-angle)
- [Selector calibration](#selector-calibration)
- [Slicing](#slicing)
- [Changing Slicer\_Unload macro settings](#changing-slicer_unload-macro-settings)
- [First load and unload](#first-load-and-unload)
  - [Setup](#setup)
  - [Loading the toolhead](#loading-the-toolhead)
  - [Unloading the toolhead](#unloading-the-toolhead)
  - [Relevance to print setup](#relevance-to-print-setup)
- [Further reading](#further-reading)

## BOM/sourcing and other required hardware

The bill of materials/sourcing guide for Trad Rack can be found
[here](https://docs.google.com/spreadsheets/d/1SKBtkgSVPqqGEjftI6v6i6T5Bh3Phx-4YXsJYH17ggs/edit?usp=sharing).

Before placing any orders for parts for Trad Rack, it is recommended to read the
[Printer and hardware requirements document](Printer_and_Hardware_Requirements.md)
in case there are any other items you may want to combine into your orders.

### Item Calculator

Several parts of the build are scalable to the needs of the builder. There are two ways to use our item calculator, which can help you determine how many and what sizes of these parts you need.

  - [Web Based Calculator](https://coddy.tech/embed-editor?lang=python&code=aW1wb3J0IG1hdGgKCmRlZiBtYWluKCk6CiAgICBsYW5lX3NwYWNpbmcgPSAxNy4KICAgIGNfY2FydF93aWR0aCA9IDI4LjkKICAgIGhfY2FydF93aWR0aCA9IDM5LjkKICAgIGV4dHJ1c2lvbl9leHRyYV9sZW4gPSAzMC4KICAgIGJlbHRfYmFzZV9sZW4gPSAxOTkuMQogICAgYmVsdF9zYWZldHkgPSAzMC4KICAgIGNoYWluX2Jhc2VfbGVucyA9IHsKICAgICAgICAxNS46ICAgIDEyMCwKICAgICAgICAxNi43OiAgIDEyNCwKICAgICAgICAyMC46ICAgIDEzMAogICAgfQogICAgbTN4OF9iYXNlX2NvdW50ID0gMjUKICAgIG0zeDhfc2FmZXR5ID0gMTAKICAgIG0zeDhfcmFpbF9waXRjaCA9IDQwLgogICAgbTN4OF9yYWlsX2VuZCA9IDQuNQogICAgbTNfdF9udXRfYmFzZV9jb3VudCA9IDMKCiAgICAjIGdldCBsYW5lIGNvdW50CiAgICBsYW5lX2NvdW50ID0gaW50KGlucHV0KCJFbnRlciB0aGUgbnVtYmVyIG9mIGxhbmVzOiAiKSkKCiAgICAjIGNhbGN1bGF0ZSBsYW5lX3NwYW4gYW5kIG1pbmltdW0gcmFpbCBsZW5ndGhzCiAgICBsYW5lX3NwYW4gPSBnZXRfbGFuZV9zcGFuKGxhbmVfY291bnQsIGxhbmVfc3BhY2luZykKICAgIGNfcmFpbF9sZW4gPSBsYW5lX3NwYW4gKyBjX2NhcnRfd2lkdGgKICAgIGhfcmFpbF9sZW4gPSBsYW5lX3NwYW4gKyBoX2NhcnRfd2lkdGgKCiAgICAjIGRpc3BsYXkgcmVxdWlyZWQgcmFpbCBsZW5ndGhzCiAgICBwcmludCgiXG5NaW5pbXVtIHJhaWwgbGVuZ3RoIHdpdGggYy1jYXJ0OiB7fSIuZm9ybWF0KGNfcmFpbF9sZW4pKQogICAgcHJpbnQoIk1pbmltdW0gcmFpbCBsZW5ndGggd2l0aCBoLWNhcnQ6IHt9Ii5mb3JtYXQoaF9yYWlsX2xlbikpCgogICAgIyBnZXQgcmFpbCBjYXJ0IHR5cGUgYW5kIGNvcnJlc3BvbmRpbmcgbWluaW11bSByYWlsIGxlbmd0aAogICAgY2FydF90eXBlID0gaW5wdXQoIlxuRW50ZXIgc2VsZWN0ZWQgcmFpbCBjYXJ0IHR5cGUgKGMvaCk6ICIpLmxvd2VyKCkKICAgIG1pbl9yYWlsX2xlbiA9IGNfcmFpbF9sZW4gaWYgY2FydF90eXBlID09ICJjIiBlbHNlIGhfcmFpbF9sZW4KCiAgICAjIGdldCByYWlsIGxlbmd0aAogICAgcmFpbF9sZW5fc3RyID0gaW5wdXQoIkVudGVyIHNlbGVjdGVkIHJhaWwgbGVuZ3RoICIKICAgICAgICAgICAgICAgICAgICAgICAgIihsZWF2ZSBibGFuayB0byB1c2UgbWluaW11bSB2YWx1ZSk6ICIpCiAgICByYWlsX2xlbiA9IG1heChmbG9hdChyYWlsX2xlbl9zdHIpLCBtaW5fcmFpbF9sZW4pIGlmIHJhaWxfbGVuX3N0ciBcCiAgICAgICAgZWxzZSBtaW5fcmFpbF9sZW4KCiAgICAjIGNoZWNrIGlmIHVzZXIgd2FudHMgdG8gaW5jcmVhc2UgdGhlIG51bWJlciBvZiBsYW5lcwogICAgY2FydF93aWR0aCA9IGNfY2FydF93aWR0aCBpZiBjYXJ0X3R5cGUgPT0gImMiIGVsc2UgaF9jYXJ0X3dpZHRoCiAgICBtYXhfbGFuZV9jb3VudCA9IG1hdGguZmxvb3IoKHJhaWxfbGVuIC0gY2FydF93aWR0aCkgLyBsYW5lX3NwYWNpbmcpICsgMQogICAgaWYgbWF4X2xhbmVfY291bnQgPiBsYW5lX2NvdW50OgogICAgICAgIGNoYW5nZV9sYW5lX2NvdW50ID0gaW5wdXQoIllvdXIgc2VsZWN0ZWQgcmFpbCBhbGxvd3MgYSBtYXhpbXVtIG9mIHt9ICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICJsYW5lcy4gSW5jcmVhc2UgbGFuZSBjb3VudCBmcm9tIHt9IHRvIHt9PyAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAiKHkvbik6ICIuZm9ybWF0KG1heF9sYW5lX2NvdW50LCBsYW5lX2NvdW50LCAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgbWF4X2xhbmVfY291bnQpKS5sb3dlcigpCiAgICAgICAgaWYgY2hhbmdlX2xhbmVfY291bnQgPT0gInkiOgogICAgICAgICAgICBsYW5lX2NvdW50ID0gbWF4X2xhbmVfY291bnQKICAgICAgICAgICAgbGFuZV9zcGFuID0gZ2V0X2xhbmVfc3BhbihsYW5lX2NvdW50LCBsYW5lX3NwYWNpbmcpCgogICAgIyBnZXQgY2FibGUgY2hhaW4gcGl0Y2gKICAgIHByaW50KCJcbkNhYmxlIGNoYWluIHBpdGNoIG9wdGlvbnM6IgogICAgICAgICAgIlxuXHQxNVx0KGUuZy4gSkZMTyBKMTBRLjEuMTBCKSIKICAgICAgICAgICJcblx0MTYuN1x0KGUuZy4gSkZMTyBKMTBRLjEuMTBXKSIKICAgICAgICAgICJcblx0MjBcdChlLmcuIElHVVMgRTItMTAtMTAtMDI4LTApXG4iKQogICAgY2hhaW5fcGl0Y2ggPSAwLgogICAgd2hpbGUobm90IGNoYWluX3BpdGNoIGluIGNoYWluX2Jhc2VfbGVucyk6CiAgICAgICAgY2hhaW5fcGl0Y2ggPSBmbG9hdChpbnB1dCgiRW50ZXIgc2VsZWN0ZWQgY2FibGUgY2hhaW4gcGl0Y2g6ICIpKQoKICAgIHByaW50KCkKCiAgICAjIGxhbmUgY291bnQKICAgIHByaW50KCJTZWxlY3RlZCBsYW5lIGNvdW50OiB7fSIuZm9ybWF0KGxhbmVfY291bnQpKQoKICAgICMgcmFpbAogICAgcHJpbnQoIlNlbGVjdGVkIHJhaWwgY2FydCB0eXBlOiB7fSIuZm9ybWF0KCJjIiBpZiBtaW5fcmFpbF9sZW4gPT0gY19yYWlsX2xlbiBcCiAgICAgICAgZWxzZSAiaCIpKQogICAgcHJpbnQoIlNlbGVjdGVkIHJhaWwgbGVuZ3RoOiB7fW1tIi5mb3JtYXQocmFpbF9sZW4pKQoKICAgICMgZXh0cnVzaW9uCiAgICBleHRydXNpb25fbGVuID0gcmFpbF9sZW4gKyBleHRydXNpb25fZXh0cmFfbGVuCiAgICBwcmludCgiTWluaW11bSBleHRydXNpb24gbGVuZ3RoOiB7fW1tIi5mb3JtYXQoZXh0cnVzaW9uX2xlbikpCgogICAgIyBiZWx0CiAgICBiZWx0X2xlbiA9IGJlbHRfYmFzZV9sZW4gKyBsYW5lX3NwYW4gKiAyCiAgICBiZWx0X2xlbl9yZWMgPSBtYXRoLmNlaWwoYmVsdF9sZW4gKyBiZWx0X3NhZmV0eSkKICAgIHByaW50KCJCZWx0IGxlbmd0aDoge31tbSByZWNvbW1lbmRlZCAoe31tbSBlc3RpbWF0ZWQpIi5mb3JtYXQoYmVsdF9sZW5fcmVjLCAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGJlbHRfbGVuKSkKCiAgICAjIGNhYmxlIGNoYWluCiAgICBjaGFpbl9sZW5ndGggPSBsYW5lX3NwYW4gLyAyICsgY2hhaW5fYmFzZV9sZW5zW2NoYWluX3BpdGNoXQogICAgY2hhaW5fbGlua19jb3VudCA9IG1hdGguY2VpbChjaGFpbl9sZW5ndGggLyBjaGFpbl9waXRjaCkKICAgIHByaW50KCJBcHByb3hpbWF0ZSBjYWJsZSBjaGFpbiBsZW5ndGg6IHt9bW0iLmZvcm1hdChjaGFpbl9sZW5ndGgpKQogICAgcHJpbnQoIlF1YW50aXR5IG9mIGNhYmxlIGNoYWluIGxpbmtzIChub3QgaW5jbHVkaW5nIHRoZSBlbmRzKToge30iIFwKICAgICAgICAuZm9ybWF0KGNoYWluX2xpbmtfY291bnQpKQoKICAgICMgTTN4OCBzY3Jld3MgYW5kIE0zIFQtbnV0cwogICAgcmFpbF9zY3Jld19jb3VudCA9IG1hdGguZmxvb3IoKHJhaWxfbGVuIC0gMiAqIG0zeDhfcmFpbF9lbmQpIFwKICAgICAgICAvIG0zeDhfcmFpbF9waXRjaCkgKyAxCiAgICBtM3g4X2NvdW50ID0gbTN4OF9iYXNlX2NvdW50ICsgbGFuZV9jb3VudCArIHJhaWxfc2NyZXdfY291bnQKICAgIG0zeDhfY291bnRfcmVjID0gbTN4OF9jb3VudCArIG0zeDhfc2FmZXR5CiAgICB0X251dF9jb3VudCA9IHJhaWxfc2NyZXdfY291bnQgKyBtM190X251dF9iYXNlX2NvdW50CiAgICBwcmludCgiUXVhbnRpdHkgb2YgTTMgeCA4bW0gU29ja2V0IEhlYWQgQ2FwIFNjcmV3czoge30gcmVjb21tZW5kZWQgIgogICAgICAgICIoe30gZXhwZWN0ZWQpIi5mb3JtYXQobTN4OF9jb3VudF9yZWMsIG0zeDhfY291bnQpKQogICAgcHJpbnQoIlF1YW50aXR5IG9mIE0zIEJhbGwgU3ByaW5nIFQtTnV0czoge30iLmZvcm1hdCh0X251dF9jb3VudCkpCgpkZWYgZ2V0X2xhbmVfc3BhbihsYW5lX2NvdW50LCBsYW5lX3NwYWNpbmcpOgogICAgcmV0dXJuIChsYW5lX2NvdW50IC0gMSkgKiBsYW5lX3NwYWNpbmcKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBtYWluKCkK)
  - [Spreadsheet Calculator](https://docs.google.com/spreadsheets/d/1RdqxC5n0PXs8FgdxJVkqQUN2aY69W7eFC76b8XtMozI/edit?usp=sharing)

## Printing required parts

See the following files/folders:

- [Print Settings and File Key](/Print_Settings_and_File_Key.txt):
  print settings to use and info on reading the STL filenames.
- [STLs folder](/STLs): contains all STL files.
- [STLs README](/STLs/README.md): information on what parts to print.

## Mechanical assembly

See the [build instructions](build_instructions) for guidance on
assembling Trad Rack.

> [!TIP]
> An [eDrawing](/eDrawings/) is also available if you want to view a
> 3D model of Trad Rack. You will need
> [eDrawings Viewer](https://www.edrawingsviewer.com/) to open this
> file. If you are using the Nebula control board, a separate eDrawing
> is also available for help on assembling its enclosure.

## Wiring

See the [Wiring document](Wiring.md).

## Kalico installation

See the [Kalico installation document](kalico/Installation.md).

## Servo calibration

This section involves setting the rotation direction and angles of the
servo. You will need to have Trad Rack fully assembled, wired, and
connected to your printer with Kalico running.

To prepare, remove the servo from Trad Rack by undoing the 2 screws
that attach it to the right carriage.

### Servo rotation direction

Run the following gcode command:

```
TR_SERVO_UP
```

Then run the following gcode command, and this time observe the motion
of the servo. When viewed from the front of the servo spline, the
servo should rotate clockwise:

```
TR_SERVO_DOWN FORCE=1
```

If the servo rotated clockwise, you can continue on to setting the
[servo horn angle](#servo-horn-angle). Otherwise, in your Kalico
config, swap the values of `servo_down_angle` and `servo_up_angle` in
the [trad_rack] section. Then restart Kalico and continue.

### Servo horn angle

Run the following gcode command:

```
TR_SERVO_DOWN FORCE=1
```

Loosen the screw in the center of the servo horn and the screw in
the clamp.

For this section, you will need the servo jig that has "HORN ANGLE"
written on the side:

![HORN ANGLE servo jig](images/servo_jigs/horn_angle_jig.png?raw=true)

Insert the servo into the servo jig. You may need to rotate the
servo horn around the servo spline by hand so that it is at the
correct angle for the bearing to fit into the jig. The servo's wires
should be exiting to the left to match the orientation in the image:

![Servo in HORN ANGLE jig](images/servo_jigs/servo_in_horn_angle_jig.png?raw=true)

Tighten the two screws you loosened earlier. Then remove the servo
jig.

### Servo up angle

For this section, you will need the servo jig that has "UP ANGLE"
written on the side:

![UP ANGLE servo jig](images/servo_jigs/up_angle_jig.png?raw=true)

Insert the servo into the servo jig. The servo's wires should be
exiting to the left to match the orientation in the image:

![Servo in UP ANGLE jig](images/servo_jigs/servo_in_up_angle_jig.png?raw=true)

Run the following gcode command. Observe the "commanded angle" that is
reported in the console:

```
TR_SERVO_TEST
```

Look at the front of the servo jig and check the position of the screw
in the bearing relative to the slots. The goal of this section is
to get the screw close to lining up with the slots:

![UP ANGLE servo jig slot check](images/servo_jigs/up_angle_jig_slot_check.png?raw=true)

There is a range of acceptable angles, and the screw does not
have to exactly align with the slots. If the servo angle is within the
target range, the jig will be able to slide far enough over the servo
that the screw protrudes from the front of the jig:

| Wrong angle (screw can't protrude)                              | Angle within target range (screw protrudes)       |
| ---                                                             | ---                                               |
| ![](images/servo_jigs/up_angle_jig_no_protrusion.png?raw=true)  | ![](images/servo_jigs/up_angle_jig_protrusion.png?raw=true)  |

If the jig is blocked from being able to slide far enough for the
screw to protrude, you will need to try another angle. Use the
following command to test a specific angle. The "commanded angle" from
earlier corresponds to the current angle of the servo. A higher angle
will turn the servo counterclockwise, and a lower angle will turn it
clockwise:

```
TR_SERVO_TEST ANGLE=<angle>
```

Repeat with different angles as necessary until the servo is
within the target range.

Once the servo aligns well enough with the slots that the screw can
protrude from the jig, observe the last "raw angle" value reported in
the console. In your main Trad Rack config file, replace the value of
`servo_up_angle` in the [trad_rack] section with the "raw angle"
value. Remove the servo jig and restart Kalico. Then run the
following gcode command:

```
TR_SERVO_DOWN FORCE=1
```

Finally, reattach the servo to Trad Rack.

## Selector calibration

This section involves calibrating `lane_spacing`, as well as the min,
endstop, and max positions of the selector motor.

You will be prompted to enter the `TR_NEXT` macro several times during
the calibration procedure. You should be prepared to load filament
into the first and last lanes when prompted during the procedure.
You can pre-load each lane if you wish to prevent timeouts, or you can
use the same piece of test filament for both lanes.

Run the following gcode command and follow the instructions in the
console:

```
TR_CALIBRATE_SELECTOR
```

When the calibration finishes and you are prompted to do so, replace
the values in your main Trad Rack config file with the new values
for the following:

- in [trad_rack]:
  - `lane_spacing`
- in [stepper_tr_selector]:
  - `position_min`
  - `position_endstop`
  - `position_max`

## Slicing

See the [Slicing document](slicing/Slicing.md).

## Changing Slicer_Unload macro settings

This section involves adjusting the settings of the
[Slicer_Unload macro](kalico/Customization.md#tip-shaping) to match
your slicer settings so that toolhead unloads performed outside of a
print will closely match toolhead unloads performed during a print.

Under `[gcode_macro Slicer_Unload]` in your copy of
[trad_rack_optional.cfg](/Kalico/kalico_config/trad_rack_optional.cfg),
change the values of the following variables to match the values you
set in the slicer profile. Variable names match the "parameter names"
used in the slicer config files:

- all variables under the comment `# printer settings`
- all variables under the comment `# filament settings`

In addition, if you are using SuperSlicer, do the same for all
variables under the comment `# filament settings only in SuperSlicer`.

Set `variable_superslicer` to `True` if you are using SuperSlicer. If
you are using PrusaSlicer or OrcaSlicer, set it to `False`.

Optional: if you want to use different tip-shaping settings for
different filaments (when unloading the toolhead outside of a print),
you can define presets in `[gcode_macro Set_Slicer_Unload_Preset]` in
the same file. See the comments in the macro and the example preset
variables for reference.

## First load and unload

This section goes through the process of running your first toolhead
load and unload to test Trad Rack.

### Setup

Run the following command to home Trad Rack's selector:

```
TR_HOME
```

Get a filament spool ready to feed into Trad Rack. Then run the
following command, and insert the filament into lane module 0 when
prompted to do so in the console:

```
TR_LOAD_LANE LANE=0
```

Trad Rack should now have a filament loaded into lane module 0.

### Loading the toolhead

To load the toolhead from tool 0 (which starts with lane 0 as its
default lane*), run the following command:

```
T0
```

\* see the [G-Codes document](kalico/G-Codes.md#tr_load_toolhead)
for more details on the available parameters for the `TR_LOAD_TOOLHEAD`
and `T<tool index>` toolchange commands.

Depending on your `hotend_load_length` value, filament may or may not
come out of the nozzle.[^1] For the sake of this test, run the
following commands to ensure filament comes out of the nozzle:

```
M83
G1 E10
```

[^1]: It is recommended to set `hotend_load_length` to a value small
enough that filament does not ooze out directly after calling the
toolchange command so that you do not get a blob on the wipe tower.
However, it should not be so small that there are large gaps in the
wipe tower.

### Unloading the toolhead

Run the following command to unload the toolhead. Trad Rack
should retract the filament back into lane module 0:

```
TR_UNLOAD_TOOLHEAD
```

### Relevance to print setup

Congrats, you have completed your first load and unload with Trad
Rack!

When printing with Trad Rack, make sure to load all the filaments you
might need into their lane modules beforehand using the `TR_LOAD_LANE`
command (after ensuring Trad Rack's selector is homed using `TR_HOME`
as needed). It is also possible to load filaments into the lane
modules completely by hand without any gcode commands, but this is
generally not recommended since you will need to make sure the
filament tip is pushed far enough forward that Trad Rack can grab it
but not so far that it blocks selector movement.

It is up to you whether or not to load the first filament to the
toolhead (using `T<tool index>` or `TR_LOAD_TOOLHEAD` commands)
before starting a print. Either way works, as the start gcode in the
slicer will ensure that the first filament gets loaded if it isn't
already.

Whenever you need to unload filament from the toolhead, you can use
the `TR_UNLOAD_TOOLHEAD` command. If a filament is currently loaded
and you want to load a different one, you do not have to call
`TR_UNLOAD_TOOLHEAD` before calling a toolchange command (either
`T<tool index>` or `TR_LOAD_TOOLHEAD`) to load the next filament since
the toolchange command will automatically include the unload as
needed.

## Further reading

This marks the end of the required steps to get Trad Rack running.
See the [Overview document](README.md) to see the full list of
documents available. Some of these were already linked in this guide,
but there are additional ones that provide more information on what
values can be changed for fine tuning, what gcode commands are
available, etc.
