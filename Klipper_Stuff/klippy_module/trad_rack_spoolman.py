# Support for using Spoolman with Trad Rack
#
# Copyright (C) 2023 Ryan Ghosh <rghosh776@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
class TradRackSpoolman:
    def __init__(self, config):
        self.printer = config.get_printer()

        # register event handlers
        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        event_handlers = [
            (self.handle_assign_id,     ["trad_rack:assigned_id"]),
            (self.handle_remove_id,     ["trad_rack:removed_lane_id"]),
            (self.handle_reset_ids,     ["trad_rack:reset_lane_ids"]),
            (self.handle_set_active,    ["trad_rack:load_complete",
                                         "trad_rack:forced_active_lane"]),
            (self.handle_set_inactive,  ["trad_rack:unload_complete",
                                         "trad_rack:reset_active_lane"])
        ]
        for callback, events in event_handlers:
            for event in events:
                self.printer.register_event_handler(event, callback)

        # other variables
        self.lane_count = None
        self.id_map = []
        self.webhooks = self.printer.lookup_object('webhooks')
        self.trad_rack = None

        # register gcode commands
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('TR_PRINT_LANE_IDS',
                                    self.cmd_TR_PRINT_LANE_IDS,
                                    self.cmd_TR_PRINT_LANE_IDS_help)

    def handle_connect(self):
        self.trad_rack = self.printer.lookup_object('trad_rack')
        self.lane_count = self.trad_rack.lane_count
        self._reset_id_map()

    def handle_assign_id(self, lane, id):
        # check for ID conflict
        curr_lane = self._get_assigned_lane(id)
        if curr_lane is not None and lane != curr_lane:
            raise self.gcode.error("ID {id} is already assigned to lane "
                                   "{curr_lane}. To assign it to lane {lane}, "
                                   "use TR_REMOVE_LANE_ID LANE={curr_lane} "
                                   "before trying again."
                                   .format(id=id, curr_lane=curr_lane,
                                           lane=lane))
        
        # assign ID
        self.id_map[lane] = id

    def handle_remove_id(self, lane):
        self.id_map[lane] = None

    def handle_reset_ids(self):
        self._reset_id_map()

    def handle_set_active(self, lane):
        id = self.id_map[lane]
        self._set_active_spool(id)
        if id is None:
            self.gcode.respond_info("WARNING: No spool ID assigned to lane %d"
                                    % lane)

    def handle_set_inactive(self):
        self._set_active_spool(None)
        
    # gcode commands
    cmd_TR_PRINT_LANE_IDS_help = "Print Spoolman ID for each lane"
    def cmd_TR_PRINT_LANE_IDS(self, gcmd):
        msg = ""
        for lane in range(self.lane_count):
            # create id message
            id = self.id_map[lane]
            if id is None:
                id_msg = "No ID assigned"
            else:
                id_msg = "ID=%d" % id

            # create tool message
            tool = self.trad_rack.tool_map[lane]
            tool_msg = ", Tool=%d" % tool

            # create name message
            name = self.trad_rack.tool_names[tool]
            if name is None:
                name_msg = ""
            else:
                name_msg = ", Name=%s" % name

            msg += "Lane {}: {}{}{}\n".format(lane, id_msg, tool_msg, name_msg)
        gcmd.respond_info(msg)

    # helper functions
    def _reset_id_map(self):
        self.id_map = [None] * self.lane_count

    def _get_assigned_lane(self, id):
        for lane in range(len(self.id_map)):
            if self.id_map[lane] == id:
                return lane
        return None
    
    def _set_active_spool(self, id):
        self.webhooks.call_remote_method("spoolman_set_active_spool",
                                         spool_id=id)

def load_config(config):
    return TradRackSpoolman(config)
