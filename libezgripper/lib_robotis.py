#!/usr/bin/python
#
# Copyright (c) 2009, Georgia Tech Research Corporation
# Copyright (c) 2015, SAKE Robotics
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Georgia Tech Research Corporation nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY GEORGIA TECH RESEARCH CORPORATION ''AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL GEORGIA TECH BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

## Controlling Robotis Dynamixel RX-28 & RX-64 servos from python
## using the USB2Dynamixel adaptor.

## Authors: Travis Deyle, Advait Jain & Marc Killpack (Healthcare Robotics Lab, Georgia Tech.)
## Updated by: Girts Linde

from __future__ import print_function
import serial
import serial.tools.list_ports
import time
import threading
import sys, optparse
import math
import socket 

def warning(msg):
    print(msg, file=sys.stderr)
    
class ErrorResponse(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "Dynamixel error: "+repr(self.value)

class CommunicationError(RuntimeError):
    def __init__(self, text):
        RuntimeError.__init__(self, text)

def create_connection(dev_name = '/dev/ttyUSB0', baudrate = 57600):
    return USB2Dynamixel_Device(dev_name, baudrate)
    
class USB2Dynamixel_Device():
    ''' Class that manages serial port contention between servos on same bus
    '''
    def __init__( self, dev_name = '/dev/ttyUSB0', baudrate = 57600 ):
        try:
            self.dev_name = int( dev_name ) # stores the serial port as 0-based integer for Windows
        except:
            self.dev_name = dev_name # stores it as a /dev-mapped string for Linux / Mac

        self.lock = threading.Lock()
        self.servo_dev = None

        with self.lock:
            self._open_serial( baudrate )

    def send_serial(self, msg):
        # It is up to the caller to acquire lock
        self.servo_dev.write( msg )

    def flush_input(self):
        self.servo_dev.flushInput()

    def read_serial(self, nBytes=1):
        # It is up to the caller to acquire lock
        rep = self.servo_dev.read( nBytes )
        if len(rep) < nBytes:
            raise CommunicationError('read_serial: not enough bytes received (expected %d, received %d)'%(nBytes, len(rep)))
        return rep
        

    def _open_serial(self, baudrate):
        try:
            self.servo_dev = serial.serial_for_url(url=self.dev_name, baudrate=baudrate, timeout=0.2, writeTimeout=0.2)
            # Closing the device first seems to prevent "Access Denied" errors on WinXP
            # (Conversations with Brian Wu @ MIT on 6/23/2010)
            self.servo_dev.close()  
            self.servo_dev.parity = serial.PARITY_NONE
            self.servo_dev.stopbits = serial.STOPBITS_ONE
            self.servo_dev.open()

            self.servo_dev.flushOutput()
            self.servo_dev.flushInput()

        except (serial.serialutil.SerialException) as e:
            raise RuntimeError("lib_robotis: Serial port not found!\n%s"%e)
        if(self.servo_dev == None):
            raise RuntimeError('lib_robotis: Serial port not found!\n')





class Robotis_Servo():
    ''' Class to use a robotis RX-28 or RX-64 servo.
    '''
    def __init__(self, USB2Dynamixel, servo_id, retry_count=3 ):
        ''' USB2Dynamixel - USB2Dynamixel_Device object to handle serial port.
                            Handles threadsafe operation for multiple servos
            servo_id - servo ids connected to USB2Dynamixel 1,2,3,4 ... (1 to 253)
                       [0 is broadcast if memory serves]
        '''

        self.retry_count = retry_count
        # Error Checking
        if USB2Dynamixel == None:
            raise RuntimeError('lib_robotis: Robotis Servo requires USB2Dynamixel!\n')
        else:
            self.dyn = USB2Dynamixel

        # ID exists on bus?
        self.servo_id = servo_id
        try:
            self.read_address(3)
        except Exception as e:
            if self.retry_count == 0:
                raise
            print("Exception:", e)
            print("Get ID failed once, retrying")
            self.dyn.flush_input()
            try:
                self.read_address(3)
            except:
                raise RuntimeError('lib_robotis: Error encountered.  Could not find ID (%d) on bus (%s), or USB2Dynamixel 3-way switch in wrong position.\n' %
                                   ( servo_id, self.dyn.dev_name ))

        # Set Return Delay time - Used to determine when next status can be requested
        data = self.read_address( 0x05, 1)
        self.return_delay = data[0] * 2e-6

        
    def flushAll(self):
        self.dyn.flush_input()

    def init_cont_turn(self):
        '''sets CCW angle limit to zero and allows continuous turning (good for wheels).
        After calling this method, simply use 'set_angvel' to command rotation.  This 
        rotation is proportional to torque according to Robotis documentation.
        '''
        self.write_address(0x08, [0,0])

    def kill_cont_turn(self):
        '''resets CCW angle limits to allow commands through 'move_angle' again
        '''
        self.write_address(0x08, [255, 3])

    def is_moving(self):
        ''' returns True if servo is moving.
        '''
        data = self.read_address( 0x2e, 1 )
        return data[0] != 0

    def read_voltage(self):
        ''' returns voltage (Volts)
        '''
        data = self.read_address( 0x2a, 1 )
        return data[0] / 10.

    def read_temperature(self):
        ''' returns the temperature (Celcius)
        '''
        data = self.read_address( 0x2b, 1 )
        return data[0]

    def read_load(self):
        ''' number proportional to the torque applied by the servo.
            sign etc. might vary with how the servo is mounted.
        '''
        data = self.read_address( 0x28, 2 )
        load = data[0] + (data[1] >> 6) * 256
        if data[1] >> 2 & 1 == 0:
            return -1.0 * load
        else:
            return 1.0 * load

    def read_present_speed(self):
        speed = self.read_word(38)
        if speed == 1024: # 1024 is zero speed clockwise
            speed = 0
        return speed
        
    def read_encoder(self):
        ''' returns position in encoder ticks
        '''
        data = self.read_address( 0x24, 2 )
        enc_val = data[0] + data[1] * 256
        return enc_val

    def read_word(self, addr):
        data = self.read_address( addr, 2 )
        value = data[0] + data[1] * 256
        return value
    
    def read_word_signed(self, addr):
        value = self.read_word(addr)
        if value >= 32768: value -= 65536
        return value

    def enable_torque(self):
        return self.write_address(0x18, [1])

    def disable_torque(self):
        return self.write_address(0x18, [0])

    def set_angvel(self, angvel):
        ''' angvel - in rad/sec
        '''     
        rpm = angvel / (2 * math.pi) * 60.0
        angvel_enc = int(round( rpm / 0.111 ))
        if angvel_enc<0:
            hi,lo = abs(angvel_enc) // 256 + 4, abs(angvel_enc) % 256
        else:
            hi,lo = angvel_enc // 256, angvel_enc % 256
        
        return self.write_address( 0x20, [lo,hi] )

    def write_id(self, new_id):
        ''' changes the servo id
        '''
        return self.write_address( 0x03, [new_id] )

    def write_baudrate(self, rate):
        return self.write_address( 0x04, [rate] )
        
    def write_word(self, addr, word):
        while word > 65535:
            word = word - 65536
        while word < 0:
            word = word + 65536
        hi,lo = word // 256, word % 256
        return self.write_address( addr, [lo,hi] )        
        
    def write_wordX(self, addr, word):
        while word > 65535:
            word = word - 65536
        while word < 0:
            word = word + 65536
        hi,lo = word // 256, word % 256
        return self.write_addressX( addr, [lo,hi] )        
        
    def __calc_checksum_str(self, msg):
        cs = 0
        if sys.version_info.major == 2:
            for c in msg:
                cs += ord(c)
        else:
            for c in msg:
                cs += c

        return ( ~cs ) & 0xFF

    def __calc_checksum(self, msg):
        chksum = 0
        for m in msg:
            chksum += m
        chksum = ( ~chksum ) % 256
        return chksum

    def read_address(self, address, nBytes=1):
        ''' reads nBytes from address on the servo.
            returns [n1,n2 ...] (list of parameters)
        '''
        msg = [ 0x02, address, nBytes ]
        return self.send_instruction( msg )

    def write_address(self, address, data):
        ''' writes data at the address.
            data = [n1,n2 ...] list of numbers.
            return [n1,n2 ...] (list of return parameters)
        '''
        msg = [ 0x03, address ] + data
        return self.send_instruction( msg )

    def write_addressX(self, address, data):
        ''' writes data at the address.
            data = [n1,n2 ...] list of numbers.
            return [n1,n2 ...] (list of return parameters)
        '''
        msg = [ 0x03, address ] + data
        return self.send_instruction( msg, exceptionOnErrorResponse = False )

    def ensure_byte_set(self, address, byte):
        value = self.read_address(address)[0]
        if value != byte:
            print('Servo [%d]: change setting %d from %d to %d'%(self.servo_id, address, value, byte))
            self.write_address(address, [byte])
        
    def ensure_word_set(self, address, word):
        value = self.read_word(address)
        if value != word:
            print('Servo [%d]: change setting %d from %d to %d (word)'%(self.servo_id, address, value, word))
            self.write_word(address, word)
    
    def send_instruction(self, instruction, exceptionOnErrorResponse = True):
        ''' send_instruction with Retries
        '''
        msg = [ self.servo_id, len(instruction) + 1 ] + instruction # instruction includes the command (1 byte + parameters. length = parameters+2)
        chksum = self.__calc_checksum( msg )
        msg = [ 0xff, 0xff ] + msg + [chksum]
        
        with self.dyn.lock:
            failures = 0
            while True:
                try:
                    self.dyn.flush_input()
                    self.send_serial( msg )
                    data, err = self.receive_reply()
                    if err & 16 != 0:
                        raise CommunicationError("Dynamixel error 16 - sent packet checksum invalid")
                    break
                except (CommunicationError, serial.SerialException, socket.timeout) as e:
                    failures += 1
                    if failures > self.retry_count:
                        raise
                    warning("send_instruction retry %d, error: %s"%(failures, e))
        
        if exceptionOnErrorResponse:
            if err != 0:
                self.process_err( err )
            return data
        else:
            return data, err

    def read_wordX(self, addr):
        data, err = self.read_addressX( addr, 2 )
        value = data[0] + data[1] * 256
        return value, err

    def read_addressX(self, address, nBytes=1):
        ''' reads nBytes from address on the servo.
            returns [n1,n2 ...] (list of parameters)
        '''
        msg = [ 0x02, address, nBytes ]
        return self.send_instruction( msg, exceptionOnErrorResponse = False )

    def process_err( self, err ):
        raise ErrorResponse(err)

    def receive_reply(self):
        start_bytes_received = 0
        while (start_bytes_received < 2):
            one = self.dyn.read_serial( 1 )
            if ord(one) == 0xff:
                start_bytes_received += 1
            else:
                start_bytes_received = 0

        servo_id = self.dyn.read_serial( 1 )
        if ord(servo_id) != self.servo_id:
            raise CommunicationError('lib_robotis: Incorrect servo ID received: %d, expected %d' % (ord(servo_id), self.servo_id))
        data_len = self.dyn.read_serial( 1 )
        err = self.dyn.read_serial( 1 )
        data = self.dyn.read_serial( ord(data_len) - 2 )
        chksum_in = ord(self.dyn.read_serial( 1 ))
        chksum_calc = self.__calc_checksum_str(servo_id + data_len + err + data)
        if chksum_calc != chksum_in:
            raise CommunicationError('Checksum mismatch: calculated %02X, received %02X'%(chksum_calc, chksum_in))

        if sys.version_info.major == 2:
            return [ord(v) for v in data], ord(err)
        else:
            return list(data), ord(err)

    def send_serial(self, msg):
        """ sends the command to the servo
        """
        if sys.version_info.major == 2:
            out = ''
            for m in msg:
                out += chr(m)
        else:
            out = bytes(msg)

        self.dyn.send_serial( out )

    def check_overload_and_recover(self):
        _, e = self.read_wordX(34)
        if e & 32 != 0:
            print("Servo %d: status code %d, will try to recover"%(self.servo_id, e))
            self.write_wordX(71, 0)             # reset goal torque
            self.write_addressX(70, [0])        # torque control off
            self.write_wordX(34, 500)           # restore torque limit
            _, e = self.read_wordX(34) # check stats
            if e & 32 == 0:
                print("Servo %d: recovery done, status code %d"%(self.servo_id, e))
            else:
                print("Servo %d: recovery failed, status code %d"%(self.servo_id, e))

def find_servos(dyn, max_id=252, print_progress=False):
    ''' Finds all servo IDs on the USB2Dynamixel '''
    servos = []
    prev_timeout = dyn.servo_dev.timeout
    dyn.servo_dev.timeout = 0.03 # To make the scan faster
    for i in range(max_id+1): # 0..max_id
        try:
            _ = Robotis_Servo( dyn, i, retry_count=0 )
            if print_progress:
                print(' FOUND A SERVO @ ID %d' % i)
            servos.append( i )
        except:
            pass
    dyn.servo_dev.timeout = prev_timeout
    return servos

def find_servos_on_all_ports(max_id=252, baudrate=57600, print_progress=False):
    ports = serial.tools.list_ports.comports()
    result = []
    for port in ports:
        device_name = port[0]
        if 'ttyUSB' in device_name or 'ttyACM' in device_name or 'COM' in device_name:
            if print_progress:
                print("device:", device_name)
            try:
                connection = create_connection(device_name, 57600)
                servo_ids = find_servos(connection, max_id=max_id, print_progress=print_progress)
                if servo_ids:
                    result.append( (device_name, servo_ids) )
            except:
                pass
    return result

def recover_servo(dyn):
    ''' Recovers a bricked servo by booting into diagnostic bootloader and resetting '''
    raw_input('Make sure only one servo connected to USB2Dynamixel Device [ENTER]')
    raw_input('Disconnect power from the servo, but leave USB2Dynamixel connected to USB. [ENTER]')

    dyn.servo_dev.baudrate = 57600
    
    print('Get Ready.  Be ready to reconnect servo power when I say \'GO!\'')
    print('After a second, the red LED should become permanently lit.')
    print('After that happens, Ctrl + C to kill this program.')
    print()
    print('Then, you will need to use a serial terminal to issue additional commands.', end=' ')
    print('Here is an example using screen as serial terminal:')
    print()
    print('Command Line:  screen /dev/robot/servo_left 57600')
    print('Type: \'h\'')
    print('Response: Command : L(oad),G(o),S(ystem),A(pplication),R(eset),D(ump),C(lear)')
    print('Type: \'C\'')
    print('Response:  * Clear EEPROM ')
    print('Type: \'A\'')
    print('Response: * Application Mode')
    print('Type: \'G\'')
    print('Response:  * Go')
    print()
    print('Should now be able to reconnect to the servo using ID 1')
    print()
    print()
    raw_input('Ready to reconnect power? [ENTER]')
    print('GO!')

    while True:
        dyn.servo_dev.write('#')
        time.sleep(0.0001)


if __name__ == '__main__':
    p = optparse.OptionParser()
    p.add_option('-d', action='store', type='string', dest='dev_name',
                 help='Required: Device string for USB2Dynamixel. [i.e. /dev/ttyUSB0 for Linux, \'0\' (for COM1) on Windows]')
    p.add_option('--scan', action='store_true', dest='scan', default=False,
                 help='Scan the device for servo IDs attached.')
    p.add_option('--scan-ports', action='store_true', dest='scan_ports', default=False,
                 help='Scan all serial ports for servo IDs attached.')
    p.add_option('--recover', action='store_true', dest='recover', default=False,
                 help='Recover from a bricked servo (restores to factory defaults).')
    p.add_option('--id', action='store', type='int', dest='id',
                 help='id of servo to connect to, [default = 1]', default=1)
    p.add_option('--baud', action='store', type='int', dest='baud',
                 help='baudrate for USB2Dynamixel connection [default = 57600]', default=57600)

    opt, args = p.parse_args()

    if opt.scan_ports:
        print('Scanning for Servos...')
        find_servos_on_all_ports(max_id=252, baudrate=57600, print_progress=True)
        sys.exit(0)

    if opt.dev_name == None:
        p.print_help()
        sys.exit(1)

    dyn = USB2Dynamixel_Device(opt.dev_name, opt.baud)

    if opt.scan:
        print('Scanning for Servos...')
        find_servos( dyn, print_progress=True )

    if opt.recover:
        recover_servo( dyn )
