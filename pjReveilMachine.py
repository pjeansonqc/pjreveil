#!/usr/bin/env python

import ptvsd
print "tcp://pj@pifamille/"
ptvsd.enable_attach(secret='pj', address = ('0.0.0.0', 5678))  #tcp://pj@pifamille/
#ptvsd.wait_for_attach()
import sys
import os
from time import sleep
import pifacecad
import time
import signal
from MpcRadio.MpcRadio import MpcRadio 

#*****************************************************************************************
# ReveilStateBase
# 
# 
#
#*****************************************************************************************
class ReveilStateBase(object):
   cad=0
   alarm="00:00"
   currentNav=0
   currentKey=0
   def __init__(self):
      self.cad = pifacecad.PiFaceCAD()
      self.cad.lcd.blink_off()
      self.cad.lcd.cursor_off()
      self.cad.lcd.backlight_on()

      self.listener = pifacecad.SwitchEventListener()
      self.listener.register(0, pifacecad.IODIR_ON, self.callNav)
    
      # wait for button presses
      self.listener = pifacecad.SwitchEventListener(chip=self.cad)
      for pstation in range(5):
         self.listener.register(
         pstation, pifacecad.IODIR_ON, self.callKey)
      self.listener.register(5, pifacecad.IODIR_ON, self.callNav)
      self.listener.register(6, pifacecad.IODIR_ON, self.callNav)
      self.listener.register(7, pifacecad.IODIR_ON, self.callNav)
      self.listener.activate()
      signal.signal(signal.SIGINT, self.stop)

   def stop(self, signal, frame):
    print "Stop listening switches"
    self.listener.deactivate()
    #call(["mpc", "stop"])
    sys.exit(0)


   def callNav(self, event):
      print "callNav"
      print "Switch pressed"
      print event.interrupt_flag
      self.currentNav=event.interrupt_flag
    
   def callKey(self, event):
      print "callKey"
      print "Switch pressed"
      print event.interrupt_flag
      self.currentKey=event.interrupt_flag

   def time(self):
       wTime = time.strftime("%H:%M:%S", time.localtime())
       return wTime

   def writeToDisplay(self, iCol, iRow, iText):
    self.cad.lcd.set_cursor(iCol, iRow) # col, row
    self.cad.lcd.write("{:16}".format(iText))
    #print "[{0}:{1}]{2}".format(iCol, iRow, iText)

   def next_state(self,cls):
      print '-> %s' % (cls.__name__,),
      self.__class__ = cls

#*****************************************************************************************
# ReveilStateClock
# 
# 
#
#*****************************************************************************************
class ReveilStateClock(ReveilStateBase):
   __call = 0  # state variable
   def __call__(self):
      self.clock()
      if self.currentKey==2:
         self.next_state(ReveilStateRadio)
         self.play()
         self.currentKey=0
         self()

   def clock(self):
      wTime = self.time()
      self.writeToDisplay( 0,0,"{0}".format(wTime))
      self.writeToDisplay( 0,1,"nav:{0} key:{1}".format(self.currentNav, self.currentKey))

#*****************************************************************************************
# ReveilStateAlarm
# 
# 
#
#*****************************************************************************************
class ReveilStateAlarm(ReveilStateBase):
   __call = 0
   def __call__(self):
      self.clock()
      if self.currentKey==1:
         self.next_state(ReveilStateClock)
         self.currentKey=0
         self()
   
   def clock(self):
      wTime = self.time()
      self.writeToDisplay( 0,0,"{0}".format(wTime))
      self.writeToDisplay( 0,1,"Alarm:{0}".format(self.alarm))

#*****************************************************************************************
# ReveilStateRadio
# 
# 
#
#*****************************************************************************************
class ReveilStateRadio(ReveilStateBase):
   __call = 0
   radio = MpcRadio()

   def __call__(self):
      self.clock()
      if self.currentKey==1:
         self.stop()
         self.next_state(ReveilStateClock)
         self.currentKey=0
         self()
      if self.currentKey==2:
         self.currentKey=0
         if self.radio.isRadioPlaying():
            self.stop()
         else:
            self.play()

   def clock(self):
      wTime = self.time()
      self.writeToDisplay( 0,0,"{0}".format(wTime))
      self.writeToDisplay( 0,1,"Radio:{0}".format(self.radio.isRadioPlaying()))

   def play(self):
      print __name__
      print "play:" + str(self.radio.isRadioPlaying())
      self.radio.play()


   def stop(self):
      self.radio.stop()

#*****************************************************************************************
# MAIN
# 
# 
#
#*****************************************************************************************
if __name__ == '__main__':
   sm = ReveilStateClock()

   while 1:
       sm()
       time.sleep(0.5)