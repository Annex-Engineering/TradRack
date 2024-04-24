# Trad Rack multimaterial system support
#
# Copyright (C) 2022-2024 Ryan Ghosh <rghosh776@gmail.com>
# based on code by Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging, math, os, time
from collections import deque
from extras.homing import Homing, HomingMove
from gcode import CommandError
from stepper import LookupMultiRail
import chelper, toolhead, kinematics.extruder

SERVO_NAME = "servo tr_servo"
SELECTOR_STEPPER_NAME = "stepper_tr_selector"
FIL_DRIVER_STEPPER_NAME = "stepper_tr_fil_driver"


class TradRack:

    VARS_CALIB_BOWDEN_LOAD_LENGTH = "tr_calib_bowden_load_length"
    VARS_CALIB_BOWDEN_UNLOAD_LENGTH = "tr_calib_bowden_unload_length"
    VARS_CONFIG_BOWDEN_LENGTH = "tr_config_bowden_length"
    VARS_TOOL_STATUS = "tr_state_tool_status"
    VARS_HEATER_TARGET = "tr_last_heater_target"
    VARS_ACTIVE_LANE = "tr_active_lane"

    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.printer.register_event_handler(
            "klippy:connect", self.handle_connect
        )
        self.printer.register_event_handler("klippy:ready", self.handle_ready)

        # read spool and buffer pull speeds
        self.spool_pull_speed = config.getfloat(
            "spool_pull_speed", default=100.0, above=0.0
        )
        self.buffer_pull_speed = config.getfloat(
            "buffer_pull_speed", default=self.spool_pull_speed, above=0.0
        )

        # create toolhead
        self.tr_toolhead = TradRackToolHead(
            config,
            self.buffer_pull_speed,
            lambda: self.extruder_sync_manager.is_extruder_synced(),
        )
        self.sel_max_velocity, _ = self.tr_toolhead.get_sel_max_velocity()

        # get servo
        self.servo = TradRackServo(
            self.printer.load_object(config, SERVO_NAME), self.tr_toolhead
        )

        # get kinematics and filament driver endstops
        self.tr_kinematics = self.tr_toolhead.get_kinematics()
        self.fil_driver_endstops = (
            self.tr_kinematics.get_fil_driver_rail().get_endstops()
        )

        # set up toolhead filament sensor
        toolhead_fil_sensor_pin = config.get("toolhead_fil_sensor_pin", None)
        self.toolhead_fil_endstops = []
        if toolhead_fil_sensor_pin is not None:
            # register endstop
            ppins = self.printer.lookup_object("pins")
            mcu_endstop = ppins.setup_pin("endstop", toolhead_fil_sensor_pin)
            name = "toolhead_fil_sensor"
            self.toolhead_fil_endstops.append((mcu_endstop, name))
            query_endstops = self.printer.load_object(config, "query_endstops")
            query_endstops.register_endstop(mcu_endstop, name)

            # add filament driver stepper to endstop
            for (
                stepper
            ) in self.tr_kinematics.get_fil_driver_rail().get_steppers():
                mcu_endstop.add_stepper(stepper)

        # set up selector sensor as a runout sensor
        pin = config.getsection(FIL_DRIVER_STEPPER_NAME).get("endstop_pin")
        self.selector_sensor = TradRackRunoutSensor(
            config, self.handle_runout, pin
        )

        # read lane count and get lane positions
        self.lane_count = config.getint("lane_count", minval=2)
        self.lane_position_manager = TradRackLanePositionManager(
            self.lane_count, config
        )
        self.lane_positions = self.lane_position_manager.get_lane_positions()

        # create bowden length filters
        bowden_samples = config.getint(
            "bowden_length_samples", default=10, minval=1
        )
        self.bowden_load_length_filter = MovingAverageFilter(bowden_samples)
        self.bowden_unload_length_filter = MovingAverageFilter(bowden_samples)

        # create extruder sync manager
        self.extruder_sync_manager = TradRackExtruderSyncManager(
            self.printer,
            self.tr_toolhead,
            self.tr_kinematics.get_fil_driver_rail(),
        )

        # read other values
        self.servo_down_angle = config.getfloat("servo_down_angle")
        self.servo_up_angle = config.getfloat("servo_up_angle")
        self.servo_wait = (
            config.getfloat("servo_wait_ms", default=500.0, above=0.0) / 1000.0
        )
        self.selector_unload_length = config.getfloat(
            "selector_unload_length", above=0.0
        )
        self.selector_unload_length_extra = config.getfloat(
            "selector_unload_length_extra", default=0.0, minval=0.0
        )
        self.eject_length = config.getfloat(
            "eject_length", default=30.0, above=0.0
        )
        self.config_bowden_length = self.bowden_load_length = (
            self.bowden_unload_length
        ) = config.getfloat("bowden_length", above=0.0)
        self.extruder_load_length = config.getfloat(
            "extruder_load_length", above=0.0
        )
        self.hotend_load_length = config.getfloat(
            "hotend_load_length", above=0.0
        )
        if self.toolhead_fil_endstops:
            self.toolhead_unload_length = config.getfloat(
                "toolhead_unload_length", minval=0.0
            )
        else:
            self.toolhead_unload_length = config.getfloat(
                "toolhead_unload_length",
                default=self.extruder_load_length + self.hotend_load_length,
                above=0.0,
            )
        self.selector_sense_speed = config.getfloat(
            "selector_sense_speed", default=40.0, above=0.0
        )
        self.selector_unload_speed = config.getfloat(
            "selector_unload_speed", default=60.0, above=0.0
        )
        self.eject_speed = config.getfloat(
            "eject_speed", default=80.0, above=0.0
        )
        self.toolhead_sense_speed = config.getfloat(
            "toolhead_sense_speed", default=self.selector_sense_speed, above=0.0
        )
        self.extruder_load_speed = config.getfloat(
            "extruder_load_speed", default=60.0, above=0.0
        )
        self.hotend_load_speed = config.getfloat(
            "hotend_load_speed", default=7.0, above=0.0
        )
        self.toolhead_unload_speed = config.getfloat(
            "toolhead_unload_speed", default=self.extruder_load_speed, above=0.0
        )
        self.load_with_toolhead_sensor = config.getboolean(
            "load_with_toolhead_sensor", True
        )
        self.unload_with_toolhead_sensor = config.getboolean(
            "unload_with_toolhead_sensor", True
        )
        self.fil_homing_retract_dist = config.getfloat(
            "fil_homing_retract_dist", 20.0, minval=0.0
        )
        self.target_toolhead_homing_dist = config.getfloat(
            "target_toolhead_homing_dist",
            max(10.0, self.toolhead_unload_length),
            above=0.0,
        )
        self.target_selector_homing_dist = config.getfloat(
            "target_selector_homing_dist", 10.0, above=0.0
        )
        self.fil_homing_lengths = {
            "user load lane": (
                config.getint(
                    "load_lane_time",
                    default=15,
                    minval=self.selector_unload_length
                    / self.selector_sense_speed,
                )
                * self.selector_sense_speed
            ),
            "load selector": config.getfloat(
                "load_selector_homing_dist",
                default=self.selector_unload_length * 2,
                above=self.selector_unload_length,
            ),
            "bowden load": config.getfloat(
                "bowden_load_homing_dist",
                default=self.config_bowden_length,
                above=self.target_toolhead_homing_dist,
            ),
            "bowden unload": config.getfloat(
                "bowden_unload_homing_dist",
                default=self.config_bowden_length,
                above=self.target_selector_homing_dist,
            ),
            "unload toolhead": config.getfloat(
                "unload_toolhead_homing_dist",
                default=(self.extruder_load_length + self.hotend_load_length)
                * 2,
                above=0.0,
            ),
        }
        self.sync_to_extruder = config.getboolean("sync_to_extruder", False)
        self.user_wait_time = config.getint(
            "user_wait_time", default=15, minval=-1
        )
        register_toolchange_commands = config.getboolean(
            "register_toolchange_commands", default=True
        )
        self.save_active_lane = config.getboolean("save_active_lane", True)
        self.log_bowden_lengths = config.getboolean("log_bowden_lengths", False)

        # other variables
        self.toolhead = None
        self.curr_lane = None  # which lane the selector is positioned at
        self.active_lane = None  # lane currently loaded in the toolhead
        self.retry_lane = None  # lane to reload before resuming
        self.retry_tool = None  # tool to load a lane from before resuming
        self.next_lane = None  # next lane to load to toolhead
        self.servo_raised = None
        self.lanes_unloaded = [False] * self.lane_count
        self.bowden_load_calibrated = False
        self.bowden_unload_calibrated = False
        self.bowden_load_lengths_filename = os.path.expanduser(
            "~/bowden_load_lengths.csv"
        )
        self.bowden_unload_lengths_filename = os.path.expanduser(
            "~/bowden_unload_lengths.csv"
        )
        self.ignore_next_unload_length = False
        self.last_heater_target = 0.0
        self.tr_next_generator = None

        # resume variables
        self.resume_callbacks = {
            "load toolhead": self._resume_load_toolhead,
            "check condition": self._resume_check_condition,
            "runout": self._resume_runout,
        }
        self.resume_stack = deque()

        # tool mapping
        self.lanes_dead = [False] * self.lane_count
        self.tool_map = []
        self.default_lanes = []
        self._reset_tool_map()

        # runout variables
        self.runout_lane = None
        self.runout_steps_done = 0
        self.replacement_lane = None

        # custom user macros
        gcode_macro = self.printer.load_object(config, "gcode_macro")
        self.pre_unload_macro = gcode_macro.load_template(
            config, "pre_unload_gcode", ""
        )
        self.post_unload_macro = gcode_macro.load_template(
            config, "post_unload_gcode", ""
        )
        self.pre_load_macro = gcode_macro.load_template(
            config, "pre_load_gcode", ""
        )
        self.post_load_macro = gcode_macro.load_template(
            config, "post_load_gcode", ""
        )
        self.pause_macro = gcode_macro.load_template(
            config, "pause_gcode", "PAUSE"
        )
        self.resume_macro = gcode_macro.load_template(
            config, "resume_gcode", "RESUME"
        )

        # register gcode commands
        self.gcode = self.printer.lookup_object("gcode")
        self.gcode.register_command(
            "TR_HOME", self.cmd_TR_HOME, desc=self.cmd_TR_HOME_help
        )
        self.gcode.register_command(
            "TR_GO_TO_LANE",
            self.cmd_TR_GO_TO_LANE,
            desc=self.cmd_TR_GO_TO_LANE_help,
        )
        self.gcode.register_command(
            "TR_LOAD_LANE",
            self.cmd_TR_LOAD_LANE,
            desc=self.cmd_TR_LOAD_LANE_help,
        )
        self.gcode.register_command(
            "TR_LOAD_TOOLHEAD",
            self.cmd_TR_LOAD_TOOLHEAD,
            desc=self.cmd_TR_LOAD_TOOLHEAD_help,
        )
        self.gcode.register_command(
            "TR_UNLOAD_TOOLHEAD",
            self.cmd_TR_UNLOAD_TOOLHEAD,
            desc=self.cmd_TR_UNLOAD_TOOLHEAD_help,
        )
        self.gcode.register_command(
            "TR_SERVO_DOWN",
            self.cmd_TR_SERVO_DOWN,
            desc=self.cmd_TR_SERVO_DOWN_help,
        )
        self.gcode.register_command(
            "TR_SERVO_UP", self.cmd_TR_SERVO_UP, desc=self.cmd_TR_SERVO_UP_help
        )
        self.gcode.register_command(
            "TR_SERVO_TEST",
            self.cmd_TR_SERVO_TEST,
            desc=self.cmd_TR_SERVO_TEST_help,
        )
        self.gcode.register_command(
            "TR_SET_ACTIVE_LANE",
            self.cmd_TR_SET_ACTIVE_LANE,
            desc=self.cmd_TR_SET_ACTIVE_LANE_help,
        )
        self.gcode.register_command(
            "TR_RESET_ACTIVE_LANE",
            self.cmd_TR_RESET_ACTIVE_LANE,
            desc=self.cmd_TR_RESET_ACTIVE_LANE_help,
        )
        self.gcode.register_command(
            "TR_RESUME", self.cmd_TR_RESUME, desc=self.cmd_TR_RESUME_help
        )
        self.gcode.register_command(
            "TR_LOCATE_SELECTOR",
            self.cmd_TR_LOCATE_SELECTOR,
            desc=self.cmd_TR_LOCATE_SELECTOR_help,
        )
        self.gcode.register_command(
            "TR_CALIBRATE_SELECTOR",
            self.cmd_TR_CALIBRATE_SELECTOR,
            desc=self.cmd_TR_CALIBRATE_SELECTOR_help,
        )
        self.gcode.register_command(
            "TR_NEXT", self.cmd_TR_NEXT, desc=self.cmd_TR_NEXT_help
        )
        self.gcode.register_command(
            "TR_SET_HOTEND_LOAD_LENGTH",
            self.cmd_TR_SET_HOTEND_LOAD_LENGTH,
            desc=self.cmd_TR_SET_HOTEND_LOAD_LENGTH_help,
        )
        self.gcode.register_command(
            "TR_DISCARD_BOWDEN_LENGTHS",
            self.cmd_TR_DISCARD_BOWDEN_LENGTHS,
            desc=self.cmd_TR_DISCARD_BOWDEN_LENGTHS_help,
        )
        self.gcode.register_command(
            "TR_SYNC_TO_EXTRUDER",
            self.cmd_TR_SYNC_TO_EXTRUDER,
            desc=self.cmd_TR_SYNC_TO_EXTRUDER_help,
        )
        self.gcode.register_command(
            "TR_UNSYNC_FROM_EXTRUDER",
            self.cmd_TR_UNSYNC_FROM_EXTRUDER,
            desc=self.cmd_TR_UNSYNC_FROM_EXTRUDER_help,
        )
        self.gcode.register_command(
            "TR_ASSIGN_LANE",
            self.cmd_TR_ASSIGN_LANE,
            desc=self.cmd_TR_ASSIGN_LANE_help,
        )
        self.gcode.register_command(
            "TR_SET_DEFAULT_LANE",
            self.cmd_TR_SET_DEFAULT_LANE,
            desc=self.cmd_TR_SET_DEFAULT_LANE_help,
        )
        self.gcode.register_command(
            "TR_RESET_TOOL_MAP",
            self.cmd_TR_RESET_TOOL_MAP,
            desc=self.cmd_TR_RESET_TOOL_MAP_help,
        )
        self.gcode.register_command(
            "TR_PRINT_TOOL_MAP",
            self.cmd_TR_PRINT_TOOL_MAP,
            desc=self.cmd_TR_PRINT_TOOL_MAP_help,
        )
        self.gcode.register_command(
            "TR_PRINT_TOOL_GROUPS",
            self.cmd_TR_PRINT_TOOL_GROUPS,
            desc=self.cmd_TR_PRINT_TOOL_GROUPS_help,
        )
        if register_toolchange_commands:
            for i in range(self.lane_count):
                self.gcode.register_command(
                    "T{}".format(i),
                    lambda params: self.cmd_SELECT_TOOL(
                        self.gcode._get_extended_params(params)
                    ),
                    desc=self.cmd_SELECT_TOOL_help,
                )

    def handle_connect(self):
        self.toolhead = self.printer.lookup_object("toolhead")
        save_variables = self.printer.lookup_object("save_variables", None)
        if save_variables is None:
            raise self.printer.config_error(
                "[save_variables] is required for trad_rack"
            )
        self.variables = save_variables.allVariables

    def handle_ready(self):
        self._load_saved_state()

    def _load_saved_state(self):
        # load bowden lengths if the user has not changed the config value
        prev_config_bowden_length = self.variables.get(
            self.VARS_CONFIG_BOWDEN_LENGTH
        )
        if (
            prev_config_bowden_length
            and self.config_bowden_length == prev_config_bowden_length
        ):
            # update load length
            load_length_stats = self.variables.get(
                self.VARS_CALIB_BOWDEN_LOAD_LENGTH
            )
            if load_length_stats:
                self.bowden_load_length = load_length_stats["new_set_length"]
                for _ in range(load_length_stats["sample_count"]):
                    self.bowden_load_length_filter.update(
                        self.bowden_load_length
                    )

            # update unload length
            unload_length_stats = self.variables.get(
                self.VARS_CALIB_BOWDEN_UNLOAD_LENGTH
            )
            if unload_length_stats:
                self.bowden_unload_length = unload_length_stats[
                    "new_set_length"
                ]
                for _ in range(unload_length_stats["sample_count"]):
                    self.bowden_unload_length_filter.update(
                        self.bowden_unload_length
                    )
        else:
            # save bowden_length config value
            self.gcode.run_script_from_command(
                'SAVE_VARIABLE VARIABLE=%s VALUE="%s"'
                % (self.VARS_CONFIG_BOWDEN_LENGTH, self.config_bowden_length)
            )

        # load last heater target
        self.last_heater_target = self.variables.get(
            self.VARS_HEATER_TARGET, 0.0
        )

    def handle_runout(self, eventtime):
        # send pause command
        pause_resume = self.printer.lookup_object("pause_resume")
        pause_resume.send_pause_command()
        # self.printer.get_reactor().pause(eventtime + self.pause_delay)

        # set up resume callback and run pause gcode
        self._set_up_resume_and_pause("runout", {})

        # note runout
        self.runout_lane = self.active_lane
        self._set_active_lane(None)
        self.lanes_unloaded[self.runout_lane] = False
        self.lanes_dead[self.runout_lane] = True
        self.gcode.respond_info(
            "Runout detected at selector on lane {} (tool {})".format(
                self.runout_lane, self.tool_map[self.runout_lane]
            )
        )

        # unload filament and reload from a new lane
        self.runout_steps_done = 0
        self.cmd_TR_RESUME(
            self.gcode.create_gcode_command("TR_RESUME", "TR_RESUME", {})
        )

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
                    "Homing failed due to printer shutdown"
                )
            self.printer.lookup_object("stepper_enable").motor_off()
            raise

    cmd_TR_GO_TO_LANE_help = "Move Trad Rack's selector to a filament lane"

    def cmd_TR_GO_TO_LANE(self, gcmd):
        self._go_to_lane(gcmd.get_int("LANE", None))

    cmd_TR_LOAD_LANE_help = (
        "Load filament from the spool into Trad Rack in the specified lane"
    )

    def cmd_TR_LOAD_LANE(self, gcmd):
        lane = gcmd.get_int("LANE", None)
        self._load_lane(lane, gcmd, gcmd.get_int("RESET_SPEED", 1), True)
        self.lanes_dead[lane] = False

    cmd_TR_LOAD_TOOLHEAD_help = "Load filament from Trad Rack into the toolhead"

    def cmd_TR_LOAD_TOOLHEAD(self, gcmd):
        start_lane = self.active_lane
        lane = gcmd.get_int("LANE", None)
        tool = gcmd.get_int("TOOL", None)

        # select lane
        if lane is None:
            # check tool
            self._check_tool_valid(tool)

            # get default lane for the selected tool
            lane = self.default_lanes[tool]
            if lane is None:
                gcmd.respond_info(
                    "Tool {tool} has no lanes assigned to it. Use"
                    " TR_ASSIGN_LANE LANE=&lt;lane index&gt; TOOL={tool} to"
                    " assign a lane to tool {tool}, then use TR_RESUME to"
                    " continue.".format(tool=str(tool))
                )

                # set up resume callback and pause the print
                # (and wait for user to resume)
                resume_kwargs = {
                    "condition": (
                        lambda t=tool: self.default_lanes[t] is not None
                    ),
                    "action": lambda g=gcmd: self.cmd_TR_LOAD_TOOLHEAD(g),
                    "fail_msg": (
                        "Cannot resume. Please use TR_ASSIGN_LANE to assign a"
                        " lane to tool %d, then use TR_RESUME." % tool
                    ),
                }
                self._set_up_resume_and_pause("check condition", resume_kwargs)
                return

        # load toolhead
        try:
            self._load_toolhead(
                lane,
                gcmd,
                tool,
                gcmd.get_float("MIN_TEMP", 0.0, minval=0.0),
                gcmd.get_float("EXACT_TEMP", 0.0, minval=0.0),
                gcmd.get_float("BOWDEN_LENGTH", None, minval=0.0),
                gcmd.get_float("EXTRUDER_LOAD_LENGTH", None, minval=0.0),
                gcmd.get_float("HOTEND_LOAD_LENGTH", None, minval=0.0),
            )
        except TradRackLoadError:
            logging.warning(
                "trad_rack: Toolchange from lane {} to {} failed".format(
                    start_lane, lane
                ),
                exc_info=True,
            )

            # set up resume callback and pause the print
            # (and wait for user to resume)
            self._set_up_resume_and_pause("load toolhead", {})
        except SelectorNotHomedError:
            gcmd.respond_info(
                "Selector not homed. Use TR_LOCATE_SELECTOR (or TR_HOME to home"
                " the selector directly), then use TR_RESUME to continue."
            )

            # set up resume callback and pause the print
            # (and wait for user to resume)
            resume_kwargs = {
                "condition": self._is_selector_homed,
                "action": lambda g=gcmd: self.cmd_TR_LOAD_TOOLHEAD(g),
                "fail_msg": (
                    "Cannot resume. Please use either TR_LOCATE_SELECTOR or"
                    " TR_HOME to home the selector, then use TR_RESUME."
                ),
            }
            self._set_up_resume_and_pause("check condition", resume_kwargs)

    cmd_TR_UNLOAD_TOOLHEAD_help = "Unload filament from the toolhead"

    def cmd_TR_UNLOAD_TOOLHEAD(self, gcmd):
        self._unload_toolhead(
            gcmd,
            gcmd.get_float("MIN_TEMP", 0.0, minval=0.0),
            gcmd.get_float("EXACT_TEMP", 0.0, minval=0.0),
        )

    cmd_TR_SERVO_DOWN_help = "Lower the servo"

    def cmd_TR_SERVO_DOWN(self, gcmd):
        if not gcmd.get_int("FORCE", 0):
            # check that the selector is at a lane
            if not self._can_lower_servo():
                raise self.gcode.error(
                    "Selector must be moved to a lane before lowering the servo"
                )

        # lower servo
        self._lower_servo()

    cmd_TR_SERVO_UP_help = "Raise the servo"

    def cmd_TR_SERVO_UP(self, gcmd):
        # raise servo
        self._raise_servo()

    cmd_TR_SERVO_TEST_help = (
        "Test an angle for Trad Rack's servo relative to servo_down_angle"
    )

    def cmd_TR_SERVO_TEST(self, gcmd):
        # get commanded and raw angles
        cmd_angle = gcmd.get_float(
            "ANGLE", abs(self.servo_up_angle - self.servo_down_angle)
        )
        if self.servo_up_angle > self.servo_down_angle:
            raw_angle = self.servo_down_angle + cmd_angle

            def raw_to_cmd(raw):
                return raw - self.servo_down_angle

        else:
            raw_angle = self.servo_down_angle - cmd_angle

            def raw_to_cmd(raw):
                return self.servo_down_angle - raw

        # display angles
        gcmd.respond_info(
            "commanded angle: %.3f\nraw angle: %.3f" % (cmd_angle, raw_angle)
        )

        # check raw angle
        max_angle = self.servo.get_max_angle()
        if raw_angle > max_angle:
            raise self.gcode.error(
                "Raw angle is above the maximum of %.3f (corresponding to a"
                " commanded angle of %.3f). If the servo is not rotating far"
                " enough, try increasing maximum_pulse_width in the [%s]"
                " section in the config file."
                % (max_angle, raw_to_cmd(max_angle), SERVO_NAME)
            )
        elif raw_angle < 0.0:
            raise self.gcode.error(
                "Raw angle is below the minimum of 0.0 (corresponding to a"
                " commanded angle of %.3f). If the servo is not rotating far"
                " enough, try decreasing minimum_pulse_width in the [%s]"
                " section in the config file." % (raw_to_cmd(0.0), SERVO_NAME)
            )

        # set servo
        self.servo.set_servo(angle=raw_angle)

    cmd_TR_SET_ACTIVE_LANE_help = (
        "Set lane number that is currently loaded in the toolhead"
    )

    def cmd_TR_SET_ACTIVE_LANE(self, gcmd):
        # get lane
        lane = gcmd.get_int("LANE", None)

        # check lane
        self._check_lane_valid(lane)

        # check for filament in the selector
        if not self._query_selector_sensor():
            raise self.gcode.error(
                "Cannot set active lane without filament in selector"
            )

        # set selector position
        print_time = self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[0] = self.lane_positions[lane]
        self.tr_toolhead.set_position(pos, homing_axes=(0,))
        stepper_enable = self.printer.lookup_object("stepper_enable")
        enable = stepper_enable.lookup_enable(SELECTOR_STEPPER_NAME)
        enable.motor_enable(print_time)

        # set current lane and active lane
        self.curr_lane = lane
        self._set_active_lane(lane)

        # restore extruder sync
        self._restore_extruder_sync()

        # make lane the new default for its assigned tool
        self._make_lane_default(lane)

        # enable runout detection
        self.selector_sensor.set_active(True)

        # notify active lane was set without loading the toolhead
        self.printer.send_event("trad_rack:forced_active_lane")

    cmd_TR_RESET_ACTIVE_LANE_help = (
        "Resets active lane to None to indicate the toolhead is not loaded"
    )

    def cmd_TR_RESET_ACTIVE_LANE(self, gcmd):
        self._set_active_lane(None)
        self._raise_servo()
        self.extruder_sync_manager.unsync()
        self.selector_sensor.set_active(False)
        self.printer.send_event("trad_rack:reset_active_lane")

    cmd_TR_RESUME_help = "Resume after a failed load or unload"

    def cmd_TR_RESUME(self, gcmd):
        resume_msg = None

        # loop through all resumes in the stack
        while True:
            # pop the last resume
            try:
                resume_callback, resume_kwargs = self.resume_stack.pop()
            except IndexError:
                break
            curr_stack_size = len(self.resume_stack)

            # run the resume callback
            try:
                retry_resume, resume_msg = resume_callback(
                    gcmd, **resume_kwargs
                )
            except:
                # if the resume callback raised an error, add the resume back to
                # the stack
                self.resume_stack.append((resume_callback, resume_kwargs))
                raise

            # if a new resume was set up by the callback, return since the user
            # needs to handle that and call TR_RESUME again
            if len(self.resume_stack) > curr_stack_size:
                return

            # if the resume needs to be retried, add it back to the stack and
            # wait for the user to call TR_RESUME again
            if retry_resume:
                self.resume_stack.append((resume_callback, resume_kwargs))
                return

        # resume the print
        self._send_resume(resume_msg)

    cmd_TR_LOCATE_SELECTOR_help = (
        "Ensures the position of Trad Rack's selector is known so that it is"
        " ready for a print"
    )

    def cmd_TR_LOCATE_SELECTOR(self, gcmd):
        if self._query_selector_sensor():
            if self.active_lane is None and self.save_active_lane:
                # set active lane if a valid lane was saved
                saved_active_lane = self.variables.get(self.VARS_ACTIVE_LANE)
                try:
                    self._check_lane_valid(saved_active_lane)
                    self.active_lane = saved_active_lane
                except self.gcode.error:
                    pass

            if self.active_lane is None:
                # ask user to set the active lane or unload the lane
                gcmd.respond_info(
                    "Selector sensor is triggered but no active lane is set."
                    " Please use TR_SET_ACTIVE_LANE LANE=&lt;lane index&gt; if"
                    " the toolhead is already loaded, else use"
                    " TR_UNLOAD_TOOLHEAD to unload the filament. Then use"
                    " TR_RESUME to resume the print."
                )
                self.ignore_next_unload_length = True

                # set up callback to run if user takes no action
                if self.user_wait_time != -1:
                    gcmd.respond_info(
                        "If no action is taken within %d seconds, Trad Rack"
                        " will unload the toolhead and resume automatically."
                        % (self.user_wait_time)
                    )
                    RunIfNoActivity(
                        self.tr_toolhead,
                        self.reactor,
                        self._unload_toolhead_and_resume,
                        self.user_wait_time,
                    )

                # set up resume callback and pause the print
                # (and wait for user to resume)
                resume_kwargs = {
                    "condition": (
                        lambda: self.active_lane is not None
                        or not self._query_selector_sensor()
                    ),
                    "action": self._resume_act_locate_selector,
                    "fail_msg": (
                        "Cannot resume. Please use either TR_SET_ACTIVE_LANE or"
                        " TR_UNLOAD_TOOLHEAD, then use TR_RESUME."
                    ),
                }
                self._set_up_resume_and_pause("check condition", resume_kwargs)
            else:
                # (if the selector is homed, nothing needs to be done)
                if not self._is_selector_homed():
                    # set selector position and enable motor
                    # (this allows printing again without reloading the
                    # toolhead if the motor was disabled after the last print)
                    self.cmd_TR_SET_ACTIVE_LANE(
                        self.gcode.create_gcode_command(
                            "TR_SET_ACTIVE_LANE",
                            "TR_SET_ACTIVE_LANE",
                            {"LANE": self.active_lane},
                        )
                    )
                    gcmd.respond_info(
                        "Set lane %d as the active lane" % (self.active_lane)
                    )
        else:
            self._set_active_lane(None)
            self.selector_sensor.set_active(False)
            if not self._is_selector_homed():
                self.cmd_TR_HOME(
                    self.gcode.create_gcode_command("TR_HOME", "TR_HOME", {})
                )

    cmd_TR_CALIBRATE_SELECTOR_help = (
        "Calibrate lane_spacing and the selector's min, endstop, and max"
        " positions"
    )

    def cmd_TR_CALIBRATE_SELECTOR(self, gcmd):
        self.tr_next_generator = self._calibrate_selector(gcmd)
        next(self.tr_next_generator)

    cmd_TR_NEXT_help = (
        "You will be prompted to use this command if Trad Rack requires user"
        " confirmation"
    )

    def cmd_TR_NEXT(self, gcmd):
        if self.tr_next_generator:
            try:
                next(self.tr_next_generator)
            except Exception as e:
                self.tr_next_generator = None
                if not isinstance(e, StopIteration):
                    raise
        else:
            raise self.gcode.error("TR_NEXT command is inactive")

    cmd_TR_SET_HOTEND_LOAD_LENGTH_help = (
        "Sets hotend_load_length. Does not persist across restarts."
    )

    def cmd_TR_SET_HOTEND_LOAD_LENGTH(self, gcmd):
        value = gcmd.get_float("VALUE", None, minval=0.0)
        if value is None:
            adjust = gcmd.get_float("ADJUST", None)
            if adjust is None:
                raise self.gcode.error("VALUE or ADJUST must be specified")
            value = max(0.0, self.hotend_load_length + adjust)
        self.hotend_load_length = value
        gcmd.respond_info("hotend_load_length: %f" % (self.hotend_load_length))

    cmd_TR_DISCARD_BOWDEN_LENGTHS_help = (
        "Discards saved bowden lengths and reverts them to the bowden_length"
        " config value"
    )

    def cmd_TR_DISCARD_BOWDEN_LENGTHS(self, gcmd):
        mode = gcmd.get("MODE", "ALL").upper()
        if mode not in ["ALL", "LOAD", "UNLOAD"]:
            raise gcmd.error("Invalid MODE: %s" % mode)

        # discard load length
        if mode in ["ALL", "LOAD"]:
            self.bowden_load_length = self.config_bowden_length
            self.bowden_load_length_filter.reset()
            self.gcode.run_script_from_command(
                'SAVE_VARIABLE VARIABLE=%s VALUE="%s"'
                % (self.VARS_CALIB_BOWDEN_LOAD_LENGTH, {})
            )

        # discard unload length
        if mode in ["ALL", "UNLOAD"]:
            self.bowden_unload_length = self.config_bowden_length
            self.bowden_unload_length_filter.reset()
            self.gcode.run_script_from_command(
                'SAVE_VARIABLE VARIABLE=%s VALUE="%s"'
                % (self.VARS_CALIB_BOWDEN_UNLOAD_LENGTH, {})
            )

    cmd_TR_SYNC_TO_EXTRUDER_help = (
        "Sync Trad Rack's filament driver to the extruder"
    )

    def cmd_TR_SYNC_TO_EXTRUDER(self, gcmd):
        self.toolhead.wait_moves()
        self.sync_to_extruder = True
        self._restore_extruder_sync()

    cmd_TR_UNSYNC_FROM_EXTRUDER_help = (
        "Unsync Trad Rack's filament driver from the extruder"
    )

    def cmd_TR_UNSYNC_FROM_EXTRUDER(self, gcmd):
        self.toolhead.wait_moves()
        self.sync_to_extruder = False
        self._restore_extruder_sync()

    cmd_TR_ASSIGN_LANE_help = "Assign a lane to a tool"

    def cmd_TR_ASSIGN_LANE(self, gcmd):
        lane = gcmd.get_int("LANE", None)
        tool = gcmd.get_int("TOOL", None)

        # check lane and tool
        self._check_lane_valid(lane)
        self._check_tool_valid(tool)

        # assign lane
        self._assign_lane(lane, tool)

        # mark lane as not dead
        self.lanes_dead[lane] = False

        # make lane the new default for the tool
        if gcmd.get_int("SET_DEFAULT", 0):
            self.default_lanes[tool] = lane

    cmd_TR_SET_DEFAULT_LANE_help = "Set the default lane for a tool"

    def cmd_TR_SET_DEFAULT_LANE(self, gcmd):
        lane = gcmd.get_int("LANE", None)
        tool = gcmd.get_int("TOOL", None)

        # check lane
        self._check_lane_valid(lane)

        if tool is None:
            # set lane as default for its currently-assigned tool
            self._make_lane_default(lane)
        else:
            # check tool
            self._check_tool_valid(tool)

            # set lane as default for the tool
            self._set_default_lane(tool, lane)

    cmd_TR_RESET_TOOL_MAP_help = "Reset tools assigned to each lane"

    def cmd_TR_RESET_TOOL_MAP(self, gcmd):
        self._reset_tool_map()

    cmd_TR_PRINT_TOOL_MAP_help = "Print tool assignment for each lane"

    def cmd_TR_PRINT_TOOL_MAP(self, gcmd):
        num_chars = len(str(self.lane_count - 1))
        lane_msg = "|Lane: |"
        tool_msg = "|Tool: |"
        for lane in range(self.lane_count):
            lane_str = str(lane)
            lane_msg += " " * (num_chars - len(lane_str)) + lane_str + "|"
            tool_str = str(self.tool_map[lane])
            tool_msg += " " * (num_chars - len(tool_str)) + tool_str + "|"
        gcmd.respond_info(lane_msg + "\n" + tool_msg)

    cmd_TR_PRINT_TOOL_GROUPS_help = "Print lanes assigned to each tool"

    def cmd_TR_PRINT_TOOL_GROUPS(self, gcmd):
        tool_groups = []
        for _ in range(self.lane_count):
            tool_groups.append([])
        for lane in range(self.lane_count):
            tool_groups[self.tool_map[lane]].append(lane)
        msg = ""
        for tool in range(len(tool_groups)):
            msg += "Tool {}: {}".format(tool, tool_groups[tool])
            if len(tool_groups[tool]) > 1:
                msg += " (default: {})".format(self.default_lanes[tool])
            msg += "\n"
        gcmd.respond_info(msg)

    cmd_SELECT_TOOL_help = (
        "Load filament from Trad Rack into the toolhead with T<index> commands"
    )

    def cmd_SELECT_TOOL(self, gcmd):
        tool = int(gcmd.get_command().partition("T")[2])
        params = gcmd.get_command_parameters()
        params["TOOL"] = tool
        self.cmd_TR_LOAD_TOOLHEAD(
            self.gcode.create_gcode_command(
                "TR_LOAD_TOOLHEAD", "TR_LOAD_TOOLHEAD", params
            )
        )

    # helper functions
    def _lower_servo(self, toolhead_dwell=False):
        self.tr_toolhead.wait_moves()
        self.servo.set_servo(angle=self.servo_down_angle)
        if self.servo_raised or self.servo_raised is None:
            self.tr_toolhead.dwell(self.servo_wait)
            if toolhead_dwell:
                self.toolhead.dwell(self.servo_wait)
        self.servo_raised = False

    def _raise_servo(
        self,
        toolhead_dwell=False,
        tr_toolhead_dwell=True,
        wait_moves=True,
        print_time=None,
    ):
        if wait_moves:
            self.tr_toolhead.wait_moves()
        self.servo.set_servo(angle=self.servo_up_angle, print_time=print_time)
        if not self.servo_raised:
            if tr_toolhead_dwell:
                self.tr_toolhead.dwell(self.servo_wait)
            if toolhead_dwell:
                self.toolhead.dwell(self.servo_wait)
        self.servo_raised = True

    def _is_selector_homed(self):
        return (
            "x"
            in self.tr_toolhead.get_kinematics().get_status(
                self.reactor.monotonic()
            )["homed_axes"]
        )

    def _query_selector_sensor(self):
        move_time = self.tr_toolhead.get_last_move_time()
        return not not self.fil_driver_endstops[0][0].query_endstop(move_time)

    def _query_toolhead_sensor(self):
        if not self.toolhead_fil_endstops:
            return None
        move_time = self.tr_toolhead.get_last_move_time()
        return not not self.toolhead_fil_endstops[0][0].query_endstop(move_time)

    def _check_lane_valid(self, lane):
        if lane is None or lane > self.lane_count - 1 or lane < 0:
            raise self.gcode.error("Invalid LANE")

    def _check_tool_valid(self, tool):
        try:
            self._check_lane_valid(tool)
        except:
            raise self.gcode.error("Invalid TOOL")

    def _check_selector_homed(self):
        if not self._is_selector_homed():
            raise SelectorNotHomedError("Must home selector first")

    def _can_lower_servo(self):
        return (
            self._is_selector_homed() and self.curr_lane is not None
        ) or self._query_selector_sensor()

    def _reset_fil_driver(self):
        self.extruder_sync_manager.reset_fil_driver()

    def _restore_extruder_sync(self):
        if self.sync_to_extruder and self.active_lane is not None:
            self.extruder_sync_manager.sync_fil_driver_to_extruder()
            self._lower_servo(True)
        else:
            self._raise_servo()
            self.tr_toolhead.wait_moves()
            self.extruder_sync_manager.unsync()

    def _go_to_lane(self, lane):
        # check if homed
        self._check_selector_homed()

        # check lane
        self._check_lane_valid(lane)
        if lane == self.curr_lane:
            return

        # check for filament in the selector
        if self._query_selector_sensor():
            raise self.gcode.error(
                "Cannot change lane with filament in selector"
            )

        # raise servo
        self._raise_servo()

        # move to lane
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[0] = self.lane_positions[lane]
        self.tr_toolhead.move(pos, self.sel_max_velocity)

        # set current lane
        self.curr_lane = lane

    def _load_lane(self, lane, gcmd, reset_speed=False, user_load=False):
        # check lane
        self._check_lane_valid(lane)

        # reset lane speed
        if reset_speed:
            self.lanes_unloaded[lane] = False

        # move selector
        self._go_to_lane(lane)

        # lower servo and turn the drive gear until filament is detected
        self._lower_servo()
        self.tr_toolhead.wait_moves()
        if user_load:
            gcmd.respond_info("Please insert filament in lane %d" % (lane))

        # load filament into the selector
        self._load_selector(lane, user_load=user_load)

        # retract filament into the module
        self._reset_fil_driver()
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[1] -= (
            self.selector_unload_length + self.selector_unload_length_extra
        )
        self.tr_toolhead.move(pos, self.selector_unload_speed)

        # undo extra unload length offset
        pos[1] += self.selector_unload_length_extra
        self.tr_toolhead.move(pos, self.selector_unload_speed)

        # reset filament driver position
        self._reset_fil_driver()

        # raise servo
        self._raise_servo()

        if user_load:
            gcmd.respond_info("Load complete")

    def _wait_for_heater_temp(self, min_temp=0.0, exact_temp=0.0):
        # get current and target temps
        heater = self.toolhead.get_extruder().get_heater()
        smoothed_temp, target_temp = heater.get_temp(self.reactor.monotonic())
        min_extrude_temp = heater.min_extrude_temp

        # raise an error if no valid temp has been set
        if (
            max(min_temp, exact_temp, target_temp, self.last_heater_target)
            < min_extrude_temp
        ):
            raise self.gcode.error(
                "Extruder temperature must be set above min_extrude_temp"
            )

        # set temp and wait if below acceptable temp
        min_temp = max(min_temp, min_extrude_temp)
        if exact_temp or smoothed_temp < min_temp:
            if exact_temp:
                temp = save_temp = exact_temp
            elif target_temp > min_temp:
                temp = save_temp = target_temp
            else:
                temp = max(min_temp, self.last_heater_target)
                if min_temp >= min_extrude_temp:
                    save_temp = min_temp
                else:
                    save_temp = None
            pheaters = self.printer.lookup_object("heaters")
            pheaters.set_temperature(heater, temp, True)
            return save_temp
        return target_temp

    def _save_heater_target(self, target_temp=None):
        if target_temp is None:
            heater = self.toolhead.get_extruder().get_heater()
            _, target_temp = heater.get_temp(self.reactor.monotonic())
        self.gcode.run_script_from_command(
            'SAVE_VARIABLE VARIABLE=%s VALUE="%s"'
            % (self.VARS_HEATER_TARGET, target_temp)
        )
        self.last_heater_target = target_temp

    def _load_toolhead(
        self,
        lane,
        gcmd,
        tool=None,
        min_temp=0.0,
        exact_temp=0.0,
        selector_already_loaded=False,
        bowden_length=None,
        extruder_load_length=None,
        hotend_load_length=None,
    ):
        # keep track of lane in case of an error (and for status)
        self.next_lane = lane

        # check lane
        self._check_lane_valid(lane)
        if lane == self.active_lane:
            return

        # check if homed
        self._check_selector_homed()

        # check and set lengths
        if bowden_length is None:
            bowden_length = self.bowden_load_length
        if extruder_load_length is None:
            extruder_load_length = self.extruder_load_length
        if hotend_load_length is None:
            hotend_load_length = self.hotend_load_length

        # save gcode state
        self.gcode.run_script_from_command(
            "SAVE_GCODE_STATE NAME=TR_TOOLCHANGE_STATE"
        )

        # wait for heater temp if needed
        save_temp = self._wait_for_heater_temp(min_temp, exact_temp)

        # disable runout detection
        self.selector_sensor.set_active(False)

        # unload current lane (if filament is detected)
        if not (selector_already_loaded and self.curr_lane == lane):
            try:
                self._unload_toolhead(gcmd)
            except:
                self._raise_servo()
                if self.curr_lane is None:
                    gcmd.respond_info(
                        "Failed to unload. Please either pull the filament out"
                        " of the toolhead and selector or retry with"
                        " TR_UNLOAD_TOOLHEAD, then use TR_RESUME to continue."
                    )
                else:
                    gcmd.respond_info(
                        "Failed to unload. Please either pull the filament in"
                        " lane {lane} out of the toolhead and selector or retry"
                        " with TR_UNLOAD_TOOLHEAD, then use TR_RESUME to reload"
                        " lane {lane} and continue.".format(
                            lane=str(self.curr_lane)
                        )
                    )
                    self.lanes_unloaded[self.curr_lane] = False
                self.retry_lane = self.curr_lane
                logging.warning(
                    "trad_rack: Failed to unload toolhead", exc_info=True
                )
                raise TradRackLoadError(
                    "Failed to load toolhead. Could not unload toolhead before"
                    " load"
                )

        # notify toolhead load started
        self.printer.send_event("trad_rack:load_started")

        # run pre-load custom gcode
        self.pre_load_macro.run_gcode_from_command()
        self.toolhead.wait_moves()
        self.tr_toolhead.wait_moves()

        # load filament into the selector
        try:
            selected_lane = self._load_selector(lane, tool=tool)
        except:
            self._raise_servo()
            if tool is None:
                gcmd.respond_info(
                    "Failed to load selector from lane {lane}. Use TR_RESUME to"
                    " reload lane {lane} and retry.".format(lane=str(lane))
                )
            else:
                assigned_lanes = self._get_assigned_lanes(tool)
                gcmd.respond_info(
                    "Failed to load selector from any of the lanes assigned to"
                    " tool {tool}: {lanes}. Use TR_LOAD_LANE LANE=&lt;lane"
                    " index&gt to reload one of these lanes, then use TR_RESUME"
                    " to retry. (If you want to use a different lane, use"
                    " TR_ASSIGN_LANE LANE=&lt;lane index&gt TOOL={tool}"
                    " beforehand.)".format(tool=tool, lanes=assigned_lanes)
                )
            self.retry_lane = lane
            self.retry_tool = tool
            logging.warning("trad_rack: Failed to load selector", exc_info=True)
            raise TradRackLoadError(
                "Failed to load toolhead. Could not load selector from lane %d"
                % lane
            )
        self.retry_tool = None

        # update lane and next_lane in case the selector was loaded from a lane
        # other than what was initially specified
        lane = self.next_lane = selected_lane

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
            hmove = HomingMove(
                self.printer, self.toolhead_fil_endstops, self.tr_toolhead
            )
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
        self.extruder_sync_manager.sync_extruder_to_fil_driver()

        # move filament until toolhead sensor is triggered
        if self.load_with_toolhead_sensor and self.toolhead_fil_endstops:
            pos = self.tr_toolhead.get_position()
            move_start = pos[1]
            pos[1] += self.fil_homing_lengths["bowden load"]
            hmove = HomingMove(
                self.printer, self.toolhead_fil_endstops, self.tr_toolhead
            )
            try:
                trigpos = hmove.homing_move(
                    pos, self.toolhead_sense_speed, probe_pos=True
                )
            except:
                self._raise_servo()
                self.extruder_sync_manager.unsync()
                gcmd.respond_info(
                    "Failed to load toolhead from lane {lane} (no trigger on"
                    " toolhead sensor). Please either pull the filament in lane"
                    " {lane} out of the toolhead and selector or use"
                    " TR_UNLOAD_TOOLHEAD. Then use TR_RESUME to reload lane"
                    " {lane} and retry.".format(lane=str(lane))
                )
                self.retry_lane = lane
                logging.warning(
                    "trad_rack: Toolhead sensor homing move failed",
                    exc_info=True,
                )
                raise TradRackLoadError(
                    "Failed to load toolhead. No trigger on toolhead sensor"
                    " after full movement"
                )

            # update bowden_load_length
            length = (
                trigpos[1]
                - move_start
                + base_length
                - self.target_toolhead_homing_dist
            )
            old_set_length = self.bowden_load_length
            self.bowden_load_length = self.bowden_load_length_filter.update(
                length
            )
            samples = self.bowden_load_length_filter.get_entry_count()
            if self.log_bowden_lengths:
                self._write_bowden_length_data(
                    self.bowden_load_lengths_filename,
                    length,
                    old_set_length,
                    self.bowden_load_length,
                    samples,
                )
            self._save_bowden_length("load", self.bowden_load_length, samples)
            if not (self.bowden_load_calibrated or reached_sensor_early):
                self.bowden_load_calibrated = True
                gcmd.respond_info(
                    "Calibrated bowden_load_length: {}".format(
                        self.bowden_load_length
                    )
                )

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
            if hasattr(toolhead, "LookAheadQueue"):
                hotend_load_time = (
                    self.tr_toolhead.lookahead.get_last().min_move_t
                )
            else:
                hotend_load_time = (
                    self.tr_toolhead.move_queue.get_last().min_move_t
                )
        else:
            hotend_load_time = 0.0
        servo_delay = max(0.0, self.servo_wait - hotend_load_time)

        # flush lookahead and raise servo before move ends
        print_time = (
            self.tr_toolhead.get_last_move_time()
            - self.servo_wait
            + servo_delay
        )
        if not self.sync_to_extruder:
            self._raise_servo(
                tr_toolhead_dwell=False, wait_moves=False, print_time=print_time
            )

            # wait for servo move if necessary
            if servo_delay:
                self.tr_toolhead.dwell(servo_delay)

        # set active lane
        self._set_active_lane(lane)

        # unsync extruder from filament driver
        self.tr_toolhead.wait_moves()
        self._restore_extruder_sync()

        # make lane the new default for its assigned tool
        self._make_lane_default(lane)

        # enable runout detection
        self.selector_sensor.set_active(True)

        # save heater target
        if save_temp is not None:
            self._save_heater_target(target_temp=save_temp)

        # run post-load custom gcode
        self.post_load_macro.run_gcode_from_command()
        self.toolhead.wait_moves()
        self.tr_toolhead.wait_moves()

        # restore gcode state
        self.gcode.run_script_from_command(
            "RESTORE_GCODE_STATE NAME=TR_TOOLCHANGE_STATE MOVE=1"
        )

        # reset next lane
        self.next_lane = None

        # notify toolhead load complete
        self.printer.send_event("trad_rack:load_complete")

    def _load_selector(self, lane, tool=None, user_load=False):
        try:
            self._do_load_selector(lane, user_load=user_load)
        except self.gcode.error:
            if tool is None:
                raise
            else:
                lane = self._find_replacement_lane(lane)
                if lane is None:
                    raise self.gcode.error(
                        "Failed to load filament into selector from any of the"
                        " lanes assigned to tool {}".format(tool)
                    )
        return lane

    def _do_load_selector(self, lane, user_load=False):
        # move selector
        self._go_to_lane(lane)

        # lower servo and turn the drive gear until filament is detected
        self._lower_servo()
        self._reset_fil_driver()
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        hmove = HomingMove(
            self.printer, self.fil_driver_endstops, self.tr_toolhead
        )
        if user_load:
            length_key = "user load lane"
        else:
            length_key = "load selector"
        pos[1] += self.fil_homing_lengths[length_key]
        try:
            hmove.homing_move(pos, self.selector_sense_speed)
        except:
            self._raise_servo()
            logging.warning(
                "trad_rack: Selector homing move failed", exc_info=True
            )
            raise self.gcode.error(
                "Failed to load filament into selector. No trigger on selector"
                " sensor after full movement"
            )

    def _unload_selector(
        self, gcmd, base_length=None, mark_calibrated=False, eject=False
    ):
        # check for filament in selector
        if not self._query_selector_sensor():
            gcmd.respond_info(
                "No filament detected. Attempting to load selector"
            )
            self._load_selector(self.curr_lane)
            gcmd.respond_info(
                "Loaded selector. Retracting filament into module"
            )
        else:
            # lower servo and turn the drive gear until filament
            # is no longer detected
            self._lower_servo()
            self._reset_fil_driver()
            self.tr_toolhead.get_last_move_time()
            pos = self.tr_toolhead.get_position()
            move_start = pos[1]
            hmove = HomingMove(
                self.printer, self.fil_driver_endstops, self.tr_toolhead
            )
            pos[1] -= self.fil_homing_lengths["bowden unload"]
            try:
                trigpos = hmove.homing_move(
                    pos,
                    self.selector_sense_speed,
                    probe_pos=True,
                    triggered=False,
                )
            except:
                self._raise_servo()
                logging.warning(
                    "trad_rack: Selector homing move failed", exc_info=True
                )
                raise self.gcode.error(
                    "Failed to unload filament from selector. Selector sensor"
                    " still triggered after full movement"
                )

            # update bowden_unload_length
            if base_length is not None and not self.ignore_next_unload_length:
                length = (
                    move_start
                    - trigpos[1]
                    + base_length
                    - self.target_selector_homing_dist
                )
                old_set_length = self.bowden_unload_length
                self.bowden_unload_length = (
                    self.bowden_unload_length_filter.update(length)
                )
                samples = self.bowden_unload_length_filter.get_entry_count()
                if self.log_bowden_lengths:
                    self._write_bowden_length_data(
                        self.bowden_unload_lengths_filename,
                        length,
                        old_set_length,
                        self.bowden_unload_length,
                        samples,
                    )
                self._save_bowden_length(
                    "unload", self.bowden_unload_length, samples
                )
                if mark_calibrated:
                    self.bowden_unload_calibrated = True
                    gcmd.respond_info(
                        "Calibrated bowden_unload_length: {}".format(
                            self.bowden_unload_length
                        )
                    )

        # retract filament into the module
        self._reset_fil_driver()
        pos = self.tr_toolhead.get_position()
        if eject:
            pos[1] -= self.selector_unload_length + self.eject_length
            speed = self.eject_speed
        else:
            pos[1] -= (
                self.selector_unload_length + self.selector_unload_length_extra
            )
            speed = self.selector_unload_speed
        self.tr_toolhead.move(pos, speed)

        if not eject:
            # undo extra unload length offset
            pos[1] += self.selector_unload_length_extra
            self.tr_toolhead.move(pos, self.selector_unload_speed)

        # reset filament driver position
        self._reset_fil_driver()

        # raise servo
        self._raise_servo()

    def _unload_toolhead(
        self,
        gcmd,
        min_temp=0.0,
        exact_temp=0.0,
        force_unload=False,
        sync=False,
        eject=False,
    ):
        selector_sensor_state = self._query_selector_sensor()
        toolhead_sensor_state = self._query_toolhead_sensor()

        # check for filament
        self.toolhead.wait_moves()
        if not (force_unload or selector_sensor_state or toolhead_sensor_state):
            # reset ignore_next_unload_length
            self.ignore_next_unload_length = False

            return

        # check for faulty toolhead or selector sensor
        if not force_unload:
            if toolhead_sensor_state and not selector_sensor_state:
                gcmd.respond_info(
                    "WARNING: The toolhead filament sensor is triggered but the"
                    " selector sensor is not. This may indicate that one of the"
                    " sensors is faulty or that there is a short piece of"
                    " filament in the bowden tube that does not reach the"
                    " selector."
                )

        # check that the selector is at a lane
        if not self._can_lower_servo():
            raise self.gcode.error(
                "Selector must be moved to a lane before unloading"
            )

        # disable runout detection
        self.selector_sensor.set_active(False)

        # notify toolhead unload started
        self.printer.send_event("trad_rack:unload_started")

        # wait for heater temp if needed
        self._wait_for_heater_temp(min_temp, exact_temp)

        # sync filament driver to extruder for pre-unload custom gcode
        if sync:
            self.extruder_sync_manager.sync_fil_driver_to_extruder()
            self._lower_servo(True)

        # run pre-unload custom gcode
        try:
            self.pre_unload_macro.run_gcode_from_command()
            self.toolhead.wait_moves()
            self.tr_toolhead.wait_moves()
        finally:
            # unsync filament driver from extruder
            self.extruder_sync_manager.unsync()

            # reset active lane
            self._set_active_lane(None)

        # lower servo
        self._lower_servo(True)

        # sync extruder to filament driver
        self.tr_toolhead.wait_moves()
        self.extruder_sync_manager.sync_extruder_to_fil_driver()

        # move filament until toolhead sensor is untriggered
        if self.unload_with_toolhead_sensor and self.toolhead_fil_endstops:
            pos = self.tr_toolhead.get_position()
            pos[1] -= self.fil_homing_lengths["unload toolhead"]
            hmove = HomingMove(
                self.printer, self.toolhead_fil_endstops, self.tr_toolhead
            )
            try:
                hmove.homing_move(
                    pos, self.toolhead_sense_speed, triggered=False
                )
            except:
                self._raise_servo()
                self.extruder_sync_manager.unsync()
                logging.warning(
                    "trad_rack: Toolhead sensor homing move failed",
                    exc_info=True,
                )
                raise self.gcode.error(
                    "Failed to unload toolhead. Toolhead sensor still triggered"
                    " after full movement"
                )

        # get filament out of the extruder
        self._reset_fil_driver()
        pos = self.tr_toolhead.get_position()
        pos[1] -= self.toolhead_unload_length
        self.tr_toolhead.move(pos, self.toolhead_unload_speed)

        # unsync extruder from filament driver
        self.tr_toolhead.wait_moves()
        self.extruder_sync_manager.unsync()

        # move filament through the bowden tube
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        move_start = pos[1]
        pos[1] -= self.bowden_unload_length
        hmove = HomingMove(
            self.printer, self.fil_driver_endstops, self.tr_toolhead
        )
        reached_sensor_early = True
        try:
            # move and check for early sensor trigger
            trigpos = hmove.homing_move(
                pos, self.buffer_pull_speed, probe_pos=True, triggered=False
            )

            # if sensor triggered early, retract before next homing move
            pos[1] = trigpos[1] + self.fil_homing_retract_dist
        except self.printer.command_error:
            reached_sensor_early = False
        self.tr_toolhead.move(pos, self.buffer_pull_speed)

        # unload selector
        mark_calibrated = not (
            self.bowden_unload_calibrated or reached_sensor_early
        )
        self._unload_selector(gcmd, move_start - pos[1], mark_calibrated, eject)

        # note that the current lane's buffer has been filled
        if self.curr_lane is not None:
            self.lanes_unloaded[self.curr_lane] = True

        # reset ignore_next_unload_length
        self.ignore_next_unload_length = False

        # run post-unload custom gcode
        self.post_unload_macro.run_gcode_from_command()
        self.toolhead.wait_moves()
        self.tr_toolhead.wait_moves()

        # notify toolhead unload complete
        self.printer.send_event("trad_rack:unload_complete")

    def _send_pause(self):
        pause_resume = self.printer.lookup_object("pause_resume")
        if not pause_resume.get_status(self.reactor.monotonic())["is_paused"]:
            self.pause_macro.run_gcode_from_command()

    def _send_resume(self, resume_msg=None):
        pause_resume = self.printer.lookup_object("pause_resume")
        if not pause_resume.get_status(self.reactor.monotonic())["is_paused"]:
            return
        if resume_msg:
            self.gcode.respond_info(resume_msg)
        self.resume_macro.run_gcode_from_command()

    def _set_active_lane(self, lane):
        self.active_lane = lane
        if self.save_active_lane:
            self.gcode.run_script_from_command(
                'SAVE_VARIABLE VARIABLE=%s VALUE="%s"'
                % (self.VARS_ACTIVE_LANE, lane)
            )

    def _reset_tool_map(self):
        self.tool_map = list(range(self.lane_count))
        self.default_lanes = list(range(self.lane_count))

    def _find_replacement_lane(self, runout_lane):
        tool = self.tool_map[runout_lane]
        pre_dead_lanes = []

        # 1st pass - check lanes not marked as dead
        lane = (runout_lane + 1) % self.lane_count
        while True:
            if self.tool_map[lane] == tool:
                if self.lanes_dead[lane]:
                    pre_dead_lanes.append(lane)
                else:
                    try:
                        self._load_selector(lane)
                        self.default_lanes[tool] = lane
                        return lane
                    except:
                        self.lanes_dead[lane] = True
            if lane == runout_lane:
                break
            lane = (lane + 1) % self.lane_count

        # 2nd pass - check lanes previously marked as dead
        for lane in pre_dead_lanes:
            try:
                self._load_selector(lane)
                self.lanes_dead[lane] = False
                self.default_lanes[tool] = lane
                return lane
            except:
                pass
        return None

    def _set_default_lane(self, tool, lane=None):
        # set lane that was passed in
        if lane is not None:
            self._assign_lane(lane, tool)
            self.default_lanes[tool] = lane
            return

        # find a lane that is already assigned to the tool
        for lane in range(self.lane_count):
            if self.tool_map[lane] == tool:
                self.default_lanes[tool] = lane
                return
        self.default_lanes[tool] = None

    def _make_lane_default(self, lane):
        self.default_lanes[self.tool_map[lane]] = lane

    def _assign_lane(self, lane, tool):
        prev_tool = self.tool_map[lane]

        # assign lane to tool
        self.tool_map[lane] = tool

        # reassign default lane for previous tool if needed
        if self.default_lanes[prev_tool] == lane:
            self._set_default_lane(prev_tool)

        # ensure new tool has a default lane assigned
        if self.default_lanes[tool] is None:
            self.default_lanes[tool] = lane

    def _get_assigned_lanes(self, tool):
        lanes = []
        for lane in range(self.lane_count):
            if self.tool_map[lane] == tool:
                lanes.append(lane)
        return lanes

    def _runout_replace_filament(self, gcmd):
        # unload
        if self.runout_steps_done < 1:
            try:
                self._unload_toolhead(
                    gcmd, force_unload=True, sync=True, eject=True
                )
            except:
                self._raise_servo()
                gcmd.respond_info(
                    "Failed to unload. Please pull filament {} out of the"
                    " toolhead and selector, then use TR_RESUME to continue."
                    .format(self.runout_lane)
                )
                logging.warning(
                    "trad_rack: Failed to unload toolhead", exc_info=True
                )
                return False
            self.runout_steps_done = 1

        # find a new lane to use
        selector_already_loaded = False
        if self.runout_steps_done < 2:
            lane = self._find_replacement_lane(self.runout_lane)
            if lane is None:
                runout_tool = self.tool_map[self.runout_lane]
                assigned_lanes = self._get_assigned_lanes(runout_tool)
                gcmd.respond_info(
                    "No replacement lane found for tool {tool}. The following"
                    " lanes are assigned to tool {tool}: {lanes}. Use"
                    " TR_LOAD_LANE LANE=&lt;lane index&gt; to load one of these"
                    " lanes, or use TR_ASSIGN_LANE LANE=&lt;lane index&gt;"
                    " TOOL={tool} to assign another lane. Then use TR_RESUME to"
                    " continue.".format(
                        tool=str(runout_tool), lanes=str(assigned_lanes)
                    )
                )
                return False
            self.replacement_lane = lane
            selector_already_loaded = True
            self.runout_lane = None
            self.runout_steps_done = 2

        # load toolhead
        self._load_toolhead(
            self.replacement_lane,
            gcmd,
            selector_already_loaded=selector_already_loaded,
        )
        return True

    def _write_bowden_length_data(
        self, filename, length, old_set_length, new_set_length, samples
    ):
        try:
            with open(filename, "a+") as f:
                if os.stat(filename).st_size == 0:
                    f.write(
                        "time,length,diff_from_set_length,new_set_length,"
                        "new_sample_count\n"
                    )
                f.write(
                    "{},{:.3f},{:.3f},{:.3f},{}\n".format(
                        time.strftime("%Y%m%d_%H%M%S"),
                        length,
                        length - old_set_length,
                        new_set_length,
                        samples,
                    )
                )
        except IOError as e:
            raise self.printer.command_error(
                "Error writing to file '%s': %s", filename, str(e)
            )

    def _save_bowden_length(self, mode, new_set_length, samples):
        length_stats = {
            "new_set_length": new_set_length,
            "sample_count": samples,
        }
        if mode == "load":
            self.gcode.run_script_from_command(
                'SAVE_VARIABLE VARIABLE=%s VALUE="%s"'
                % (self.VARS_CALIB_BOWDEN_LOAD_LENGTH, length_stats)
            )
        else:
            self.gcode.run_script_from_command(
                'SAVE_VARIABLE VARIABLE=%s VALUE="%s"'
                % (self.VARS_CALIB_BOWDEN_UNLOAD_LENGTH, length_stats)
            )

    def _calibrate_selector(self, gcmd):
        extra_travel = 1.0

        # prompt user to set the selector at lane 0
        self._prompt_selector_calibration(0, gcmd)
        yield

        # measure position of lane 0 relative to endstop
        pos_endstop = (
            self.tr_kinematics.get_selector_rail()
            .get_homing_info()
            .position_endstop
        )
        max_travel = self.lane_positions[0] - pos_endstop + extra_travel
        endstop_to_lane0 = self._measure_selector_to_endstop(max_travel, gcmd)

        # prompt user to set the selector at the last lane
        self._prompt_selector_calibration(self.lane_count - 1, gcmd)
        yield

        # measure position of last lane relative to endstop
        max_travel = (
            self.lane_positions[self.lane_count - 1]
            - self.lane_positions[0]
            + endstop_to_lane0
            + extra_travel
        )
        endstop_to_last_lane = self._measure_selector_to_endstop(
            max_travel, gcmd
        )

        # process calibration and set new lane positions
        pos_endstop, lane_spacing, self.lane_positions = (
            self.lane_position_manager.process_selector_calibration(
                endstop_to_lane0, endstop_to_last_lane, 6
            )
        )

        # round new config values
        pos_endstop = round(pos_endstop, 3)
        pos_min = (
            math.floor(min(pos_endstop, self.lane_positions[0]) * 1000) / 1000
        )
        pos_max = (
            math.ceil(self.lane_positions[self.lane_count - 1] * 1000) / 1000
        )

        # set new selector values
        rail = self.tr_kinematics.get_selector_rail()
        rail.position_min = pos_min
        rail.position_endstop = pos_endstop
        rail.position_max = pos_max

        # set current selector position
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[0] = pos_endstop
        self.tr_toolhead.set_position(pos, homing_axes=(0,))

        # show results and prompt user to save config
        gcmd.respond_info(
            "trad_rack: lane_spacing: {lane_spacing:.6f}\n{stepper}:"
            " position_min: {pos_min:.3f}\n{stepper}: position_endstop:"
            " {pos_endstop:.3f}\n{stepper}: position_max: {pos_max:.3f}\nMake"
            " sure to update the printer config file with these parameters so"
            " they will be kept across restarts.".format(
                lane_spacing=lane_spacing,
                stepper=SELECTOR_STEPPER_NAME,
                pos_min=pos_min,
                pos_endstop=pos_endstop,
                pos_max=pos_max,
            )
        )

    def _prompt_selector_calibration(self, lane, gcmd):
        # go to lane
        if not self._is_selector_homed():
            self.cmd_TR_HOME(
                self.gcode.create_gcode_command("TR_HOME", "TR_HOME", {})
            )
        self._go_to_lane(lane)

        # lower servo and turn the drive gear until filament is detected
        self._lower_servo()
        self.tr_toolhead.wait_moves()
        gcmd.respond_info("Please insert filament in lane %d" % (lane))

        # disable selector motor
        print_time = self.tr_toolhead.get_last_move_time()
        stepper_enable = self.printer.lookup_object("stepper_enable")
        enable = stepper_enable.lookup_enable(SELECTOR_STEPPER_NAME)
        enable.motor_disable(print_time)

        # load filament into the selector
        self._load_selector(lane, user_load=True)

        # extend filament past the sensor
        self._reset_fil_driver()
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[1] += 15.0
        self.tr_toolhead.move(pos, self.selector_unload_speed)

        # reset filament driver position
        self._reset_fil_driver()

        # raise servo
        self._raise_servo()

        # prompt user to position selector
        self.tr_toolhead.wait_moves()
        gcmd.respond_info(
            "To ensure that the filament paths of the lane module and selector"
            " are aligned, adjust the selector's position by hand until the"
            " filament can slide smoothly with very little resistance. Then use"
            " TR_NEXT to continue selector calibration."
        )

    def _measure_selector_to_endstop(self, max_travel, gcmd):
        # set selector position
        print_time = self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[0] = max_travel
        self.tr_toolhead.set_position(pos, homing_axes=(0,))
        stepper_enable = self.printer.lookup_object("stepper_enable")
        enable = stepper_enable.lookup_enable(SELECTOR_STEPPER_NAME)
        enable.motor_enable(print_time)

        # unload selector into current lane
        self._unload_selector(gcmd)

        # clear current lane
        self.curr_lane = None

        # prepare for homing move
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[0] = 0.0
        rail = self.tr_kinematics.get_selector_rail()
        endstops = rail.get_endstops()
        hi = rail.get_homing_info()
        if hi.retract_dist:
            speed = hi.second_homing_speed
        else:
            speed = hi.speed

        # retract first if endstop is already triggered
        self.selector_endstops = (
            self.tr_kinematics.get_selector_rail().get_endstops()
        )
        move_time = self.tr_toolhead.get_last_move_time()
        if not not self.selector_endstops[0][0].query_endstop(move_time):
            curr_pos = self.tr_toolhead.get_position()
            curr_pos[0] += 5.0
            self.tr_toolhead.move(curr_pos, hi.speed)
            self.tr_toolhead.wait_moves()

        # homing move
        hmove = HomingMove(self.printer, endstops, self.tr_toolhead)
        trigpos = hmove.homing_move(pos, speed, probe_pos=True)

        # set selector position
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[0] = hi.position_endstop
        self.tr_toolhead.set_position(pos, homing_axes=(0,))

        # return distance traveled
        return max_travel - trigpos[0]

    # resume callbacks
    def _resume_load_toolhead(self, gcmd):
        # load any of the tool's assigned lanes to selector
        selector_already_loaded = False
        if self.retry_tool is not None:
            replacement_lane = self._find_replacement_lane(self.retry_lane)
            if replacement_lane is None:
                raise self.gcode.error(
                    "Failed to load filament into selector from any of the"
                    " lanes assigned to tool {}".format(self.retry_tool)
                )
            self.next_lane = replacement_lane
            selector_already_loaded = True

        # retry loading lane
        elif self.retry_lane is not None:
            self._load_lane(self.retry_lane, gcmd, user_load=True)

        # load next filament into toolhead
        self._load_toolhead(
            self.next_lane,
            gcmd,
            selector_already_loaded=selector_already_loaded,
        )

        return False, "Toolhead loaded successfully. Resuming print"

    def _resume_check_condition(
        self,
        gcmd,
        condition,
        action=None,
        resume_msg="Resuming print",
        fail_msg="Condition not met to resume",
    ):
        if condition():
            if action is not None:
                action()
            return False, resume_msg
        gcmd.respond_info(fail_msg)
        return True, None

    def _resume_runout(self, gcmd):
        if self._runout_replace_filament(gcmd):
            return False, "Toolhead loaded successfully. Resuming print"
        return True, None

    # other resume helper functions
    def _set_up_resume_and_pause(self, resume_type, resume_kwargs):
        # clear the resume stack if the print is not paused
        # (if the stack is not already empty but the print is not paused, then
        # the user likely resumed the print manually without using TR_RESUME, so
        # the existing resume setup is no longer relevant)
        pause_resume = self.printer.lookup_object("pause_resume")
        if not pause_resume.get_status(self.reactor.monotonic())["is_paused"]:
            self.resume_stack.clear()

        # add resume callback and arguments
        self.resume_stack.append(
            (self.resume_callbacks[resume_type], resume_kwargs)
        )

        # pause the print
        self._send_pause()

    def _unload_toolhead_and_resume(self):
        pause_resume = self.printer.lookup_object("pause_resume")
        if pause_resume.get_status(self.reactor.monotonic())["is_paused"]:
            self.gcode.respond_info("Unloading toolhead")
            self.cmd_TR_UNLOAD_TOOLHEAD(
                self.gcode.create_gcode_command(
                    "TR_UNLOAD_TOOLHEAD", "TR_UNLOAD_TOOLHEAD", {}
                )
            )
            self.cmd_TR_RESUME(
                self.gcode.create_gcode_command("TR_RESUME", "TR_RESUME", {})
            )

    def _resume_act_locate_selector(self):
        if not self._is_selector_homed():
            self.cmd_TR_HOME(
                self.gcode.create_gcode_command("TR_HOME", "TR_HOME", {})
            )
        self.ignore_next_unload_length = False

    # other functions
    def set_fil_driver_multiplier(self, multiplier):
        self.extruder_sync_manager.set_fil_driver_multiplier(multiplier)

    def is_fil_driver_synced(self):
        return self.extruder_sync_manager.is_fil_driver_synced()

    def get_status(self, eventtime):
        return {
            "curr_lane": self.curr_lane,
            "active_lane": self.active_lane,
            "next_lane": self.next_lane,
            "tool_map": self.tool_map,
            "selector_homed": self._is_selector_homed(),
        }


class TradRackToolHead(toolhead.ToolHead, object):
    def __init__(self, config, buffer_pull_speed, is_extruder_synced):
        self.printer = config.get_printer()
        try:
            self.danger_options = self.printer.lookup_object("danger_options")
        except config.error:
            pass
        self.reactor = self.printer.get_reactor()
        self.all_mcus = [
            m for n, m in self.printer.lookup_objects(module="mcu")
        ]
        self.mcu = self.all_mcus[0]
        if hasattr(toolhead, "LookAheadQueue"):
            self.lookahead = toolhead.LookAheadQueue(self)
            self.lookahead.set_flush_time(toolhead.BUFFER_TIME_HIGH)
        else:
            self.move_queue = toolhead.MoveQueue(self)
            self.move_queue.set_flush_time(toolhead.BUFFER_TIME_HIGH)
        self.commanded_pos = [0.0, 0.0, 0.0, 0.0]
        # Velocity and acceleration control
        tr_config = config.getsection("trad_rack")
        self.sel_max_velocity = tr_config.getfloat(
            "selector_max_velocity", above=0.0
        )
        self.fil_max_velocity = tr_config.getfloat(
            "filament_max_velocity", default=buffer_pull_speed, above=0.0
        )
        self.max_velocity = max(self.sel_max_velocity, self.fil_max_velocity)
        self.sel_max_accel = tr_config.getfloat("selector_max_accel", above=0.0)
        self.fil_max_accel = tr_config.getfloat(
            "filament_max_accel", default=1500.0, above=0.0
        )
        self.max_accel = max(self.sel_max_accel, self.fil_max_accel)
        self.min_cruise_ratio = config.getfloat(
            "minimum_cruise_ratio", None, below=1.0, minval=0.0
        )
        if self.min_cruise_ratio is None:
            self.min_cruise_ratio = 0.5
            req_accel_to_decel = config.getfloat(
                "max_accel_to_decel", None, above=0.0
            )
            if req_accel_to_decel is not None:
                config.deprecate("max_accel_to_decel")
                self.min_cruise_ratio = 1.0 - min(
                    1.0, (req_accel_to_decel / self.max_accel)
                )
        self.requested_accel_to_decel = self.min_cruise_ratio * self.max_accel
        self.square_corner_velocity = config.getfloat(
            "square_corner_velocity", 5.0, minval=0.0
        )
        self.junction_deviation = self.max_accel_to_decel = 0.0
        self._calc_junction_deviation()
        # Input stall detection
        self.check_stall_time = 0.0
        self.print_stall = 0
        # Input pause tracking
        self.can_pause = True
        if self.mcu.is_fileoutput():
            self.can_pause = False
        self.need_check_pause = -1.0
        # Print time tracking
        self.print_time = 0.0
        self.special_queuing_state = "NeedPrime"
        self.priming_timer = None
        self.drip_completion = None
        # Flush tracking
        self.flush_timer = self.reactor.register_timer(self._flush_handler)
        self.do_kick_flush_timer = True
        self.last_flush_time = self.last_sg_flush_time = (
            self.min_restart_time
        ) = 0.0
        self.need_flush_time = self.step_gen_time = self.clear_history_time = (
            0.0
        )
        # Kinematic step generation scan window time tracking
        self.kin_flush_delay = toolhead.SDS_CHECK_TIME
        self.kin_flush_times = []
        # Setup iterative solver
        ffi_main, ffi_lib = chelper.get_ffi()
        self.trapq = ffi_main.gc(ffi_lib.trapq_alloc(), ffi_lib.trapq_free)
        self.trapq_append = ffi_lib.trapq_append
        self.trapq_finalize_moves = ffi_lib.trapq_finalize_moves
        self.step_generators = []
        # Create kinematic class
        gcode = self.printer.lookup_object("gcode")
        self.Coord = gcode.Coord
        self.extruder = kinematics.extruder.DummyExtruder(self.printer)
        try:
            self.kin = TradRackKinematics(self, config, is_extruder_synced)
        except config.error as e:
            raise
        except self.printer.lookup_object("pins").error as e:
            raise
        except:
            msg = "Error loading kinematics 'trad_rack'"
            logging.exception(msg)
            raise config.error(msg)
        self.printer.register_event_handler(
            "klippy:shutdown", self._handle_shutdown
        )

    def set_position(self, newpos, homing_axes=()):
        for _ in range(4 - len(newpos)):
            newpos.append(0.0)
        super(TradRackToolHead, self).set_position(newpos, homing_axes)

    def get_sel_max_velocity(self):
        return self.sel_max_velocity, self.sel_max_accel

    def get_fil_max_velocity(self):
        return self.fil_max_velocity, self.fil_max_accel


class TradRackKinematics:
    def __init__(self, toolhead, config, is_extruder_synced):
        self.printer = config.get_printer()
        # Setup axis rails
        selector_stepper_section = config.getsection(SELECTOR_STEPPER_NAME)
        fil_driver_stepper_section = config.getsection(FIL_DRIVER_STEPPER_NAME)
        selector_rail = LookupMultiRail(selector_stepper_section)
        fil_driver_rail = LookupMultiRail(fil_driver_stepper_section)
        self.rails = [selector_rail, fil_driver_rail]
        for rail, axis in zip(self.rails, "xy"):
            rail.setup_itersolve("cartesian_stepper_alloc", axis.encode())
        for s in self.get_steppers():
            s.set_trapq(toolhead.get_trapq())
            toolhead.register_step_generator(s.generate_steps)
        self.printer.register_event_handler(
            "stepper_enable:motor_off", self._motor_off
        )

        # Setup boundary checks
        self.sel_max_velocity, self.sel_max_accel = (
            toolhead.get_sel_max_velocity()
        )
        self.fil_max_velocity, self.fil_max_accel = (
            toolhead.get_fil_max_velocity()
        )
        self.stepper_count = len(self.rails)
        self.limits = [(1.0, -1.0)] * self.stepper_count
        self.selector_min = selector_stepper_section.getfloat(
            "position_min", note_valid=False
        )
        self.selector_max = selector_stepper_section.getfloat(
            "position_max", note_valid=False
        )

        self.is_extruder_synced = is_extruder_synced

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
            if move.axes_d[i] and (
                end_pos[i] < self.limits[i][0] or end_pos[i] > self.limits[i][1]
            ):
                if self.limits[i][0] > self.limits[i][1]:
                    raise move.move_error("Must home axis first")
                raise move.move_error()

    def check_move(self, move):
        limits = self.limits
        xpos, ypos = move.end_pos[:2]
        if (
            xpos < limits[0][0]
            or xpos > limits[0][1]
            or ypos < limits[1][0]
            or ypos > limits[1][1]
        ):
            self._check_endstops(move)

        # Get filament driver speed and accel limits
        if self.is_extruder_synced():
            extruder = self.printer.lookup_object("toolhead").get_extruder()
            fil_max_velocity = min(
                self.fil_max_velocity, extruder.max_e_velocity
            )
            fil_max_accel = min(self.fil_max_accel, extruder.max_e_accel)
        else:
            fil_max_velocity = self.fil_max_velocity
            fil_max_accel = self.fil_max_accel

        # Move with both axes - update velocity and accel
        if move.axes_d[0] and move.axes_d[1]:
            vel = move.move_d * min(
                self.sel_max_velocity / abs(move.axes_d[0]),
                fil_max_velocity / abs(move.axes_d[1]),
            )
            accel = move.move_d * min(
                self.sel_max_accel / abs(move.axes_d[0]),
                fil_max_accel / abs(move.axes_d[1]),
            )
            move.limit_speed(vel, accel)

        # Move with selector - update velocity and accel
        elif move.axes_d[0]:
            move.limit_speed(self.sel_max_velocity, self.sel_max_accel)

        # Move with filament driver - update velocity and accel
        elif move.axes_d[1]:
            move.limit_speed(fil_max_velocity, fil_max_accel)

    def get_status(self, eventtime):
        axes = [a for a, (l, h) in zip("xy", self.limits) if l <= h]
        return {
            "homed_axes": "".join(axes),
            "selector_min": self.selector_min,
            "selector_max": self.selector_max,
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
            move_d = math.sqrt(sum([d * d for d in axes_d[:3]]))
            retract_r = min(1.0, hi.retract_dist / move_d)
            retractpos = [
                hp - ad * retract_r for hp, ad in zip(homepos, axes_d)
            ]
            self.toolhead.move(retractpos, hi.retract_speed)
            # Home again
            startpos = [
                rp - ad * retract_r for rp, ad in zip(retractpos, axes_d)
            ]
            self.toolhead.set_position(startpos)
            hmove = HomingMove(self.printer, endstops, self.toolhead)
            hmove.homing_move(homepos, hi.second_homing_speed)
            if hmove.check_no_movement() is not None:
                raise self.printer.command_error(
                    "Endstop %s still triggered after retract"
                    % (hmove.check_no_movement(),)
                )
        # Signal home operation complete
        self.toolhead.flush_step_generation()
        self.trigger_mcu_pos = {
            sp.stepper_name: sp.trig_pos for sp in hmove.stepper_positions
        }
        self.adjust_pos = {}
        self.printer.send_event("homing:home_rails_end", self, rails)
        if any(self.adjust_pos.values()):
            # Apply any homing offsets
            kin = self.toolhead.get_kinematics()
            homepos = self.toolhead.get_position()
            kin_spos = {
                s.get_name(): s.get_commanded_position() + self.adjust_pos.get(
                    s.get_name(), 0.0
                )
                for s in kin.get_steppers()
            }
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
            self.servo._set_pwm(
                print_time, self.servo._get_pwm_from_pulse_width(width)
            )
        else:
            self.servo._set_pwm(
                print_time, self.servo._get_pwm_from_angle(angle)
            )

    def get_max_angle(self):
        return self.servo.max_angle


class TradRackLanePositionManager:
    def __init__(self, lane_count, config):
        self.lane_count = lane_count
        self.lane_spacing = config.getfloat("lane_spacing", above=0.0)
        self.lane_spacing_mods = []
        self.lane_spacing_mod_internal = 0.0
        self.lane_offsets = []
        for i in range(lane_count):
            self.lane_spacing_mods.append(
                config.getfloat("lane_spacing_mod_" + str(i), default=0.0)
            )
            self.lane_spacing_mod_internal += self.lane_spacing_mods[i]
            self.lane_offsets.append(
                config.getfloat("lane_offset_" + str(i), default=0.0)
            )
        self.lane_spacing_mod_internal -= self.lane_spacing_mods[0]

    def get_lane_positions(self):
        lane_positions = []
        curr_pos = 0.0
        for i in range(self.lane_count):
            curr_pos += self.lane_spacing_mods[i]
            lane_positions.append(curr_pos + self.lane_offsets[i])
            curr_pos += self.lane_spacing
        return lane_positions

    def process_selector_calibration(
        self, endstop_to_lane0, endstop_to_last_lane, lane_spacing_ndigits=6
    ):
        # account for lane offsets
        endstop_to_lane0 -= self.lane_offsets[0]
        endstop_to_last_lane -= self.lane_offsets[self.lane_count - 1]

        # calculate endstop position and lane settings
        pos_endstop = self.lane_spacing_mods[0] - endstop_to_lane0
        lane_span = endstop_to_last_lane - endstop_to_lane0
        lane_spacing = (lane_span - self.lane_spacing_mod_internal) / (
            self.lane_count - 1
        )
        self.lane_spacing = round(lane_spacing, lane_spacing_ndigits)
        lane_positions = self.get_lane_positions()

        return pos_endstop, self.lane_spacing, lane_positions


EXTRUDER_TO_FIL_DRIVER = 0
FIL_DRIVER_TO_EXTRUDER = 1


class TradRackExtruderSyncManager:
    def __init__(self, printer, tr_toolhead, fil_driver_rail):
        self.printer = printer
        self.toolhead = None
        self.tr_toolhead = tr_toolhead
        self.fil_driver_rail = fil_driver_rail

        self.printer.register_event_handler(
            "klippy:connect", self.handle_connect
        )
        self.sync_state = None
        self._prev_sks = None
        self._prev_trapq = None
        self._prev_rotation_dists = None

    def handle_connect(self):
        self.toolhead = self.printer.lookup_object("toolhead")

    def _get_extruder_mcu_steppers(self):
        extruder = self.toolhead.get_extruder()
        if hasattr(extruder, "get_extruder_steppers"):
            steppers = []
            for extruder_stepper in extruder.get_extruder_steppers():
                steppers.append(extruder_stepper.stepper)
            return steppers
        else:
            return [extruder.extruder_stepper.stepper]

    def reset_fil_driver(self):
        self.tr_toolhead.get_last_move_time()
        pos = self.tr_toolhead.get_position()
        pos[1] = 0.0
        self.tr_toolhead.set_position(pos, homing_axes=(1,))
        if self.sync_state == EXTRUDER_TO_FIL_DRIVER:
            steppers = self._get_extruder_mcu_steppers()
            for stepper in steppers:
                stepper.set_position((0.0, 0.0, 0.0))

    def _sync(self, sync_type):
        self.unsync()
        self.toolhead.flush_step_generation()
        self.tr_toolhead.flush_step_generation()

        ffi_main, ffi_lib = chelper.get_ffi()
        if sync_type == EXTRUDER_TO_FIL_DRIVER:
            steppers = self._get_extruder_mcu_steppers()
            self._prev_trapq = steppers[0].get_trapq()
            external_trapq = self.tr_toolhead.get_trapq()
            stepper_alloc = ffi_lib.cartesian_stepper_alloc(b"y")
            prev_toolhead = self.toolhead
            external_toolhead = self.tr_toolhead
            self.reset_fil_driver()
            new_pos = 0.0
        elif sync_type == FIL_DRIVER_TO_EXTRUDER:
            steppers = self.fil_driver_rail.get_steppers()
            self._prev_trapq = self.tr_toolhead.get_trapq()
            extruder = self.toolhead.get_extruder()
            external_trapq = extruder.get_trapq()
            stepper_alloc = ffi_lib.extruder_stepper_alloc()
            prev_toolhead = self.tr_toolhead
            external_toolhead = self.toolhead
            new_pos = extruder.last_position
        else:
            raise Exception("Invalid sync_type: %d" % sync_type)

        self._prev_sks = []
        self._prev_rotation_dists = []
        for stepper in steppers:
            stepper_kinematics = ffi_main.gc(stepper_alloc, ffi_lib.free)
            self._prev_rotation_dists.append(stepper.get_rotation_distance()[0])
            self._prev_sks.append(
                stepper.set_stepper_kinematics(stepper_kinematics)
            )
            stepper.set_trapq(external_trapq)
            stepper.set_position((new_pos, 0.0, 0.0))
            prev_toolhead.step_generators.remove(stepper.generate_steps)
            external_toolhead.register_step_generator(stepper.generate_steps)
        self.sync_state = sync_type

    def sync_extruder_to_fil_driver(self):
        self._sync(EXTRUDER_TO_FIL_DRIVER)

    def sync_fil_driver_to_extruder(self):
        self._sync(FIL_DRIVER_TO_EXTRUDER)
        self.printer.send_event("trad_rack:synced_to_extruder")

    def unsync(self):
        if self.sync_state is None:
            return

        self.toolhead.flush_step_generation()
        self.tr_toolhead.flush_step_generation()

        if self.sync_state == EXTRUDER_TO_FIL_DRIVER:
            steppers = self._get_extruder_mcu_steppers()
            prev_toolhead = self.toolhead
            external_toolhead = self.tr_toolhead
        elif self.sync_state == FIL_DRIVER_TO_EXTRUDER:
            self.printer.send_event("trad_rack:unsyncing_from_extruder")
            steppers = self.fil_driver_rail.get_steppers()
            prev_toolhead = self.tr_toolhead
            external_toolhead = self.toolhead
        else:
            raise Exception("Invalid sync_state: %d" % self.sync_state)

        for i in range(len(steppers)):
            stepper = steppers[i]
            external_toolhead.step_generators.remove(stepper.generate_steps)
            prev_toolhead.register_step_generator(stepper.generate_steps)
            stepper.set_trapq(self._prev_trapq)
            stepper.set_stepper_kinematics(self._prev_sks[i])
            stepper.set_rotation_distance(self._prev_rotation_dists[i])
        self.sync_state = None

    def is_extruder_synced(self):
        return self.sync_state == EXTRUDER_TO_FIL_DRIVER

    def is_fil_driver_synced(self):
        return self.sync_state == FIL_DRIVER_TO_EXTRUDER

    def set_fil_driver_multiplier(self, multiplier):
        if not self.is_fil_driver_synced():
            raise Exception(
                "Cannot set stepper multiplier when filament driver is not"
                " synced to extruder"
            )
        steppers = self.fil_driver_rail.get_steppers()
        for i in range(len(steppers)):
            steppers[i].set_rotation_distance(
                self._prev_rotation_dists[i] / multiplier
            )


class RunIfNoActivity:
    def __init__(self, toolhead, reactor, callback, delay):
        self.toolhead = toolhead
        self.initial_print_time = self.toolhead.get_last_move_time()
        self.callback = callback
        reactor.register_callback(
            self._run_if_no_activity, reactor.monotonic() + delay
        )

    def _run_if_no_activity(self, eventtime):
        print_time, _, lookahead_empty = self.toolhead.check_busy(eventtime)
        if lookahead_empty and print_time == self.initial_print_time:
            self.callback()


class MovingAverageFilter:
    def __init__(self, max_entries):
        self.max_entries = max_entries
        self.queue = deque()
        self.total = 0.0

    def update(self, value):
        if len(self.queue) >= self.max_entries:
            self.total -= self.queue.popleft()
        self.total += value
        self.queue.append(value)
        return self.total / len(self.queue)

    def reset(self):
        self.queue.clear()
        self.total = 0.0

    def get_entry_count(self):
        return len(self.queue)


class TradRackLoadError(CommandError):
    pass


class SelectorNotHomedError(CommandError):
    pass


class TradRackRunoutSensor:
    def __init__(self, config, runout_callback, pin):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.runout_callback = runout_callback

        # disable config checks for duplicate pins
        pin_desc = pin
        if pin_desc.startswith("^") or pin_desc.startswith("~"):
            pin_desc = pin_desc[1:].strip()
        if pin_desc.startswith("!"):
            pin_desc = pin_desc[1:].strip()
        ppins = self.printer.lookup_object("pins")
        ppins.allow_multi_use_pin(pin_desc)

        # register button
        buttons = config.get_printer().load_object(config, "buttons")
        buttons.register_buttons([pin], self.sensor_callback)

        self.active = False

    def sensor_callback(self, eventtime, state):
        if self.active and not state:
            idle_timeout = self.printer.lookup_object("idle_timeout")
            if idle_timeout.get_status(eventtime)["state"] == "Printing":
                self.active = False
                self.reactor.register_callback(self.runout_callback)

    def set_active(self, active):
        self.active = active


def load_config(config):
    return TradRack(config)
