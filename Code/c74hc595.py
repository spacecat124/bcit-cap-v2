import RPi.GPIO as GPIO         # controls GPIO pins
import time                     # time related functions

__led_Ds = 0
__led_STcp = 0
__led_SHcp = 0
LED_State = [0, 0, 0, 0, 0, 0, 0, 0]

# name:     initLEDS()
# function: - 
# inputs:   none
# outputs:  none
# Notes:    sets pins low
def initLEDS(__led_Ds, __led_STcp, __led_SHcp):
    GPIO.output(__led_Ds, GPIO.LOW)
    GPIO.output(__led_STcp, GPIO.LOW)
    GPIO.output(__led_SHcp, GPIO.LOW)


# name:     updateLED()
# function: - 
# inputs:   index - which LED do you want to edit?
#           state - what state is that LED? - 1=on, 0=off 
# outputs:  none
# Notes:    interfaces with 74HC595
#           updates the array of LEDs
def updateLED(index, state):
    if(state == 1 or state == 0):   # only accept 1 or 0 for LED state
        LED_State[index] = state    # update current state of LED list

        # shift out LED list bits
        for i in range (8):
            # set/reset the bit
            if LED_State[i] == 1:
                GPIO.output(__led_Ds, GPIO.HIGH)
            else:
                 GPIO.output(__led_Ds, GPIO.LOW)
            # shift to next bit
            GPIO.output(__led_SHcp, GPIO.HIGH)
            GPIO.output(__led_SHcp, GPIO.LOW)

        # set/save to the IC
        GPIO.output(__led_STcp, GPIO.HIGH)
        GPIO.output(__led_STcp, GPIO.LOW)
        return
    else:
        print("!!! bad LED input value !!!")
        return