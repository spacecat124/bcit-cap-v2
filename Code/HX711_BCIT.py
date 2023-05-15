# Mechatronics Final Project v1
# Author: Carter Wright
# This code includes a modified version of the HX711 library created by Gandalf
# https://github.com/gandalf15/HX711/blob/master/HX711_Python3/hx711.py


# libraries n such
import RPi.GPIO as GPIO  # import GPIO
from hx711 import HX711  # import the class HX711
import keypad4x4 as KEYPAD
import carterTM1637 as c7SEG

#GPIO Basic RASPI initialization 
GPIO.setmode(GPIO.BCM)     # address GPIO pins by their PIN NUMBER - NOT by their name
GPIO.setwarnings(False)

# -------------------- define macros --------------------
pinHigh = 1
pinLow = 0
#   ----- GPIO TERMINALS -----
pinCLK = 0
pinDATA = 0

#   ----- STRINGS -----
dataFileName = "MeasuredData.txt"
#   Error Codes
strErrorTareUnsuccessful = "ERROR: - Tare is unsuccessful"
strErrorInvalidData = "ERROR: - Invalid Data: "
strErrorMeanvalue = "ERROR: - Cannot compute mean value. Data mean: "

# name:     initAmp
# inputs:   clock - clock pin for hx711
#           data - data pin for hx711
# outputs:  none
# Notes:    sets up hx711 object to use scale features   
def initAmp(clock, data):
    global hx
    global pinCLK
    global pinDATA
    pinCLK = clock
    pinDATA = data
    hx = HX711(dout_pin=pinDATA, pd_sck_pin=pinCLK)

# name:     loadCellInit
# inputs:   none
# outputs:  none
# Notes:    measures zero value/tare and saves the value for offset
def loadCellInit():
    print("")
    print("Setting up the scale. Remove any weight on it and press 'C'")
    c7SEG.writeDisplay([0x5B, 0x79, 0x50, 0x3f])   # display 'zero' on 7segment
    while (KEYPAD.checkKeypad("scan for key", "C") == False):   # wait for keypress
        pass
    print("* Zeroing the scale... *")
    error = hx.zero()
    if error: # check for errors
        raise ValueError(strErrorTareUnsuccessful)

# name:     loadCellCalibration
# inputs:   none
# outputs:  none
# Notes:    measures known value to calculate ratio
#           will be modified later to allow for other weights, not just 500g
def loadCellCalibration():
    print("")
    print("Place a 500.0g weight on the scale and press 'C'")
    c7SEG.writeDisplay([0x39, 0x77, 0x38, 0x06])   # display 'cali' on 7segment
    while (KEYPAD.checkKeypad("scan for key", "C") == False):   # wait for keypress
        pass
    print("* Calibating the scale...")
    dataMean = hx.get_data_mean()           # read scale
    known_weight_grams = 500.0              # known weight - will changed later to accept a user input for other known weights
    print("* Calibrated to", known_weight_grams)
    ratio = dataMean / known_weight_grams   # calculate the ratio
    hx.set_scale_ratio(ratio)               # save ratio

# name:     infiniteLoop
# inputs:   none
# outputs:  none
# Notes:    continuously reads scale values and displays to console
#           used for testing
#           saves data to file
def infiniteLoop():
    global file
    print("The scale data will be continuously displayed to the console. To exit SPEED WEIGH press 'CTRL + C'")
    input("Press Enter to begin")
    openFile()
    while True: ## THE MAIN JUICE LOOP
        dataMean = (hx.get_weight_mean(2))
        print(dataMean, "g")
        file.write(repr(dataMean) + "\n") # save the measured data

# FILES
# name:     openFile
# inputs:   none
# outputs:  none
# Notes:    open a file to save the data
def openFile():
    global file
    file = open(dataFileName, "w")
    print("Opened File: ", dataFileName)

# name:     closeFile
# inputs:   none
# outputs:  none
# Notes:    stop writing and close a file
def closeFile():
    global file
    file.close()
    print("Closed File: ", dataFileName)

# name:     readScale
# inputs:   none
# outputs:  data - the scale weight reading
# Notes:    takes 2 readings of the scale and returns the average value
def readScale():
    global file
    data = (hx.get_weight_mean(2))
    return data

# name:     endScale
# inputs:   none
# outputs:  none
# Notes:    clean up loose ends when program ends       
def endScale():
    closeFile()
    
