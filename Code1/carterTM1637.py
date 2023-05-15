##          A
##         ---
##      F |   | B
##         -G-
##      E |   | C
##         ---
##          D
##
##      HGFE DCBA
##    0b0110 1101 = 0x6D = display "5"
# libraries n such
import RPi.GPIO as GPIO # import GPIO
import time
import numpy

pinCLK = 0
pinDATA = 0
__CMD_1 = 0x40  # data command
__CMD_2 = 0xC0  # address command
__CMD_3 = 0x80  # display command
brightness = 2

# name:     init7segment
# inputs:   none
# outputs:  none
# Notes:    set-up for 7-segment display
def init7segment(clock, data, bright):
    pinCLK = clock
    pinDATA = data
    brightness = bright
    GPIO.setup(pinCLK, GPIO.OUT)
    GPIO.setup(pinDATA, GPIO.OUT)

    print("Starting 7-Segment Module...")
    print("* Brightness Level = ", brightness, " *")
    writeBrightness()
    clearScrn()

# name:     shiftByte
# inputs:   none
# outputs:  none
# Notes:    move byte out of PI into 7seg
def shiftByte(byte):
    GPIO.output(pinCLK, GPIO.LOW)           # start clk low
    for index in range(8):
        if byte & 0x01:                     # what is first bit?
            GPIO.output(pinDATA, GPIO.HIGH) # data high
        else:
            GPIO.output(pinDATA, GPIO.LOW)  # data low
        GPIO.output(pinCLK, GPIO.HIGH)      # pulse clk
        byte >>= 1                          # right shift byte by 1
    GPIO.output(pinCLK, GPIO.LOW)           # done sending pulse
    GPIO.output(pinCLK, GPIO.HIGH)
    GPIO.output(pinCLK, GPIO.LOW)

# name:     writeBrightness
# inputs:   none
# outputs:  none
# Notes:    set-up for 7-segment display - hard coded brightness to 2
def writeBrightness():
    shiftByte(__CMD_1)  # data command
    shiftByte(__CMD_3 | 0x08 | 2)  # display cmd, display on, bightness

# name:     writeDisplay
# inputs:   myList - list of 4 bytes to be displayed on 7seg
# outputs:  none
# Notes:    sends the list of 4 bytes to the 7seg
def writeDisplay(myList):
    shiftByte(__CMD_1)  # data command
    GPIO.output(pinCLK, GPIO.HIGH)  # new bytes
    GPIO.output(pinDATA, GPIO.HIGH)
    GPIO.output(pinCLK, GPIO.LOW)
    GPIO.output(pinDATA, GPIO.LOW)
    shiftByte(__CMD_2)  # address command
    for obj in myList:  # shift out bytes
        shiftByte(obj)
    GPIO.output(pinCLK, GPIO.LOW)   # end bytes
    GPIO.output(pinDATA, GPIO.LOW)
    GPIO.output(pinCLK, GPIO.HIGH)
    GPIO.output(pinDATA, GPIO.HIGH)
    shiftByte(__CMD_3 | 0x08 | 2)  # display cmd, display on, bightness

# name:     intToCode
# inputs:   value - integer to convert
# outputs:  a byte value corresponding to the int
# Notes:    converts int to a byte that will display said int on the 7seg
def intToCode(value):
    if value == 0:
        return 0x3F
    elif value == 1:
        return 0x06
    elif value == 2:
        return 0x5B
    elif value == 3:
        return 0x4F
    elif value == 4:
        return 0x66
    elif value == 5:
        return 0x6D
    elif value == 6:
        return 0x7D
    elif value == 7:
        return 0x07
    elif value == 8:
        return 0x7F
    elif value == 9:
        return 0x6F

# name:     displayInt
# inputs:   value - integer to be displayed
# outputs:  none
# Notes:    displays integer to 7seg
def displayInt(value):
    intBuff = [int(x) for x in str(value)]  # change value from int to a list of individual ints 1234->[1,2,3,4]
    for index in range (4):
        intBuff[index] = intToCode(intBuff[index])
    writeDisplay(intBuff)   # display the list

# name:     clearScrn
# inputs:   none
# outputs:  none
# Notes:    clears display
def clearScrn():
    writeDisplay([0, 0, 0, 0])

# name:     dispUserInput
# inputs:   mode - 'U' or 'L'
#           value - integer to be displayed
# outputs:  none
# Notes:    displays an integer and U/L 
def dispUserInput(mode, value):
    bufferList = [int(x) for x in str(value)]  # change value from int to a list of individual ints 1234->[1,2,3,4]
    for index in range (4):
        bufferList[index] = intToCode(bufferList[index])
        
    if (mode == 'U' or mode == 'u'):
        bufferList[0] = 0x3E    # left most digit is 'U'
    elif (mode == 'L' or mode == 'l'):
        bufferList[0] = 0x38    # left most digit is 'L'
    writeDisplay(bufferList)