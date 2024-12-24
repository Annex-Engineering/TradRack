# Tool Mapping

This document contains info on tool mapping/lane groups and how
runouts are handled.

By default, each tool or extruder number specified in gcode
corresponds to a lane module on Trad Rack. However, tool numbers can
be decoupled from lane numbers. This allows reassigning a lane to a
tool with a different number and/or assigning a group of lanes to the
same tool.

**Table of Contents**
- [Use cases](#use-cases)
  - [Chaining identical spools together](#chaining-identical-spools-together)
  - [Remapping right before a print](#remapping-right-before-a-print)
- [Slicer and gcode](#slicer-and-gcode)
- [Runouts](#runouts)

## Use cases

Tool mapping has a couple use cases:

### Chaining identical spools together

If you have multiple identical spools of filament, you may want to
swap from one to the next each time one runs out during a print. This
can be accomplished by feeding each spool into a different lane module
in Trad Rack and assigning each of these lanes to the same tool so
that Trad Rack will recognize that they are interchangeable. When
filament from one lane runs out, Trad Rack will automatically initiate
a toolchange to filament from another lane that is assigned to the
same tool, and it will continue the print.

Since you can have as many tools/lane groups as you want (up to the
number of lanes), you can use up old spools while still being able to
print with multiple colors/materials.

### Remapping right before a print

If you already have filaments loaded into Trad Rack and you want to
run a print file that you sliced previously, you don't have to be
restricted to using the same color/material order as what is defined
in the gcode. The tool numbers match the order defined in the gcode,
but you can map whichever lane(s) you want to each tool so that the
correct filament is used for each part of the print.

## Slicer and gcode

The slicer does not need to be aware of the lane groups; it only
tells Trad Rack which tool needs to be loaded. Extruder numbers in the
slicer correspond directly to tool numbers.

Each tool has a default lane that is loaded with every
`TR_LOAD_TOOLHEAD TOOL=<tool index>` or `T<tool index>` command.
Whenever the filament from one lane runs out, another lane in the
tool's lane group will become the new default lane. In addition, if
you load the toolhead with filament from a specific lane using
`TR_LOAD_TOOLHEAD LANE=<lane index>`, that lane will become the new
default lane for its assigned tool.
[Several gcode commands](klipper/G-Codes.md#tool-mapping) are
available for viewing and manipulating the tool mapping/lane
groups.

## Runouts

Whenever Trad Rack detects that the filament has run out (via the
selector filament sensor), it will pause the print, unload the current
filament, and attempt to load new filament from a lane assigned to the
same tool. If successful, it will resume the print automatically. If
unsuccessful, a message will be sent to the console prompting the user
to take action and resume the print manually.
