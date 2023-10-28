# Support for an extruder-syncing sensor as an add-on for Trad Rack
#
# Copyright (C) 2023 Ryan Ghosh <rghosh776@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
class TradRackExtruderSyncSensor:
    def __init__(self, config):
        self.printer = config.get_printer()

        # register event handlers
        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        enable_events = [
            "trad_rack:load_complete",
            "trad_rack:forced_active_lane"
        ]
        disable_events = [
            "trad_rack:unload_started",
            "trad_rack:reset_active_lane"
        ]
        for event in enable_events:
            self.printer.register_event_handler(event, self.handle_enable)
        for event in disable_events:
            self.printer.register_event_handler(event, self.handle_disable)
        
        # register button
        sensor_pin = config.get('sensor_pin')
        buttons = config.get_printer().load_object(config, "buttons")
        buttons.register_buttons([sensor_pin], self.sensor_callback)

        # read other values
        self.multiplier_high = config.getfloat(
            'multiplier_high', default=1.05, minval=1.)
        self.multiplier_low = config.getfloat(
            'multiplier_low', default=0.95, minval=0., maxval=1.)
        self.verbose = config.getboolean('verbose', False)

        # other variables
        self.enabled = False
        self.last_state = False
        self.set_multiplier = None
        self.enable_conditions = [lambda : not self.enabled]
        self.disable_conditions = [lambda : self.enabled]
        self.gcode = self.printer.lookup_object('gcode')
    
    def handle_connect(self):
        trad_rack = self.printer.lookup_object('trad_rack')
        self.set_multiplier = trad_rack.set_fil_driver_multiplier
        self.enable_conditions.append(trad_rack.is_fil_driver_synced)
        self.disable_conditions.append(trad_rack.is_fil_driver_synced)

    def handle_enable(self):
        for condition in self.enable_conditions:
            if not condition():
                return
        self.enabled = True
        self.update_multiplier()

    def handle_disable(self):
        for condition in self.disable_conditions:
            if not condition():
                return
        self.reset_multiplier()
        self.enabled = False

    def sensor_callback(self, eventtime, state):
        self.last_state = state
        if self.enabled:
            self.update_multiplier()

    def update_multiplier(self):
        if self.last_state:
            # buffer is compressed
            multiplier = self.multiplier_high
        else:
            # buffer is expanded
            multiplier = self.multiplier_low
        self.set_multiplier(multiplier)
        if self.verbose:
            self.gcode.respond_info("Set filament driver multiplier: %f"
                                    % multiplier)

    def reset_multiplier(self):
        self.set_multiplier(1.)
        if self.verbose:
            self.gcode.respond_info("Reset filament driver multiplier")

    def get_status(self, eventtime):
        return {
            'last_state': self.last_state,
            'enabled': self.enabled
        }

def load_config(config):
    return TradRackExtruderSyncSensor(config)
