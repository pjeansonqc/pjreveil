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
from collections import deque
from timeit import default_timer as timer


LCD_BUTTON_00 = 0
LCD_BUTTON_01 = 1
LCD_BUTTON_02 = 2
LCD_BUTTON_03 = 4
LCD_BUTTON_04 = 8
LCD_BUTTON_05 = 16
LCD_BUTTON_06 = 32
LCD_BUTTON_07 = 64
LCD_BUTTON_08 = 128

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
   keyQueue = deque([])
   navQueue = deque([])

   def __init__(self):
      self.cad = pifacecad.PiFaceCAD()
      self.cad.lcd.blink_off()
      self.cad.lcd.cursor_off()
      self.cad.lcd.backlight_on()
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
      self.navQueue.appendleft(event.interrupt_flag)
      self.currentNav=event.interrupt_flag
    
   def callKey(self, event):
      print "callKey"
      print "Switch pressed"
      print event.interrupt_flag
      self.keyQueue.appendleft(event.interrupt_flag)
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
   def __call__(self):
      self.clock()
      if len(self.keyQueue):
         key = self.keyQueue.pop()
         if key==LCD_BUTTON_02:
            self.next_state(ReveilStateRadio)
            self.play()
            self()
         if key==LCD_BUTTON_05:
            self.next_state(ReveilStateExit)
            self()
      time.sleep(0.5)

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
   def __call__(self):
      self.clock()
      if len(self.keyQueue):
         key = self.keyQueue.pop()
         if key==LCD_BUTTON_01:
            self.next_state(ReveilStateClock)
            self()
      time.sleep(0.5)

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
   radio = MpcRadio()

   def __call__(self):
      self.clock()
      if len(self.keyQueue):
         key = self.keyQueue.pop()
         if key==LCD_BUTTON_01:
            self.stop()
            self.next_state(ReveilStateClock)
            self()
         if key==LCD_BUTTON_02:
            if self.radio.isRadioPlaying():
               self.stop()
            else:
               self.play()
         if key==LCD_BUTTON_03:
            self.radio.volume(self.radio.getVolume()-1)
            self.next_state(ReveilStateRadioVolume)
         if key==LCD_BUTTON_04:
            self.radio.volume(self.radio.getVolume()+1)
            self.next_state(ReveilStateRadioVolume)
      time.sleep(0.1)

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
# ReveilStateRadioVolume
# 
# 
#
#*****************************************************************************************
class ReveilStateRadioVolume(ReveilStateBase):
   radio = MpcRadio()
   start = timer()
   def __call__(self):
      self.clock()
      if len(self.keyQueue):
         key = self.keyQueue.pop()
         if key==LCD_BUTTON_03:
            self.start = timer()
            self.radio.volume(self.radio.getVolume()-1)
         if key==LCD_BUTTON_04:
            self.start = timer()
            self.radio.volume(self.radio.getVolume()+1)
      if (timer() - self.start) > 3:
         self.next_state(ReveilStateRadio)
      time.sleep(0.01)

   def clock(self):
      wTime = self.time()
      self.writeToDisplay( 0,0,"{0}".format(wTime))
      self.writeToDisplay( 0,1,"Volume:{0}".format(self.radio.getVolume() ) )

   def play(self):
      print __name__
      print "play:" + str(self.radio.isRadioPlaying())
      self.radio.play()

   def stop(self):
      self.radio.stop()

#*****************************************************************************************
# ReveilStateExit
# 
# 
#
#*****************************************************************************************
class ReveilStateExit(ReveilStateBase):
   def __call__(self):
      self.keyQueue.clear()
      self.navQueue.clear()
      self.writeToDisplay( 0,0,"")
      self.writeToDisplay( 0,1,"")
      self.cad.lcd.backlight_off()
      self.listener.deactivate()
      sys.exit(0)

   def clock(self):
      wTime = self.time()
      self.writeToDisplay( 0,0,"{0}".format(wTime))
      self.writeToDisplay( 0,1,"nav:{0} key:{1}".format(self.currentNav, self.currentKey))

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
       