# Quick Start

This document provides an overview of how to get Trad Rack running.
Each section should be completed before moving on to the next.

## Printing and assembly
- [Print Settings and File Key](/Print_Settings_and_File_Key.txt):
  print settings to use and info on reading the STL filenames.
- [STLs folder](/STLs): contains all STL files.
- [eDrawing](/eDrawings): 3D model for understanding how the parts
  fit together and helping with assembly. You will need [eDrawings
  Viewer](https://www.edrawingsviewer.com/) to open this file.

## Wiring

See the [Wiring document](Wiring.md).

## Klipper installation

See the [Klipper installation document](klipper/Installation.md).

## Servo calibration

This section involves setting the rotation direction and angles of the
servo. You will need to have Trad Rack fully assembled, wired, and
connected to your printer with Klipper running.

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
[servo horn angle](#servo-horn-angle). Otherwise, in your Klipper
config, swap the values of `servo_down_angle` and `servo_up_angle` in
the [trad_rack] section. Then restart Klipper and continue.

### Servo horn angle

Run the following gcode command:

```
TR_SERVO_DOWN FORCE=1
```

Loosen the screw in the center of the servo horn and the screw in
the clamp.

For this section, you will need the servo jig that has "HORN ANGLE"
written on the side:

![HORN ANGLE servo jig](images/horn_angle_jig.png?raw=true)

Insert the servo into the servo jig. You may need to rotate the
servo horn around the servo spline by hand so that it is at the
correct angle for the bearing to fit into the jig. The servo's wires
should be exiting to the left to match the orientation in the image:

![Servo in HORN ANGLE jig](images/servo_in_horn_angle_jig.png?raw=true)

Tighten the two screws you loosened earlier. Then remove the servo
jig.

## Servo up angle

For this section, you will need the servo jig that has "UP ANGLE"
written on the side:

![UP ANGLE servo jig](images/up_angle_jig.png?raw=true)

Insert the servo into the servo jig. The servo's wires should be
exiting to the left to match the orientation in the image:

![Servo in UP ANGLE jig](images/servo_in_up_angle_jig.png?raw=true)

Run the following gcode command. Observe the "commanded angle" that is
reported in the console:

```
TR_SERVO_TEST
```

Look at the front of the servo jig and check the position of the screw
in the bearing relative to the slots. The goal of this section is
to get the screw close to lining up with the slots:

![UP ANGLE servo jig slot check](images/up_angle_jig_slot_check.png?raw=true)

There is a range of acceptable angles, and the screw does not
have to exactly align with the slots. If the servo angle is within the
target range, the jig will be able to slide far enough over the servo
that the screw protrudes from the front of the jig:

| Wrong angle (screw can't protrude)                  | Angle within target range (screw protrudes)       |
| ---                                                 | ---                                               |
| ![](images/up_angle_jig_no_protrusion.png?raw=true) | ![](images/up_angle_jig_protrusion.png?raw=true)  |

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
value. Remove the servo jig and restart Klipper. Then run the
following gcode command:

```
TR_SERVO_DOWN FORCE=1
```

Finally, reattach the servo to Trad Rack.

## Selector calibration

This section involves calibrating `lane_spacing`, as well as the min,
endstop, and max positions of the selector motor. You will need access
to filament (either a spool or a short piece is fine).

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

## Further reading

This marks the end of the required steps to get Trad Rack running.
See the [Overview document](README.md) to see the full list of
documents available. Some of these were already linked in this guide,
but there are additional ones that provide more information on what
values can be changed for fine tuning, what gcode commands are
available, etc.
