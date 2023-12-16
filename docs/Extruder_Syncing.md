# Extruder Syncing

Extruder syncing is an optional feature that syncs Trad Rack's
filament driver to the extruder during printing, as well as during any
extrusion moves within toolhead loading or unloading that would
normally involve only the extruder. It is highly recommended to use
this feature in conjunction with a
[Belay sensor](#belay-extruder-sync-sensor) rather than by itself.

**Table of Contents**
- [Purpose](#purpose)
- [Belay (extruder sync sensor)](#belay-extruder-sync-sensor)
- [Enabling extruder syncing](#enabling-extruder-syncing)

## Purpose

Long filament paths, buffers, or very heavy spools can cause extra resistance
in filament movement, potentially causing the printer's extruder to
struggle. One solution is to use Trad Rack as a secondary extruder in
series with the primary extruder to take some of the load. With
extruder syncing enabled, Trad Rack's filament driver motor is synced
to the primary extruder.

## Belay (extruder sync sensor)

By default, with extruder syncing enabled Trad Rack's filament driver
will be directly synced to the primary extruder. It is not recommended
to use extruder syncing in this way without a sensor since Trad Rack's
filament driver and the primary extruder may gradually drift out of
sync during a long print with no toolchanges or very long extrusion
distances between toolchanges.

The [Belay sensor][1] solves this problem by dynamically
adjusting the `rotation_distance` setting of Trad Rack's filament
driver to keep it in sync with the primary extruder. See
[the Belay repository][1] for details.

[1]: https://github.com/Annex-Engineering/Belay

## Enabling extruder syncing

To enable extruder syncing, set `sync_to_extruder` to `True` in the
[trad_rack config section](klipper/Config_Reference.md#trad_rack).
The [TR_SYNC_TO_EXTRUDER gcode command](klipper/G-Codes.md#tr_sync_to_extruder)
can also be used to enable syncing, and
[TR_UNSYNC_FROM_EXTRUDER](klipper/G-Codes.md#tr_unsync_from_extruder)
can be used to disable syncing. However, any changes made by these
gcode commands will not persist across restarts.
