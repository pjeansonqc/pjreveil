#!/usr/bin/env python
#import ptvsd
#ptvsd.enable_attach(secret='my_secret', address = ('0.0.0.0', 5678))  #tcp://my_secret@pifamille/
#ptvsd.wait_for_attach()
import sys, os
import subprocess
from subprocess import call
from time import sleep
import alsaaudio
import time
import signal




class MpcRadio(object):
    def __init__(self):
        self._radioIsPlaying=False
        self.wifi = True
        # liste des radio enregistree avec MPC
        self.listeRadio = ["ShoutCast", "Classique", "Radio-Canada"]
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

    def radioPlay(self, val):
        if val > len(self.listeRadio):
            self.stop()
            self._radioIsPlaying = False
        else: 
            radioTitre=val
            if self.wifi==0:
                call(["ifup", "wlan0"])
                time.sleep(15)
                self.wifi=1
            call(["mpc", "play", str(radioTitre)])
            self._radioIsPlaying = True


if __name__ == "__main__":
    radio = MpcRadio()
    print __name__
    print "play:" + str(radio.isRadioPlaying())
    radio.play()
    print "play:" + str(radio.isRadioPlaying())
    time.sleep(2)
    radio.radioPlay(2)