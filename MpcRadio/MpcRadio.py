#!/usr/bin/env python
#import ptvsd

#ptvsd.enable_attach(secret='my_secret', address = ('0.0.0.0', 5678))  #tcp://pj@pifamille/
#ptvsd.wait_for_attach()
import sys
import os
import subprocess
from subprocess import call
from time import sleep
import alsaaudio
import time
import signal




class MpcRadio(object):
    def __init__(self, iVerbose=0):
        self.verbose = iVerbose
        self._volume = 50
        try :
            mixer = alsaaudio.Mixer('PCM', 0)
        except alsaaudio.ALSAAudioError :
            sys.stderr.write("No such mixer\n")
            sys.exit(1)
        self._radioIsPlaying = False
        self.wifi = True
        # liste des radio enregistree avec MPC
        self.listeRadio = ["ShoutCast", "Classique", "Radio-Canada"]
        self.playingTitle = ""
        # Stop Radio
        call(["mpc", "stop"])
    #
    # isRadioPlaying
    #
    #@property
    def isRadioPlaying(self):
        return self._radioIsPlaying

    def play(self):
        call(["mpc", "play"])
        self._radioIsPlaying = True

    def stop(self):
        call(["mpc", "stop"])
        self._radioIsPlaying = False

    def stats(self):
        call(["mpc", "stats"])

    def nowPlaying(self):
        return self.playingTitle

    def radioPlay(self, val):
        print "radioPlay val:{0}".format(val)
        if val > len(self.listeRadio):
            self.stop()
            self._radioIsPlaying = False
        else: 
            radioTitre = val
            if self.wifi == 0:
                call(["ifup", "wlan0"])
                time.sleep(15)
                self.wifi = 1
            call(["mpc", "play", str(radioTitre + 1)])
            self._radioIsPlaying = True
            self.playingTitle = self.listeRadio[val]

    def volume(self, value):
       if value > 100:
          self._volume = 100
       elif value >= 0:
         self._volume = value
       #print("volume:{0}".format(self._volume))
       call(["mpc", "volume", str(self._volume)])
       #print("volume:{0}".format(self._volume))

    def getVolume(self):
       return self._volume

if __name__ == "__main__":
    radio = MpcRadio()
    print __name__
    print "play:" + str(radio.isRadioPlaying())
    radio.play()
    print "play:" + str(radio.isRadioPlaying())
    time.sleep(2)
    radio.radioPlay(2)