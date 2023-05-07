# SuperSlicer Setup

This document explains how to add the provided SuperSlicer profiles
to your slicer, as well as setup tips pertaining to SuperSlicer
specifically. Setting names used here follow the "parameter names"
that are used in the slicer config files; you can use the search
function to see which settings these refer to in the GUI.

## Adding provided profiles
A vendor bundle for SuperSlicer 2.4.58 can be found in the
[SuperSlicer_2.4.58 folder](/Slicer_Config/PrusaSlicer_2.4.58). To use
the included profiles, first copy the contents of the folder to the
`vendor` folder located in:

- Windows: `C:\Users\<username>\AppData\Roaming\SuperSlicer`
- Mac: `/Users/<username>/Library/Application Support/SuperSlicer`

Next, launch SuperSlicer and open the Configuration Wizard by clicking
`Configuration > Configuration Wizard`. Click on "Annex Engineering"
on the left and select the printer profile(s) you want to add.

![Select printer profiles](images/ss_wizard_printer.png?raw=true)

Click on "Filaments" on the left, select the names of all the printer
profiles you added, and ensure all of the filament profiles you want
are checked by clicking the "All" button on the right.

![Select filament profiles](images/ss_wizard_filament.png?raw=true)

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

## Purge volumes

In addition to the "Purging volumes" settings accessible from the
Plater tab, SuperSlicer has the ability to calculate purge volumes
automatically based on the pigment number assigned to each filament
(a decimal between 0 and 1). This is called "Advanced wipe tower purge
volume calculs". If this is enabled (by setting `wipe_advanced` to
true), the "Purging volumes" tables will be ignored. The provided
profiles have this enabled by default. Filament profiles with
various pigment amounts in 0.1 increments are included. If you leave
automatic purge volume calculation enabled, make sure to select the
corresponding filament profile in the Plater tab for each tool.

The purge volumes used in the provided profiles are for a mosquito
magnum, but I have not done much experimentation or optimization.
I would recommend doing your own tuning on purge volumes, try
different wipe advanced algorithms, try the purging volumes tables if
you prefer, etc. You can access the multiplier and algorithm settings,
as well as enable or disable automatic purge volume calculations, in
the "Single Extruder MM setup" section in the Printer Settings tab.
You might need to uncheck and recheck `single_extruder_multi_material`
in the Printer Settings tab to get this section to appear.

![Single extruder MM setup](images/ss_single_extruder_mm_setup.png?raw=true)

## Modifying the profiles

If you modify the print, filament, or printer settings in the slicer,
you can use the save button to save a copy of your settings. A .ini
file will be saved to the corresponding `print`, `filament`, or
`printer` folder, located in the same parent folder as the `vendor`
folder. Alternatively, you can edit the `Annex_K3_TR.ini` file
directly in a text editor if you prefer.

## Experimental options

See the [Slicing document](Slicing.md#experimental-options) for more
details.
