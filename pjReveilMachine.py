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

   def __init__(self):
      self.cad = pifacecad.PiFaceCAD()
      self.cad.lcd.blink_off()
      self.cad.lcd.cursor_off()
      self.cad.lcd.backlight_on()
      self.cad.lcd.backlight_on()

      self.listener = pifacecad.SwitchEventListener()
      self.listener.register(0, pifacecad.IODIR_ON, self.callKey)
    
      # wait for button presses
      self.listener = pifacecad.SwitchEventListener(chip=self.cad)
      for pstation in range(5):
         self.listener.register(
         pstation, pifacecad.IODIR_ON, self.callKey)
      self.listener.register(5, pifacecad.IODIR_ON, self.callKey)
      self.listener.register(6, pifacecad.IODIR_ON, self.callKey)
      self.listener.register(7, pifacecad.IODIR_ON, self.callKey)
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


   def displayMenuWithChoice(self, menu,choix):
       print "meunu:{0}, choix:{1}".format(menu, choix)
       if choix > 0:
           #increment the menu position if we can
           if menuPosition==len(menu)-1:
               menuPosition=len(menu)-1
           else: 
               menuPosition=menuPosition+1
       elif choix < 0:
           #decrement the menu position if we can
           if menuPosition==0: 
               menuPosition=0
           else: 
               menuPosition=menuPosition-1
       a=(menuPosition*10)*-1
       cad.lcd.clear()
       #Display the selected menu item and the next one if possible.
       if menuPosition >= 0:
           if menuPosition < len(menu):
               writeToDisplay(0,0,">{}".format(menu[menuPosition]))
           if menuPosition+1 < len(menu):
               writeToDisplay(0,1," {}".format(menu[menuPosition+1]))
       else:
           print "menuPosition is not valid:{0:d}".format(menuPosition)


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
         if key==LCD_BUTTON_06:
            self.next_state(ReveilStateClockMenu)
            self()
      time.sleep(0.5)

   def clock(self):
      wTime = self.time()
      self.writeToDisplay( 0,0,"{0}".format(wTime))
      self.writeToDisplay( 0,1,"nav:{0} key:{1}".format(self.currentNav, self.currentKey))

#*****************************************************************************************
# ReveilStateClock
# 
# 
#
#*****************************************************************************************
class ReveilStateClockMenu(ReveilStateBase):
   start = timer()
   menu = ["REGLAGES", "RADIO", "STOP RADIO", "TIMER 30Min", "RETOUR"]
   choix = -1
   refreshMenu = True
   def __call__(self):
      if len(self.keyQueue):
         key = self.keyQueue.pop()
         if key==LCD_BUTTON_02:
            self.next_state(ReveilStateClock)
            self()
            return
         if key==LCD_BUTTON_07:
            if(self.choix>0):
               self.choix = self.choix-1
         if key==LCD_BUTTON_06:
            if self.choix==1:
               self.choix=-1
               self.next_state(ReveilStateRadio)
            self()
            return
         if key==LCD_BUTTON_05:
            self.next_state(ReveilStateExit)
            self()
            return
         if key==LCD_BUTTON_08:
            if(self.choix<len(self.menu)):
               self.choix = self.choix+1
         self.refreshMenu = True
      if self.refreshMenu == True:
         self.refreshMenu = False
         if self.choix < len(self.menu):
            self.writeToDisplay(0,0,">{}".format(self.menu[self.choix]))
         if self.choix+1 < len(self.menu):
            self.writeToDisplay(0,1," {}".format(self.menu[self.choix+1]))
         else:
            self.writeToDisplay(0,1,"----")
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
         if key==LCD_BUTTON_06:
            self.next_state(ReveilStateShowRadioMenu)
            self()
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
# ReveilStateRadioVolume
# 
# 
#
#*****************************************************************************************
class ReveilStateShowRadioMenu(ReveilStateBase):
   radio = MpcRadio()
   start = timer()
   menu = ["ShoutCast", "Classique", "Radio-Canada"]
   choix = 0

   def __call__(self):
      if len(self.keyQueue):
         key = self.keyQueue.pop()
         if key==LCD_BUTTON_07:
            if(self.choix>0):
               self.choix = self.choix-1
         if key==LCD_BUTTON_06:
            self.radio.radioPlay(self.choix)
            self.next_state(ReveilStateRadio)
            return
         if key==LCD_BUTTON_08:
            if(self.choix<len(self.menu)):
               self.choix = self.choix+1
         print("choix:{0}".format(self.choix))
      if self.choix >= 0:
         if self.choix < len(self.menu):
            self.writeToDisplay(0,0,">{}".format(self.menu[self.choix]))
         if self.choix+1 < len(self.menu):
            self.writeToDisplay(0,1," {}".format(self.menu[self.choix+1]))
         else:
            self.writeToDisplay(0,1,"----")
      else:
         print "choix is not valid:{0:d}".format(self.choix)
      time.sleep(1)

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
       