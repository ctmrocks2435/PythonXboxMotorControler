#######################################################
# RaspberryPI RC control software.
# Desined to take gamepad input and transmit via
# Serial to a Sabertooth MCU.
#
# Required inputs. Use pip install for this.
# Uses rpi.gpio for showing output on interface board... (Optional)
# Requires raspberry-config be used to enable serial ports.
#
# Collin Matthews
# 20-AUG-2017
#######################################################
from inputs import get_gamepad
import time
import queue
import threading
from multiprocessing import Queue
import RPi.GPIO as GPIO



BYTE_FILE_L="/home/pi/dataL.dat"
BYTE_FILE_R="/home/pi/dataR.dat"
STICK_ZERO_THRESH = 5
STICK_ONE_THRESH = 61
#GPIO_TX_PIN = 4
motorL=0
motorR=0
q = Queue()


    
""" Sets motor speed via TTL SERIAL. 
    Send -1 - 1? for motor speed?"""
def setMotorSpeed(speed, side):
#Motor 1: 1=FullRev 64=Stop 127=FullFwd
#Motor 2: 128=FullRev 192=Stop 255=FullFwd
#Sending 0 will stop both motors.
    global serialOut
    #print("Lm:" + str(leftMotor) + " Rm:" + str(rightMotor))
    #SCALE FOR 8 BIT
    #GPIO.output(GPIO_TX_PIN, 1)
    if side == 0:
        speed = int(speed) + 64
        if speed == 0: speed = 1 #Left has 1 less precision.
        try:
            with open(BYTE_FILE_L, 'wb') as f:
                f.write(bytes([speed]))
        except: 
            pass
    else:
        speed = int(speed) + 192
        try:
            with open(BYTE_FILE_R, 'wb') as f:
                f.write(bytes([speed]))
        except: 
            pass
    #print("Side:" + str(side) + " Speed:" + str(speed))
    #GPIO.output(GPIO_TX_PIN, 0)




"""Filter Inputs for only button/stick data.
    Outputs -64 to 63. (7 bit)"""
def inputFilter(event):
    #print(event.ev_type, event.code, event.state)
    if event.ev_type is not "Sync":
        eventcode = event.code
        data = event.state
        if eventcode in ('ABS_Y','ABS_RY'):
            data=round(data/512)
            #Force 0 on bad sticks.
            if data > -1*STICK_ZERO_THRESH and data < STICK_ZERO_THRESH: data=0
            if data > STICK_ONE_THRESH: data = 63
            if data < -1*STICK_ONE_THRESH: data = -64
            return str(eventcode) + "=" + str(data)


def gamepadMonitor():
    while True:
        for event in get_gamepad():
            eventResult = inputFilter(event)
            if eventResult is not None:
                q.put(eventResult)


def main():

    global motorL
    global motorR
    lastMotorL = 0
    lastMotorR = 0
    cnt_l=0
    max_delay_timer=0
    
    #Setup GPIO
    #Moved to BASH for more real time.
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setup(GPIO_TX_PIN, GPIO.OUT)
    #GPIO.output(GPIO_TX_PIN, 0)
    
    #Start 2nd Thread
    t = threading.Thread(target=gamepadMonitor)
    t.daemon = True
    t.start()
    
    #Start Control Loop.
    while 1:
        #Loop to eat up buffered controler inputs.
        while (q.qsize() > 0):
            eventResult = q.get()
            if eventResult.startswith("ABS_Y"):
                motorL=eventResult.split("=")[1]
                #print("  ml=" + str(motorL))
            elif eventResult.startswith("ABS_RY"):
                motorR=eventResult.split("=")[1]
                #print("  mr=" + str(motorR))
            #Check if over max update time (Constant stick movment can cause this.)
            if (time.time() - max_delay_timer)*1000 > 25: #ms
                setMotorSpeed(motorL,0)
                setMotorSpeed(motorR,1) 
                lastMotorL = motorL
                lastMotorR = motorR
                max_delay_timer = time.time()
            cnt_l = cnt_l + 1
            #print(str(cnt_l))
        #a=time.time()
        if ((lastMotorL != motorL) or (lastMotorR != motorR)):
            setMotorSpeed(motorL,0)
            setMotorSpeed(motorR,1)
            lastMotorL = motorL
            lastMotorR = motorR
        #print("Update Time" + str((time.time()-a)*1000))
        time.sleep(0.001)


           
        
if __name__ == "__main__":
    main()
    
    



    

    
    
    
    
    
    
    
    
    