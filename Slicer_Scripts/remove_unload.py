import sys, re

source_file = sys.argv[1]

with open(source_file, "r") as f:
    lines = f.readlines()
    to_skip = []
    start = None
    for i in range(len(lines)):        
        if re.match("G1 E-15[.0]* F6000", lines[i]):
            start = i
        elif start is not None and ("; Filament-specific end gcode" in lines[i]):
            to_skip.append((start, i))
            start = None

with open(source_file, "w") as f:
    start = 0
    for s in to_skip:
        for i in range(start, s[0]):
            f.write(lines[i])
        start = s[1]
    for i in range(start, len(lines)):
        f.write(lines[i])
