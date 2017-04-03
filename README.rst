A Python driver for EZGripper
=============================

1. Installation
---------------
Install dependencies. On Ubuntu::

   sudo apt-get install git python-pip python-serial

Install the package::

   sudo pip install git+https://github.com/SAKErobotics/libezgripper.git#egg=libezgripper
   
Install PyQt4 for the GUI::

   sudo apt-get install python-qt4
   
Install the ezgripperGUI.py to your desired working directory::

   $ wget https://raw.githubusercontent.com/SAKErobotics/libezgripper/master/ezgripperGUI.py
   $ sudo chmod +x ezgripperGUI.py
   
to run ezgripperGUI.py from directory it is installed.
   $ ./ezgripperGUI.py
 
2. Usage
--------

In your Python program::

   from libezgripper import create_connection, Gripper

Then create a connection to the gripper serial line. USB2Dynamixel usually comes up as /dev/ttyUSB*, so::

   connection = create_connection(dev_name='/dev/ttyUSB0', baudrate=57600)

Now create one or more Gripper objects, according to your configuration::

   # A single gripper, with servo ID 1
   gripper = Gripper(connection, 'gripper1', [1])
   
   # Or a paired gripper, servo IDs 1 and 2
   gripper = Gripper(connection, 'gripper1', [1,2])
   
   # Or two independenty controlled grippers on the same serial line
   grip1 = Gripper(connection, 'gripper1', [1])
   grip2 = Gripper(connection, 'gripper2', [2])

Next, each gripper must be calibrated. The gripper will close and configure itself::

   gripper.calibrate()
   
After calibration is done you can start moving the gripper with the method 
``goto_position(position,effort)``. The parameters are:
   * position - 0..100, where 0 is fully closed, 100 is fully open,
   * effort - 0..100, where 100 is the maximum speed/force.

Here are a few examples::

   # Open the gripper
   gripper.goto_position(100, 100)
   
   # Close the gripper
   gripper.goto_position(0, 100)
   
   # Open the gripper half way
   gripper.goto_position(50, 100)
   
   # Close the gripper with half the force
   gripper.goto_position(0, 50)
   
2.1 Serial Port URLs
--------------------
Referencing the USB port by the device name /dev/ttyUSB0 is sometimes problematic.
If you have several USB devices with similar names it is not always clear which is
the one you want. And even when you find it they can switch names later. To make 
finding the port easier you can use 'hwgrep://' URLs::

   # Find the port by vendor:device id
   connection = create_connection(dev_name='hwgrep://0403:6001', baudrate=57600)
   
   # Find the port by serial number
   connection = create_connection(dev_name='hwgrep://A4012B2G', baudrate=57600)

To see the properties of your serial ports the library can find try this::

   python -c "import serial.tools.list_ports;print serial.tools.list_ports.comports()"

For network connected serial devices you can use the 'socket://' URL::

   connection = create_connection('socket://192.168.1.200:4000')


3. QuickStart Demo - ezgripperGUI.py
------------------------------------   

In the directory of ezgripperGUI.py, run the following command::

   ./ezgripperGUI.py
   
This should open a push-button GUI using the two base commands - calibrate and goto_position.
   
Make sure ezgripperGUI.py is executable. 

This program can operate an array of EZGripper robotic grippers.  Just modify the line near the top of the file::

    gripper = Gripper(connection, 'gripper1', [1,2,3])

    gripper = Gripper(connection, 'gripper1', [1])

