# Mechatronics Final Project v1
# Author: Carter Wright
#
# GPIO Pin & Function
#~~~~~~~~~~~~~~~~~~~~~
# 3.3V
#   2   
#   3   
#   4   CAN - Limit Switch
# GND
#   17  
#   27  Load Cell Amp - CLOCK
#   22  Load Cell Amp - DATA
# 3.3V
#   10  LCD - R/W(DATA) [SPI0 MOSI]
#   9   LED = SHcp
#   11  LCD - E(CLK) [SPI0 SCLK]
# GND
# ID SD
#   5   Keypad - L4
#   6   Keypad - L3
#   13  Keypad - L2
#   19  Keypad - L1
#   26  Keypad - C4
# GND
#~~~~~~~~~~~~~~
# 5V
# 5V
# GND
#   14  Switch 1 - Mode: Input/Scale
#   15  Switch 2 - Program: Running/Idle
#   18  Solenoid - Activate
# GND
#   23  7Segment - Clock
#   24  7Segment - Data In/Out
# GND
#   25  LED = STcp
#   8   LCD - RS(CS) [SPI0 CE0]
#   7   
# ID SC
# GND
#   12  LED = Ds
# GND
#   16  Keypad - C3
#   20  Keypad - C2
#   21  Keypad - C1
#
# libraries n such
import RPi.GPIO as GPIO         # controls GPIO pins
import tkinter as tk            # used for function scheduling
import time                     # time related functions
import keypad4x4 as KEYPAD      # Keypad interfacing
from hx711 import HX711         # import the class HX711
import HX711_BCIT as SCALE      # scale interfacing
import carterTM1637 as c7SEG    # 7 segment display
from c74hc595 import updateLED  # LED controls
from c74hc595 import initLEDS  # LED controls
import numpy
from statistics import mean

#GPIO Basic RASPI initialization 
GPIO.setmode(GPIO.BCM)          # address GPIO pins by their PIN NUMBER - NOT by their name
GPIO.setwarnings(False)

# -------------------- define macros -----------------------------------------------------
__pinHIGH = 1
__pinLOW  = 0
__ON = 1
__OFF = 0

#   ----- GPIO TERMINALS -----
# LED control
__led_Ds = 12
__led_STcp = 25
__led_SHcp = 9
# load cell amp
ampCLK = 27
ampDAT = 22
# LCD
lcdCLK = 11
lcdDAT = 10
lcdCS = 8
# 7-segment
segCLK = 23
segDAT = 24
# keypad
keypadL1 = 19
keypadL2 = 13
keypadL3 = 6
keypadL4 = 5
keypadC1 = 21
keypadC2 = 20
keypadC3 = 16
keypadC4 = 26
# piston system
solenoid = 18
# switches
limitSwitch = 4 # new can sensor
switch_1 = 14   # switch_1 = ON  -> mode = input
                # switch_1 = OFF -> mode = scale
switch_2 = 15   # switch_2 = ON  -> program running (starts calibration)
                # switch_2 = OFF -> program idle

# -------------------- variables & values-------------------------------------------------
# scale
upperLimit = 0
lowerLimit = 0
limitWarning = 0.20
# data aquisition
listDAQ = []  # received values
listCan = []  # valid values
i = 0   # index for setting up listDAQ
k = 0 # index for setting up listCan
# LED control
__LED_reject    = 7
__LED_accept    = 6
__LED_nearLim   = 2
__LED_scaleMode = 3
__LED_inputMode = 4
__LED_UL        = 0
__LED_LL        = 1
__LED_pistExt   = 5
LED_CLR = [0, 0, 0, 0, 0, 0, 0, 0]
LED_State = [0, 0, 0, 0, 0, 0, 0, 0]
# piston system
__piston_cycle = 1.4 # units [seconds]
__piston_extend = 0.35      # units [seconds]
__piston_delay = .7
# time
t_limSw = 0
lS_timer_ON = 0

# -------------------- STATE MACHINE -----------------------------------------------------
currentState = 0
nextState = 0
flag_firstScan = 1

__state_init = 0
__state_setup = 1
__state_scale = 2

__state_rejectCan = 4
__state_input = 3
__state5 = 5

# -------------------- classes/other -----------------------------------------------------------
class sealedCan:
    def __init__(self, weight, accept):
        self.weight = weight
        self.accept = accept
# -------------------- initialize GPIO pins ----------------------------------------------
# switches
GPIO.setup(switch_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(switch_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(limitSwitch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# solenoid
GPIO.setup(solenoid, GPIO.OUT)
# LEDs
GPIO.setup(__led_Ds, GPIO.OUT)
GPIO.setup(__led_STcp, GPIO.OUT)
GPIO.setup(__led_SHcp, GPIO.OUT)

# -------------------- FUNCTIONS ---------------------------------------------------------
# name:     checkAcceptable()
# function: - 
# inputs:   myList - the list to check
#           value - what to reference the list to
# outputs:  True - all items in 'myList'== value
#           False - 1 item in 'myList'!= value 
# Notes:    scans 'myList' referencing each item to 'value'
#           if they are all equal to 'value' returns true, otherwise false
def checkAcceptable(myList, value):
    for obj in myList:
        if obj.accept != value:
            return False
    return True


# name:     scanWeight()
# function: - gets the weight from the loadcell-amp
#           - checks the validity of the data
#           - saves the weight in a file
#           - activates lights+piston depending on acceptable range
# inputs:   none
# outputs:  0 - 
#           1 - 
# Notes:    none
def scanWeight():
    global nextState
    global upperLimit
    global lowerLimit
    global listDAQ
    global listCan
    global i
    global k
    
    # save the measured value from the scale
    scaleData = int(SCALE.readScale())
    
    # leave function if bad data
    if(scaleData < 0 or scaleData > 1500):
        return
    
    # save data in object
    measuredCan = sealedCan(scaleData, True)

    # determine if outside the  desired range
    if (scaleData > upperLimit or scaleData < lowerLimit):
        measuredCan.accept = False
        
    # !!!!! !!!!! !!!!! !!!!! !!!!! !!!!! !!!!! !!!!! !!!!! !!!!!
    # ADD CONDITION IF WITHIN 0-10g FOR NO CAN ON SCALE
    # !!!!! !!!!! !!!!! !!!!! !!!!! !!!!! !!!!! !!!!! !!!!! !!!!!
    
    # DAQ
    if(i < 24):                             # save the last 24 values
        listDAQ.append(measuredCan)
        i += 1
    else:
        listDAQ.insert(0, listDAQ.pop())    # shift list 1 to the right
        listDAQ[0] = measuredCan
    
    # MOVING AVERAGE
    if(k < 6):                              # save the last 6 values
        listCan.append(measuredCan)
        k += 1
    else:
        listCan.insert(0, listCan.pop())    # shift list 1 to the right
        listCan[0] = measuredCan
    
    # calculate the average weight of last 6 measurments
    averageWeight = int(mean(obj.weight for obj in listCan))
    
    # only display if last 6 values are ALL good or ALL bad
    if(checkAcceptable(listCan, True) or checkAcceptable(listCan, False)):
        c7SEG.displayInt(averageWeight)  # display to 7-segment
        pass
    
    
    # SOLENOID & PISTON LOGIC
    # check last 6 values
    if(checkAcceptable(listCan, False)):    # if ALL the last 6 values are bad 
        updateLED(__LED_reject, 1)
        updateLED(__LED_accept, 0)
        # SAVE THE DATA TO THE .TXT/.CSV FILE
        SCALE.file.write(repr(scaleData) + "," + repr(listCan[0].weight) + "," + repr(listCan[0].accept) + "," + repr(averageWeight) + "," + repr(0) + "\n")
        return 0
        
    else:   # at least 1 of the 6 values was good
        updateLED(__LED_reject, 0)
        updateLED(__LED_accept, 1)
        # SAVE THE DATA TO THE .TXT/.CSV FILE
        SCALE.file.write(repr(scaleData) + "," + repr(listCan[0].weight) + "," + repr(listCan[0].accept) + "," + repr(averageWeight) + "," + repr(1) + "\n")
        return 1

# name:     nearLimits
# inputs:   myList - the list to examine
# outputs:  True - average weight is acceptable and within limitWarning% of the acceptable limits
#           False - average weight is NOT acceptable or NOT within limitWarning% of the acceptable limits
# Notes:    used to control the yellow indicator light
def nearLimits(myList):
    ave = numpy.average(myList)
    range = upperLimit - lowerLimit
    rangeWarning = range*limitWarning
    if(ave < upperLimit and ave > upperLimit-rangeWarning):
        return True
    elif(ave > lowerLimit and ave < lowerLimit+rangeWarning):
        return True
    else:
        return False

# name:     switchActive()
# function: - checks if the range switch is active
# inputs:   switch_num - which switch to examine
#           PUD - does the GPIO pin have pull up or pull down resistor?
# outputs:  True - switch active
#           False - switch not active
# Notes:    checks if switch is active or not. check            
def switchActive(switch_num, PUD):
    if(PUD == "UP"):
        if (GPIO.input(switch_num) == 0):
            return True
        else:
            return False
        
    elif(PUD == "DOWN"):
        if (GPIO.input(switch_num) == 1):
            return True
        else:
            return False
        
    else:
        return False



#################


# name:     pistonExtend
# inputs:   none
# outputs:  none
# Notes:    activates solenoid to extend piston
def pistonExtend():
    GPIO.output(solenoid, GPIO.HIGH)
    print("! PISTON EXTEND  @ t =", time.time() - t_start)
# name:     pistonRetract
# inputs:   none
# outputs:  none
# Notes:    deactivates solenoid to retract piston
def pistonRetract():
    GPIO.output(solenoid, GPIO.LOW)
    print("! PISTON RETRACT @ t =", time.time() - t_start)
# name:     rejectCan
# inputs:   none
# outputs:  none
# Notes:    extends and retracts piston to reject can
#           timing contorlled by '__piston_extend'
def rejectCan():
    updateLED(__LED_pistExt, 1)
    pistonExtend()              # reject can
    time.sleep(__piston_extend) # time buffer
    pistonRetract()             # return piston to neutral
    time.sleep(__piston_extend) # time buffer
    updateLED(__LED_pistExt, 0)



#################


# name:     state0
# inputs:   none
# outputs:  none
# Notes:    what the state machine does in state0
def state0():
    global nextState
    # code
    print("Welcome to the T H E   S P E E D   W E I G H")
    print("To quit the program, press CTRL+C")
    print("")
    print("Starting Program...")
    # initialize modules
    KEYPAD.initKeypad(keypadL1, keypadL2, keypadL3, keypadL4,
                      keypadC1, keypadC2, keypadC3, keypadC4)
    #
    c7SEG.init7segment(segCLK, segDAT, 2)
    initLEDS(__led_Ds, __led_STcp, __led_SHcp)
    #
    print("* SCALE CALIBRATION SEQUENCE *")
    SCALE.initAmp(ampCLK, ampDAT)
    SCALE.loadCellInit()
    SCALE.loadCellCalibration()
    SCALE.openFile()
    SCALE.file.write("scaleData,listCan_0_weight,listCan_0_accept,averageValue,want_reject\n") # save the measured data
    nextState = 1

# name:     state1
# inputs:   none
# outputs:  none
# Notes:    what the state machine does in state1
def state1():
    global nextState
    global upperLimit
    global lowerLimit
    # code
    # make sure the operator sets the initial weight range at least once
    if (switchActive(switch_1, "UP") == False):
        print("Activate the switch to continue")
        c7SEG.writeDisplay([0b01000000, 0b01000000, 0b01110000, 0b00000000])    # shows an arrow to indicate activating a switch
        while(switchActive(switch_1, "UP") == False): # make operator activate switch
            pass
    # operator enters valid range
    c7SEG.writeDisplay([0x79, 0x54, 0x78, 0x50])  # shows 'entr' on 7seg
    print("Enter upper and lower limits on keypad")
    while(switchActive(switch_1, "UP") == True):
        upperLimit, lowerLimit = KEYPAD.checkKeypad("UpperLower", "")
    nextState = __state_scale

# name:     state2
# inputs:   none
# outputs:  none
# Notes:    what the state machine does in state2
def state2():
    # code
    pass

# name:     state3
# inputs:   none
# outputs:  none
# Notes:    what the state machine does in state3
def state3():
    global upperLimit
    global lowerLimit
    # code
    upperLimit, lowerLimit = KEYPAD.checkKeypad("UpperLower", "")

# name:     state4
# inputs:   none
# outputs:  none
# Notes:    what the state machine does in state4
def state4():
    # code
    pass

# name:     state5
# inputs:   none
# outputs:  none
# Notes:    what the state machine does in state5
def state5():
    # code
    pass

# -------------------- Main Client Code --------------------------------------------------
def main():
    global currentState
    global nextState
    global flag_firstScan
    print("*** start t =", t_start)
    t_limSw = 0
    try:
        while(True):
            if (currentState == nextState):
                # ------------------------------------------------------------
                # __state0
                if(currentState == __state_init and
                   nextState == __state_init):                  # initialize
                    print("* state 0 *      @ t =", time.time() - t_start)
                    state0()
                # ------------------------------------------------------------
                # __state1
                elif(currentState == __state_setup and
                     nextState == __state_setup):               # initial setup
                    print("* state 1 *      @ t =", time.time() - t_start)
                    state1()
                # ------------------------------------------------------------
                # __state2
                elif(currentState == __state_scale and
                     nextState == __state_scale):               # MODE: SCALE
                    print("* state 2 *      @ t =", time.time() - t_start)
                    print("* MODE: SCALE *")
                    flag_rejectCan = 0
                    lS_timer_ON = 0
                    c7SEG.clearScrn()
                    updateLED(__LED_inputMode, 0)
                    updateLED(__LED_scaleMode, 1)
                    while(switchActive(switch_1, "UP") == False):   # while in scale mode
                        # read scale - return 0 if bad value, 1 if good value
                        scale_state = scanWeight()
                        # was limit switch activated? is already timing?
                        # then save the time and start LS timer
                        if(switchActive(limitSwitch, "DOWN") and lS_timer_ON == 0):
                            t_limSw = time.time() - t_start # time when detect new can
                            lS_timer_ON = 1
                        # is the elaspsed time greater than the piston_delay time?
                        # is the timer on?
                        # then reject the can
                        if(time.time() - t_start - t_limSw >= __piston_delay and
                           lS_timer_ON == 1):
                            if(scale_state == 0):
                                nextState = __state_rejectCan   # next state will reject the can
                                lS_timer_ON = 0
                                flag_rejectCan = 1
                                break
                            else:
                                lS_timer_ON = 0
                                flag_rejectCan = 0
                    # if dont want to reject can go to INPUT mode
                    if(flag_rejectCan == 0):
                        nextState = __state_input
                    
                    # INCLUDE CODE TO SAVE CURRENT TIME TO THE .CSV FILE

                # ------------------------------------------------------------
                # __state3
                elif(currentState == __state_input and
                     nextState == __state_input):               # MODE: INPUT
                    print("* state 3      * @ t =", time.time() - t_start)
                    print("* MODE: INPUT *")
                    c7SEG.clearScrn()
                    updateLED(__LED_inputMode, 1)
                    updateLED(__LED_scaleMode, 0)
                    while(switchActive(switch_1, "UP") == True):
                        state3()
                    nextState = __state_scale
                # ------------------------------------------------------------
                # __state4
                elif(currentState == __state_rejectCan and
                    nextState == __state_rejectCan):            # reject piston
                    print("* state 4 *      @ t =", time.time() - t_start)
                    rejectCan()
                    nextState = __state_scale
                # ------------------------------------------------------------
                # __state5
                elif(currentState == 5 and nextState == 5):
                    print("* state 5 *      @ t =", time.time() - t_start)
                    state5()
                    
                else:
                    # error not a state
                    pass
            else:
                flag_firstScan = 1          # reset first scan flag
                currentState = nextState    # update the state machine
    
    
    
    
    
    except KeyboardInterrupt:
        print("\nApplication Stopped!")
    finally:
        GPIO.cleanup()
        SCALE.endScale()

if __name__ == "__main__":
    t_start = time.time()   # record program start-up time
    main()

