#!/usr/bin/env python
import ptvsd
ptvsd.enable_attach(secret='my_secret', address = ('0.0.0.0', 5678))  #tcp://my_secret@pifamille/
#ptvsd.wait_for_attach()
import sys, os
import subprocess
from subprocess import call
from time import sleep
import pifacecad
import alsaaudio
import time
import signal
from MpcRadio.MpcRadio import MpcRadio 

GET_IP_CMD = "hostname --all-ip-addresses"

# pour afficher la date en FR
dic_jour={'Mon':'Lundi','Tue':'Mardi','Wed':'Mercredi','Thu':'Jeudi','Fri':'Vendredi','Sat':'Samedi','Sun':'Dimanche'}
dic_mois={'Jan':'Janvier','Feb':'Fevrier','Mar':'Mars','Apr':'Avril','May':'Mai','Jun':'Juin','Jul':'Juillet','Aug':'Aout','Sep':'Septembre','Oct':'Octobre','Nov':'Novembre','Dec':'Decembre'}
# Variable globale
global listeRadio
global radioIsPlaying
global radioTitre
global wifi
global snooze
global timerRadio
global timerAlarm
global alarmeActive
global choixMenu
global menuPosition
global etat
global alarm_snooze
global timer
global switchlistener
global radio

listeRadio = []
radioIsPlaying=0
radioTitre=1
wifi=1
snooze=0
timerRadio=0
timerAlarm=0
alarmeActive=0
choixMenu=0
etat=1
# valplus = volume son
valplus=30
processSleepTime=0.01
timeok=time.time()
# menuPosition position menu en memoire
menuPosition=0
alarm_snooze=""
timer=""
radio = MpcRadio()

STATE_ONE = 1
STATE_TWO = 2
STATE_THREE = 3
STATE_FOUR = 4
STATE_PLAY_ALARM=5


# liste des radio enregistr? avec MPC
listeRadio.append("ShoutCast")
listeRadio.append("Classique")
listeRadio.append("Radio-Canada")

ALARM="00:00"
ALARMCHOIX=ALARM
ALARMDUR="00:00"

# Stop Radio
call(["mpc", "stop"])
#call(["mpc", "play"])
#call(["mpc", "stats"])
    
cad = pifacecad.PiFaceCAD()
cad.lcd.blink_off()
cad.lcd.cursor_off()

listener = pifacecad.SwitchEventListener()

    
def stop(signal, frame):
    print "Stop listening switches"
    listener.deactivate()
    call(["mpc", "stop"])
    sys.exit(0)

signal.signal(signal.SIGINT, stop)

def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')


def get_my_ip():
    return run_cmd(GET_IP_CMD)[:-1]

def wait_for_ip():
    ip = ""
    while len(ip) <= 0:
        sleep(1)
        ip = get_my_ip()    

def writeToDisplay(iCol, iRow, iText):
    cad.lcd.set_cursor(iCol, iRow) # col, row
    cad.lcd.write("{:16}".format(iText ) )

def show_sysinfo():
    writeToDisplay(0,1,"IP:{}".format(get_my_ip()))

def get_time():
    d=time.asctime()
    d=d.split()
    date=dic_jour[d[0]]+" "+d[2]+" "+dic_mois[d[1]]+" "+d[4]
    heure=d[3]
    heure=heure.split(":")
    heure=heure[0]+":"+heure[1]
    return date,heure

def volume(deltak):
    global valplus
    #os.system('clear')
    if deltak > 0: valplus=valplus+1
    else: valplus=valplus-1
    if valplus>=100: valplus=100
    call(["mpc", "volume", str(valplus)])   
    #led.draw_text2(0,24,"Volume :" + str(valplus) +" % ",1)
    writeToDisplay(1,0,"Volume :{}".format(str(valplus)))
    
def radioplay(val):
    global wifi
    global radioIsPlaying
    global radioTitre
    global snooze
    global ALARM
    global ALARMDUR
    if val > len(listeRadio): 
        call(["mpc", "stop"])
        snooze=0
        radioIsPlaying=0
        ALARM=ALARMDUR
    else: 
        radioTitre=val
        if wifi==0:
            cad.lcd.clear()
            writeToDisplay(1,0,"Wifi Activation")
            call(["ifup", "wlan0"])
            time.sleep(15)
            writeToDisplay(1,0,"Wifi Actif")
            wifi=1
        call(["mpc", "play", str(radioTitre)])
        radioIsPlaying=1

    
    #cad.lcd.write("Volume :" + str(valplus) +" % ")
    writeToDisplay(0,0,"Volume :" + str(valplus) +" % ")

    #led.display()       

def displayMenuWithChoice(menu,choix):
    global menuPosition
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
    writeToDisplay(0,0,">{}".format(menu[menuPosition]))
    if menuPosition+1 < len(menu):
        writeToDisplay(0,1," {}".format(menu[menuPosition+1]))
def menuGeneral(choix):
    menu = []
    menu.append("REGLAGES")
    menu.append("RADIO")
    menu.append("STOP RADIO")
    menu.append("TIMER 30Min")
    menu.append("RETOUR")
    displayMenuWithChoice(menu,choix)

def menuReglage(choix):
    menu = []
    menu.append("REVEIL :" + ALARM)
    if alarmeActive==1: 
        menu.append("ALARME OFF")
    else: 
        menu.append("ALARME ON")
    menu.append("RETOUR")
    menu.append("ETEINDRE")
    displayMenuWithChoice(menu,choix)

def menuRadio(choix):
    global listeRadio
    displayMenuWithChoice(listeRadio,choix)   
    
    

    
def clock():
    if alarmeActive==1: 
        plus="on"
    else: 
        plus="off"
    #cad.lcd.clear()
    #led.draw_text2(0,0,time.strftime("%H:%M:%S", time.localtime()) + plus,2,2)
    wTime = time.strftime("%H:%M:%S", time.localtime())
    writeToDisplay(0,0,"{0} {1}".format(wTime, plus) )
    if radio.wifi==0: 
        #led.draw_text2(0,24,"Wifi Inactif",1)
        #cad.lcd.set_cursor(1, 1) # col, row
        #cad.lcd.write("Wifi Inactif    ")
        writeToDisplay(1,1,"Wifi Inactif    ")
    if radioIsPlaying==1: 
        #led.draw_text2(0,24,listeRadio[radioTitre-1]+" "+timer,1)
        #cad.lcd.set_cursor(0, 1) # col, row
        #cad.lcd.write(listeRadio[radioTitre-1]+" "+timer)
        writeToDisplay(0,1,listeRadio[radioTitre-1]+" "+timer)
    else:
        #cad.lcd.set_cursor(0, 1) # col, row
        #cad.lcd.write("               ")
        writeToDisplay(0,1,"               ")
    #led.display()


def clockAlarm():
    #affiche l'heure quand alarm regl?
    cad.lcd.clear()
    #led.draw_text2(0,0,time.strftime("%H:%M:%S", time.localtime()),2,2)
    #cad.lcd.set_cursor(0, 0) # col, row
    #cad.lcd.write(time.strftime("%H:%M:%S", time.localtime()))
    writeToDisplay(0,0,time.strftime("%H:%M:%S", time.localtime()))
    
    #led.display()
    #led.draw_text2(0,18,ALARM,1,0)
    #cad.lcd.set_cursor(10, 1) # col, row
    #cad.lcd.write(ALARM)
    writeToDisplay(10,1,ALARM)
    #led.display()
    time.sleep(1)

# vous connaissez le snooze ;-) c'est celui qui vous permet de dormir 10 minutes de plus ;-)
def snoozeit():
    global ALARM
    global snooze
    global radioIsPlaying
    global alarm_snooze
    plus=0
    alarm_snooze=get_time()
    alarm_snooze=(alarm_snooze[1])
    hour=alarm_snooze.split(":")
    varsnooze=10
    if (int(hour[1])+varsnooze)>59: 
        newM=(int(hour[1])+varsnooze)-60
        plus=1
    else: newM=(int(hour[1])+varsnooze)
    if len(str(newM))<2: 
        newM=str('0')+str(newM)
    if len(str(int(hour[0])+plus))<2: newH=str('0')+str(int(hour[0])+plus)
    else: newH=str(int(hour[0])+plus)
    alarm_snooze=str(newH)+":"+str(newM)
    #snooze=0
    call(["mpc", "stop"])
    radioIsPlaying=0
    cad.lcd.clear()
    #led.draw_text2(0,0,time.strftime("%H:%M:%S", time.localtime()),2,0)
    cad.lcd.set_cursor(0, 0) # col, row
    cad.lcd.write(time.strftime("%H:%M:%S", time.localtime()))
    writeToDisplay(0,0,time.strftime("%H:%M:%S", time.localtime()))
    #led.draw_text2(23,0,"Dodo pour "+str(alarm_snooze),1)
    #cad.lcd.set_cursor(1, 1) # col, row
    #cad.lcd.write("Dodo pour "+str(alarm_snooze))
    writeToDisplay(1,1,"Dodo pour "+str(alarm_snooze))
    #led.display()
    time.sleep(0.5)

def timerRadio(varsnooze=30):
    global timer
    plus=0
    timer=get_time()
    timer=(timer[1])
    hour=timer.split(":")
    #varsnooze=30
    if (int(hour[1])+varsnooze)>59: 
        newM=(int(hour[1])+varsnooze)-60
        plus=1
    else: newM=(int(hour[1])+varsnooze)
    if len(str(newM))<2: 
        newM=str('0')+str(newM)
    if len(str(int(hour[0])+plus))<2: newH=str('0')+str(int(hour[0])+plus)
    else: newH=str(int(hour[0])+plus)
    timer=str(newH)+":"+str(newM)
    
def alarm(deltak,type):
    global etat
    global ALARM
    global ALARMDUR
    global INFOAL
    global ALARMCHOIX
    os.system('clear')
    hour=ALARM.split(":")
    if len(str(int(hour[0])))<2: 
        res=str('0')+str(int(hour[0]))
    else: 
        res=str(int(hour[0]))
    ALARMCHOIX=str(int(hour[0]))+str(int(hour[1]))
    if type=='heure':
        if deltak > 0:
            if len(str(int(hour[0])+1))<2: res=str('0')+str(int(hour[0])+1)
            else: res=str(int(hour[0])+1)
            if str(res)=="24": res="00"
            ALARM=str(res)+":"+str(hour[1])
        elif deltak < 0:
            if len(str(int(hour[0])-1))<2: res=str('0')+str(int(hour[0])-1)
            else: res=str(int(hour[0])-1)
            if str(res)=="-1" or str(res)=="-1": res="23"
            ALARM=str(res)+":"+str(hour[1])
        ALARMCHOIX=">"+str(res)+":"+str(hour[1])
    if type=='minute':
        if len(str(int(hour[1])))<2: res=str('0')+str(int(hour[1]))
        else: res=str(int(hour[1]))
        if deltak > 0:
            if len(str(int(hour[1])+1))<2: res=str('0')+str(int(hour[1])+1)
            else: res=str(int(hour[1])+1)
            if str(res)=="60": res="00"
            ALARM=str(hour[0])+":"+str(res)	
        elif deltak < 0:
            if len(str(int(hour[1])-1))<2: res=str('0')+str(int(hour[1])-1)
            else: res=str(int(hour[1])-1)
            if str(res)=="-1": res="59"
            ALARM=str(hour[0])+":"+str(res)
        ALARMCHOIX=str(hour[0])+":>"+str(res)
    ALARMDUR=ALARM
    cad.lcd.clear()
    
    #led.draw_text2(0,0,time.strftime("%H:%M:%S", time.localtime()),2,0)
    cad.lcd.set_cursor(0, 0) # col, row
    cad.lcd.write(time.strftime("%H:%M:%S", time.localtime()))
    writeToDisplay(0,0,time.strftime("%H:%M:%S", time.localtime()))
    
    #led.draw_text2(0,18,ALARMCHOIX,2,0)
    #cad.lcd.set_cursor(17, 0) # col, row
    #cad.lcd.write(ALARMCHOIX)
    writeToDisplay(10,0,ALARMCHOIX)
    #led.display()
#click est celui qu'on appelle quand on tourne le bouton
def rotation(etat, delta):
    global processSleepTime
    global timeok
    global wifi
    global radioIsPlaying
    global radioTitre
    global snooze
    print ("etat:{0} delta:{1}".format(etat, delta ))
    deltak=0
    if delta!=0:
        #processSleepTime=0.01
        timeok=time.time()
        if delta == 128: 
            deltak=1
        if delta == 64:
            deltak=-1
        if etat==STATE_ONE or etat==STATE_PLAY_ALARM:
            processSleepTime=0.01
            volume(deltak)
        elif etat==30:
            processSleepTime=0.2
            menuRadio(deltak)       
        elif etat==20:
            processSleepTime=0.2
            menuReglage(deltak)
        elif etat==11:
            processSleepTime=0.2
            menuGeneral(deltak)
        elif etat==2:
            processSleepTime=0.2
            radiomenu(deltak)
        elif etat==21:
            processSleepTime=0.2
            alarm(deltak,"heure")
        elif etat==22:
            processSleepTime=0.2
            alarm(deltak,"minute")  
#click est celui qu'on appelle quand on appui sur le bouton
def click(etat1, event):
    global menuPosition
    global etat
    global processSleepTime
    global alarmeActive
    global timeok
    global snooze
    global ALARM
    global alarm_snooze
    global radio
    sw_state = event
    if sw_state==32:
        processSleepTime=0.01
        #processSleepTime=0.7
        timeok=time.time()
        if etat==30:
            radio.radioPlay(menuPosition+1)
            etat=STATE_ONE
            clock()
        elif etat==11:
            processSleepTime=0.2
            if menuPosition==4:
                menuPosition=0
                etat=STATE_ONE
                clock()
            if menuPosition==3:
                timerRadio(30)
                etat=STATE_ONE
                clock()
            elif menuPosition==2:
                radio.radioPlay(10)
                snooze=0
                alarm_snooze=""
                etat=STATE_ONE                  
                clock()
            elif menuPosition==1:
                menuPosition=0
                menuRadio(0)
                etat=30
            elif menuPosition==0:
                menuPosition=0
                menuReglage(0)
                etat=20
        elif etat==20:
            processSleepTime=0.2
            if menuPosition==3:
                call(["shutdown", "-h", "now"])
            elif menuPosition==2:
                etat=STATE_ONE
                clock()
            elif menuPosition==1:
                if alarmeActive==1: alarmeActive=0
                else: alarmeActive=1
                etat=STATE_ONE
                clock()
            elif menuPosition==0:
                alarm(0,'heure')
                etat=21 
        elif etat==22:
            clockAlarm()
            etat=STATE_ONE
        elif etat==21:
            processSleepTime=0.2
            etat=22
            alarm(0,'minute')
        elif etat==STATE_ONE: 
            menuPosition=0
            processSleepTime=0.2
            menuGeneral(0)
            time.sleep(1)
            etat=11
        elif etat1==STATE_PLAY_ALARM:
            snoozeit()
            etat=STATE_ONE  

def callRotation(event):
    print "callRotation"
    print "Switch pressed"
    print event.interrupt_flag
    rotation(etat, event.interrupt_flag)
    
def callClick(event):
    print "callClick"
    print "Switch pressed"
    print event.interrupt_flag
    click(etat, event.interrupt_flag)

if __name__ == "__main__":

    listener.register(0, pifacecad.IODIR_ON, callRotation)
    
    
    # wait for button presses
    listener = pifacecad.SwitchEventListener(chip=cad)
    for pstation in range(4):
        listener.register(
            pstation, pifacecad.IODIR_ON, callRotation)
    listener.register(4, pifacecad.IODIR_ON, callRotation)
    listener.register(5, pifacecad.IODIR_ON, callClick)
    listener.register(6, pifacecad.IODIR_ON, callRotation)
    listener.register(7, pifacecad.IODIR_ON, callRotation)
    listener.activate()
    
    cad.lcd.blink_off()
    cad.lcd.cursor_off()
    if "clear" in sys.argv:
        cad.lcd.clear()
        cad.lcd.display_off()
        cad.lcd.backlight_off()
    else:
        cad.lcd.backlight_on()
        #cad.lcd.set_cursor(0, 0) # col, row
        #cad.lcd.write("Waiting for IP..")
        #writeToDisplay(1,1,"Waiting for IP..")
        #wait_for_ip()
        #show_sysinfo()
    clock() 
    # Trouver le mixer et utilise le 1er.
    try :
        mixer = alsaaudio.Mixer('PCM', 0)
    except alsaaudio.ALSAAudioError :
        sys.stderr.write("No such mixer\n")
        sys.exit(1)
    # la boucle while permet de gerer les process suivant si on tourne ou appui sur le bouton  et check de l'alarme + snooze
    while 1:
        #print time.time()
        #print str(snooze)
        al=get_time()   
        if (ALARM==al[1] and alarmeActive==1 and etat==1 and snooze==0) or (alarm_snooze==al[1] and snooze==1 and etat==1):
            snooze=1
            etat=STATE_PLAY_ALARM
            radio.radioPlay(radioTitre)
            #timerRadio(60)
        if (timer==al[1] and radioIsPlaying==1):
            call(["mpc", "stop"])
            radioIsPlaying=0
            snooze=0
            etat=1
            alarm_snooze=""
            timer=""
        if (time.time()-timeok) > 10:
            if (time.time()-timeok) > 560:
                if radio.wifi==True and radio.isRadioPlaying==False:
                    radio.wifi=False
                    call(["ifdown", "wlan0"])
                    time.sleep(10)
                    #led.draw_text2(0,18,"Wifi Down",2,0)
                    #led.display()
                timeok=time.time()
            processSleepTime=0.9
            clock()
        #if snooze==1: etat=STATE_PLAY_ALARM   
        processSleepTime=processSleepTime
        time.sleep(processSleepTime)
        #rotation(etat)
        #click(etat)