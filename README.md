# Trad Rack

Trad Rack is a multimaterial system for FFF printers with a focus on scalability at low cost.

This is currently in Internal Alpha, with no tenative public release date. 

A video of it in action can be found here: https://youtu.be/hxGiJGAnO-A

Our discord server can be found here: 

[![Join me on Discord](https://discord.com/api/guilds/641407187004030997/widget.png?style=banner2)](https://discord.gg/MzTR3zE)

![Image of TradRack](Images/render1.png?raw=true)

## Stats

- Single 2020 extrusion as the frame
- Pivoting arm on the selector that lowers a hobbed gear onto the filament, indirectly coupled to a servo through a spring
- MGN9 rail and either 6mm or 9mm 2GT belt for selector movement
- NEMA17 motor for selector movement, and either NEMA17 or 36mm round NEMA14 motor for filament movement

## Scalability

One of the main focuses of Trad Rack is allowing additional filament lanes to be added at the lowest possible cost and assembly/disassembly. Rather than using a separate drive gear (or drive gear pair) for each filament lane, Trad Rack uses a single drive gear pair mounted to the selector for the entire unit. One module is required for each filament lane, and modules can be attached or detached with one screw. Each module consists of the following parts:

- 1X printed module body
- 1X 623 bearing
- 1X M3x8 screw
- 1X M5x10 screw
- 1X M5 T-nut
- 1X bowden fitting

The extrusion, rail, and belt must be long enough to support the selected number of filament lanes, but they can be oversized in order to allow for additional modules to be added later.

## Acknowledgments

- Main filament-switching concept inspired by the [Prusa MMU2](https://github.com/prusa3d/Original-Prusa-i3/tree/MMU2)
- Idea to use a servo to engage/disengage with each filament inspired by the [SMuFF](https://github.com/technik-gegg/SMuFF-1.1)
