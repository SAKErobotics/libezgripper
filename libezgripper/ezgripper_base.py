#!/usr/bin/python3

#####################################################################
# Software License Agreement (BSD License)
#
# Copyright (c) 2016, SAKE Robotics
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
##

from .lib_robotis import create_connection, Robotis_Servo
import time


def set_torque_mode(servo, val):
    if val:
        servo.write_address(70, [1])
    else:
        servo.write_address(70, [0])

def wait_for_stop(servo):
    wait_start = time.time()
    last_position = 1000000 # read_encoder() cannot return more than 65536
    while True:
        current_position = servo.read_encoder()
        if current_position == last_position:
            break
        last_position = current_position
        time.sleep(0.1)

        if time.time() - wait_start > 5:
            break


class Gripper:

    GRIP_MAX = 2500 # maximum open position for grippers
    TORQUE_MAX = 800 # maximum torque - MX-64=500, MX-106=350
    TORQUE_HOLD = 13 # This is percentage of TORQUE_MAX. In absolute units: holding torque - MX-64=100, MX-106=80

    OPEN_DUAL_GEN2_POS = 1.94
    CLOSE_DUAL_GEN2_POS = 0.0
    MAX_DUAL_GEN2_EFFORT = 1.0


    def __init__(self, connection, name, servo_ids):
        self.name = name
        self.servos = [Robotis_Servo( connection, servo_id ) for servo_id in servo_ids]
        for servo in self.servos:
            servo.ensure_byte_set(22, 1) # Make sure 'Resolution divider' is set to 1
        self.zero_positions = [0] * len(self.servos)

    def scale(self, n, to_max):
        # Scale from 0..100 to 0..to_max
        result = int(n * to_max / 100)
        if result > to_max: result = to_max
        if result < 0: result = 0
        return result

    def down_scale (self, n, to_max):
        # Scale from 0..to_max to 0..100
        result = int(round(n * 100.0 / to_max))
        if result > 100: result = 100
        if result < 0: result = 0
        return result

    def calibrate(self):
        print("calibrating: " + self.name)

        for servo in self.servos:
            servo.write_address(6, [255,15,255,15] )   # 1) "Multi-Turn" - ON
            servo.write_word(34, 500)                  # 2) "Torque Limit" to 500 (or so)
            servo.write_address(24, [0])               # 3) "Torque Enable" to OFF
            servo.write_address(70, [1])               # 4) Set "Goal Torque Mode" to ON
            servo.write_word(71, 1024 + 100)           # 5) Set "Goal Torque" Direction to CW and Value 100

        time.sleep(4.0)                               # 6) give it time to stop

        for i in range(len(self.servos)):
            servo = self.servos[i]
            servo.write_word(71, 1024 + 10)            # 7) Set "Goal Torque" Direction to CW and Value 10 - reduce load on servo
            servo.write_word(20, 0)                    # 8) set "Multi turn offset" to 0
            self.zero_positions[i] = servo.read_word_signed(36) # 9) read current position of servo

        print("calibration done")

    def set_max_effort(self, max_effort):
        # sets torque for moving to position (moving_torque) and for torque only mode (torque_mode_max_effort)
        # range 0-100% (0-100) - this range is in 0-100 whole numbers so that it can be used where Newton force is expected
        # max dynamixel torque is 0-1023(unitless)

        torque_mode_max_effort = moving_torque = self.scale(max_effort, self.TORQUE_MAX)

        print("set_max_effort(%d): moving torque: %d, goal torque: %d"%(
                    max_effort, moving_torque, torque_mode_max_effort))
        for servo in self.servos:
            servo.write_word(34, moving_torque) # torque for moving to position,and due to Dynamixel architecture, this also limits max value for register 71 below
            servo.write_word(71, 1024+torque_mode_max_effort) # torque mode of closing gripper

    def _goto_position(self, position):
        for servo in self.servos:
            set_torque_mode(servo, False)
        for i in range(len(self.servos)):
            self.servos[i].write_word(30, self.zero_positions[i] + position)
        wait_for_stop(self.servos[0])

    def _close_with_torque(self):
        for servo in self.servos:
            set_torque_mode(servo, True)
        wait_for_stop(self.servos[0])

    def get_position(self, servo_num=0, use_percentages = True):
        servo_position = self.servos[servo_num].read_word_signed(36) - self.zero_positions[servo_num]

        current_position = self.down_scale(servo_position, self.GRIP_MAX)

        if not use_percentages:
            current_position = self.OPEN_DUAL_GEN2_POS * ((100.0 - current_position) / 100.0)

        return current_position

    def get_positions(self):
        positions = []
        for i in range(len(self.servos)):
            positions.append(self.get_position(i))
        return positions

    def goto_position(self, position, closing_torque, use_percentages = True):
        # Using the 0-100% range allows the user to define the definition of where the gap is measured.
        # position: 0..100, 0 - close, 100 - open
        # closing_torque: 0..100

        if not use_percentages:
            position = 100.0 - (100.0 / self.OPEN_DUAL_GEN2_POS) * position
            closing_torque *= 100.0 / self.MAX_DUAL_GEN2_EFFORT

        servo_position = self.scale(position, self.GRIP_MAX)
        print("goto_position(%d, %d): servo position %d"%(position, closing_torque, servo_position))
        self.set_max_effort(closing_torque)  # essentially sets velocity of movement, but also sets max_effort for initial half second of grasp.

        if position == 0:
            self._close_with_torque()
        else:
            self._goto_position(servo_position)

        # Sets torque to keep gripper in position, but does not apply torque if there is no load.
        # This does not provide continuous grasping torque.
        holding_torque = min(self.TORQUE_HOLD, closing_torque)
        self.set_max_effort(holding_torque)
        print("goto_position done")

    def release(self):
        for servo in self.servos:
            set_torque_mode(servo, False)

    def open(self):
        self.goto_position(100, 100)

    def get_temperatures(self):
        temperatures = []
        for servo in self.servos:
            temperatures.append(servo.read_temperature())
        return temperatures

if __name__ == '__main__':
    # Sample code
    connection = create_connection(dev_name='/dev/ttyUSB0', baudrate=57600)
    #connection = create_connection(dev_name='hwgrep://0403:6001', baudrate=57600)
    #connection = create_connection(dev_name='socket://127.0.0.1:4000', baudrate=57600)
    gripper = Gripper(connection, 'gripper1', [1])
    #gripper = Gripper(connection, 'gripper1', [1,2])

    print("temperatures:", gripper.get_temperatures())

    gripper.calibrate()
    gripper.goto_position(100, 100) # open
    time.sleep(2.0)
    print("positions:", gripper.get_positions())
    gripper.goto_position(0, 50) # close
    time.sleep(2.0)
    print("positions:", gripper.get_positions())
    gripper.goto_position(100, 50) # open
    time.sleep(2.0)
    gripper.goto_position(70, 100) # position 70
    print("positions:", gripper.get_positions())
    print("position:", gripper.get_position())
    print("DONE")
