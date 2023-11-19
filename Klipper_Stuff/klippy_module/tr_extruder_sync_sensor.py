# Support for an extruder-syncing sensor as an add-on for Trad Rack
#
# Copyright (C) 2023 Ryan Ghosh <rghosh776@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
DIRECTION_UPDATE_INTERVAL = 0.1
POSITION_TIME_DIFF = 0.3

class TradRackExtruderSyncSensor:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()

        # register event handlers
        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        enable_events = [
            "trad_rack:synced_to_extruder"
        ]
        disable_events = [
            "trad_rack:unsyncing_from_extruder"
        ]
        for event in enable_events:
            self.printer.register_event_handler(event, self.handle_enable)
        for event in disable_events:
            self.printer.register_event_handler(event, self.handle_disable)
        
        # register button
        sensor_pin = config.get('sensor_pin')
        buttons = self.printer.load_object(config, "buttons")
        buttons.register_buttons([sensor_pin], self.sensor_callback)

        # read other values
        self.multiplier_high = config.getfloat(
            'multiplier_high', default=1.05, minval=1.)
        self.multiplier_low = config.getfloat(
            'multiplier_low', default=0.95, minval=0., maxval=1.)
        self.debug_level = config.getint(
            'debug_level', default=0., minval=0., maxval=2.)

        # other variables
        self.enabled = False
        self.last_state = False
        self.last_direction = True
        self.set_multiplier = None
        self.enable_conditions = [lambda : not self.enabled]
        self.disable_conditions = [lambda : self.enabled]
        self.gcode = self.printer.lookup_object('gcode')
        self.toolhead = None
        self.update_direction_timer = self.reactor.register_timer(
            self.update_direction)
    
    def handle_connect(self):
        self.toolhead = self.printer.lookup_object('toolhead')
        trad_rack = self.printer.lookup_object('trad_rack')
        self.set_multiplier = trad_rack.set_fil_driver_multiplier
        self.enable_conditions.append(trad_rack.is_fil_driver_synced)
        self.disable_conditions.append(trad_rack.is_fil_driver_synced)

    def handle_enable(self):
        for condition in self.enable_conditions:
            if not condition():
                return
        self.enabled = True
        self.reactor.update_timer(self.update_direction_timer, self.reactor.NOW)
        self.update_multiplier()

    def handle_disable(self):
        for condition in self.disable_conditions:
            if not condition():
                return
        self.reset_multiplier()
        self.reactor.update_timer(self.update_direction_timer,
                                  self.reactor.NEVER)
        self.enabled = False

    def sensor_callback(self, eventtime, state):
        self.last_state = state
        if self.enabled:
            self.update_multiplier()
            
    def update_multiplier(self, print_msg=True):
        if self.last_state == self.last_direction:
            # compressed/forward or expanded/backward
            multiplier = self.multiplier_high
        else:
            # compressed/backward or expanded/forward
            multiplier = self.multiplier_low
        self.set_multiplier(multiplier)
        if (print_msg and self.debug_level >= 1) or self.debug_level >= 2:
            self.gcode.respond_info("Set filament driver multiplier: %f"
                                    % multiplier)

    def reset_multiplier(self):
        self.set_multiplier(1.)
        if self.verbose:
            self.gcode.respond_info("Reset filament driver multiplier")

    def update_direction(self, eventtime):
        mcu = self.printer.lookup_object('mcu')
        print_time = mcu.estimated_print_time(eventtime)
        extruder = self.toolhead.get_extruder()
        curr_pos = extruder.find_past_position(print_time)
        past_pos = extruder.find_past_position(
            max(0., print_time - POSITION_TIME_DIFF))
        prev_direction = self.last_direction
        self.last_direction = (curr_pos >= past_pos)
        if self.last_direction != prev_direction:
            if self.debug_level >= 2:
                self.gcode.respond_info("New extruder sensor direction: %s"
                                        % self.last_direction)
            self.update_multiplier(False)
        return eventtime + DIRECTION_UPDATE_INTERVAL

    def get_status(self, eventtime):
        return {
            'last_state': self.last_state,
            'enabled': self.enabled
        }

def load_config(config):
    return TradRackExtruderSyncSensor(config)
