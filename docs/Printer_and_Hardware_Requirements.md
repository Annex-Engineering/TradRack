# Printer and Hardware Requirements

This document covers prerequisites for your printer to work with Trad
Rack, as well as other hardware you might need/want to use with Trad
Rack.

**Table of Contents**
- [Printer](#printer)
- [Electronics](#electronics)
- [Toolhead filament sensor](#toolhead-filament-sensor)
- [Buffers](#buffers)
- [Mounting](#mounting)
  - [Provided mounts](#provided-mounts)
  - [Other recommended mounts](#other-recommended-mounts)
  - [Designing your own mounts](#designing-your-own-mounts)
- [Optional add-ons](#optional-add-ons)
  - [Extruder sync sensor](#extruder-sync-sensor)
  - [Toolhead filament cutter](#toolhead-filament-cutter)
  - [Nozzle wiper and purge bucket](#nozzle-wiper-and-purge-bucket)

## Printer

Your 3D printer must meet the following requirements to work with Trad
Rack:

- Must use 1.75mm filament.
- Must run [Klipper firmware](https://github.com/Klipper3d/klipper/)[^1].
- The toolhead or extruder must have a collet/bowden coupling to
  secure a 4mm bowden tube at the inlet[^2].
  
[^1]: We only provide software for using Trad Rack with Klipper.
However, Trad Rack's hardware is not inherently reliant on Klipper, so
you can use it with another 3D printer firmware if you write your own
software for making Trad Rack work with that firmware.

[^2]: If you are adding a mod to your toolhead in order to add a
filament sensor, it is likely that the mod also includes support for a
collet/bowden coupling. See the table in the
[toolhead filament sensor section](#toolhead-filament-sensor) for
example recommended sensors.

## Electronics

Trad Rack requires the following ports for its actuators and sensors:

| Port                                      | Quantity  |
| ---                                       | ---       |
| Stepper motor output port                 | 2         |
| Endstop input port (pins: GND, signal)    | 2         |
| Servo output port (pins: GND, 5V, PWM)    | 1         |

If your printer's main control board already has these ports/pins
available, you can connect Trad Rack's actuators and sensors directly
to the board. If you do not have these ports available, you may need
to use a separate control board for Trad Rack. The option of using a
separate control board attached to Trad Rack also allows you to easily
connect/disconnect Trad Rack from the rest of your printer with only
USB and power cables.

**In addition to the ports listed above, you will need a port for a
toolhead filament sensor[^3].** This will likely be a simple endstop
input port, but it may depend on the type of sensor you use. It is
recommended to use a port either on your printer's main control board
or on a toolhead board (rather than on a separate control board
attached to Trad Rack) as doing so will likely simplify the wiring.

[^3]: A toolhead filament sensor is highly recommended for
reliability and precise filament positioning, but it is not quite
mandatory.

If you choose to use a separate control board attached to Trad Rack,
see the table below for some example recommended control board
mounts[^4]:

[^4]: If there are other control board mounts, toolhead filament
sensors, buffers, or Trad Rack mounts that you think should be added
to the tables in this document, feel free to submit pull requests to
add them. Please only submit a pull request once you have tested the
design with Trad Rack and confirmed that it works well for you.

(TODO: insert table here)

## Toolhead filament sensor

Using a filament sensor on your printer's toolhead is highly
recommended[^3]. This sensor can have its trigger point be above the
extruder gears, below the extruder gears, or at the extruder gears
(e.g. by sensing the idler arm movement). See the table below for
some example recommended sensors[^4]:

(TODO: insert table here)

## Buffers

Trad Rack requires a buffer for each filament[^5]. The buffer provides
a place for filament to collect when it is retracted from the toolhead
back into Trad Rack, while ensuring that the filament does not get
tangled when it needs to be used again.

[^5]: It is also possible to use an "air buffer": a short section of
bowden tube is attached to the spool holder and another to Trad Rack's
lane module, and a gap is allowed to form between the 2 tubes for the
filament to expand. This setup is not recommended as a permanent
solution since it is very messy and the filaments may tangle with each
other. However, if the filaments are separated from each other so that
they cannot tangle, this setup can be very reliable.

The following are some items you may want to take into consideration
when selecting a buffer design:

- Filament capacity: each buffer must be able to fit a length of
  filament approximately equal to the length of the bowden tube
  between Trad Rack and the printer's toolhead/extruder.
- Number of filament loops: some buffer designs wrap the filament
  around a wheel. The filament can be looped around the wheel for part of a
  revolution, a full revolution, or multiple revolutions. In general, a buffer
  with more loops takes up less space for the same filament capacity, while a
  buffer with less loops does not add as much resistance to filament movement.
  If you have the space for it, a buffer with 1 or less loops is preferred.
- Snag points and filament constraint: some buffer designs with wheels
  may have the possibility for filament to slip around the wheel and
  get stuck. It is important to keep the filament well-constrained and
  prevent snagging. In addition, it is important to ensure the filament does not
  cross over itself in ways that may cause a tangle.
- Induced filament movement: it is important that the buffer does not
  push or pull the filament while it is buffered, as this may block
  the movement of Trad Rack's selector or prevent Trad Rack from being
  able to grab the filament. Long narrow buffers (in which the filament follows
  one wall, makes a U-turn, and follows an opposite parallel wall back) are
  particularly good at avoiding this problem, since the only forces exerted by
  the walls of the buffer on the filament are perpendicular to the filament. If
  you are having problems with the buffer causing the filament to move, you can
  try adding a section of PTFE tube with a 2mm inner diameter at the inlet to
  Trad Rack's filament modules to add more resistance. See the
  [Extruder Syncing document](Extruder_Syncing.md) for ways to compensate for
  the added resistance by using Trad Rack as a secondary extruder.
- Bend radius: different filament types may require a different minimum bend
  radius in order to avoid breaking the filament or causing excess resistance in
  the filament path. For example, filled filaments may require a larger minimum
  bend radius than non-filled filaments. It is important to select a buffer that
  satisfies the largest minimum bend radius of the filaments you might use.
- Mounting: some buffer designs are meant to be attached to the
  printer. Others fit inside a filament drybox so that the filament
  inside the buffer is kept dry. You may want to consider how the
  buffer will fit into your printer and filament management setup when
  selecting a buffer design.

See the table below for some example recommended buffers[^4]:

(TODO: insert table here)

## Mounting

Trad Rack can be mounted however you want: to your printer, to a
filament storage enclosure, to a table, etc. For most setups, it will
likely be most convenient to mount Trad Rack directly to your printer.

### Provided mounts

We provide mounting brackets for attaching Trad Rack to the side of an
Annex K3 printer; these brackets can be found in the
[Trad Rack Mounts folder](/STLs/Trad%20Rack%20Mounts/).

### Other recommended mounts

The following community-designed mounts are also recommended[^4]:

(TODO: insert table here)

### Designing your own mounts

The recommended way to mount Trad Rack is to attach brackets to the
underside of its 2020 extrusion, and then attach those brackets to
whatever you are mounting Trad Rack to. Depending on your setup, you
may also want to consider using an extra-long extrusion for Trad Rack
so that you can use more sides of the extrusion to attach brackets at
the ends.

It is recommended that the underside of Trad Rack's extrusion is
spaced at least 11.6mm from any surface below it in order to maintain
compatibility with any electronics mounts that are attached to the
underside of the extrusion.

## Optional add-ons

The following are optional items that can be added to your printer for
use with Trad Rack.

### Extruder sync sensor

See the [Extruder Syncing document](Extruder_Syncing.md).

### Toolhead filament cutter

An alternative to PrusaSlicer's tip-shaping process for getting clean
filament tips at the beginning of an unload is to use a filament
cutter. A filament cutter cuts off the end of the filament, which may
be bulged or stringy, in order to leave a clean end.

Trad Rack currently supports using a filament cutter mounted to the
printer's toolhead (see the
[Customization document](klipper/Customization.md#tip-shaping) for
more details on software setup). Support for a filament cutter either
inline with the bowden tube between Trad Rack and the toolhead or
mounted to Trad Rack's selector is planned but not implemented yet.

### Nozzle wiper and purge bucket

The most common method for purging material at the end of a toolchange
with Trad Rack is to use PrusaSlicer's wipe tower. However, you may
want to consider using a purge bucket with a nozzle wiper for a
portion of the purging[^6] to reduce the size of the wipe tower and
reclaim build space.

[^6]: To completely eliminate the wipe tower, additional code would be
required to tell Klipper how much material to purge depending on the
specific filaments being unloaded and loaded. However, it is
recommended to always at least use a small wipe tower to ensure the
hotend is primed for printing (as is commonly done on toolchanger and
IDEX setups).

In addition, a nozzle wiper and purge bucket may be useful if you are
replacing PrusaSlicer's ramming procedure (which deposits material on
the wipe tower) with your own tip-shaping procedure that produces
waste material that must be collected. See the
[Customization document](klipper/Customization.md#tip-shaping) for
more details on tip-shaping options.

For the Annex K3 printer, the
[trad_rack_optional.cfg config file](/Klipper_Stuff/klipper_config/trad_rack_optional.cfg)
provides the option of performing the tip-shaping process over its
purge bucket and wiping the nozzle afterwards. This option can work
with other printers as well (with their own bucket/wiper setup) if
`Go_To_Purge_Location` and `Wipe_Nozzle` macros are included, either
by copying these from a provided
[K3 config file](https://github.com/Annex-Engineering/ANNEX-Printer-Firmware/tree/main/Klipper_and_Klipper_Derivatives/K3)
or by writing your own implementation of these macros (or by
modifying/replacing trad_rack_optional.cfg). If using this option on
another printer, it is recommended that you pick a bucket/wiper that
stays at a constant height relative to the toolhead so that you do not
risk the toolhead crashing into the print when it moves to the bucket.
