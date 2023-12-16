# Tool Naming

Coming soon. See the `work-name-groups-and-spoolman` branch.

This feature will allow assigning names to tools. Optionally,
toolchanges can be initiated by selecting a name rather than a tool
or lane. For example, the filament profile name in the slicer could
be passed as the name in the toolchange command so that the order of
extruders in the slicer and the order in which filaments are loaded
into trad rack will not matter (as long as the same name is assigned
to a tool). This feature may later tie into
[Spoolman support](Spoolman_Support.md) for automatically assigning
names to tools when a spool ID is assigned to a lane.
