# PrusaSlicer Setup

This document explains how to add the provided PrusaSlicer profiles
to your slicer, as well as setup tips pertaining to PrusaSlicer
specifically. Setting names used here follow the "parameter names"
that are used in the slicer config files; you can use the search
function to see which settings these refer to in the GUI.

## Adding provided profiles
A vendor bundle for PrusaSlicer 2.6.0 can be found in the
[PrusaSlicer_2.6.0 folder](/Slicer_Config/PrusaSlicer_2.6.0). To use
the included profiles, first copy the contents of the folder to the
`vendor` folder located in:

- PrusaSlicer ***stable***\* version:
  - Windows: `C:\Users\<username>\AppData\Roaming\PrusaSlicer`
  - Mac: `/Users/<username>/Library/Application Support/PrusaSlicer`
- PrusaSlicer ***alpha***\* version:
  - Windows: `C:\Users\<username>\AppData\Roaming\PrusaSlicer-alpha`
  - Mac: `/Users/<username>/Library/Application Support/PrusaSlicer-alpha`

\* the vendor .ini file will have the slicer version it is meant for
written at the top. Make sure you check whether it is a stable or
alpha version so that you copy the items to the correct folder.

Next, launch PrusaSlicer and open the Configuration Wizard by clicking
`Configuration > Configuration Wizard`. Click on "Other Vendors" on
the left side and ensure "Annex Engineering" is checked.

![Check "Annex Engineering"](images/ps_wizard_vendor.png?raw=true)

Click on "Annex Engineering FFF" on the left and select the printer
profile(s) you want to add.

![Select printer profiles](images/ps_wizard_printer.png?raw=true)

Click on "Filaments" on the left, select the names of all the printer
profiles you added, and ensure all of the filament profiles you want
are checked by clicking the "All" button on the right.

![Select filament profiles](images/ps_wizard_filament.png?raw=true)

Finally, click Finish. In the Plater tab, you should now be able to
select the Printer, Print settings, and Filament from the profiles
you just added.

![Plater: select profiles](images/ps_profile_selection.png?raw=true)

## Extruder count

Set `extruders_count` to match the number of tools on your Trad Rack.
This setting is located in the Printer Settings Tab.

## Setting up a print

See "9 Printing in Multi Material Mode" in the 
[Prusa MMU2S manual](https://www.prusa3d.com/downloads/manual/prusa3d_manual_mmu2s_en.pdf)
for details on how to set up a multimaterial print. In particular,
make sure to set the purge volumes, as these cannot be saved in a
profile.

## Modifying the profiles

If you modify the print, filament, or printer settings in the slicer,
you can use the save button to save a copy of your settings. A .ini
file will be saved to the corresponding `print`, `filament`, or
`printer` folder, located in the same parent folder as the `vendor`
folder. Alternatively, you can edit the `Annex_K3_TR.ini` file
directly in a text editor if you prefer.

## Experimental options

See the [Slicing](Slicing.md#experimental-options) document for more
details.
