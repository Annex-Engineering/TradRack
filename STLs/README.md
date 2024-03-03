# What to print

In general, all parts in the STLs folder need to be printed. However,
there are some exceptions. Some subfolders contain files that you may
not need, and some parts have multiple variants that you can choose
from depending on what hardware you are using.

**Table of Contents**
- [Subfolders that may not be needed](#subfolders-that-may-not-be-needed)
- [STL variants](#stl-variants)
  - [Rail cart variants](#rail-cart-variants)
  - [Belt width variants](#belt-width-variants)

## Subfolders that may not be needed

The following subfolders contain STL files that you may or may not
need to print:

- [Electronics Mounts/Nebula Enclosure](Electronics%20Mounts/Nebula%20Enclosure/):
  these files are only required if you are using the Nebula control
  board. See the
  [Printer and hardware requirements document](/docs/Printer_and_Hardware_Requirements.md#electronics)
  for recommended mounts for other control board options.
- [Electronics Mounts/Base Distribution Board](Electronics%20Mounts/Base%20Distribution%20Board/):
  these files are only required if you are using the optional Trad
  Rack wiring kit.
- [Experimental](Experimental/): experimental parts. These are not
  recommended at this time.
- [Stationary Parts/Numbered Collet Clips](Stationary%20Parts/Numbered%20Collet%20Clips/):
  optional collet clips for labeling the lane modules.
- [Trad Rack Mounts/K3 Side Mount](Trad%20Rack%20Mounts/K3%20Side%20Mount/):
  brackets for mounting Trad Rack to the side of an Annex K3 printer.
  These brackets may also work for mounting Trad Rack to other
  printers or for serving as legs for Trad Rack to sit on a horizontal
  surface. See the
  [Printer and hardware requirements document](/docs/Printer_and_Hardware_Requirements.md#other-recommended-mounts)
  for alternative recommended mounting parts that may work better with
  other printers/setups.

## STL variants

Subfolders containing multiple variants of each part will generally
contain a README file that lists which files you need to print for
each option. The following sections explain file labels that apply to
all STL subfolders in general:

### Rail cart variants

Trad Rack uses an MGN9 rail with either a C-cart or an H-cart. Files
with `(c_cart)` in the filename are only required if using a C-cart.
Files with `(h_cart)` in the filename are only required if using an
H-cart.

### Belt width variants

Trad Rack is compatible with either 6mm or 9mm wide belts (and
pulleys sized for each). Files with `(6mm_belt)` in the filename are
only required if using 6mm wide belts and pulleys/idlers sized for 6mm
belts. Files with `(9mm_belt)` in the filename are only required if
using 9mm wide belts and pulleys/idlers sized for 9mm belts.
