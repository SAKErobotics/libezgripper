# libezgripper

A Python library that serves as a driver to the [EZGripper module](https://sakerobotics.com/) designed by SAKE Robotics.

## Tutorial

* On Ubuntu, install all the required dependencies. The library supports both Python 2 and Python 3:

  For Python 2

      sudo apt-get install python-serial python-qt4

  For Python 3

      sudo apt-get install python3-serial python3-pyqt4

* Install the library:
  
  For Python 2

      sudo pip install git+https://github.com/SAKErobotics/libezgripper.git@master
  
  For Python 3
      
      sudo pip3 install git+https://github.com/SAKErobotics/libezgripper.git@master

## Quickstart

* Install the ezgripperGUI.py to your desired working directory:

      wget https://raw.githubusercontent.com/SAKErobotics/libezgripper/master/ezgripperGUI.py

* Launch the EZGripper GUI in python2 or python3, this should open a push-button GUI using the two base commands - calibrate and goto_position.:

      python ezgripperGUI.py
  
  or

      python3 ezgripperGUI.py

## Usage

* In your Python program:

      from libezgripper import create_connection, Gripper

* Then create a connection to the gripper serial line. USB2Dynamixel usually comes up as `/dev/ttyUSB*`, so:

      connection = create_connection(dev_name='/dev/ttyUSB0', baudrate=57600)

* Now create one or more Gripper objects, according to your configuration:

      # A single gripper, with servo ID 1
      gripper = Gripper(connection, 'gripper1', [1])

      # Or a paired gripper, servo IDs 1 and 2
      gripper = Gripper(connection, 'gripper1', [1,2])

      # Or two independently controlled grippers on the same serial line
      grip1 = Gripper(connection, 'gripper1', [1])
      grip2 = Gripper(connection, 'gripper2', [2])

* Next, each gripper must be calibrated. The gripper will close and configure itself::

      gripper.calibrate()

* After calibration is done you can start moving the gripper with the method
`goto_position(position,effort)`. The parameters are:

    * `position`: The position in degrees, between 0 and 180.
    * `effort`: The effort in percent, between 0 and 100.


* Here are a few examples:

      # Open the gripper
      gripper.goto_position(100, 100)

      # Close the gripper
      gripper.goto_position(0, 100)

      # Open the gripper halfway
      gripper.goto_position(50, 100)

      # Close the gripper with half the force
      gripper.goto_position(0, 50)

## Serial Port URLs

* Referencing the USB port by the device name `/dev/ttyUSB0` is sometimes problematic.
If you have several USB devices with similar names it is not always clear which is
the one you want. And even when you find it they can switch names later. To make
finding the port easier you can use `hwgrep://` URLs::

      # Find the port by vendor:device id
      connection = create_connection(dev_name='hwgrep://0403:6001', baudrate=57600)

      # Find the port by serial number
      connection = create_connection(dev_name='hwgrep://A4012B2G', baudrate=57600)

* To see the properties of your serial ports the library can find try this::

      python -c "import serial.tools.list_ports;print serial.tools.list_ports.comports()"

* For network connected serial devices you can use the `socket://` URL::

      connection = create_connection('socket://192.168.1.200:4000')
