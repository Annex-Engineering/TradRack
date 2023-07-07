# Trad Rack multimaterial system support
#
# Copyright (C) 2022-2023 Ryan Ghosh <rghosh776@gmail.com>
# based on code by Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging, math, os, time
from collections import deque
from extras.homing import Homing, HomingMove
import stepper, chelper, toolhead, kinematics.extruder

SERVO_NAME = 'servo tr_servo'
SELECTOR_STEPPER_NAME = 'stepper_tr_selector'
FIL_DRIVER_STEPPER_NAME = 'stepper_tr_fil_driver'

class TradRack:

    VARS_CALIB_BOWDEN_LOAD_LENGTH   = "calib_bowden_load_length"
    VARS_CALIB_BOWDEN_UNLOAD_LENGTH = "calib_bowden_unload_length"
    VARS_CONFIG_BOWDEN_LENGTH = "config_bowden_length"
    VARS_TOOL_STATUS = "tr_state_tool_status"

    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        self.printer.register_event_handler("klippy:ready", 
                                            self.handle_ready)

        # read spool and buffer pull speeds
        self.spool_pull_speed = config.getfloat(
            'spool_pull_speed', default=100., above=0.)
        self.buffer_pull_speed = config.getfloat(
            'buffer_pull_speed', default=self.spool_pull_speed, above=0.)

        # create toolhead
        self.tr_toolhead = TradRackToolHead(config, self.buffer_pull_speed)
        self.sel_max_velocity, _ = self.tr_toolhead.get_sel_max_velocity()

        # get servo
        self.servo = TradRackServo(self.printer.load_object(config, SERVO_NAME),
                                   self.tr_toolhead)

        # get kinematics and filament driver endstops
        self.tr_kinematics = self.tr_toolhead.get_kinematics()
        self.fil_driver_endstops = self.tr_kinematics.get_fil_driver_rail() \
                                                     .get_endstops()

        # set up toolhead filament sensor
        toolhead_fil_sensor_pin = config.get('toolhead_fil_sensor_pin', None)
        self.toolhead_fil_endstops = []
        if toolhead_fil_sensor_pin is not None:
            # register endstop
            ppins = self.printer.lookup_object('pins')
            mcu_endstop = ppins.setup_pin('endstop', toolhead_fil_sensor_pin)
            name = 'toolhead_fil_sensor'
            self.toolhead_fil_endstops.append((mcu_endstop, name))
            query_endstops = self.printer.load_object(config, 'query_endstops')
            query_endstops.register_endstop(mcu_endstop, name)

            # add filament driver stepper to endstop
            for stepper in self.tr_kinematics.get_fil_driver_rail() \
                                             .get_steppers():
                mcu_endstop.add_stepper(stepper)
        
        # read lane count and get lane positions
        self.lane_count = config.getint('lane_count', minval=2)
        self.lane_spacing = config.getfloat('lane_spacing', above=0.)
        self.lane_positions = []
        curr_pos = 0
        for i in range(self.lane_count):
            curr_pos += config.getfloat('lane_spacing_mod_' + str(i), 
                                        default=0.)
            offset = config.getfloat('lane_offset_' + str(i), default=0.)
            self.lane_positions.append(curr_pos + offset)
            curr_pos += self.lane_spacing

        # create bowden length filters
        bowden_samples = config.getint(
            'bowden_length_samples', default=10, minval=1)
        self.bowden_load_length_filter = MovingAverageFilter(bowden_samples)
        self.bowden_unload_length_filter = MovingAverageFilter(bowden_samples)

        # read other values
        self.servo_down_angle = config.getfloat('servo_down_angle')
        self.servo_up_angle = config.getfloat('servo_up_angle')
        self.servo_wait = config.getfloat(
            'servo_wait_ms', default=500., above=0.) / 1000.
        self.selector_unload_length = config.getfloat(
            'selector_unload_length', above=0.)
        self.config_bowden_length = self.bowden_load_length \
                                  = self.bowden_unload_length \
                                  = config.getfloat('bowden_length', above=0.)
        self.extruder_load_length = config.getfloat(
            'extruder_load_length', above=0.)
        self.hotend_load_length = config.getfloat(
            'hotend_load_length', above=0.)
        if self.toolhead_fil_endstops:
            self.toolhead_unload_length = config.getfloat(
                'toolhead_unload_length',
                above=0.)
        else:
            self.toolhead_unload_length = config.getfloat(
                'toolhead_unload_length',
                default=self.extruder_load_length + self.hotend_load_length,
                above=0.)
        self.selector_sense_speed = config.getfloat(
            'selector_sense_speed', default=40., above=0.)
        self.selector_unload_speed = config.getfloat(
            'selector_unload_speed', default=60., above=0.)
        self.toolhead_sense_speed = config.getfloat(
            'toolhead_sense_speed', default=self.selector_sense_speed, above=0.)
        self.extruder_load_speed = config.getfloat(
            'extruder_load_speed', default=60., above=0.)
        self.hotend_load_speed = config.getfloat(
            'hotend_load_speed', default=7., above=0.)
        self.toolhead_unload_speed = config.getfloat(
            'toolhead_unload_speed', default=self.extruder_load_speed, above=0.)
        self.load_with_toolhead_sensor = config.getboolean(
            'load_with_toolhead_sensor', True)
        self.unload_with_toolhead_sensor = config.getboolean(
            'unload_with_toolhead_sensor', True)
        self.fil_homing_retract_dist = config.getfloat(
            'fil_homing_retract_dist', 20., minval=0.)
        self.target_toolhead_homing_dist = config.getfloat(
            'target_toolhead_homing_dist', 
            max(10., self.toolhead_unload_length), above=0.)
        self.target_selector_homing_dist = config.getfloat(
            'target_selector_homing_dist', 10., above=0.)

        # other variables
        self.toolhead = None
        self.curr_lane = None       # which lane the selector is positioned at
        self.active_lane = None     # lane currently loaded in the toolhead
        self.retry_lane = None      # lane to reload before resuming
        self.next_lane = None       # next lane to load to toolhead if resuming
        self.load_length = 600      # filament homing move distance
        self.servo_raised = None
        self.extruder_synced = False
        self.lanes_unloaded = [False] * self.lane_count
        self.bowden_load_calibrated = False
        self.bowden_unload_calibrated = False
        self.bowden_load_lengths_filename = os.path.expanduser(
            "~/bowden_load_lengths.csv")
        self.bowden_unload_lengths_filename = os.path.expanduser(
            "~/bowden_unload_lengths.csv")

        # custom user macros
        gcode_macro = self.printer.load_object(config, 'gcode_macro')
        self.pre_unload_macro = gcode_macro.load_template(
            config, 'pre_unload_gcode', '')
        self.post_load_macro = gcode_macro.load_template(
            config, 'post_load_gcode', '')
        self.pause_macro = gcode_macro.load_template(
            config, 'pause_gcode', 'PAUSE')
        self.resume_macro = gcode_macro.load_template(
            config, 'resume_gcode', 'RESUME')

        # register gcode commands
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('TR_HOME', self.cmd_TR_HOME, 
            desc=self.cmd_TR_HOME_help)
        self.gcode.register_command('TR_GO_TO_LANE', self.cmd_TR_GO_TO_LANE, 
            desc=self.cmd_TR_GO_TO_LANE_help)
        self.gcode.register_command('TR_LOAD_LANE', self.cmd_TR_LOAD_LANE, 
            desc=self.cmd_TR_LOAD_LANE_help)
        self.gcode.register_command('TR_LOAD_TOOLHEAD', 
            self.cmd_TR_LOAD_TOOLHEAD, 
            desc=self.cmd_TR_LOAD_TOOLHEAD_help)
        self.gcode.register_command('TR_UNLOAD_TOOLHEAD', 
            self.cmd_TR_UNLOAD_TOOLHEAD, 
            desc=self.cmd_TR_UNLOAD_TOOLHEAD_help)
        self.gcode.register_command('TR_SERVO_DOWN', self.cmd_TR_SERVO_DOWN,
            desc=self.cmd_TR_SERVO_DOWN_help)
        self.gcode.register_command('TR_SERVO_UP', self.cmd_TR_SERVO_UP,
            desc=self.cmd_TR_SERVO_UP_help)
        self.gcode.register_command('TR_SET_ACTIVE_LANE', 
            self.cmd_TR_SET_ACTIVE_LANE,
            desc=self.cmd_TR_SET_ACTIVE_LANE_help)
        self.gcode.register_command('TR_RESET_ACTIVE_LANE', 
            self.cmd_TR_RESET_ACTIVE_LANE,
            desc=self.cmd_TR_RESET_ACTIVE_LANE_help)
        self.gcode.register_command('TR_RESUME',
            self.cmd_TR_RESUME,
            desc=self.cmd_TR_RESUME_help)
        self.gcode.register_command('TR_LOCATE_SELECTOR',
            self.cmd_TR_LOCATE_SELECTOR,
            desc=self.cmd_TR_LOCATE_SELECTOR_help)
        for i in range(self.lane_count):
            self.gcode.register_command('T{}'.format(i),
                self.cmd_SELECT_TOOL,
                desc=self.cmd_SELECT_TOOL_help)

    def handle_connect(self):
        self.toolhead = self.printer.lookup_object('toolhead')
        save_variables = self.printer.lookup_object('save_variables', None)
        if save_variables is None:
            raise self.printer.config_error("[save_variables] is required for "
                                            "trad_rack")
        self.variables = save_variables.allVariables

    def handle_ready(self):
        self._load_saved_state()
        
    def _load_saved_state(self):
        # load bowden lengths if the user has not changed the config value
        prev_config_bowden_length = self.variables.get(
            self.VARS_CONFIG_BOWDEN_LENGTH)
        if prev_config_bowden_length \
            and self.config_bowden_length == prev_config_bowden_length:
            # update load length
            load_length_stats = self.variables.get(
                self.VARS_CALIB_BOWDEN_LOAD_LENGTH)
            if load_length_stats:
                self.bowden_load_length = load_length_stats['new_set_length']
                for _ in range(load_length_stats['sample_count']):
                    self.bowden_load_length_filter.update(
                        self.bowden_load_length)
            
            # update unload length
            unload_length_stats = self.variables.get(
                self.VARS_CALIB_BOWDEN_UNLOAD_LENGTH)
            if unload_length_stats:
                self.bowden_unload_length = \
                    unload_length_stats['new_set_length']
                for _ in range(unload_length_stats['sample_count']):
                    self.bowden_unload_length_filter.update(
                        self.bowden_unload_length)
        else:
            # save bowden_length config value
            self.gcode.run_script_from_command(
                "SAVE_VARIABLE VARIABLE=%s VALUE=\"%s\""
                % (self.VARS_CONFIG_BOWDEN_LENGTH, self.config_bowden_length))

    # gcode commands
    cmd_TR_HOME_help = "Home Trad Rack's selector"
    def cmd_TR_HOME(self, gcmd):
        # check for filament in the selector
        if self._query_selector_sensor():
            raise self.gcode.error("Cannot home with filament in selector")

        # reset current lane
        self.curr_lane = None

        # raise servo
        self._raise_servo()
        
        # home selector
        homing_state = TradRackHoming(self.printer, self.tr_toolhead)
        homing_state.set_axes([0])
        try:
            self.tr_kinematics.home(homing_state)
        except self.printer.command_error:
            if self.printer.is_shutdown():
                raise self.printer.command_error(
                    "Homing failed due to printer shutdown")
            self.printer.lookup_object('stepper_enable').motor_off()
            raise

    cmd_TR_GO_TO_LANE_help = "Move Trad Rack's selector to a filament lane"
    def cmd_TR_GO_TO_LANE(self, gcmd):
        self._go_to_lane(gcmd.get_int('LANE', None))

    cmd_TR_LOAD_LANE_help = ("Load filament from the spool into Trad Rack in "
                             "the specified lane")
    def cmd_TR_LOAD_LANE(self, gcmd):
        lane = gcmd.get_int('LANE', None)
        self._load_lane(lane, gcmd, gcmd.get_int('RESET_SPEED', 1))


    cmd_TR_LOAD_TOOLHEAD_help = "Load filament from Trad Rack into the toolhead"
    def cmd_TR_LOAD_TOOLHEAD(self, gcmd):
        start_lane = self.active_lane
        lane = gcmd.get_int('LANE', None)
        try:
            self._load_toolhead(lane, gcmd, 
                                gcmd.get_float('BOWDEN_LENGTH', None, 
                                               minval=0.),
                                gcmd.get_float('EXTRUDER_LOAD_LENGTH', None, 
                                               minval=0.),
                                gcmd.get_float('HOTEND_LOAD_LENGTH', None, 
                                               minval=0.))
        except:
            logging.warning("trad_rack: Toolchange from lane {} to {} failed"
                            .format(start_lane, lane), exc_info=True)
            self._send_pause()
    
    cmd_TR_UNLOAD_TOOLHEAD_help = "Unload filament from the toolhead"
    def cmd_TR_UNLOAD_TOOLHEAD(self, gcmd):
        self._unload_toolhead(gcmd)

    cmd_TR_SERVO_DOWN_help = "Lower the servo"
    def cmd_TR_SERVO_DOWN(self, gcmd):
        if not gcmd.get_int('FORCE', 0):
            # check that the selector is at a lane
            if self.curr_lane is None or not self._is_selector_homed:
                raise self.gcode.error("Selector must be moved to a lane "
                                       "before lowering the servo")

        # lower servo
        self._lower_servo()

    cmd_TR_SERVO_UP_help = "Raise the servo"
    def cmd_TR_SERVO_UP(self, gcmd):
        # raise servo
        self._raise_servo()

    cmd_TR_SET_ACTIVE_LANE_help = ("Set lane number that is currently loaded "
                                   "in the toolhead")
    def cmd_TR_SET_ACTIVE_LANE(self, gcmd):
        # get lane
        lane = gcmd.get_int('LANE', None)

        # check lane
        self._check_lane_valid(lane)

        # check for filament in the selector
        if not self._query_selector_sensor():
            raise self.gcode.error("Cannot set active lane without filament "
                                   "in selector")

        # set selector position
        print_time = self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[0] = self.lane_positions[lane]
        self.tr_toolhead.set_position(pos, homing_axes=(0,))
        stepper_enable = self.printer.lookup_object('stepper_enable')
        enable = stepper_enable.lookup_enable(SELECTOR_STEPPER_NAME)
        enable.motor_enable(print_time)

        # set current lane and active lane
        self.curr_lane = lane
        self.active_lane = lane

    cmd_TR_RESET_ACTIVE_LANE_help = ("Resets active lane to None to indicate "
                                     "the toolhead is not loaded")
    def cmd_TR_RESET_ACTIVE_LANE(self, gcmd):
        self.active_lane = None

    cmd_TR_RESUME_help = ("Resume after a failed load or unload")
    def cmd_TR_RESUME(self, gcmd):
        # retry loading lane
        self._load_lane(self.retry_lane, gcmd)

        # load next filament into toolhead
        self._load_toolhead(self.next_lane, gcmd)

        # resume
        gcmd.respond_info("Toolhead loaded succesfully. Resuming print")
        self.resume_macro.run_gcode_from_command()

    cmd_TR_LOCATE_SELECTOR_help = ("Ensures the position of Trad Rack's "
                                   "selector is known so that it is ready for "
                                   "a print")
    def cmd_TR_LOCATE_SELECTOR(self, gcmd):
        if self._query_selector_sensor():
            if self._is_selector_homed():
                if self.active_lane is None:
                    if self.curr_lane is None:
                        # ask user to set the active lane or reload the lane
                        gcmd.respond_info("Selector sensor is triggered but no "
                                          "active lane is set. Please use "
                                          "TR_SET_ACTIVE_LANE if the toolhead "
                                          "is already loaded, else remove the "
                                          "filament and use TR_LOAD_LANE to "
                                          "reload the current lane. Then use "
                                          "RESUME to resume the print.")
                        self._send_pause()
                    else:
                        # unload selector into current lane
                        self._unload_selector(gcmd)
                # (else assume the toolhead is already loaded)
            else:
                if self.active_lane is None:
                    # ask user to set the active lane or home and reload the
                    # lane
                    gcmd.respond_info("Selector sensor is triggered but no "
                                      "active lane is set. Please use "
                                      "TR_SET_ACTIVE_LANE if the toolhead "
                                      "is already loaded, else remove the "
                                      "filament and use TR_HOME to home the "
                                      "selector and TR_LOAD_LANE to "
                                      "reload the current lane. Then use "
                                      "RESUME to resume the print.")
                    self._send_pause()
                else:
                    # set selector position and enable motor
                    # (this allows printing again without reloading the
                    # toolhead if the motor was disabled after the last print)
                    self.cmd_TR_SET_ACTIVE_LANE(self.gcode.create_gcode_command(
                        "TR_SET_ACTIVE_LANE", "TR_SET_ACTIVE_LANE", 
                        {"LANE": self.active_lane}))
                    gcmd.respond_info("Set lane %d as the active lane" 
                                      % (self.active_lane))
        else:
            self.active_lane = None
            if not self._is_selector_homed():
                self.cmd_TR_HOME(self.gcode.create_gcode_command(
                    "TR_HOME", "TR_HOME", {}))

    cmd_SELECT_TOOL_help = ("Load filament from Trad Rack into the toolhead "
                            "with T<index> commands")
    def cmd_SELECT_TOOL(self, gcmd):
        lane = int(gcmd.get_command().partition('T')[2])
        params = gcmd.get_command_parameters()
        params["LANE"] = lane
        self.cmd_TR_LOAD_TOOLHEAD(self.gcode.create_gcode_command(
            "TR_LOAD_TOOLHEAD", "TR_LOAD_TOOLHEAD", params))

    # helper functions
    def _lower_servo(self, toolhead_dwell=False):
        self.tr_toolhead.wait_moves()
        self.servo.set_servo(angle=self.servo_down_angle)
        if self.servo_raised or self.servo_raised is None:
            self.tr_toolhead.dwell(self.servo_wait)
            if toolhead_dwell:
                self.toolhead.dwell(self.servo_wait)
        self.servo_raised = False
    
    def _raise_servo(self, toolhead_dwell=False, tr_toolhead_dwell=True,
                     wait_moves=True, print_time=None):
        if wait_moves:
            self.tr_toolhead.wait_moves()
        self.servo.set_servo(angle=self.servo_up_angle, print_time=print_time)
        if not self.servo_raised:
            if tr_toolhead_dwell:
                self.tr_toolhead.dwell(self.servo_wait)
            if toolhead_dwell:
                self.toolhead.dwell(self.servo_wait)
        self.servo_raised = True
    
    def _get_time(self):
        return self.printer.get_reactor().monotonic()

    def _is_selector_homed(self):
        return 'x' in self.tr_toolhead.get_kinematics() \
                                      .get_status(self._get_time()) \
                                      ['homed_axes']

    def _query_selector_sensor(self):
        move_time = self.tr_toolhead.get_last_move_time()
        return not not self.fil_driver_endstops[0][0].query_endstop(move_time)
    
    def _check_lane_valid(self, lane):
        if lane is None or lane > self.lane_count - 1 or lane < 0:
            raise self.gcode.error("Invalid LANE")
    
    def _reset_fil_driver(self):
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[1] = 0.
        self.tr_toolhead.set_position(pos, homing_axes=(1,))
        if self.extruder_synced:
            e_stepper = self.toolhead.get_extruder().extruder_stepper.stepper
            e_stepper.set_position((0., 0., 0.))
    
    def _go_to_lane(self, lane):
        # check if homed
        if not self._is_selector_homed():
            raise self.gcode.error("Must home selector first")

        # check lane
        self._check_lane_valid(lane)
        if lane == self.curr_lane:
            return
        
        # check for filament in the selector
        if self._query_selector_sensor():
            raise self.gcode.error("Cannot change lane with filament "
                                   "in selector")

        # raise servo
        self._raise_servo()

        # move to lane
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[0] = self.lane_positions[lane]
        self.tr_toolhead.move(pos, self.sel_max_velocity)

        # set current lane
        self.curr_lane = lane

    def _load_lane(self, lane, gcmd, reset_speed=False):
        # reset lane speed
        if reset_speed and lane is not None:
            self.lanes_unloaded[lane] = False

        # move selector
        self._go_to_lane(lane)

        # lower servo and turn the drive gear until filament is detected
        self._lower_servo()
        self.tr_toolhead.wait_moves()
        gcmd.respond_info("Please insert filament in lane %d" % (lane))

        # load filament into the selector
        self._load_selector(lane)

        # retract filament into the module
        self._reset_fil_driver()
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[1] -= self.selector_unload_length
        self.tr_toolhead.move(pos, self.selector_unload_speed)

        # reset filament driver position
        self._reset_fil_driver()

        # raise servo
        self._raise_servo()

        gcmd.respond_info("Load complete")


    def _load_toolhead(self, lane, gcmd, bowden_length=None,
                       extruder_load_length=None, hotend_load_length=None):
        # keep track of lane in case of an error
        self.next_lane = lane

        # check lane
        self._check_lane_valid(lane)
        if lane == self.active_lane:
            return

        # check and set lengths
        if bowden_length is None:
            bowden_length = self.bowden_load_length
        if extruder_load_length is None:
            extruder_load_length = self.extruder_load_length
        if hotend_load_length is None:
            hotend_load_length = self.hotend_load_length

        # unload current lane if there is filament in the selector
        self.toolhead.wait_moves()
        if self._query_selector_sensor():
            try:
                self._unload_toolhead(gcmd)
            except:
                self._raise_servo()
                gcmd.respond_info("Failed to unload. Please pull "
                                  "filament {lane} out of the toolhead and "
                                  "selector, then use TR_RESUME to reload "
                                  "lane {lane} and continue."
                                  .format(lane=str(self.curr_lane)))
                self.retry_lane = self.curr_lane
                self.lanes_unloaded[self.curr_lane] = False
                logging.warning("trad_rack: Failed to unload toolhead",
                                exc_info=True)
                raise self.gcode.error("Failed to load toolhead")

        # load filament into the selector
        try:
            self._load_selector(lane)
        except:
            self._raise_servo()
            gcmd.respond_info("Failed to load selector from lane {lane}. "
                              "Use TR_RESUME to reload lane {lane} and retry."
                              .format(lane=str(lane)))
            self.retry_lane = lane
            logging.warning("trad_rack: Failed to load selector", 
                            exc_info=True)
            raise self.gcode.error("Failed to load toolhead")

        # move filament through the bowden tube
        self._reset_fil_driver()
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        move_start = pos[1]
        pos[1] += bowden_length
        if self.lanes_unloaded[self.curr_lane]:
            speed = self.buffer_pull_speed
        else:
            speed = self.spool_pull_speed
        reached_sensor_early = True
        if self.load_with_toolhead_sensor and self.toolhead_fil_endstops:
            hmove = HomingMove(self.printer, self.toolhead_fil_endstops,
                               self.tr_toolhead)
            try:
                # move and check for early sensor trigger
                trigpos = hmove.homing_move(pos, speed, probe_pos=True)

                # if sensor triggered early, retract before next homing move
                pos[1] = trigpos[1] - self.fil_homing_retract_dist
            except self.printer.command_error:
                reached_sensor_early = False
        self.tr_toolhead.move(pos, speed)
        base_length = pos[1] - move_start

        # sync extruder to filament driver
        self.tr_toolhead.wait_moves()
        prev_sk, prev_trapq = self._sync_extruder_to_fil_driver()

        # move filament until toolhead sensor is triggered
        if self.load_with_toolhead_sensor and self.toolhead_fil_endstops:
            pos = self.tr_toolhead.get_position()
            move_start = pos[1]
            pos[1] += self.load_length
            hmove = HomingMove(self.printer, self.toolhead_fil_endstops,
                               self.tr_toolhead)
            try:
                trigpos = hmove.homing_move(pos, self.toolhead_sense_speed,
                                            probe_pos=True)
            except:
                self._raise_servo()
                self._unsync_extruder_from_fil_driver(prev_sk, prev_trapq)
                gcmd.respond_info("Failed to load toolhead from lane {lane}. "
                                  "Use TR_RESUME to reload lane {lane} and "
                                  "retry.".format(lane=str(lane)))
                self.retry_lane = lane
                logging.warning("trad_rack: Toolhead sensor homing move failed", 
                                exc_info=True)
                raise self.gcode.error("Failed to load toolhead. No trigger on "
                                       "toolhead sensor after full movement")
            
            # update bowden_load_length
            length = trigpos[1] - move_start + base_length \
                     - self.target_toolhead_homing_dist
            old_set_length = self.bowden_load_length
            self.bowden_load_length = self.bowden_load_length_filter \
                                      .update(length)
            samples = self.bowden_load_length_filter.get_entry_count()
            self._write_bowden_length_data(
                self.bowden_load_lengths_filename, length, old_set_length,
                self.bowden_load_length, samples)
            self._save_bowden_length("load", self.bowden_load_length, samples)
            if not (self.bowden_load_calibrated or reached_sensor_early):
                self.bowden_load_calibrated = True
                gcmd.respond_info("Calibrated bowden_load_length: {}"
                                  .format(self.bowden_load_length))

        # finish loading filament into extruder
        self._reset_fil_driver()
        pos = self.tr_toolhead.get_position()
        pos[1] += extruder_load_length
        self.tr_toolhead.move(pos, self.extruder_load_speed)

        # load filament into hotend
        pos[1] += hotend_load_length
        self.tr_toolhead.move(pos, self.hotend_load_speed)

        # check whether servo move might overlap extruder loading move
        if hotend_load_length:
            hotend_load_time = self.tr_toolhead.move_queue.get_last().min_move_t
        else:
            hotend_load_time = 0.
        servo_delay = max(0., self.servo_wait - hotend_load_time)

        # flush lookahead and raise servo before move ends
        print_time = self.tr_toolhead.get_last_move_time() - self.servo_wait \
                     + servo_delay
        self._raise_servo(tr_toolhead_dwell=False, wait_moves=False, 
                          print_time=print_time)
        
        # wait for servo move if necessary
        if servo_delay:
            self.tr_toolhead.dwell(servo_delay)
        
        # unsync extruder from filament driver
        self.tr_toolhead.wait_moves()
        self._unsync_extruder_from_fil_driver(prev_sk, prev_trapq)

        # set active lane
        self.active_lane = lane

        # run post-load custom gcode
        self.post_load_macro.run_gcode_from_command()
        self.toolhead.wait_moves()
        self.tr_toolhead.wait_moves()

    def _load_selector(self, lane):
        # move selector
        self._go_to_lane(lane)

        # lower servo and turn the drive gear until filament is detected
        self._lower_servo()
        self._reset_fil_driver()
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        hmove = HomingMove(self.printer, self.fil_driver_endstops, 
                           self.tr_toolhead)
        pos[1] += self.load_length
        try:
            hmove.homing_move(pos, self.selector_sense_speed)
        except:
            self._raise_servo()
            logging.warning("trad_rack: Selector homing move failed", 
                            exc_info=True)
            raise self.gcode.error("Failed to load filament into selector. "
                                    "No trigger on selector sensor after full "
                                    "movement")

    def _unload_selector(self, gcmd, base_length=None, mark_calibrated=False):
        # check for filament in selector
        if not self._query_selector_sensor():
            gcmd.respond_info("No filament detected. "
                              "Attempting to load selector")
            self._load_selector(self.curr_lane)
            gcmd.respond_info("Loaded selector. "
                              "Retracting filament into module")
        else:
            # lower servo and turn the drive gear until filament 
            # is no longer detected
            self._lower_servo()
            self._reset_fil_driver()
            self.tr_toolhead.get_last_move_time()
            pos = self.tr_toolhead.get_position()
            move_start = pos[1]
            hmove = HomingMove(self.printer, self.fil_driver_endstops, 
                               self.tr_toolhead)
            pos[1] -= self.load_length
            try:
                trigpos = hmove.homing_move(pos, self.selector_sense_speed, 
                                            probe_pos = True, triggered=False)
            except:
                self._raise_servo()
                logging.warning("trad_rack: Selector homing move failed", 
                                exc_info=True)
                raise self.gcode.error("Failed to unload filament from "
                                       "selector. Selector sensor still "
                                       "triggered after full movement")
            
            # update bowden_unload_length
            if base_length is not None:
                length = move_start - trigpos[1] + base_length \
                         - self.target_selector_homing_dist
                old_set_length = self.bowden_unload_length
                self.bowden_unload_length = self.bowden_unload_length_filter \
                                            .update(length)
                samples = self.bowden_unload_length_filter.get_entry_count()
                self._write_bowden_length_data(
                    self.bowden_unload_lengths_filename, length, old_set_length,
                    self.bowden_unload_length, samples)
                self._save_bowden_length("unload", self.bowden_unload_length, 
                                         samples)
                if mark_calibrated:
                    self.bowden_unload_calibrated = True
                    gcmd.respond_info("Calibrated bowden_unload_length: {}"
                                      .format(self.bowden_unload_length))

        # retract filament into the module
        self._reset_fil_driver()
        pos = self.tr_toolhead.get_position()
        pos[1] -= self.selector_unload_length
        self.tr_toolhead.move(pos, self.selector_unload_speed)

        # reset filament driver position
        self._reset_fil_driver()

        # raise servo
        self._raise_servo()

    def _unload_toolhead(self, gcmd):
        # reset active lane
        self.active_lane = None
        
        # check that the selector is at a lane
        if self.curr_lane is None or not self._is_selector_homed:
            raise self.gcode.error("Selector must be moved to a lane "
                                   "before unloading")

        # run pre-unload custom gcode
        self.pre_unload_macro.run_gcode_from_command()
        self.toolhead.wait_moves()
        self.tr_toolhead.wait_moves()

        # lower servo
        self._lower_servo(True)

        # sync extruder to filament driver
        self.tr_toolhead.wait_moves()
        prev_sk, prev_trapq = self._sync_extruder_to_fil_driver()

        # move filament until toolhead sensor is untriggered
        if self.unload_with_toolhead_sensor and self.toolhead_fil_endstops:
            pos = self.tr_toolhead.get_position()
            pos[1] -= self.load_length
            hmove = HomingMove(self.printer, self.toolhead_fil_endstops,
                               self.tr_toolhead)
            try:
                hmove.homing_move(pos, self.toolhead_sense_speed,
                                  triggered=False)
            except:
                self._raise_servo()
                self._unsync_extruder_from_fil_driver(prev_sk, prev_trapq)
                logging.warning("trad_rack: Toolhead sensor homing move failed",
                                exc_info=True)
                raise self.gcode.error("Failed to unload toolhead. Toolhead "
                                       "sensor still triggered after full "
                                       "movement")          

        # get filament out of the extruder
        self._reset_fil_driver()
        pos = self.tr_toolhead.get_position()
        pos[1] -= self.toolhead_unload_length
        self.tr_toolhead.move(pos, self.toolhead_unload_speed)

        # unsync extruder from filament driver
        self.tr_toolhead.wait_moves()
        self._unsync_extruder_from_fil_driver(prev_sk, prev_trapq)

        # move filament through the bowden tube
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        move_start = pos[1]
        pos[1] -= self.bowden_unload_length
        hmove = HomingMove(self.printer, self.fil_driver_endstops, 
                           self.tr_toolhead)
        reached_sensor_early = True
        try:
            # move and check for early sensor trigger
            trigpos = hmove.homing_move(pos, self.buffer_pull_speed, 
                                        probe_pos=True, triggered=False)
            
            # if sensor triggered early, retract before next homing move
            pos[1] = trigpos[1] + self.fil_homing_retract_dist
        except self.printer.command_error:
            reached_sensor_early = False
        self.tr_toolhead.move(pos, self.buffer_pull_speed)

        # unload selector
        mark_calibrated = not (self.bowden_unload_calibrated \
                               or reached_sensor_early)
        self._unload_selector(gcmd, move_start - pos[1], mark_calibrated)

        # note that the current lane's buffer has been filled
        self.lanes_unloaded[self.curr_lane] = True

    def _send_pause(self):
        self.pause_macro.run_gcode_from_command()

    def _sync_extruder_to_fil_driver(self):
        self.toolhead.flush_step_generation()
        self.tr_toolhead.flush_step_generation()
        e_stepper = self.toolhead.get_extruder().extruder_stepper.stepper
        tr_trapq = self.tr_toolhead.get_trapq()
        ffi_main, ffi_lib = chelper.get_ffi()
        stepper_kinematics = ffi_main.gc(
            ffi_lib.cartesian_stepper_alloc(b'y'), ffi_lib.free)
        prev_sk = e_stepper.set_stepper_kinematics(stepper_kinematics)
        prev_trapq = e_stepper.set_trapq(tr_trapq)
        self._reset_fil_driver()
        e_stepper.set_position((0., 0., 0.))
        handler = e_stepper.generate_steps
        self.tr_toolhead.register_step_generator(handler)
        self.extruder_synced = True
        return prev_sk, prev_trapq

    def _unsync_extruder_from_fil_driver(self, prev_sk, prev_trapq):
        self.toolhead.flush_step_generation()
        self.tr_toolhead.flush_step_generation()
        e_stepper = self.toolhead.get_extruder().extruder_stepper.stepper
        handler = e_stepper.generate_steps
        self.tr_toolhead.step_generators.remove(handler)
        e_stepper.set_trapq(prev_trapq)
        e_stepper.set_stepper_kinematics(prev_sk)
        self.extruder_synced = False

    def _write_bowden_length_data(self, filename, length, old_set_length,
                                  new_set_length, samples):
        try:
            with open(filename, 'a+') as f:
                if os.stat(filename).st_size == 0:
                    f.write(("time,length,diff_from_set_length,new_set_length,"
                             "new_sample_count\n"))
                f.write("{},{:.3f},{:.3f},{:.3f},{}\n"
                        .format(time.strftime("%Y%m%d_%H%M%S"),
                                length, length - old_set_length, new_set_length,
                                samples))
        except IOError as e:
            raise self.printer.command_error("Error writing to file '%s': %s",
                                             filename, str(e))
    def _save_bowden_length(self, mode, new_set_length, samples):
        length_stats = {
            'new_set_length': new_set_length,
            'sample_count': samples
            }
        if mode == 'load':
            self.gcode.run_script_from_command("SAVE_VARIABLE VARIABLE=%s "
                "VALUE=\"%s\""
                % (self.VARS_CALIB_BOWDEN_LOAD_LENGTH, length_stats))
        else:
            self.gcode.run_script_from_command("SAVE_VARIABLE VARIABLE=%s "
                "VALUE=\"%s\""
                % (self.VARS_CALIB_BOWDEN_UNLOAD_LENGTH, length_stats))
    
    # other functions
    def get_status(self, eventtime):
        return {
            'curr_lane': self.curr_lane,
            'active_lane': self.active_lane,
            'retry_lane': self.retry_lane,
            'next_lane': self.next_lane
        }

SDS_CHECK_TIME = 0.001 # step+dir+step filter in stepcompress.c

class TradRackToolHead(toolhead.ToolHead, object):
    def __init__(self, config, buffer_pull_speed):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.all_mcus = [
            m for n, m in self.printer.lookup_objects(module='mcu')]
        self.mcu = self.all_mcus[0]
        self.can_pause = True
        if self.mcu.is_fileoutput():
            self.can_pause = False
        self.move_queue = toolhead.MoveQueue(self)
        self.commanded_pos = [0., 0., 0., 0.]
        self.printer.register_event_handler("klippy:shutdown",
                                            self._handle_shutdown)
        # Velocity and acceleration control
        tr_config = config.getsection('trad_rack')
        extruder_accel = config.getsection('extruder') \
                               .getfloat('max_extrude_only_accel')
        self.sel_max_velocity = tr_config.getfloat('selector_max_velocity', 
            above=0.)
        self.fil_max_velocity = tr_config.getfloat('filament_max_velocity',
            default=buffer_pull_speed, above=0.)
        self.max_velocity = max(self.sel_max_velocity, self.fil_max_velocity)
        self.sel_max_accel = tr_config.getfloat('selector_max_accel', above=0.)
        self.fil_max_accel = tr_config.getfloat('filament_max_accel',
            default=extruder_accel, above=0.)
        self.max_accel = max(self.sel_max_accel, self.fil_max_accel)
        self.requested_accel_to_decel = config.getfloat(
            'max_accel_to_decel', self.max_accel * 0.5, above=0.)
        self.max_accel_to_decel = self.requested_accel_to_decel
        self.square_corner_velocity = config.getfloat(
            'square_corner_velocity', 5., minval=0.)
        self.junction_deviation = 0.
        self._calc_junction_deviation()
        # Print time tracking
        self.buffer_time_low = config.getfloat(
            'buffer_time_low', 1.000, above=0.)
        self.buffer_time_high = config.getfloat(
            'buffer_time_high', 2.000, above=self.buffer_time_low)
        self.buffer_time_start = config.getfloat(
            'buffer_time_start', 0.250, above=0.)
        self.move_flush_time = config.getfloat(
            'move_flush_time', 0.050, above=0.)
        self.print_time = 0.
        self.special_queuing_state = "Flushed"
        self.need_check_stall = -1.
        self.flush_timer = self.reactor.register_timer(self._flush_handler)
        self.move_queue.set_flush_time(self.buffer_time_high)
        self.idle_flush_print_time = 0.
        self.print_stall = 0
        self.drip_completion = None
        # Kinematic step generation scan window time tracking
        self.kin_flush_delay = SDS_CHECK_TIME
        self.kin_flush_times = []
        self.force_flush_time = self.last_kin_flush_time \
                              = self.last_kin_move_time = 0.
        # Setup iterative solver
        ffi_main, ffi_lib = chelper.get_ffi()
        self.trapq = ffi_main.gc(ffi_lib.trapq_alloc(), ffi_lib.trapq_free)
        self.trapq_append = ffi_lib.trapq_append
        self.trapq_finalize_moves = ffi_lib.trapq_finalize_moves
        self.step_generators = []
        # Create kinematic class
        gcode = self.printer.lookup_object('gcode')
        self.Coord = gcode.Coord
        self.extruder = kinematics.extruder.DummyExtruder(self.printer)
        try:
            self.kin = TradRackKinematics(self, config)
        except config.error as e:
            raise
        except self.printer.lookup_object('pins').error as e:
            raise
        except:
            msg = "Error loading kinematics 'trad_rack'"
            logging.exception(msg)
            raise config.error(msg)
    
    def set_position(self, newpos, homing_axes=()):
        for _ in range(4 - len(newpos)):
            newpos.append(0.)
        super(TradRackToolHead, self).set_position(newpos, homing_axes)
    
    def get_sel_max_velocity(self):
        return self.sel_max_velocity, self.sel_max_accel

    def get_fil_max_velocity(self):
        return self.fil_max_velocity, self.fil_max_accel

class TradRackKinematics:
    def __init__(self, toolhead, config):
        self.printer = config.get_printer()
        # Setup axis rails
        selector_stepper_section = config.getsection(SELECTOR_STEPPER_NAME)
        fil_driver_stepper_section = config.getsection(FIL_DRIVER_STEPPER_NAME)
        selector_rail = stepper.LookupMultiRail(selector_stepper_section)
        fil_driver_rail = stepper.LookupMultiRail(fil_driver_stepper_section)
        self.rails = [selector_rail, fil_driver_rail]
        for rail, axis in zip(self.rails, 'xy'):
            rail.setup_itersolve('cartesian_stepper_alloc', axis.encode())
        for s in self.get_steppers():
            s.set_trapq(toolhead.get_trapq())
            toolhead.register_step_generator(s.generate_steps)
        self.printer.register_event_handler("stepper_enable:motor_off",
            self._motor_off)

        # Setup boundary checks
        self.sel_max_velocity, self.sel_max_accel = \
            toolhead.get_sel_max_velocity()
        self.fil_max_velocity, self.fil_max_accel = \
            toolhead.get_fil_max_velocity()
        self.stepper_count = len(self.rails)
        self.limits = [(1.0, -1.0)] * self.stepper_count
        self.selector_min = selector_stepper_section.getfloat('position_min', 
            note_valid=False)
        self.selector_max = selector_stepper_section.getfloat('position_max', 
            note_valid=False)
    
    def get_steppers(self):
        rails = self.rails
        return [s for rail in rails for s in rail.get_steppers()]

    def calc_position(self, stepper_positions):
        return [stepper_positions[rail.get_name()] for rail in self.rails]

    def set_position(self, newpos, homing_axes):
        for i, rail in enumerate(self.rails):
            rail.set_position(newpos)
            if i in homing_axes:
                self.limits[i] = rail.get_range()
    
    def note_z_not_homed(self):
        # Helper for Safe Z Home
        pass

    def _home_axis(self, homing_state, axis, rail):
        # Determine movement
        position_min, position_max = rail.get_range()
        hi = rail.get_homing_info()
        homepos = [None, None, None, None]
        homepos[axis] = hi.position_endstop
        forcepos = list(homepos)
        if hi.positive_dir:
            forcepos[axis] -= 1.5 * (hi.position_endstop - position_min)
        else:
            forcepos[axis] += 1.5 * (position_max - hi.position_endstop)
        # Perform homing
        homing_state.home_rails([rail], forcepos, homepos)

    def home(self, homing_state):
        # Each axis is homed independently and in order
        for axis in homing_state.get_axes():
            self._home_axis(homing_state, axis, self.rails[axis])
    
    def _motor_off(self, print_time):
        self.limits = [(1.0, -1.0)] * self.stepper_count

    def _check_endstops(self, move):
        end_pos = move.end_pos
        for i in range(self.stepper_count):
            if (move.axes_d[i]
                and (end_pos[i] < self.limits[i][0]
                     or end_pos[i] > self.limits[i][1])):
                if self.limits[i][0] > self.limits[i][1]:
                    raise move.move_error("Must home axis first")
                raise move.move_error()

    def check_move(self, move):
        limits = self.limits
        xpos, ypos = move.end_pos[:2]
        if (xpos < limits[0][0] or xpos > limits[0][1]
            or ypos < limits[1][0] or ypos > limits[1][1]):
            self._check_endstops(move)
        
        # Move with selector - update velocity and accel
        if move.axes_d[0]:
            move.limit_speed(self.sel_max_velocity, self.sel_max_accel)
        
        # Move with filament driver - update velocity and accel
        elif move.axes_d[1]:
            move.limit_speed(self.fil_max_velocity, self.fil_max_accel)

    def get_status(self, eventtime):
        axes = [a for a, (l, h) in zip("xy", self.limits) if l <= h]
        return {
            'homed_axes': "".join(axes),
            'selector_min': self.selector_min,
            'selector_max': self.selector_max,
        }

    def get_selector_rail(self):
        return self.rails[0]
    
    def get_fil_driver_rail(self):
        return self.rails[1]

class TradRackHoming(Homing, object):
    def __init__(self, printer, toolhead):
        super(TradRackHoming, self).__init__(printer)
        self.toolhead = toolhead
    
    def home_rails(self, rails, forcepos, movepos):
        # Notify of upcoming homing operation
        self.printer.send_event("homing:home_rails_begin", self, rails)
        # Alter kinematics class to think printer is at forcepos
        homing_axes = [axis for axis in range(3) if forcepos[axis] is not None]
        startpos = self._fill_coord(forcepos)
        homepos = self._fill_coord(movepos)
        self.toolhead.set_position(startpos, homing_axes=homing_axes)
        # Perform first home
        endstops = [es for rail in rails for es in rail.get_endstops()]
        hi = rails[0].get_homing_info()
        hmove = HomingMove(self.printer, endstops, self.toolhead)
        hmove.homing_move(homepos, hi.speed)
        # Perform second home
        if hi.retract_dist:
            # Retract
            startpos = self._fill_coord(forcepos)
            homepos = self._fill_coord(movepos)
            axes_d = [hp - sp for hp, sp in zip(homepos, startpos)]
            move_d = math.sqrt(sum([d*d for d in axes_d[:3]]))
            retract_r = min(1., hi.retract_dist / move_d)
            retractpos = [hp - ad * retract_r
                          for hp, ad in zip(homepos, axes_d)]
            self.toolhead.move(retractpos, hi.retract_speed)
            # Home again
            startpos = [rp - ad * retract_r
                        for rp, ad in zip(retractpos, axes_d)]
            self.toolhead.set_position(startpos)
            hmove = HomingMove(self.printer, endstops, self.toolhead)
            hmove.homing_move(homepos, hi.second_homing_speed)
            if hmove.check_no_movement() is not None:
                raise self.printer.command_error(
                    "Endstop %s still triggered after retract"
                    % (hmove.check_no_movement(),))
        # Signal home operation complete
        self.toolhead.flush_step_generation()
        self.trigger_mcu_pos = {sp.stepper_name: sp.trig_pos
                                for sp in hmove.stepper_positions}
        self.adjust_pos = {}
        self.printer.send_event("homing:home_rails_end", self, rails)
        if any(self.adjust_pos.values()):
            # Apply any homing offsets
            kin = self.toolhead.get_kinematics()
            homepos = self.toolhead.get_position()
            kin_spos = {s.get_name(): (s.get_commanded_position()
                                       + self.adjust_pos.get(s.get_name(), 0.))
                        for s in kin.get_steppers()}
            newpos = kin.calc_position(kin_spos)
            for axis in homing_axes:
                homepos[axis] = newpos[axis]
            self.toolhead.set_position(homepos)

class TradRackServo:
    def __init__(self, servo, toolhead):
        self.servo = servo
        self.toolhead = toolhead

    def set_servo(self, width=None, angle=None, print_time=None):
        if print_time is None:
            print_time = self.toolhead.get_last_move_time()
        if width is not None:
            self.servo._set_pwm(print_time, 
                                self.servo._get_pwm_from_pulse_width(width))
        else:
            self.servo._set_pwm(print_time, 
                                self.servo._get_pwm_from_angle(angle))
            
class MovingAverageFilter:
    def __init__(self, max_entries):
        self.max_entries = max_entries
        self.queue = deque()
        self.total = 0.

    def update(self, value):
        if len(self.queue) >= self.max_entries:
            self.total -= self.queue.popleft()
        self.total += value
        self.queue.append(value)
        return self.total / len(self.queue)
    
    def get_entry_count(self):
        return len(self.queue)

def load_config(config):
    return TradRack(config)
