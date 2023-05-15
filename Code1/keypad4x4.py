# Mechatronics Final Project v1
# Author: Carter Wright

# libraries n such
import RPi.GPIO as GPIO
import time
import LED
import carterTM1637 as c7SEG
from c74hc595 import updateLED

#GPIO Basic RASPI initialization 
GPIO.setmode(GPIO.BCM)     # address GPIO pins by their PIN NUMBER - NOT by their name
GPIO.setwarnings(False) 



# -------------------- define macros --------------------
pinHigh = 1
pinLow = 0
#   ----- GPIO TERMINALS -----
#   Keypad Rows
L1 = 19
L2 = 13
L3 = 6
L4 = 5
#   Keypad Columns
C1 = 21
C2 = 20
C3 = 16
C4 = 26
#   LEDS
red     = 2    # red
yellow  = 25    # yellow
green   = 3    # green
#   ----- STRINGS -----
#   Error Codes
strErrorUpper = "ERROR: - Input is equal to or less than Lower Limit"
strErrorLower = "ERROR: - Input is equal to or more than Upper Limit"
strErrorOverFlow1 = "ERROR: - Input too long"
strErrorOverFlow2 = "       - Buffer cleared"
#   Console Display
strInputModeWaiting = "* Input Mode: Waiting for A/B keypress *"
strInputModeUL = "* Input Mode: Setting Upper Limit *"
strInputModeLL = "* Input Mode: Setting Lower Limit *"
strInputModeSC = "* Input Mode: Scale Calibration *"
# -------------------------------------------------------



# -------------------- variables --------------------
keyPressed = -1         # -1 if no key is pressed -> column of the key that is currently pressed
operatorCode = "999"    # special access commands? not sure if needed
input = "0"             # user input number
lastKeyPressed = ""
inputMode = "none"
modeNONE = "none"
modeUL = "u"
modeLL = "l"
modeSCAN = "scan"
upperWeightLimit = 0    # initialize as 0
lowerWeightLimit = 0    # initialize as 0
# ---------------------------------------------------


# name:     initKeypad
# inputs:   pinL1, pinL2, pinL3, pinL4, pinC1, pinC2, pinC3, pinC4
#           - the RPI GPIO pins that the keypad connects to
# outputs:  none
# Notes:    configures RPI GPIO pins   
def initKeypad(pinL1, pinL2, pinL3, pinL4, pinC1, pinC2, pinC3, pinC4):
    global L1
    global L2
    global L3
    global L4
    global C1
    global C2
    global C3
    global C4
    L1 = pinL1
    L2 = pinL2
    L3 = pinL3
    L4 = pinL4
    C1 = pinC1
    C2 = pinC2
    C3 = pinC3
    C4 = pinC4
    print("Starting Keypad Module...")
    # -------------------- initialize GPIO pins --------------------
    # configure outputs
    GPIO.setup(L1, GPIO.OUT)
    GPIO.setup(L2, GPIO.OUT)
    GPIO.setup(L3, GPIO.OUT)
    GPIO.setup(L4, GPIO.OUT)
    # configure inputs to use internal pulldown resistors
    GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # detect rising edges at columns so we can act when a key is pressed
    GPIO.add_event_detect(C1, GPIO.RISING, callback=keypadDetect)
    GPIO.add_event_detect(C2, GPIO.RISING, callback=keypadDetect)
    GPIO.add_event_detect(C3, GPIO.RISING, callback=keypadDetect)
    GPIO.add_event_detect(C4, GPIO.RISING, callback=keypadDetect)
    # --------------------------------------------------------------

# -------------------- set up GPIO callback --------------------
# name:     function(argument)
# inputs:   none
# outputs:  none
# Notes:    none
def keypadDetect(channelPin):
    global keyPressed
    if (keyPressed == -1):
        keyPressed = channelPin
# ----------------------------------------------------------------------


# name:     setAllLines
# inputs:   state - high or low?
# outputs:  none
# Notes:    sets all lines high or low because using one function is easier
def setAllLines(state):
    if state == "HIGH":
        GPIO.output(L1, GPIO.HIGH)
        GPIO.output(L2, GPIO.HIGH)
        GPIO.output(L3, GPIO.HIGH)
        GPIO.output(L4, GPIO.HIGH)
    elif state == "LOW":
        GPIO.output(L1, GPIO.LOW)
        GPIO.output(L2, GPIO.LOW)
        GPIO.output(L3, GPIO.LOW)
        GPIO.output(L4, GPIO.LOW)

# name:     functionKeyPressed
# inputs:   none
# outputs:  pressed = True if a function key was pressed
#                           = False if key press was not a function key
# Notes:    a function key is A B C D * #
#           they act different than the regular 0-9 keys
#           used for complex user input
def functionKeyPressed():
    global input
    global upperWeightLimit
    global lowerWeightLimit
    global lastKeyPressed
    global inputMode
    pressed = False
    # Button A  |  Upper Limit Select ----------------------------------------------------
    GPIO.output(L1, GPIO.HIGH)
    if (GPIO.input(C4) == 1):
        if (inputMode == modeNONE):   # if no mode, set to Upper Limit
            inputMode = modeUL
            print(strInputModeUL)
            updateLED(6, 1)
        pressed = True
    GPIO.output(L1, GPIO.LOW)
    
    # Button B  |  Lower Limit Select ----------------------------------------------------
    GPIO.output(L2, GPIO.HIGH)
    if (GPIO.input(C4) == 1):
        if (inputMode == modeNONE):   # if no mode, set to Lower Limit
            inputMode = modeLL
            print(strInputModeLL)
            updateLED(7, 1)
        pressed = True
    GPIO.output(L2, GPIO.LOW)
    
    # Button C  |  Upper/Lower Limits View -----------------------------------------------
    GPIO.output(L3, GPIO.HIGH)
    if (GPIO.input(C4) == 1):
        # FOR INDIVIDUAL KEY SCANS
        if(inputMode == modeSCAN):
            lastKeyPressed = "C"
        else:
            print("DISPLAY VALUES:")
            print("Upper Weight Limit = ", upperWeightLimit)
            print("Lower Weight Limit = ", lowerWeightLimit)
        pressed = True
    GPIO.output(L3, GPIO.LOW)
    
    # Button D  |  Save Input Buffer -----------------------------------------------------
    GPIO.output(L4, GPIO.HIGH)
    if (GPIO.input(C4) == 1):
        
        # SET UPPER LIMIT
        if(inputMode == modeUL):  # if mode = setting Upper limit
            if(input == "0"):    # if no input value save as 0
                upperWeightLimit = 0
            else:
                if (eval(input) > lowerWeightLimit or lowerWeightLimit == 0): # valid input
                    upperWeightLimit = int(input)   # save the input value
                    print("SET Upper Limit as:", upperWeightLimit)
                else:
                    print("User Input:",input)
                    print(strErrorUpper)
                    
            c7SEG.dispUserInput(inputMode, upperWeightLimit)
            input = "0"  # clear the input buffer
            inputMode = modeNONE  # reset input mode
            print(strInputModeWaiting)
            updateLED(6, 0)
        
        # SET LOWER LIMIT
        if(inputMode == modeLL):  # if mode = setting lower limit
            if(input == "0"):    # if no input value save as 0
                lowerWeightLimit = 0
            else:
                if (eval(input) < upperWeightLimit or upperWeightLimit == 0): # valid input
                    lowerWeightLimit = int(input)   # save the input value
                    print("SET Lower Limit as:", lowerWeightLimit)
                else:
                    print("User Input:",input)
                    print(strErrorLower)
            
            c7SEG.dispUserInput(inputMode, lowerWeightLimit)
            input = "0"  # clear the input buffer
            inputMode = modeNONE  # reset input mode
            print(strInputModeWaiting)
            updateLED(7, 0)
            
        pressed = True
    GPIO.output(L4, GPIO.LOW)
    
    # Button *  |  Input Buffer Clear ----------------------------------------------------
    GPIO.output(L4, GPIO.HIGH)
    if (GPIO.input(C1) == 1):
        input = "0"              # clear the input buffer
        print("* Cleared Input *")
        pressed = True
    GPIO.output(L4, GPIO.LOW)
    
    # Button #  |  Input Buffer View -----------------------------------------------------
    GPIO.output(L4, GPIO.HIGH)
    if (GPIO.input(C3) == 1):
        print("DISPLAY:")
        print("Current Input:", input)
        pressed = True
    GPIO.output(L4, GPIO.LOW)

    return pressed


# name:     scanLine
# inputs:   lineNum - which keypad line to examine
#           lineChars - the chars that the line contains
# outputs:  none
# Notes:    scans the line and saves the pressed key number to the input buffer
def scanLine(lineNum, lineChars):
    global input
    global keyPressed
    global lastKeyPressed
    GPIO.output(lineNum, GPIO.HIGH)
    if(GPIO.input(C1) == 1):
        if(input == "0"):
            input = ""
        lastKeyPressed = lineChars[0]
        if(lastKeyPressed!="A" and lastKeyPressed!="B" and lastKeyPressed!="C" and
           lastKeyPressed!="D" and lastKeyPressed!="*" and lastKeyPressed!="#"):
            input = input + lastKeyPressed
        print("Current Input: ", input)
        
    if(GPIO.input(C2) == 1):
        if(input == "0"):
            input = ""
        lastKeyPressed = lineChars[1]
        if(lastKeyPressed!="A" and lastKeyPressed!="B" and lastKeyPressed!="C" and
           lastKeyPressed!="D" and lastKeyPressed!="*" and lastKeyPressed!="#"):
            input = input + lastKeyPressed
        print("Current Input: ", input)
        
    if(GPIO.input(C3) == 1):
        if(input == "0"):
            input = ""
        lastKeyPressed = lineChars[2]
        if(lastKeyPressed!="A" and lastKeyPressed!="B" and lastKeyPressed!="C" and
           lastKeyPressed!="D" and lastKeyPressed!="*" and lastKeyPressed!="#"):
            input = input + lastKeyPressed
        print("Current Input: ", input)
        
    if(GPIO.input(C4) == 1):
        if(input == "0"):
            input = ""
        lastKeyPressed = lineChars[3]
        if(lastKeyPressed!="A" and lastKeyPressed!="B" and lastKeyPressed!="C" and
           lastKeyPressed!="D" and lastKeyPressed!="*" and lastKeyPressed!="#"):
            input = input + lastKeyPressed
        print("Current Input: ", input)
    
    GPIO.output(lineNum, GPIO.LOW)




# name:     checkKeypad
# inputs:   returnMode - "UpperLower" or "scan for key"
#           scanKey - scan the keypad until this key is pressed
# outputs:  upperWeightLimit, lowerWeightLimit when returnMode == "UpperLower"
#           True, False when returnMode == "scan for key"
# Notes:    the main juice where the keypad scanning happens   
def checkKeypad(returnMode, scanKey):
    global input
    global inputMode
    global keyPressed
    global lastKeyPressed
    global upperWeightLimit
    global lowerWeightLimit
    # if a button is already pressed, is it still being held?
    if (keyPressed != -1):
        setAllLines("HIGH")
        if (GPIO.input(keyPressed) == 0):
            keyPressed = -1
    # if not then scan keypad for new key
    else:
        if (not functionKeyPressed() and inputMode != modeNONE):
            scanLine(L1, ["1","2","3","A"])
            scanLine(L2, ["4","5","6","B"])
            scanLine(L3, ["7","8","9","C"])
            scanLine(L4, ["*","0","#","D"]) # '*' and '#' shouldnt be accessed as they are used in functionKeyPressed()
            if(len(input) == 5): # input is too long! cant display 5 digits on 7seg
                input = "0"
                print(strErrorOverFlow1)
                print(strErrorOverFlow2)
    time.sleep(0.01) # delay for good data collection
        

    # return different things depending on input nmode
    if (returnMode == "UpperLower"):
        return upperWeightLimit, lowerWeightLimit
        
    elif (returnMode == "scan for key"):
        inputMode = modeSCAN
        if (lastKeyPressed == scanKey):
            lastKeyPressed = ""
            inputMode = modeNONE
            return True
        else:
            return False
        
    else:
        pass

