# Quick Start

This document provides an overview of how to get Trad Rack running.
Each section should be completed before moving on to the next.

## Printing and assembly
- [Print Settings and File Key](/Print_Settings_and_File_Key.txt):
  print settings to use and info on reading the STL filenames.
- [STL folder](/STLs): contains all STL files.
- [eDrawing](/eDrawings): 3D model for understanding how the parts
  fit together and helping with assembly. You will need [eDrawings
  Viewer](https://www.edrawingsviewer.com/) to open this file.

## Wiring

See the [Wiring](Wiring.md) document.

## Klipper installation

See the [Klipper installation](klipper/Installation.md) document.

## Servo calibration

This section involves setting the rotation direction and angle of the
servo. You will need to have Trad Rack fully assembled, wired, and
connected to your printer with Klipper running.

To prepare, remove the servo from Trad Rack by undoing the 2 screws
that attach it to the right carriage.

### Servo rotation direction

Run the following gcode command:

```
TR_SERVO_UP
```

Run the following gcode command and observe the motion of the servo.
When viewed from the front of the servo spline, the servo should
rotate clockwise.
    
```
TR_SERVO_DOWN FORCE=1
```

If the servo rotated clockwise, you can continue on to setting the
[servo horn angle](#servo-horn-angle). Otherwise, in your Klipper
config, swap the values of `servo_down_angle` and `servo_up_angle` in
the [trad_rack] section. Then restart Klipper and continue.

## Servo horn angle

Run the following gcode command:

```
TR_SERVO_DOWN FORCE=1
```

Loosen the screw in the center of the servo horn and the screw in
the clamp.

Insert the servo into the servo jig. You may need to rotate the
servo horn around the servo spline by hand so that it is at the
correct angle for the bearing to fit into the jig.

![Servo in jig](images/servo_in_jig.png?raw=true)

Tighten the two screws you loosened earlier. Then remove the servo jig
and reattach the servo to Trad Rack.

## Slicing

See the [Slicing](Slicing.md) document.

## Further reading

This marks the end of the required steps to get Trad Rack running.
See the [Overview](Overview.md) document to see the full list of
documents available. Some of these were already linked in this guide,
but there are additional ones that provide more information on what
values can be changed for fine tuning, what gcode commands are
available, etc.
