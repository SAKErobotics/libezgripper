#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from libezgripper import create_connection, Gripper
from PyQt5 import QtWidgets

connection = create_connection(dev_name='/dev/ttyUSB0', baudrate= 57600)
gripper = Gripper(connection, 'gripper1', [1])
#gripper = Gripper(connection, 'gripper1', [1,2,3])
#gripper = Gripper(connection, 'gripper1', [2,3])

class GripperGUI(QtWidgets.QMainWindow):

   def __init__(self):
      super(GripperGUI, self).__init__()
      self.initUI()

   def initUI(self):

      calibrateButton=QtWidgets.QPushButton("Calibrate",self)
      calibrateButton.resize(100,30)
#      calibrateButton.setStyleSheet("background-color:rgb(153, 153, 153)")
      calibrateButton.clicked.connect(gripper.calibrate)
      calibrateButton.move(50,10)
      calibrateButton.show()

      releaseButton=QtWidgets.QPushButton("Release",self)
      releaseButton.resize(600,40)
      releaseButton.clicked.connect(gripper.release)
      releaseButton.move(50,50)

      hard_closeButton=QtWidgets.QPushButton("Hard Close 100%",self)
      hard_closeButton.resize(200,100)
      hard_closeButton.clicked.connect(self.submit_goto_hard_close)
      hard_closeButton.move(50,100)

      gotoButton=QtWidgets.QPushButton("Medium Close 50%", self)
      gotoButton.resize(200,100)
      gotoButton.clicked.connect(self.submit_goto_medium_close)
      gotoButton.move(250,100)

      openButton=QtWidgets.QPushButton("Soft Close 10%", self)
      openButton.clicked.connect(self.submit_goto_soft_close)
      openButton.resize(200,100)
      openButton.move(450,100)

      gotoButton=QtWidgets.QPushButton("0% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto1)
      gotoButton.move(50,210)

      gotoButton=QtWidgets.QPushButton("10% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto2)
      gotoButton.move(150,210)

      gotoButton=QtWidgets.QPushButton("20% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto3)
      gotoButton.move(250,210)

      gotoButton=QtWidgets.QPushButton("30% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto4)
      gotoButton.move(350,210)

      gotoButton=QtWidgets.QPushButton("40% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto5)
      gotoButton.move(450,210)

      gotoButton=QtWidgets.QPushButton("50% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto6)
      gotoButton.move(550,210)

      gotoButton=QtWidgets.QPushButton("60% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto7)
      gotoButton.move(150,260)

      gotoButton=QtWidgets.QPushButton("70% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto8)
      gotoButton.move(250,260)

      gotoButton=QtWidgets.QPushButton("80% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto9)
      gotoButton.move(350,260)

      gotoButton=QtWidgets.QPushButton("90% Open", self)
      gotoButton.resize(100,50)
      gotoButton.clicked.connect(self.submit_goto10)
      gotoButton.move(450,260)

      gotoButton=QtWidgets.QPushButton("100% Open", self)
      gotoButton.resize(100,50)
#      gotoButton.setStyleSheet("background-color:yellow")
#      gotoButton.setStyleSheet("background-color: rgb(51, 102, 153)")
#      gotoButton.setStyleSheet("border: 1px solid rgb(255, 255, 255)")
      gotoButton.clicked.connect(self.submit_goto11)
      gotoButton.move(550,260)

      self.statusBar()

      self.setGeometry(300, 200, 700, 350)
      self.setWindowTitle("EZGripper GUI")
      self.show()

   def submit_goto_hard_close(self):

      gripper.goto_position(0, 100)

   def submit_goto_medium_close(self):

      gripper.goto_position(0, 50)

   def submit_goto_soft_close(self):

      gripper.goto_position(0, 10)

   def submit_goto_open(self):

      gripper.goto_position(100, 100)

   def submit_goto1(self):

      gripper.goto_position(1, 100)

   def submit_goto2(self):

      gripper.goto_position(10, 100)

   def submit_goto3(self):

      gripper.goto_position(20, 100)

   def submit_goto4(self):

      gripper.goto_position(30, 100)

   def submit_goto5(self):

      gripper.goto_position(40, 100)

   def submit_goto6(self):

      gripper.goto_position(50, 100)

   def submit_goto7(self):

      gripper.goto_position(60, 100)

   def submit_goto8(self):

      gripper.goto_position(70, 100)

   def submit_goto9(self):

      gripper.goto_position(80, 100)

   def submit_goto10(self):

      gripper.goto_position(90, 100)

   def submit_goto11(self):

      gripper.goto_position(100, 100)

   def submit_goto12(self):

      gripper.goto_position(.20, 100)

   def submit_goto13(self):

      gripper.goto_position(.20, 100)

   def submit_goto14(self):

      gripper.goto_position(.20, 100)

def main():

   ezgripper_app=QtWidgets.QApplication(sys.argv)
   ex=GripperGUI()
   sys.exit(ezgripper_app.exec_())

if __name__== '__main__':
   main()
