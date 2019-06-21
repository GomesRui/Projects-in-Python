#NOTE: PINs 4 and 2  have been killed in action

#Libraries
import RPi.GPIO as GPIO
import time
import Adafruit_CharLCD as LCD
import math
import array
from enum import Enum


############## / Global variables \ ##############

#CUSTOMIZABLE VALUES#
size = 5 #how many times to make it detect
offset = 2 #offset to compare the 3 distance inputs
decimalPrecision = 2 #How many decimals precision to use - 1, 2, 3 ...
rangeMax = 100000000 #how further we want the 
#####################

pos = 0
arrayDistance = [None] * size

class Modes(Enum): #enum to define the possible modes
    Hold = 1
    Active = 2
    Off = 0

Mode = Modes.Off #initial mode


############## / Hardware Configuration \ ##############

#GPIO Mode (BOARD / BCM) = BOARD as number of pin + BCM = GPIO numbers
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
 
#set GPIO Pins
GPIO_TRIGGER = 6
GPIO_ECHO = 12
GPIO_LASER = 26
GPIO_LIGHT_DETECT = 5
GPIO_LIGHT_HOLD = 13
GPIO_LIGHT_OFF = 0
GPIO_END = 14
GPIO_MODE = 10

# Raspberry Pi pin setup for LCD
lcd_rs = 27
lcd_en = 24
lcd_d4 = 23
lcd_d5 = 17
lcd_d6 = 18
lcd_d7 = 22
lcd_backlight = 19

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows = 2

#set LCD
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setup(GPIO_LASER, GPIO.OUT, initial=False)

#set Output for Lights
GPIO.setup(GPIO_LIGHT_DETECT, GPIO.OUT, initial=False)
GPIO.setup(GPIO_LIGHT_HOLD, GPIO.OUT, initial=False)
GPIO.setup(GPIO_LIGHT_OFF, GPIO.OUT, initial=False)

#set Input for buttons
GPIO.setup(GPIO_END, GPIO.IN)
GPIO.setup(GPIO_MODE, GPIO.IN)


############## / Global Methods \ ##############

def distance():
    
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2

    return distance


#Function to define onHold mode behavior
def onHold():

    global arrayDistance
    arrayDistance = [] #Clearing the array
    
    print ("On hold...")
    lcd.message ("Hold mode")
    GPIO.output(GPIO_LASER, True)
    GPIO.output(GPIO_LIGHT_HOLD, True)
    GPIO.output(GPIO_LIGHT_DETECT, False)
    GPIO.output(GPIO_LIGHT_OFF, False)
        
    while (True): #In hold mode until button is pressed
        time.sleep(1)
        
        if (GPIO.input(GPIO_MODE) == True):
              break

        elif (GPIO.input(GPIO_END) == True and GPIO.input(GPIO_MODE) == True):
            return Modes.Off

    return Modes.Active


#Function to define in active mode behavior
def inActive():

    global Mode

    print ("In Active...")
    lcd.message ("Active mode")
    time.sleep(2.0)
    GPIO.output(GPIO_LIGHT_OFF, False)
    GPIO.output(GPIO_LIGHT_HOLD, False)
    GPIO.output(GPIO_LASER, False)
    #lcd.backlight(True)

    while (True):

        blinkLED() #blink red LED = detecting...
        useRuler() #to apply the function ruler
        lcd.clear()
        time.sleep(0.5)
        
        if (GPIO.input(GPIO_MODE) == True or Mode == Modes.Hold):
            break
        
        elif (GPIO.input(GPIO_END) == True and GPIO.input(GPIO_MODE) == True):
            return Modes.Off
              
    return Modes.Hold


#Function to define in active mode behavior
def inOff():
    
    print ("Turned off!")
    lcd.message ("Off mode")
    #lcd.blink(True)
    #lcd.blink(False)
    GPIO.output((GPIO_TRIGGER, GPIO_LASER,GPIO_LIGHT_HOLD, GPIO_LIGHT_DETECT,),False)
    GPIO.output(GPIO_LIGHT_OFF, True)
    #lcd.backlight(False)
    time.sleep(2)
    
    while (True): #In Off mode until both buttons are pressed
        time.sleep(0.5)
                
        if (GPIO.input(GPIO_MODE) == True and GPIO.input(GPIO_END) == False):
            return Modes.Hold
        
        else:
            return Modes.Off
    
    
#Function to define the mode the solution is in
def Modding(toMode):

    if (toMode == Modes.Hold):
        toMode = onHold()
        
    elif (toMode == Modes.Active):
        toMode = inActive()

    elif (toMode == Modes.Off):
        toMode = inOff()

    else:
        print("Error! Unknown mode!");
        theEnd()

    lcd.clear()    
    return toMode
    

def blinkLED():
    
    GPIO.output(GPIO_LIGHT_DETECT, True)
    time.sleep(0.1)
    GPIO.output(GPIO_LIGHT_DETECT, False)


def averageDistance(toAverage):

    global decimalPrecision

    averagingArray = 0
    roundingAvg = 0
    
    for i in range(0, len(toAverage)):
        averagingArray += toAverage[i]

    roundingAvg = round((averagingArray/len(toAverage)),decimalPrecision)
    
    return roundingAvg


def isDetectable(toDetect):

    isDetected = False
    posToCompare = 0

    for i in range(0, len(toDetect)):

        posToCompare = ((i+1) % len(toDetect)) #restart the position by doing 1 > 2 > 0)
        print("array: pos " + str(i) + "value " + str(toDetect[i]))
        #if ((lastresults[0] > (lastresults[1] - offset)) & (lastresults[0] < (lastresults[1] + offset)) & (lastresults[1] > (lastresults[2] - offset)) & (lastresults[1] < (lastresults[2] + offset))):            
        if (toDetect[i] > (toDetect[posToCompare] - offset)) & (toDetect[i] < (toDetect[posToCompare] + offset)):
                        
            isDetected = True
                       
        else:
                
            isDetected = False
            toDetect.pop(i)
            break      
       
    return isDetected


def buildArray(toBuild):

    global size
    global Mode
    
    valueToAdd = distance() #grab the distance from the ultrasonic sensor

    if (valueToAdd >= rangeMax):
        #Mode = Modes.Hold // too hardcore!
        lcd.clear()
        lcd.message("Range exceeded!")
        time.sleep(2)
        lcd.clear()

    if (len(toBuild) >= size):
        toBuild.pop(0)
        
    toBuild.append(valueToAdd)
        
    return toBuild


def useRuler():   

    global size
    global arrayDistance
    global offset

    detected = False
    
    arrayDistance = buildArray(arrayDistance)
    #arrayDistance[pos] = trigger #Building aray
   
    if ((arrayDistance[0] != None) and (len(arrayDistance) == size) and Mode != Modes.Hold): #check if the array is complete
        
        if (isDetectable(arrayDistance)):

            dist = averageDistance(arrayDistance) # average the distances captured
            lcddist = str(dist)
            print("Distance: " + lcddist)
            lcd.message("Distance: \n" + lcddist + "cm") 
            GPIO.output(GPIO_LIGHT_DETECT, True)
            time.sleep(3)
            lcd.clear()
                        
        else:

            GPIO.output(GPIO_LIGHT_DETECT, False)

    
def theEnd():

    lcd.message("Finishing...")
    GPIO.cleanup()
    time.sleep(5)
    exit()

    
############## / Main function \ ##############

if __name__ == '__main__':

    global Mode
    
    try:
                     
        print ("Starting Digital Ruler...")
        print (Mode)
        while (GPIO.input(GPIO_END) == 0 or Mode != Modes.Off):

            if (GPIO.input(GPIO_END) == 1):
                Mode = Modes.Off
                
            Mode = Modding(Mode) #Will choose which mode to be in
            time.sleep(1)
 
    # Reset by pressing CTRL + C
    except KeyboardInterrupt:

        print("Interrupted the code incorrectly")

    except Exception as e: #Exception thrown

        print("Another type of exception occurred: ", e)

    finally:
        
        theEnd()
[MASTER]

# A comma-separated list of package or module names from where C extensions may
# be loaded. Extensions are loading into the active Python interpreter and may
# run arbitrary code
extension-pkg-whitelist=

# Add files or directories to the blacklist. They should be base names, not
# paths.
ignore=CVS

# Add files or directories matching the regex patterns to the blacklist. The
# regex matches against base names, not paths.
ignore-patterns=

# Python code to execute, usually for sys.path manipulation such as
# pygtk.require().
#init-hook=

# Use multiple processes to speed up Pylint.
# jobs=1
jobs=2

# List of plugins (as comma separated values of python modules names) to load,
# usually to register additional checkers.
load-plugins=

# Pickle collected data for later comparisons.
persistent=yes

# Specify a configuration file.
#rcfile=

# Allow loading of arbitrary C extensions. Extensions are imported into the
# active Python interpreter and may run arbitrary code.
unsafe-load-any-extension=no


[MESSAGES CONTROL]

# Only show warnings with the listed confidence levels. Leave empty to show
# all. Valid levels: HIGH, INFERENCE, INFERENCE_FAILURE, UNDEFINED
confidence=

# Disable the message, report, category or checker with the given id(s). You
# can either give multiple identifiers separated by comma (,) or put this
# option multiple times (only on the command line, not in the configuration
# file where it should appear only once).You can also use "--disable=all" to
# disable everything first and then reenable specific checks. For example, if
# you want to run only the similarities checker, you can use "--disable=all
# --enable=similarities". If you want to run only the classes checker, but have
# no Warning level messages displayed, use"--disable=all --enable=classes
# --disable=W"
# disable=import-error,print-statement,parameter-unpacking,unpacking-in-except,old-raise-syntax,backtick,long-suffix,old-ne-operator,old-octal-literal,import-star-module-level,raw-checker-failed,bad-inline-option,locally-disabled,locally-enabled,file-ignored,suppressed-message,useless-suppression,deprecated-pragma,apply-builtin,basestring-builtin,buffer-builtin,cmp-builtin,coerce-builtin,execfile-builtin,file-builtin,long-builtin,raw_input-builtin,reduce-builtin,standarderror-builtin,unicode-builtin,xrange-builtin,coerce-method,delslice-method,getslice-method,setslice-method,no-absolute-import,old-division,dict-iter-method,dict-view-method,next-method-called,metaclass-assignment,indexing-exception,raising-string,reload-builtin,oct-method,hex-method,nonzero-method,cmp-method,input-builtin,round-builtin,intern-builtin,unichr-builtin,map-builtin-not-iterating,zip-builtin-not-iterating,range-builtin-not-iterating,filter-builtin-not-iterating,using-cmp-argument,eq-without-hash,div-method,idiv-method,rdiv-method,exception-message-attribute,invalid-str-codec,sys-max-int,bad-python3-import,deprecated-string-function,deprecated-str-translate-call
disable=print-statement,parameter-unpacking,unpacking-in-except,old-raise-syntax,backtick,long-suffix,old-ne-operator,old-octal-literal,import-star-module-level,raw-checker-failed,bad-inline-option,locally-disabled,locally-enabled,file-ignored,suppressed-message,useless-suppression,deprecated-pragma,apply-builtin,basestring-builtin,buffer-builtin,cmp-builtin,coerce-builtin,execfile-builtin,file-builtin,long-builtin,raw_input-builtin,reduce-builtin,standarderror-builtin,unicode-builtin,xrange-builtin,coerce-method,delslice-method,getslice-method,setslice-method,no-absolute-import,old-division,dict-iter-method,dict-view-method,next-method-called,metaclass-assignment,indexing-exception,raising-string,reload-builtin,oct-method,hex-method,nonzero-method,cmp-method,input-builtin,round-builtin,intern-builtin,unichr-builtin,map-builtin-not-iterating,zip-builtin-not-iterating,range-builtin-not-iterating,filter-builtin-not-iterating,using-cmp-argument,eq-without-hash,div-method,idiv-method,rdiv-method,exception-message-attribute,invalid-str-codec,sys-max-int,bad-python3-import,deprecated-string-function,deprecated-str-translate-call,import-error,attribute-defined-outside-init

# Enable the message, report, category or checker with the given id(s). You can
# either give multiple identifier separated by comma (,) or put this option
# multiple time (only on the command line, not in the configuration file where
# it should appear only once). See also the "--disable" option for examples.
enable=


[REPORTS]

# Python expression which should return a note less than 10 (10 is the highest
# note). You have access to the variables errors warning, statement which
# respectively contain the number of errors / warnings messages and the total
# number of statements analyzed. This is used by the global evaluation report
# (RP0004).
evaluation=10.0 - ((float(5 * error + warning + refactor + convention) / statement) * 10)

# Template used to display messages. This is a python new-style format string
# used to format the message information. See doc for all details
#msg-template=

# Set the output format. Available formats are text, parseable, colorized, json
# and msvs (visual studio).You can also give a reporter class, eg
# mypackage.mymodule.MyReporterClass.
output-format=text

# Tells whether to display a full report or only the messages
reports=no

# Activate the evaluation score.
score=yes


[REFACTORING]

# Maximum number of nested blocks for function / method body
max-nested-blocks=5


[LOGGING]

# Logging modules to check that the string format arguments are in logging
# function parameter format
logging-modules=logging


[SPELLING]

# Spelling dictionary name. Available dictionaries: none. To make it working
# install python-enchant package.
spelling-dict=

# List of comma separated words that should not be checked.
spelling-ignore-words=

# A path to a file that contains private dictionary; one word per line.
spelling-private-dict-file=

# Tells whether to store unknown words to indicated private dictionary in
# --spelling-private-dict-file option instead of raising a message.
spelling-store-unknown-words=no


[MISCELLANEOUS]

# List of note tags to take in consideration, separated by a comma.
# notes=FIXME,XXX,TODO
notes=FIXME,XXX


[TYPECHECK]

# List of decorators that produce context managers, such as
# contextlib.contextmanager. Add to this list to register other decorators that
# produce valid context managers.
contextmanager-decorators=contextlib.contextmanager

# List of members which are set dynamically and missed by pylint inference
# system, and so shouldn't trigger E1101 when accessed. Python regular
# expressions are accepted.
generated-members=

# Tells whether missing members accessed in mixin class should be ignored. A
# mixin class is detected if its name ends with "mixin" (case insensitive).
ignore-mixin-members=yes

# This flag controls whether pylint should warn about no-member and similar
# checks whenever an opaque object is returned when inferring. The inference
# can return multiple potential results while evaluating a Python object, but
# some branches might not be evaluated, which results in partial inference. In
# that case, it might be useful to still emit no-member and other checks for
# the rest of the inferred objects.
ignore-on-opaque-inference=yes

# List of class names for which member attributes should not be checked (useful
# for classes with dynamically set attributes). This supports the use of
# qualified names.
ignored-classes=optparse.Values,thread._local,_thread._local

# List of module names for which member attributes should not be checked
# (useful for modules/projects where namespaces are manipulated during runtime
# and thus existing member attributes cannot be deduced by static analysis. It
# supports qualified module names, as well as Unix pattern matching.
ignored-modules=

# Show a hint with possible names when a member name was not found. The aspect
# of finding the hint is based on edit distance.
missing-member-hint=yes

# The minimum edit distance a name should have in order to be considered a
# similar match for a missing member name.
missing-member-hint-distance=1

# The total number of similar names that should be taken in consideration when
# showing a hint for a missing member.
missing-member-max-choices=1


[VARIABLES]

# List of additional names supposed to be defined in builtins. Remember that
# you should avoid to define new builtins when possible.
additional-builtins=

# Tells whether unused global variables should be treated as a violation.
allow-global-unused-variables=yes

# List of strings which can identify a callback function by name. A callback
# name must start or end with one of those strings.
callbacks=cb_,_cb

# A regular expression matching the name of dummy variables (i.e. expectedly
# not used).
dummy-variables-rgx=_+$|(_[a-zA-Z0-9_]*[a-zA-Z0-9]+?$)|dummy|^ignored_|^unused_

# Argument names that match this expression will be ignored. Default to name
# with leading underscore
ignored-argument-names=_.*|^ignored_|^unused_

# Tells whether we should check for unused import in __init__ files.
init-import=no

# List of qualified module names which can have objects that can redefine
# builtins.
redefining-builtins-modules=six.moves,future.builtins


[FORMAT]

# Expected format of line ending, e.g. empty (any line ending), LF or CRLF.
# expected-line-ending-format=
expected-line-ending-format=LF

# Regexp for a line that is allowed to be longer than the limit.
ignore-long-lines=^\s*(# )?<?https?://\S+>?$

# Number of spaces of indent required inside a hanging  or continued line.
indent-after-paren=4

# String used as indentation unit. This is usually "    " (4 spaces) or "\t" (1
# tab).
indent-string='    '

# Maximum number of characters on a single line.
max-line-length=100

# Maximum number of lines in a module
max-module-lines=1000

# List of optional constructs for which whitespace checking is disabled. `dict-
# separator` is used to allow tabulation in dicts, etc.: {1  : 1,\n222: 2}.
# `trailing-comma` allows a space between comma and closing bracket: (a, ).
# `empty-line` allows space-only lines.
no-space-check=trailing-comma,dict-separator

# Allow the body of a class to be on the same line as the declaration if body
# contains single statement.
single-line-class-stmt=no

# Allow the body of an if to be on the same line as the test if there is no
# else.
single-line-if-stmt=no


[SIMILARITIES]

# Ignore comments when computing similarities.
ignore-comments=yes

# Ignore docstrings when computing similarities.
ignore-docstrings=yes

# Ignore imports when computing similarities.
ignore-imports=no

# Minimum lines number of a similarity.
min-similarity-lines=4


[BASIC]

# Naming hint for argument names
argument-name-hint=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$

# Regular expression matching correct argument names
argument-rgx=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$

# Naming hint for attribute names
attr-name-hint=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$

# Regular expression matching correct attribute names
attr-rgx=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$

# Bad variable names which should always be refused, separated by a comma
bad-names=foo,bar,baz,toto,tutu,tata

# Naming hint for class attribute names
class-attribute-name-hint=([A-Za-z_][A-Za-z0-9_]{2,30}|(__.*__))$

# Regular expression matching correct class attribute names
class-attribute-rgx=([A-Za-z_][A-Za-z0-9_]{2,30}|(__.*__))$

# Naming hint for class names
# class-name-hint=[A-Z_][a-zA-Z0-9]+$
class-name-hint=[A-Z_][a-zA-Z0-9_]+$

# Regular expression matching correct class names
# class-rgx=[A-Z_][a-zA-Z0-9]+$
class-rgx=[A-Z_][a-zA-Z0-9_]+$

# Naming hint for constant names
const-name-hint=(([A-Z_][A-Z0-9_]*)|(__.*__))$

# Regular expression matching correct constant names
const-rgx=(([A-Z_][A-Z0-9_]*)|(__.*__))$

# Minimum line length for functions/classes that require docstrings, shorter
# ones are exempt.
docstring-min-length=-1

# Naming hint for function names
function-name-hint=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$

# Regular expression matching correct function names
function-rgx=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$

# Good variable names which should always be accepted, separated by a comma
# good-names=i,j,k,ex,Run,_
good-names=r,g,b,w,i,j,k,n,x,y,z,ex,ok,Run,_

# Include a hint for the correct naming format with invalid-name
include-naming-hint=no

# Naming hint for inline iteration names
inlinevar-name-hint=[A-Za-z_][A-Za-z0-9_]*$

# Regular expression matching correct inline iteration names
inlinevar-rgx=[A-Za-z_][A-Za-z0-9_]*$

# Naming hint for method names
method-name-hint=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$

# Regular expression matching correct method names
method-rgx=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$

# Naming hint for module names
module-name-hint=(([a-z_][a-z0-9_]*)|([A-Z][a-zA-Z0-9]+))$

# Regular expression matching correct module names
module-rgx=(([a-z_][a-z0-9_]*)|([A-Z][a-zA-Z0-9]+))$

# Colon-delimited sets of names that determine each other's naming style when
# the name regexes allow several styles.
name-group=

# Regular expression which should only match function or class names that do
# not require a docstring.
no-docstring-rgx=^_

# List of decorators that produce properties, such as abc.abstractproperty. Add
# to this list to register other decorators that produce valid properties.
property-classes=abc.abstractproperty

# Naming hint for variable names
variable-name-hint=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$

# Regular expression matching correct variable names
variable-rgx=(([a-z][a-z0-9_]{2,30})|(_[a-z0-9_]*))$


[IMPORTS]

# Allow wildcard imports from modules that define __all__.
allow-wildcard-with-all=no

# Analyse import fallback blocks. This can be used to support both Python 2 and
# 3 compatible code, which means that the block might have code that exists
# only in one or another interpreter, leading to false positives when analysed.
analyse-fallback-blocks=no

# Deprecated modules which should not be used, separated by a comma
deprecated-modules=optparse,tkinter.tix

# Create a graph of external dependencies in the given file (report RP0402 must
# not be disabled)
ext-import-graph=

# Create a graph of every (i.e. internal and external) dependencies in the
# given file (report RP0402 must not be disabled)
import-graph=

# Create a graph of internal dependencies in the given file (report RP0402 must
# not be disabled)
int-import-graph=

# Force import order to recognize a module as part of the standard
# compatibility libraries.
known-standard-library=

# Force import order to recognize a module as part of a third party library.
known-third-party=enchant


[CLASSES]

# List of method names used to declare (i.e. assign) instance attributes.
defining-attr-methods=__init__,__new__,setUp

# List of member names, which should be excluded from the protected access
# warning.
exclude-protected=_asdict,_fields,_replace,_source,_make

# List of valid names for the first argument in a class method.
valid-classmethod-first-arg=cls

# List of valid names for the first argument in a metaclass class method.
valid-metaclass-classmethod-first-arg=mcs


[DESIGN]

# Maximum number of arguments for function / method
max-args=5

# Maximum number of attributes for a class (see R0902).
# max-attributes=7
max-attributes=11

# Maximum number of boolean expressions in a if statement
max-bool-expr=5

# Maximum number of branch for function / method body
max-branches=12

# Maximum number of locals for function / method body
max-locals=15

# Maximum number of parents for a class (see R0901).
max-parents=7

# Maximum number of public methods for a class (see R0904).
max-public-methods=20

# Maximum number of return / yield for function / method body
max-returns=6

# Maximum number of statements in function / method body
max-statements=50

# Minimum number of public methods for a class (see R0903).
min-public-methods=1


[EXCEPTIONS]

# Exceptions that will emit a warning when being caught. Defaults to
# "Exception"
overgeneral-exceptions=Exception
The MIT License (MIT)

Copyright (c) 2016 Adafruit Industries

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
# Copyright (c) 2016 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""I2C interface that mimics the Python SMBus API."""

from ctypes import c_uint8, c_uint16, c_uint32, cast, pointer, POINTER
from ctypes import create_string_buffer, Structure
from fcntl import ioctl
import struct

# I2C C API constants (from linux kernel headers)
# pylint: disable=bad-whitespace
I2C_M_TEN             = 0x0010  # this is a ten bit chip address
I2C_M_RD              = 0x0001  # read data, from slave to master
I2C_M_STOP            = 0x8000  # if I2C_FUNC_PROTOCOL_MANGLING
I2C_M_NOSTART         = 0x4000  # if I2C_FUNC_NOSTART
I2C_M_REV_DIR_ADDR    = 0x2000  # if I2C_FUNC_PROTOCOL_MANGLING
I2C_M_IGNORE_NAK      = 0x1000  # if I2C_FUNC_PROTOCOL_MANGLING
I2C_M_NO_RD_ACK       = 0x0800  # if I2C_FUNC_PROTOCOL_MANGLING
I2C_M_RECV_LEN        = 0x0400  # length will be first received byte

I2C_SLAVE             = 0x0703  # Use this slave address
I2C_SLAVE_FORCE       = 0x0706  # Use this slave address, even if
                                # is already in use by a driver!
I2C_TENBIT            = 0x0704  # 0 for 7 bit addrs, != 0 for 10 bit
I2C_FUNCS             = 0x0705  # Get the adapter functionality mask
I2C_RDWR              = 0x0707  # Combined R/W transfer (one STOP only)
I2C_PEC               = 0x0708  # != 0 to use PEC with SMBus
I2C_SMBUS             = 0x0720  # SMBus transfer
# pylint: enable=bad-whitespace


# ctypes versions of I2C structs defined by kernel.
# Tone down pylint for the Python classes that mirror C structs.
#pylint: disable=invalid-name,too-few-public-methods
class i2c_msg(Structure):
    """Linux i2c_msg struct."""
    _fields_ = [
        ('addr', c_uint16),
        ('flags', c_uint16),
        ('len', c_uint16),
        ('buf', POINTER(c_uint8))
    ]

class i2c_rdwr_ioctl_data(Structure): #pylint: disable=invalid-name
    """Linux i2c data struct."""
    _fields_ = [
        ('msgs', POINTER(i2c_msg)),
        ('nmsgs', c_uint32)
    ]
#pylint: enable=invalid-name,too-few-public-methods

def make_i2c_rdwr_data(messages):
    """Utility function to create and return an i2c_rdwr_ioctl_data structure
    populated with a list of specified I2C messages.  The messages parameter
    should be a list of tuples which represent the individual I2C messages to
    send in this transaction.  Tuples should contain 4 elements: address value,
    flags value, buffer length, ctypes c_uint8 pointer to buffer.
    """
    # Create message array and populate with provided data.
    msg_data_type = i2c_msg*len(messages)
    msg_data = msg_data_type()
    for i, message in enumerate(messages):
        msg_data[i].addr = message[0] & 0x7F
        msg_data[i].flags = message[1]
        msg_data[i].len = message[2]
        msg_data[i].buf = message[3]
    # Now build the data structure.
    data = i2c_rdwr_ioctl_data()
    data.msgs = msg_data
    data.nmsgs = len(messages)
    return data

# Create an interface that mimics the Python SMBus API.
class SMBus(object): # pylint: disable=useless-object-inheritance
    """I2C interface that mimics the Python SMBus API but is implemented with
    pure Python calls to ioctl and direct /dev/i2c device access.
    """

    def __init__(self, bus=None):
        """Create a new smbus instance.  Bus is an optional parameter that
        specifies the I2C bus number to use, for example 1 would use device
        /dev/i2c-1.  If bus is not specified then the open function should be
        called to open the bus.
        """
        self._device = None
        if bus is not None:
            self.open(bus)

    def __del__(self):
        """Clean up any resources used by the SMBus instance."""
        self.close()

    def __enter__(self):
        """Context manager enter function."""
        # Just return this object so it can be used in a with statement, like
        # with SMBus(1) as bus:
        #     # do stuff!
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit function, ensures resources are cleaned up."""
        self.close()
        return False  # Don't suppress exceptions.

    def open(self, bus):
        """Open the smbus interface on the specified bus."""
        # Close the device if it's already open.
        if self._device is not None:
            self.close()
        # Try to open the file for the specified bus.  Must turn off buffering
        # or else Python 3 fails (see: https://bugs.python.org/issue20074)
        self._device = open('/dev/i2c-{0}'.format(bus), 'r+b', buffering=0)
        # TODO: Catch IOError and throw a better error message that describes
        # what's wrong (i.e. I2C may not be enabled or the bus doesn't exist).

    def close(self):
        """Close the smbus connection.  You cannot make any other function
        calls on the bus unless open is called!"""
        if self._device is not None:
            self._device.close()
            self._device = None

    def _select_device(self, addr):
        """Set the address of the device to communicate with on the I2C bus."""
        ioctl(self._device.fileno(), I2C_SLAVE, addr & 0x7F)

    def read_byte(self, addr):
        """Read a single byte from the specified device."""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        self._select_device(addr)
        return ord(self._device.read(1))

    def read_bytes(self, addr, number):
        """Read many bytes from the specified device."""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        self._select_device(addr)
        return self._device.read(number)

    def read_byte_data(self, addr, cmd):
        """Read a single byte from the specified cmd register of the device."""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ctypes values to marshall between ioctl and Python.
        reg = c_uint8(cmd)
        result = c_uint8()
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 1, pointer(reg)),             # Write cmd register.
            (addr, I2C_M_RD, 1, pointer(result))    # Read 1 byte as result.
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)
        return result.value

    def read_word_data(self, addr, cmd):
        """Read a word (2 bytes) from the specified cmd register of the device.
        Note that this will interpret data using the endianness of the processor
        running Python (typically little endian)!
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ctypes values to marshall between ioctl and Python.
        reg = c_uint8(cmd)
        result = c_uint16()
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 1, pointer(reg)),             # Write cmd register.
            (addr, I2C_M_RD, 2, cast(pointer(result), POINTER(c_uint8)))   # Read word (2 bytes).
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)
        return result.value

    def read_block_data(self, addr, cmd):
        """Perform a block read from the specified cmd register of the device.
        The amount of data read is determined by the first byte send back by
        the device.  Data is returned as a bytearray.
        """
        # TODO: Unfortunately this will require calling the low level I2C
        # access ioctl to trigger a proper read_block_data.  The amount of data
        # returned isn't known until the device starts responding so an I2C_RDWR
        # ioctl won't work.
        raise NotImplementedError()

    def read_i2c_block_data(self, addr, cmd, length=32):
        """Perform a read from the specified cmd register of device.  Length number
        of bytes (default of 32) will be read and returned as a bytearray.
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ctypes values to marshall between ioctl and Python.
        reg = c_uint8(cmd)
        result = create_string_buffer(length)
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 1, pointer(reg)),             # Write cmd register.
            (addr, I2C_M_RD, length, cast(result, POINTER(c_uint8)))   # Read data.
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)
        return bytearray(result.raw)  # Use .raw instead of .value which will stop at a null byte!

    def write_quick(self, addr):
        """Write a single byte to the specified device."""
        # What a strange function, from the python-smbus source this appears to
        # just write a single byte that initiates a write to the specified device
        # address (but writes no data!).  The functionality is duplicated below
        # but the actual use case for this is unknown.
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 0, None),  # Write with no data.
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)

    def write_byte(self, addr, val):
        """Write a single byte to the specified device."""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        self._select_device(addr)
        data = bytearray(1)
        data[0] = val & 0xFF
        self._device.write(data)

    def write_bytes(self, addr, buf):
        """Write many bytes to the specified device. buf is a bytearray"""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        self._select_device(addr)
        self._device.write(buf)

    def write_byte_data(self, addr, cmd, val):
        """Write a byte of data to the specified cmd register of the device.
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Construct a string of data to send with the command register and byte value.
        data = bytearray(2)
        data[0] = cmd & 0xFF
        data[1] = val & 0xFF
        # Send the data to the device.
        self._select_device(addr)
        self._device.write(data)

    def write_word_data(self, addr, cmd, val):
        """Write a word (2 bytes) of data to the specified cmd register of the
        device.  Note that this will write the data in the endianness of the
        processor running Python (typically little endian)!
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Construct a string of data to send with the command register and word value.
        data = struct.pack('=BH', cmd & 0xFF, val & 0xFFFF)
        # Send the data to the device.
        self._select_device(addr)
        self._device.write(data)

    def write_block_data(self, addr, cmd, vals):
        """Write a block of data to the specified cmd register of the device.
        The amount of data to write should be the first byte inside the vals
        string/bytearray and that count of bytes of data to write should follow
        it.
        """
        # Just use the I2C block data write to write the provided values and
        # their length as the first byte.
        data = bytearray(len(vals)+1)
        data[0] = len(vals) & 0xFF
        data[1:] = vals[0:]
        self.write_i2c_block_data(addr, cmd, data)

    def write_i2c_block_data(self, addr, cmd, vals):
        """Write a buffer of data to the specified cmd register of the device.
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Construct a string of data to send, including room for the command register.
        data = bytearray(len(vals)+1)
        data[0] = cmd & 0xFF  # Command register at the start.
        data[1:] = vals[0:]   # Copy in the block data (ugly but necessary to ensure
                              # the entire write happens in one transaction).
        # Send the data to the device.
        self._select_device(addr)
        self._device.write(data)

    def process_call(self, addr, cmd, val):
        """Perform a smbus process call by writing a word (2 byte) value to
        the specified register of the device, and then reading a word of response
        data (which is returned).
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ctypes values to marshall between ioctl and Python.
        data = create_string_buffer(struct.pack('=BH', cmd, val))
        result = c_uint16()
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 3, cast(pointer(data), POINTER(c_uint8))),          # Write data.
            (addr, I2C_M_RD, 2, cast(pointer(result), POINTER(c_uint8)))  # Read word (2 bytes).
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)
        # Note the python-smbus code appears to have a rather serious bug and
        # does not return the result value!  This is fixed below by returning it.
        return result.value
sudo: false
dist: trusty
language: python
python:
- '2.7'
- '3.6'
install:
- pip install -r requirements.txt
- pip install pylint
script:
- pylint Adafruit_PureIO/smbus.py
deploy:
  provider: pypi
  user: adafruit-travis
  password:
    secure: WF+gNAM1RJd73JwH2oaoOz8fpAlfEhT7O6fV9fzX7qyryRCRgXPQdTvsNZgcjJ+rjkAZvIB4pLKDI2ZRxUIs0wonvDTfqRRs0N0aKxshVZZo15+Xdy2NkS5/HhBGMZpVeRWj5k2a70vxmyrbwnzlEaqeT4eiDFVpUYJsAnJkijWfWJSxL1Rl3nuG4D/HF+QTUoxHZBVoqQec4eAuy0/k7dpE0feaRiIdAYokyd2PVe8k6Ii4zmcUwDGPwsky064CLtuRaG5asMeeFQ3tlLi8jaTEcVkkYMTcXwMhX+9fkwaxgtfWH3qFnAnUxODWuuLpp5ZfTaKLKnMx74+RSgJVGD1byblcaY3LVBjqXKrY/arWUsHreoE8a/BLp5sAisUlnLXkF8u+NzrL/NqJhoJUwTLb6H5JOHtjvk/qnvuNgD77bqqJfv7EyhW9kf1TUpTJPtsNpTA4N0DOlQ/nnp0O111QLjJvRi/S/98d/Na8W2o6KX/2ytKmU5v1RnWpcnjP6xqDYzpoYOj7VjFyG/LTk+TACDOqm5uLRDvhFsVrjluS6d9CcjFPtXWEgMMCdIkLF4quPqe+QB7IWnfMrCbSJZJh2ZYowKQVyZqZ/5eCSetTuI93PD8ZVUmWDFnYE/oCCPA+GhJno6Zmxs1dtGjFFwAV7H6jPjaNmZTRWvX514k=
  on:
    tags: true
    python: '3.6'
#!/usr/bin/env python
"""Bootstrap setuptools installation

To use setuptools in your package's setup.py, include this
file in the same directory and add this to the top of your setup.py::

    from ez_setup import use_setuptools
    use_setuptools()

To require a specific version of setuptools, set a download
mirror, or use an alternate download directory, simply supply
the appropriate options to ``use_setuptools()``.

This file can also be run as a script to install or upgrade setuptools.
"""
import os
import shutil
import sys
import tempfile
import zipfile
import optparse
import subprocess
import platform
import textwrap
import contextlib

from distutils import log

try:
    from site import USER_SITE
except ImportError:
    USER_SITE = None

DEFAULT_VERSION = "3.5.1"
DEFAULT_URL = "https://pypi.python.org/packages/source/s/setuptools/"

def _python_cmd(*args):
    """
    Return True if the command succeeded.
    """
    args = (sys.executable,) + args
    return subprocess.call(args) == 0


def _install(archive_filename, install_args=()):
    with archive_context(archive_filename):
        # installing
        log.warn('Installing Setuptools')
        if not _python_cmd('setup.py', 'install', *install_args):
            log.warn('Something went wrong during the installation.')
            log.warn('See the error message above.')
            # exitcode will be 2
            return 2


def _build_egg(egg, archive_filename, to_dir):
    with archive_context(archive_filename):
        # building an egg
        log.warn('Building a Setuptools egg in %s', to_dir)
        _python_cmd('setup.py', '-q', 'bdist_egg', '--dist-dir', to_dir)
    # returning the result
    log.warn(egg)
    if not os.path.exists(egg):
        raise IOError('Could not build the egg.')


def get_zip_class():
    """
    Supplement ZipFile class to support context manager for Python 2.6
    """
    class ContextualZipFile(zipfile.ZipFile):
        def __enter__(self):
            return self
        def __exit__(self, type, value, traceback):
            self.close
    return zipfile.ZipFile if hasattr(zipfile.ZipFile, '__exit__') else \
        ContextualZipFile


@contextlib.contextmanager
def archive_context(filename):
    # extracting the archive
    tmpdir = tempfile.mkdtemp()
    log.warn('Extracting in %s', tmpdir)
    old_wd = os.getcwd()
    try:
        os.chdir(tmpdir)
        with get_zip_class()(filename) as archive:
            archive.extractall()

        # going in the directory
        subdir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        os.chdir(subdir)
        log.warn('Now working in %s', subdir)
        yield

    finally:
        os.chdir(old_wd)
        shutil.rmtree(tmpdir)


def _do_download(version, download_base, to_dir, download_delay):
    egg = os.path.join(to_dir, 'setuptools-%s-py%d.%d.egg'
                       % (version, sys.version_info[0], sys.version_info[1]))
    if not os.path.exists(egg):
        archive = download_setuptools(version, download_base,
                                      to_dir, download_delay)
        _build_egg(egg, archive, to_dir)
    sys.path.insert(0, egg)

    # Remove previously-imported pkg_resources if present (see
    # https://bitbucket.org/pypa/setuptools/pull-request/7/ for details).
    if 'pkg_resources' in sys.modules:
        del sys.modules['pkg_resources']

    import setuptools
    setuptools.bootstrap_install_from = egg


def use_setuptools(version=DEFAULT_VERSION, download_base=DEFAULT_URL,
        to_dir=os.curdir, download_delay=15):
    to_dir = os.path.abspath(to_dir)
    rep_modules = 'pkg_resources', 'setuptools'
    imported = set(sys.modules).intersection(rep_modules)
    try:
        import pkg_resources
    except ImportError:
        return _do_download(version, download_base, to_dir, download_delay)
    try:
        pkg_resources.require("setuptools>=" + version)
        return
    except pkg_resources.DistributionNotFound:
        return _do_download(version, download_base, to_dir, download_delay)
    except pkg_resources.VersionConflict as VC_err:
        if imported:
            msg = textwrap.dedent("""
                The required version of setuptools (>={version}) is not available,
                and can't be installed while this script is running. Please
                install a more recent version first, using
                'easy_install -U setuptools'.

                (Currently using {VC_err.args[0]!r})
                """).format(VC_err=VC_err, version=version)
            sys.stderr.write(msg)
            sys.exit(2)

        # otherwise, reload ok
        del pkg_resources, sys.modules['pkg_resources']
        return _do_download(version, download_base, to_dir, download_delay)

def _clean_check(cmd, target):
    """
    Run the command to download target. If the command fails, clean up before
    re-raising the error.
    """
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        if os.access(target, os.F_OK):
            os.unlink(target)
        raise

def download_file_powershell(url, target):
    """
    Download the file at url to target using Powershell (which will validate
    trust). Raise an exception if the command cannot complete.
    """
    target = os.path.abspath(target)
    cmd = [
        'powershell',
        '-Command',
        "(new-object System.Net.WebClient).DownloadFile(%(url)r, %(target)r)" % vars(),
    ]
    _clean_check(cmd, target)

def has_powershell():
    if platform.system() != 'Windows':
        return False
    cmd = ['powershell', '-Command', 'echo test']
    devnull = open(os.path.devnull, 'wb')
    try:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except Exception:
            return False
    finally:
        devnull.close()
    return True

download_file_powershell.viable = has_powershell

def download_file_curl(url, target):
    cmd = ['curl', url, '--silent', '--output', target]
    _clean_check(cmd, target)

def has_curl():
    cmd = ['curl', '--version']
    devnull = open(os.path.devnull, 'wb')
    try:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except Exception:
            return False
    finally:
        devnull.close()
    return True

download_file_curl.viable = has_curl

def download_file_wget(url, target):
    cmd = ['wget', url, '--quiet', '--output-document', target]
    _clean_check(cmd, target)

def has_wget():
    cmd = ['wget', '--version']
    devnull = open(os.path.devnull, 'wb')
    try:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except Exception:
            return False
    finally:
        devnull.close()
    return True

download_file_wget.viable = has_wget

def download_file_insecure(url, target):
    """
    Use Python to download the file, even though it cannot authenticate the
    connection.
    """
    try:
        from urllib.request import urlopen
    except ImportError:
        from urllib2 import urlopen
    src = dst = None
    try:
        src = urlopen(url)
        # Read/write all in one block, so we don't create a corrupt file
        # if the download is interrupted.
        data = src.read()
        dst = open(target, "wb")
        dst.write(data)
    finally:
        if src:
            src.close()
        if dst:
            dst.close()

download_file_insecure.viable = lambda: True

def get_best_downloader():
    downloaders = [
        download_file_powershell,
        download_file_curl,
        download_file_wget,
        download_file_insecure,
    ]

    for dl in downloaders:
        if dl.viable():
            return dl

def download_setuptools(version=DEFAULT_VERSION, download_base=DEFAULT_URL,
        to_dir=os.curdir, delay=15, downloader_factory=get_best_downloader):
    """
    Download setuptools from a specified location and return its filename

    `version` should be a valid setuptools version number that is available
    as an egg for download under the `download_base` URL (which should end
    with a '/'). `to_dir` is the directory where the egg will be downloaded.
    `delay` is the number of seconds to pause before an actual download
    attempt.

    ``downloader_factory`` should be a function taking no arguments and
    returning a function for downloading a URL to a target.
    """
    # making sure we use the absolute path
    to_dir = os.path.abspath(to_dir)
    zip_name = "setuptools-%s.zip" % version
    url = download_base + zip_name
    saveto = os.path.join(to_dir, zip_name)
    if not os.path.exists(saveto):  # Avoid repeated downloads
        log.warn("Downloading %s", url)
        downloader = downloader_factory()
        downloader(url, saveto)
    return os.path.realpath(saveto)

def _build_install_args(options):
    """
    Build the arguments to 'python setup.py install' on the setuptools package
    """
    return ['--user'] if options.user_install else []

def _parse_args():
    """
    Parse the command line for options
    """
    parser = optparse.OptionParser()
    parser.add_option(
        '--user', dest='user_install', action='store_true', default=False,
        help='install in user site package (requires Python 2.6 or later)')
    parser.add_option(
        '--download-base', dest='download_base', metavar="URL",
        default=DEFAULT_URL,
        help='alternative URL from where to download the setuptools package')
    parser.add_option(
        '--insecure', dest='downloader_factory', action='store_const',
        const=lambda: download_file_insecure, default=get_best_downloader,
        help='Use internal, non-validating downloader'
    )
    parser.add_option(
        '--version', help="Specify which version to download",
        default=DEFAULT_VERSION,
    )
    options, args = parser.parse_args()
    # positional arguments are ignored
    return options

def main():
    """Install or upgrade setuptools and EasyInstall"""
    options = _parse_args()
    archive = download_setuptools(
        version=options.version,
        download_base=options.download_base,
        downloader_factory=options.downloader_factory,
    )
    return _install(archive, _build_install_args(options))

if __name__ == '__main__':
    sys.exit(main())
Thank you for opening an issue on an Adafruit Python library repository.  To
improve the speed of resolution please review the following guidelines and
common troubleshooting steps below before creating the issue:

- **Do not use GitHub issues for troubleshooting projects and issues.**  Instead use
  the forums at http://forums.adafruit.com to ask questions and troubleshoot why
  something isn't working as expected.  In many cases the problem is a common issue
  that you will more quickly receive help from the forum community.  GitHub issues
  are meant for known defects in the code.  If you don't know if there is a defect
  in the code then start with troubleshooting on the forum first.

- **If following a tutorial or guide be sure you didn't miss a step.** Carefully
  check all of the steps and commands to run have been followed.  Consult the
  forum if you're unsure or have questions about steps in a guide/tutorial.

- **For Python/Raspberry Pi projects check these very common issues to ensure they don't apply**:

  - If you are receiving an **ImportError: No module named...** error then a
    library the code depends on is not installed.  Check the tutorial/guide or
    README to ensure you have installed the necessary libraries.  Usually the
    missing library can be installed with the `pip` tool, but check the tutorial/guide
    for the exact command.  

  - **Be sure you are supplying adequate power to the board.**  Check the specs of
    your board and power in an external power supply.  In many cases just
    plugging a board into your computer is not enough to power it and other
    peripherals.

  - **Double check all soldering joints and connections.**  Flakey connections
    cause many mysterious problems.  See the [guide to excellent soldering](https://learn.adafruit.com/adafruit-guide-excellent-soldering/tools) for examples of good solder joints.

If you're sure this issue is a defect in the code and checked the steps above
please fill in the following fields to provide enough troubleshooting information.
You may delete the guideline and text above to just leave the following details:

- Platform/operating system (i.e. Raspberry Pi with Raspbian operating system,
  Windows 32-bit, Windows 64-bit, Mac OSX 64-bit, etc.):  **INSERT PLATFORM/OPERATING
  SYSTEM HERE**

- Python version (run `python -version` or `python3 -version`):  **INSERT PYTHON
  VERSION HERE**

- Error message you are receiving, including any Python exception traces:  **INSERT
  ERROR MESAGE/EXCEPTION TRACES HERE***

- List the steps to reproduce the problem below (if possible attach code or commands
  to run): **LIST REPRO STEPS BELOW**
Thank you for creating a pull request to contribute to Adafruit's GitHub code!
Before you open the request please review the following guidelines and tips to
help it be more easily integrated:

- **Describe the scope of your change--i.e. what the change does and what parts
  of the code were modified.**  This will help us understand any risks of integrating
  the code.

- **Describe any known limitations with your change.**  For example if the change
  doesn't apply to a supported platform of the library please mention it.

- **Please run any tests or examples that can exercise your modified code.**  We
  strive to not break users of the code and running tests/examples helps with this
  process.

Thank you again for contributing!  We will try to test and integrate the change
as soon as we can, but be aware we have many GitHub repositories to manage and
can't immediately respond to every request.  There is no need to bump or check in
on a pull request (it will clutter the discussion of the request).

Also don't be worried if the request is closed or not integrated--sometimes the
priorities of Adafruit's GitHub code (education, ease of use) might not match the
priorities of the pull request.  Don't fret, the open source community thrives on
forks and GitHub makes it easy to keep your changes in a forked repo.

After reviewing the guidelines above you can delete this text from the pull request.
PK    syMEX÷µn         Adafruit_PureIO/__init__.pyccşÌË¥ò÷Wt20±³ ‰†`ˆŸH(¶ I¥™9)úI)™Å%z9™y¥º‰E¹ef9ú©ééú)‰iE¥™%ñ¥E©şúññ™y@^¼^Ae	P³Mn~JiNªÈŠb‘ PK    `yMà*»  59     Adafruit_PureIO/smbus.pyİ[aoÛ8Òş_Á4ÀûÎq“´·]È×qZß&v`;í[…!K´Í«,ùD©®qxÿûûÌ’(GÎ¦½Ãu»A±[äpføÌÃ™¡r$ºñz›¨Å2¿)ÎOÏ~À›'™JE?
2&Jêƒ#ÑÉÒeœ\ˆImÅ•êÆ¡wp„ïïd²RZ«8J‹¥Läl+‰¥2h‰y"¥ˆçÂ_zÉB¶Dó×2Ñ˜ÏROE*ZOøPâ06]BçéÆK$†ÂÓ:ö•‰"ˆıl%£ÔKiÅ¹
¥t)Å³±ñ¬ÉËÒ!OE‚æÅFÁŒ,‰$Ë|’ÒÂ ?ÌÒ#ª•²kĞtöy‚3;HÛ–XÅšÓÿ%·Îf¡ÒË–	Ÿe)¾Ôô¥/#š[Ç‰Ğ2$Õ ®5—ò(ZgMM­«4}³YÆ«ª5ŠtšgI„e%Ï
b¸Wı‡ôSú†&Ìã0Œ7d G"»ôoßO½YüE²I	QœBc£íÅºÜbûH/½03i=‡¥UaôenUB:è8P^(ÖqÂ‹îZÛ6J¼í‰ñğzò¾3ê‰şXÜ†ïúW½+ñ¬3Æçg-ñ¾?y;¼ŸŒu“bx-:ƒâ·şàª%zÿ{7êÇb8‚°şíİM¿‡oûƒîÍıUğF¼ÆÌÁp"nú·ı	ÄN†¼¤ÖïIÜmoÔ}‹×ı›şäC¢®û“É½DGÜuF“~÷ş¦3w÷£»á¸® xĞ\°Nï¶7˜´±.¾½wø Æo;77´EĞ=l‘–¢;¼û0ê¿y;o‡7W=|ùºí:¯ozf1˜Ö½éôo[âªsÛyÓãYCÈ!i ÑQ¼Û£/iÍşu'ıá€Œé“>¶`ëhRL~ß÷Z¢3êÉ-×£á-™IÅœ!‹ÁÌAÏÈ!§W÷Cèóı¸WˆW½Î¤a£;[Ù>xöìYÿ¼p¤2™{ NºôR±Bpùšqp·E¼Eb|û:Ó¢s×ocÆÁÁ<Ğıt»ÔŠ°#üi)¿¶ì/g¿ä¿½8ÇoN~1¯ÓwÃş`OÕ‰I$hdJá-¦³l>§	ã4Éü4K¤™2÷£4Ìg¨ØOÃûAóÀBÌê’ÆQsğÏU”}ŸeÉ|èà&f¬·x’^9x³P^Î¼àd³T©Ôkxæ §·ÓIo ÜŸKqúõôôìTˆ#‹øç‰TFbnğ—j-¼  ™i+`t%jœ‘ ØõRxšêĞCÜƒ"VğŸL¬„ñdx·+áWˆ 	jN†O¯ïİ)‚t2ìo¦·ÁB€?'ˆ”Êü—5óí¸\ïŞ»éU4í\]òYçß°jÿÍ`8êMßÊUÏ¾Ik¸nÚéşæúí×§Ïõºï¦7åîñü—f~(£EºÄÙb8s®M/Õ0çl›Ê–2¾é¼ë=Ü½W§/HÊ½–öhäms·'NAİ^uâ/û'¶„ü©ùøŸ#]HèÙÒyŠJ†A’CVÀ}İŸ¸Ó¬
/IÀ)N D¼bĞÒúXığÒ~pãëƒÜÃã:ü„¼‘)s†xkÀç^Äç·ªtKşÌBFWïG51ğêô	éÆ«™ŠàöÑó÷"Eš¢Á ¢G8“øqn›,ç®×µr~%9¬¾É¤ÄÁĞ˜Ù‘Û×÷u–œ3 İå«;Ü £:j ¾±4ëü%
2„¤‘íÌÙ*ì‹a6q1YÄ›ÈÊgw;¬ë‡H¬¤ÎI9Iğ¸	»Œ¥¢/ğupy+ÙJãød.7'œôø'+	‘>`™BûÓ•^4
bm^0ÌÀî7Lv€]ŒYŸOçJ†Â[\6	2Ç%õ7[Î³yè-ô¾‡ˆ¼}ÀıÇÅQÑ°ÇK³É#>8v$Á&™ò)0%îtmºèÅÌ½O4ÎÑ~Ö_ÍŠ	‘”„¹òG;pzÊ¾ Aˆ¡ÏrZØÌÖ®@ŞBêrïSÅ—‡E9V9cL$|á×:çYãé¤%iëx…œÖsøx8;ÁŒ€¶^K_Á1ƒ<×¡-8]Í?Šµ—À":¹H˜FâD°¥œ4[S€Xò—ĞlâCíÀ1 QA†äÔ]Öi2
Lñ l¤zl-é`„ÚõpüS#^
JªLôEN±nÏ¤Ù1†©ıB˜¼Ã­<¶-ó<†üj¶s×:îo[•…—$Ş–}ŸûÓ¸sÄ0Pš#ßÈ `x¦´"gaõhRîte$U&5ÌcbÕ*T€ı2B]–`ñ]È¸Ò>ªOmrI5£>~ÿj|u];Ø¸­}ö©vôw×‚3A/>Yoâü¬Â€aQE©ñšõC4‹m
FÇ[åƒÈ>yèd+<ü ØW
§'Ì–©ø‹FÌUÓƒtP«OÌ¡TG‰ùO}[¦Ÿ¥” 36¸·Ql¾+NT…\¾²Û§J¨8}È/Ï™å.8}–h7./M§*RétÚ€s
}9ÀÙæ Ãsï‰Hn„^a¬Ñl!‚–´¦4&ñÚ$%}°­…¨œ{ŒÙätÏLLrıOø—_=²]œ‰3¥Æ’BVnáÉTèÏY´@íP–1]†x_
Z-ø¬F4U>¤)ØvPZOµ§Ö±—‚ÜU<SEèQéÈb.-ÑÀ°¦»í.ìø>”ğl¶ææ¨/Îl%y„S®ø8Å<ĞÕcMìâ¬F Jê×éÊ¯À§!š°‘›V„‰¿gœns¨1›DÅqf°ª 1Ïp'´LÕ-œ%Ÿ¥#­LôgMáirå…óÜü—Ú0)Èû°xb [*6~u€-¿úL²æ7ö«ÙïX…ñ˜i„ŸvöZE>mlÌÖû}¿£ëµÒ°æ*á¯l½æc:I"`¯0…ñRÄgUáa×<,s’±íµ2ÏÕİë’n†š˜^•—	-Üv±]şã ß59s²­u‹¼¹ª§·„,vU<ŸÛÃZEGÑ9Ñrá1÷Ø’b™¦k}ñüù,[èöšG´ãdñ\iI¿¯^6÷Å3{û¸ —şßqZ®¼”c¶%“¿Î[¥N—§+‡WÃÑõR¤Eıa3ÓîKpzˆ”Jòƒüç!ÚOÔLj7$ğ ²Iâh!ª¾å”
Y	ùÑeÑ@X?‚XjBÀ«Ó¦$³'u“Á ‰W$óœìCœQ$Ór”Ä2Å[’B…Eu<”Et0š-\Ëº(ü6PÙQÀU³LË%Ğí§ö±&J—ªu°É2mKÕ
¥l<^­²HùE&hµgY%ÀøPnTô&ÈGq *zF›¨9M8¥Æ^eGÔsBF†’{¦÷T'»²«•¦ÔqÛãw œÎ“EàÌ–AÀŸÏô›‰úV^ o-<:|À‡Ç;QUu;Û°K…qTD–ã ¨ó…vœÑ²‰CSV„QÿSzä¡7¬¥51¹²ë|N0RŠÚ•UÜÿ÷=u„œ’ª†¼3C¥6İÔ$¿I7’H¥H|Í1Ğv|¹ ØÂ¯ANqé,L§Í+¹‰ü'N]¡üÕ"ëù:j˜İ8m‰³¢Ş€RM¿ûs$Ş£Xÿ·ë$åMèdJ³i$ñNŸ™-ö´µ³öÉµó–¸Ü˜I´ì6¬ÊÚ–~~—Í¨9ØÊ=ô ÓVŞÊoÀ O‡1sŞÍoDr!o§öÔå´•ûÇìQ¤aÆr¤­t©G“e(€Î€úŸê©8)ÍÌ"¾mµÙHÈUä×-’Ü4s!ÍC×¤?sTıò³…•½íjìÄVM'³YF[øX›…±ÿù	Áv‡*9/å«4ÃÜo}g¬ñ=ø*Î"îrl±8E½õ”.À£²–578Ì`Ü'œyX}¶-„9qE²”¶vKz›4ÆdnÜÕ—ïyŠ~ÁÂ4‹Ê…[‡È«Šª:ìTÎ !R÷P~‘ÜĞt$™¶ŠİZz! Q*=bÄå®ÓÛuŞpä†(Nà?GtÃ€¡*tóPTĞIÊô¾¦W £¦w?
d8f.2ÕÏNÌy
9?x°_v™¸Ziì¦ûqÓ²½ÖËçû ôTğûzcnõLÖSÈÄ“Ó5 šGQƒo°jqûÇë”±õD<ü¹¸·æ¾a6è'cã¢ƒO”lì{œ‰«ú#ù· œÕ»x›f~]L¸WG:À†¦í=
#Y§ñZ 3ñ H;,CrCœ‚¢üÏ{+CãìjÊo_Wz´Â6-yaM×2ét¾Šğ5Í”Ó(0]0CŞz«‹[#ï6›:uh!j=Ó»g¥fĞ-]Êµ¥yƒšä<‰b•7ğ°iùµz}MçL¶¹h§È™;òH—ü~JVÔiäòÆ”y-$‹˜‰Û?†3ş“aŠÜŞo•1ÉmëÁ?;àŞéz´ˆ.ÿ3 ÿƒÔùöÖ«ä‰³ê3º¹»$«¹-t}½#ÚÆÎjĞøZV{%8
ê\ètJöù¦šw£
}ÿ€.­ñ™\ç˜=iÌ^1ºòÌõ—’ÿ€t£K¯ÎÑU«asJ8µæÀ'u©©iBÚšAØj>›Úûq{^‡[òÈnùáÙP‰±Œœ+bëâ]'~j£coÃáì´¾¥òü¶®û`Ï¿Ü	öåê­‡BXÑ‚ø9Zÿ6yêñh_ûY£Tl_¾~{Ür0Ør w}İüq¨{¬„‚Šzùpùıo±OMıMo¼óå›=;Å7öPæ[R®´–÷îyAönPöóÌq²o)ó¾|™*¤ûªt¾[Îì½ß¯°+Xh‘,–QS¼’ck+èåÃ•¿DUaÕÚGŞ,áİùkí]<®g¼KyúãéÅ§*b(vjkµú½Rü™÷¢ş|Ç˜û'&IL¯˜Û›Ğ]ùşM.ÉÄ¾æºÃN¦€à®Lû1 X‹ÖÛœİD7²›Š‘H¯{æ²Ü¼pPIæşÙ£"¥¶•‰ˆ%Uc½ èMUç-;§Gù_¤@{ZMé\zÂ©[öLi§›êc¶e#Íß6¹çrÓÄ¾[VA^pûgAôªu¹ñÜ6Ù´¬‚§aÊu§õØüÉ›K6&jûGõç«Ù¶×ÿ±Ó®gÄÕµˆœVT^óVËUGîwŞü/ò4s§gãÇ„£¢Yª ¿\€½Ó¸ª8£W¯;G(½UÂÀ-Ş÷’¹ÂŒ¸CÊ4L¿d®¾æŠV3âJU6ıáeÅÿPK    `yM              Adafruit_PureIO/__init__.py PK    syMs¢0=y  ¿/     Adafruit_PureIO/smbus.pycÅZK“ÜV¾R?fz</¿Æqœ‡Igœ8!„àíq2Ä“TšP*MK=#[-u$µÇS±*Ne—
°bË5ìY6ü–TA± Š
ç;÷!õ¸í8q;™ñ\_]]İÇ9ßùÎ9Wªıkfê©ÿı÷Ç¡~jôwšşò9Kˆ@ˆ6•–l[¢g‹¶-z5Ñ®‰^]´ë¢×í†è5E»)z¢=!,ô®qïIÑ½–h·dk]ÄS¢·G´÷Èë†ˆ§E{ZôøŒèñYĞCs" ‡æE0%Ú{E@ìõÜ/‚Ñ> ‚YÑ>(‚9Ñ^Á¼hÁ^Ñ~DûDû°ö‹ö£"8 ÚGDpP„-Ñ¥¹ÄÇBÜâ½öc"8¤[1­‹à0.ÚOˆàQ>É·˜ÛV»¾øs‚ŠÕ“g()Â¬ëwB§Øò§õ¢NNõĞ¹¼Sl¥‰³~ñÌ w–/¯.EŸÑÏb“,&¨èxzø•bÒÔ_x¹rñâÉ¢?/¸{?å©¸~ùÒêÚ•wÑÆXĞ+ı"ôò"‹’MocĞíRÏİX/²A§dá¢…¾*¢´SÄkÑ<ªhŒÄÏPœFá ˜G1‰‚ÕhÂ¨‰¢¢bÅ$
gBí&:Ùñzù¦A¶y‚zŠDj1là(¬‰®4©JMWê"¤qÛÂåf€r×±êü ¢dpÃQS99ïm‰ÅäAÆ»ëÆşf^ ¿q˜ğÿ$E¬eëy‰ß=¯˜â‹^b\Nğev<Ï…P\Œå
óX7
ã ÷ÑRùwxü(NlQ^,ÅXàs~Ö»şr|"ÜÜ<±øİlŞeÒÁê¥yoc/õw\(OçXHÓjÚ-¿Å~%Ë,ØÎ<V•ø…?d™,×ã#åJò“Âƒt,E[IOæU):yHŒ$ÖœÅ˜ ÆbsgQÌ¡˜7‚Áê] Ïİ;$•Ê>z€É›J*sVÇRhÂúÎâŞo¡úg‰›»=p‹jLô–-nlˆÂV7ÎıäŠxß·jâV]Ü¬CD‡I.§oR‡š8ìÕ¸‘jºAöª—74Ê††øàñnÑäÙÍáM”‹Áå$Êu¶ôü-ÿí"Š£bÇé’N'©#-Öñ“ÀÉB2Ğ„ªÎÅ+õœ¦úé§ıALÎvTl9¾“€´ëäı°J¬ÔóÜßó%Ç¹BT¤/¾Ÿü‰Fx°|+Ä³VÆ)ı˜:noE-ZY?s²#&´(	¢ëQ0ğã¡9h7r´öÑæ¶"jËü$÷y·XƒTÍ×I“Â§/9aöhôüUöKã9×ıxçñØ’Uƒ#)Í!›Ş,¶;b§O*
u7B®²ãÑOÑ°Ì`±e@<0¡&ƒ^˜‘h]X¤»Å
`Ò…Yº`ZÉßà½ÿbF«ËÃÂämÕRğÔL0ê	¶4Ü‡ÉX^Ï¿z<ú¼6v19O´rØ:hí¥ßƒL3sÛ8{&C,¶&–¿î&–C0œ-xz²¸Ç¬•&¬•	X	*“pä¨´àËQ™‚;Ge<:*Ópê¨ÌÀ¯£2×Ê¼;¹vL7ïÆ½pğ¨ìƒGe?Ü<*àéQ9gÊü=*‡”¿§˜€ØïlíSñE6á©pÏQ¯/±ª,O#©B?Ññã¦à°é²]Qv
çD^?Ál^hJ¿Ó!H„vl%y[“Û1Á¡‘‰Ç¬Fõk-‘=–«6óœ%¬„;­s Û„°³ŠNœ$Üv´É¼ğ“NHö‡ÍĞ&ˆaÒ>L’,Ø0‹€ÃF¬hDJ²ÂPdÒ¼9c7Íœğ†‘8/8ÛlÔtCmĞŒ¥7şÜ´„Õ.D«HÒ¢ÂV4MÂs¥}ª†4ÔdFƒ€Ñ?•=ñ,ÀÜ_cÇ¶µ–&¡ôèrEÜˆ§dÀ„«<Œ»*:ÈÇb†2¸ˆºåùÚƒ‰fËš–Lÿ±’áR¡O+­R“'Ñ!IOƒ>ik‡8Oáò%qìğ¾%:~×ÊØ®§¹õÜ£còÉ:4
cÏ»Æpc¶¸sSu¹©u>ÍDôá²/?!Ú#Ì0Ik/ÉÕw±-^,Oäy©Yn£SWÄ]tPXzá§G-üFT˜u§}ä4m^ÑODĞâHIƒşkÓ}Jkå¼“Vêz£Œ•ğFGúŠ	uA®hêcÄ$ïy×µŠ„=eÚihi,iƒpS„áÛ­L¯Öµ÷ß¶-P•™G<KT\Ò&ª©Hómªšıc©9œ°a‹Ÿ¿•Ã2³g7XÒ£S^Ãî|³ğrŸĞRvˆ³5õüBÊ²v¿1&dñÃ®ÍY35c†½—b”¼½¨.•$³S|]%ğ”Í,·"2
’’PÇOï¥â¿Ì	WÏÔRßÒ˜†h2×bÆ@ƒ$F`Å¤Iì+iô¨dË]b¯-òŸIlğØ ¤Ğ,%%Âšt|§o×Hd¶P¹0ºÊXTÇ‹ˆX·´çá¸:íõIÔ7äY‰B¹²%×¤1NjHèD]¦9êì­_X~g¥¤©qQˆÇ#ÿCÚUşéÓ
­jÕ´€^/!U¤ò#Hp6ÃNWk:, ×¦àÖ€‰ŞæÖuŞlş6úÅ9¹î’Q7K{»LR.j)ÿ=GÓPj°!=4,6$#ã+Š–	z’ız~@ZÙôá•œ¨8Ê÷3B‰2Şûr‡\É²4sŸ¬qrĞYÀ®™"™àaÈ½¥Æö°ïŸ\ÚG€Ëš¹±äWJ±ÛŸ'v%ó:ÒA8ÃõÛZà=˜+&Íš´ï`ÅP@´î‹]mHœwÓE²SUÉæ¿!Z\NhÑ~RŠ¶>B´0–#åíTG¢]GĞvS»ò©”‹ã˜ƒi7ª±®7åãœL)İL2±´˜ƒT¨ëÕ)¡N––ïÛ2:=dë›$¢Ş!êyPk¸”Éì¡IÜvqîèÂBØ±ƒ£.zî9ÉbKÕf÷Ü».œ<K,•}ĞFøÚƒ¸tËsÆ,ü`@IíØ¨Î ƒóÒß`Ày	{ÚjÙ5ÊLŸ¨.aÒÒ0ù…Iî“º†I£“æ0L& 7’Ú)‡‚;Ü¶‡Q3¥Q³‡Q3]EÍŒsşR¢f›¨ËY<)müØN™À¤…ÊGùe;Šc8õ3rz|4 >ùá0	"
*.°Ÿ¥È+ÓÌ˜’ıU†ºHáf÷¿ãÄQQÄzcGËìoL æ“–µÅÙ»!Ù‚³û]LQÌbĞ.HØÅšvaØ}Å÷QœBñÚ¸|„,TÊ€ıl£ìs°ø3Î
N'>²*ÑİŸ©¸Lá/E¦„•8í\s0Ç—Å	ôü^:Hø¼qÁÃf$ô½()SÅn”A“à3>ŸÛğiö3XeÇ9‡±¢\HÒ ~ÓÃ~–ù;Õ\›3NŠjWË³vé»¼+k,Ú™3t!²zş(tèÔŠ[]yC#¿º_o#LM“À.&©1	u+ø”w4‡4GqH“9¤˜ÁcWge Àşç×C ¹_h­]à3QuFcTD=dÈ±„]ŸÈ-/<&y…L›ç)Ÿï¡íñ¹¶¹»Bó‚L
õ2¥ó·å»ŠaĞ±k“GÆƒ,ök8âäµ„äŸcÔÁÓÌßcè¸Ş$?ëâ±½J„lCà‹oİ²E5Ò¿Í;Š‘.ÕtÀ\ôİ,âSÁj\CIÒÃˆ÷kxb„†»S‡»)bl:Ağ´M{¢Îµ¿c4L-šGHÔ˜µë¢’_½#îfìÎ¯sÜdœ¾ÉÇ §Œ2$XåqÈW¬v¿Ÿ¡
NÀ*yÎú9Hdq•§SeHÑ£{d\Š™2ŠÁîÿ!Ô›O™#L[³#R°SâK§`•SƒSFş•<ìnÂÇë#>)/yğ¡%foŒ°ƒ™ñÛoøŸb8'«+2V”²nf¢@{Iüº~Í\5¤ÔwéD'f¼Î‘ÿ°bl:¹C/÷= ÅØC3òÜBjíÌ°êw:÷Mc³™¹!%²sùFÄq©¨Á¹ÌZ³vEÆ±¼woR#u^e*"1·İ’~¥±K‡M£CÃk«èpWôE´i´hâ™QyKA*ŸcÔdtd3ÉĞWñÑõkgŞ”ˆúì³»8EMä«}>ôêS\ş5aË¤:x(%¥:Wqe>½¸$Ì§ìçQ‡TìlšlÉ5ÍOÊ//™˜øh¢.ƒ•ºÿ]eN‘ˆFäH4DQùÕÃ®‰T²•\_^‚¿ª:a<GÍĞAz•»MÕMã8İ6ãEE¹Ğ;üuÍ0™pÀ¨i8È…V>>”Ì—d¦50™\°ÀsßáM’Ï¥“j\İÍ¯Ô%vl‰ûà¤UÉ/F¾NÏ²[·£‚c£êÏ±şËã´~v|Äª¸’¸’š2ù¡üù÷âó"Ò¥|ß ?’º]Óé´şJ
	³¥^â ®¥à¦*&yFj=Ä¨>}Ê{F'@³œ ÍéÙõ¼4ş ª©µ|³¦|¿	Ã1	ğ1ìÆÉ/ôÇMú¬¤ÄÏhìWä&œ`WÆ¥nY˜÷	,Ÿd.Êo­*ç.ÇÆ…@ãŒ eşòIÌíDy`AîE1tFÇ”Äùù(Rfè£êF¤á¥çsğ*mzĞ&N¥ÌYİ>«{
guµµÅÃ˜x×—Œ¼õo¢xÅ3(Eá xÊØäK(^FwqîPğ;ƒøÒÊ]E¨Ö}ÅŠ¡€¡¹îĞ†Ôv§'ß*³lÖšöôT«Şšh5Z{¨¬·šô;×Ú×Ú3½·5Ûš¤«iúiÍ,Õ[çèC~CW9µG(›AÁ_ÏòÇµ¤ˆ¥Úó®ô¢wee1ÁylZ¿ré2'/×.­_Yv¯ğ÷jêİÅÊ;Ş¹U×[>wÎeO#›WßX»ä®xkËoq¢ŸöÜsŞòÙ·øˆV?öïMŒo±M_~oë¿ä]1‹¡ÕY½b–{şíµ³ëò,iB5]^9[¾ù½xæíuùuà>m,±tãjØ)XcS'¿´9%¿C~ß8ó÷M{ÉZ°æ­ézÓúµÕŸüXh-L¶şPK    syMìN}Ÿ  õ     EGG-INFO/PKG-INFO•’»nÛ@E{~Å”qAÒ–`E*LD	P‰ÓcîˆZ€ûÀ>ëï3ËPJX¤H·»s†¼÷Î<S@óïä¼4º‚‡â!Û£¢
Ö.Ê·ÑQİd7ä¾XY•Bw© •Á^ÂÉhø *@Ğä™€ŞéÔåï û¼‡``'u|‡º©û1
©¨W@- kë`ëŒå"8²#ö¤H8^½E?qŞJAgPFÄ‘|‘=E¹ÅuŸB°¾*ËA†S|+z£Jœ­”WO¯í¤÷u¶¶|sŒ¾ÀVnÌˆPŞ€Z‹èƒ“äg2'…r¬ÀGkŸ¯ßO?Ëv²gÏ,ä¹>d[ò½“6LÁ}Ûİ7/û¬1°õçe3¢÷ò(‰EléL£±“é.``ÇU!‡/<­ÚXr4ç×]| •À¶éêé0¥¼Àge©È¬­uæL"İYëµ¼h©5P0³æ9‘î§æY!ïÃ‚m*•ôìP‘Ç1)ú½|ZŸş³ãqÁŒ•}zîÌ1üDŞ»¿Âúyæ	H=Ù/PK    syM“×2         EGG-INFO/zip-safeã PK    syMq;O         EGG-INFO/top_level.txtsLIL+*Í,‰(-Jõôç PK    syMTiŒ1i   Ù      EGG-INFO/SOURCES.txt+N-)-Ğ+¨ärLIL+*Í,‰(-Jõô×ÏÌòâ±Éç&•c‘ĞKMO×ÍÌKË×ğv×õôsóÇ­"Ø?4ÈÙ5X¯¤¢·¢”Ô‚Ô¼”Ô¼äÊøœÌ¼ìbüªKòâsRËRs@Ê PK    syM“×2         EGG-INFO/dependency_links.txtã PK    syMEX÷µn                 ¤    Adafruit_PureIO/__init__.pycPK    `yMà*»  59             ¤¨   Adafruit_PureIO/smbus.pyPK    `yM                      ¤â  Adafruit_PureIO/__init__.pyPK    syMs¢0=y  ¿/             ¤  Adafruit_PureIO/smbus.pycPK    syMìN}Ÿ  õ             ¤Í   EGG-INFO/PKG-INFOPK    syM“×2                 ¤›"  EGG-INFO/zip-safePK    syMq;O                 ¤Í"  EGG-INFO/top_level.txtPK    syMTiŒ1i   Ù              ¤#  EGG-INFO/SOURCES.txtPK    syM“×2                 ¤®#  EGG-INFO/dependency_links.txtPK    	 	 o  ì#    # Copyright (c) 2016 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""I2C interface that mimics the Python SMBus API."""

from ctypes import c_uint8, c_uint16, c_uint32, cast, pointer, POINTER
from ctypes import create_string_buffer, Structure
from fcntl import ioctl
import struct

# I2C C API constants (from linux kernel headers)
# pylint: disable=bad-whitespace
I2C_M_TEN             = 0x0010  # this is a ten bit chip address
I2C_M_RD              = 0x0001  # read data, from slave to master
I2C_M_STOP            = 0x8000  # if I2C_FUNC_PROTOCOL_MANGLING
I2C_M_NOSTART         = 0x4000  # if I2C_FUNC_NOSTART
I2C_M_REV_DIR_ADDR    = 0x2000  # if I2C_FUNC_PROTOCOL_MANGLING
I2C_M_IGNORE_NAK      = 0x1000  # if I2C_FUNC_PROTOCOL_MANGLING
I2C_M_NO_RD_ACK       = 0x0800  # if I2C_FUNC_PROTOCOL_MANGLING
I2C_M_RECV_LEN        = 0x0400  # length will be first received byte

I2C_SLAVE             = 0x0703  # Use this slave address
I2C_SLAVE_FORCE       = 0x0706  # Use this slave address, even if
                                # is already in use by a driver!
I2C_TENBIT            = 0x0704  # 0 for 7 bit addrs, != 0 for 10 bit
I2C_FUNCS             = 0x0705  # Get the adapter functionality mask
I2C_RDWR              = 0x0707  # Combined R/W transfer (one STOP only)
I2C_PEC               = 0x0708  # != 0 to use PEC with SMBus
I2C_SMBUS             = 0x0720  # SMBus transfer
# pylint: enable=bad-whitespace


# ctypes versions of I2C structs defined by kernel.
# Tone down pylint for the Python classes that mirror C structs.
#pylint: disable=invalid-name,too-few-public-methods
class i2c_msg(Structure):
    """Linux i2c_msg struct."""
    _fields_ = [
        ('addr', c_uint16),
        ('flags', c_uint16),
        ('len', c_uint16),
        ('buf', POINTER(c_uint8))
    ]

class i2c_rdwr_ioctl_data(Structure): #pylint: disable=invalid-name
    """Linux i2c data struct."""
    _fields_ = [
        ('msgs', POINTER(i2c_msg)),
        ('nmsgs', c_uint32)
    ]
#pylint: enable=invalid-name,too-few-public-methods

def make_i2c_rdwr_data(messages):
    """Utility function to create and return an i2c_rdwr_ioctl_data structure
    populated with a list of specified I2C messages.  The messages parameter
    should be a list of tuples which represent the individual I2C messages to
    send in this transaction.  Tuples should contain 4 elements: address value,
    flags value, buffer length, ctypes c_uint8 pointer to buffer.
    """
    # Create message array and populate with provided data.
    msg_data_type = i2c_msg*len(messages)
    msg_data = msg_data_type()
    for i, message in enumerate(messages):
        msg_data[i].addr = message[0] & 0x7F
        msg_data[i].flags = message[1]
        msg_data[i].len = message[2]
        msg_data[i].buf = message[3]
    # Now build the data structure.
    data = i2c_rdwr_ioctl_data()
    data.msgs = msg_data
    data.nmsgs = len(messages)
    return data

# Create an interface that mimics the Python SMBus API.
class SMBus(object): # pylint: disable=useless-object-inheritance
    """I2C interface that mimics the Python SMBus API but is implemented with
    pure Python calls to ioctl and direct /dev/i2c device access.
    """

    def __init__(self, bus=None):
        """Create a new smbus instance.  Bus is an optional parameter that
        specifies the I2C bus number to use, for example 1 would use device
        /dev/i2c-1.  If bus is not specified then the open function should be
        called to open the bus.
        """
        self._device = None
        if bus is not None:
            self.open(bus)

    def __del__(self):
        """Clean up any resources used by the SMBus instance."""
        self.close()

    def __enter__(self):
        """Context manager enter function."""
        # Just return this object so it can be used in a with statement, like
        # with SMBus(1) as bus:
        #     # do stuff!
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit function, ensures resources are cleaned up."""
        self.close()
        return False  # Don't suppress exceptions.

    def open(self, bus):
        """Open the smbus interface on the specified bus."""
        # Close the device if it's already open.
        if self._device is not None:
            self.close()
        # Try to open the file for the specified bus.  Must turn off buffering
        # or else Python 3 fails (see: https://bugs.python.org/issue20074)
        self._device = open('/dev/i2c-{0}'.format(bus), 'r+b', buffering=0)
        # TODO: Catch IOError and throw a better error message that describes
        # what's wrong (i.e. I2C may not be enabled or the bus doesn't exist).

    def close(self):
        """Close the smbus connection.  You cannot make any other function
        calls on the bus unless open is called!"""
        if self._device is not None:
            self._device.close()
            self._device = None

    def _select_device(self, addr):
        """Set the address of the device to communicate with on the I2C bus."""
        ioctl(self._device.fileno(), I2C_SLAVE, addr & 0x7F)

    def read_byte(self, addr):
        """Read a single byte from the specified device."""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        self._select_device(addr)
        return ord(self._device.read(1))

    def read_bytes(self, addr, number):
        """Read many bytes from the specified device."""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        self._select_device(addr)
        return self._device.read(number)

    def read_byte_data(self, addr, cmd):
        """Read a single byte from the specified cmd register of the device."""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ctypes values to marshall between ioctl and Python.
        reg = c_uint8(cmd)
        result = c_uint8()
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 1, pointer(reg)),             # Write cmd register.
            (addr, I2C_M_RD, 1, pointer(result))    # Read 1 byte as result.
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)
        return result.value

    def read_word_data(self, addr, cmd):
        """Read a word (2 bytes) from the specified cmd register of the device.
        Note that this will interpret data using the endianness of the processor
        running Python (typically little endian)!
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ctypes values to marshall between ioctl and Python.
        reg = c_uint8(cmd)
        result = c_uint16()
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 1, pointer(reg)),             # Write cmd register.
            (addr, I2C_M_RD, 2, cast(pointer(result), POINTER(c_uint8)))   # Read word (2 bytes).
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)
        return result.value

    def read_block_data(self, addr, cmd):
        """Perform a block read from the specified cmd register of the device.
        The amount of data read is determined by the first byte send back by
        the device.  Data is returned as a bytearray.
        """
        # TODO: Unfortunately this will require calling the low level I2C
        # access ioctl to trigger a proper read_block_data.  The amount of data
        # returned isn't known until the device starts responding so an I2C_RDWR
        # ioctl won't work.
        raise NotImplementedError()

    def read_i2c_block_data(self, addr, cmd, length=32):
        """Perform a read from the specified cmd register of device.  Length number
        of bytes (default of 32) will be read and returned as a bytearray.
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ctypes values to marshall between ioctl and Python.
        reg = c_uint8(cmd)
        result = create_string_buffer(length)
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 1, pointer(reg)),             # Write cmd register.
            (addr, I2C_M_RD, length, cast(result, POINTER(c_uint8)))   # Read data.
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)
        return bytearray(result.raw)  # Use .raw instead of .value which will stop at a null byte!

    def write_quick(self, addr):
        """Write a single byte to the specified device."""
        # What a strange function, from the python-smbus source this appears to
        # just write a single byte that initiates a write to the specified device
        # address (but writes no data!).  The functionality is duplicated below
        # but the actual use case for this is unknown.
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 0, None),  # Write with no data.
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)

    def write_byte(self, addr, val):
        """Write a single byte to the specified device."""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        self._select_device(addr)
        data = bytearray(1)
        data[0] = val & 0xFF
        self._device.write(data)

    def write_bytes(self, addr, buf):
        """Write many bytes to the specified device. buf is a bytearray"""
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        self._select_device(addr)
        self._device.write(buf)

    def write_byte_data(self, addr, cmd, val):
        """Write a byte of data to the specified cmd register of the device.
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Construct a string of data to send with the command register and byte value.
        data = bytearray(2)
        data[0] = cmd & 0xFF
        data[1] = val & 0xFF
        # Send the data to the device.
        self._select_device(addr)
        self._device.write(data)

    def write_word_data(self, addr, cmd, val):
        """Write a word (2 bytes) of data to the specified cmd register of the
        device.  Note that this will write the data in the endianness of the
        processor running Python (typically little endian)!
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Construct a string of data to send with the command register and word value.
        data = struct.pack('=BH', cmd & 0xFF, val & 0xFFFF)
        # Send the data to the device.
        self._select_device(addr)
        self._device.write(data)

    def write_block_data(self, addr, cmd, vals):
        """Write a block of data to the specified cmd register of the device.
        The amount of data to write should be the first byte inside the vals
        string/bytearray and that count of bytes of data to write should follow
        it.
        """
        # Just use the I2C block data write to write the provided values and
        # their length as the first byte.
        data = bytearray(len(vals)+1)
        data[0] = len(vals) & 0xFF
        data[1:] = vals[0:]
        self.write_i2c_block_data(addr, cmd, data)

    def write_i2c_block_data(self, addr, cmd, vals):
        """Write a buffer of data to the specified cmd register of the device.
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Construct a string of data to send, including room for the command register.
        data = bytearray(len(vals)+1)
        data[0] = cmd & 0xFF  # Command register at the start.
        data[1:] = vals[0:]   # Copy in the block data (ugly but necessary to ensure
                              # the entire write happens in one transaction).
        # Send the data to the device.
        self._select_device(addr)
        self._device.write(data)

    def process_call(self, addr, cmd, val):
        """Perform a smbus process call by writing a word (2 byte) value to
        the specified register of the device, and then reading a word of response
        data (which is returned).
        """
        assert self._device is not None, 'Bus must be opened before operations are made against it!'
        # Build ctypes values to marshall between ioctl and Python.
        data = create_string_buffer(struct.pack('=BH', cmd, val))
        result = c_uint16()
        # Build ioctl request.
        request = make_i2c_rdwr_data([
            (addr, 0, 3, cast(pointer(data), POINTER(c_uint8))),          # Write data.
            (addr, I2C_M_RD, 2, cast(pointer(result), POINTER(c_uint8)))  # Read word (2 bytes).
        ])
        # Make ioctl call and return result data.
        ioctl(self._device.fileno(), I2C_RDWR, request)
        # Note the python-smbus code appears to have a rather serious bug and
        # does not return the result value!  This is fixed below by returning it.
        return result.value
0000000000000000000000000000000000000000 6f4976d91c52d70b67b28bba75a429b5328a52c1 root <root@raspberrypi.(none)> 1543175460 +0000	clone: from https://github.com/adafruit/Adafruit_Python_PureIO.git
0000000000000000000000000000000000000000 6f4976d91c52d70b67b28bba75a429b5328a52c1 root <root@raspberrypi.(none)> 1543175460 +0000	clone: from https://github.com/adafruit/Adafruit_Python_PureIO.git
0000000000000000000000000000000000000000 6f4976d91c52d70b67b28bba75a429b5328a52c1 root <root@raspberrypi.(none)> 1543175460 +0000	clone: from https://github.com/adafruit/Adafruit_Python_PureIO.git
Unnamed repository; edit this file 'description' to name the repository.
ref: refs/remotes/origin/master
6f4976d91c52d70b67b28bba75a429b5328a52c1
DIRC      [úı$1}?[úı$1}?  ³ S  ¤          
lcD²õ¤¼Šı9*wYÃ^^¨¢ÔŞâ .github/ISSUE_TEMPLATE.md [úı$1}?[úı$1}?  ³ T  ¤          ‡{d¸bÀ^nö˜"ş¾3ìZ  .github/PULL_REQUEST_TEMPLATE.md  [úı$1}?[úı$1}?  ³ U  ¤          	â¸sŸä›$—‚~FšG¥y„ 
.gitignore        [úı$1}?[úı$1}?  ³ V  ¤          ?Ø‰[°E”2¡_vª·Ç^˜º 	.pylintrc [úı$b©™[úı$b©™  ³ W  í          Éöå_Ä0:ÿ)ÊÉ¢3‹ÿæ¬”‰ .travis.yml       [úı$b©™[úı$b©™  ³ Y  ¤            æâ›²ÑÖCK‹)®wZØÂäŒS‘ Adafruit_PureIO/__init__.py       [úı$û?Æ[úı$û?Æ  ³ Z  ¤          95y»…]9Nı>vR_;@³‰“ Adafruit_PureIO/smbus.py  [úı$û?Æ[úı$û?Æ  ³ [  ¤          >Ğ%S¿e¶`%Í<pÅ $T LICENSE   [úı$û?Æ[úı$û?Æ  ³ \  ¤          q­:ıê¾×1p‰ D¸€²Å‹ 	README.md [úı$û?Æ[úı$û?Æ  ³ ]  ¤          (\#êš+~½íñ‚>Ò†¯{Ïª­ ez_setup.py       [úı$û?Æ[úı$û?Æ  ³ ^  ¤            æâ›²ÑÖCK‹)®wZØÂäŒS‘ requirements.txt  [úı$û?Æ[úı$û?Æ  ³ _  ¤          ã³ï¤èêåQ­­†¼ëgïV–õÊ setup.py  [úı$“Õó[úı$“Õó  ³ a  ¤          Ê¯®!ŞF$E×%¥uˆÓÂ–ãªÕ tests/test_I2C.py TREE   € 13 3
XœÌ=¡ 1›ØWYI»p"tests 1 0
ôæF8Ü9pø”‰ûmd­­…½CáG.github 2 0
Ğ)½
8W"‘gÔ–Ì}yÍ¯w£sAdafruit_PureIO 2 0
™U”q³¼~Y±šïêÍRİW—İô§H|¾^èJâœ#x[õÆÛiİˆÓ[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = https://github.com/adafruit/Adafruit_Python_PureIO.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "master"]
	remote = origin
	merge = refs/heads/master
# pack-refs with: peeled fully-peeled 
6f4976d91c52d70b67b28bba75a429b5328a52c1 refs/remotes/origin/master
90e73171e3a7400e59be42fab36f4d67506fc9b7 refs/tags/0.2.3
x+)JMU0²4f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-sSÓŠJ3KâJ‹R=ıªÖó,Yôƒkÿ½7&ä4v»çBÍóñtvõve¸ ,»Ÿ1u[‚êY›‚£
Ì*!P%A®.¾®z¹)kû¬ş¾ÚWİP¶ “ÁeÂ†MG»¡ŠR«â‹SKJô
*”_ÍÒ®Ûûöc“İ¥¶õÕŒbçç®ZUWsWŸr­cWÅæç69=ëgÿ˜<#âø’Ôâ’b†/ÏÜ,îXü˜Òù;7eíÚÖ½ÎİÉ¥wòx+)JMU06g040031QrutñuÕËMa`¼ıöÄ!–ewü+7¼Ö¡² H4ÜxİZıoÛÈíÏş+61PKwª";×äjÀINÔ³%C’“A@PÔÊâ…"U~Ä1Šşï}ov—¤%ñõZ÷Ú HlrwvgöÍ›å<Jæêøé³“?ıîPõ’Í]Ş¬rÕšê¤süLuş2-Â\ãE‘åi¨³ƒCÕ-òU’ªYß©~ØK"ÿàÏ¯tº³,Lbfj¥S=¿S7©çzÑRËTk•,U°òÓİRy¢|Ìßè4Ã„dûaÆ7ÊW6q›¯ (K–ù­Ÿj_(?Ë’ ô!Q-’ Xë8÷s®¸#©F¾ÒêñÔÎxÜ”eÚ /Œ!O+÷Rİ†P£ÈUª©Y@)-
¢bÁ}¸×Q¸íœ.¢°ÿ"ƒÜmK­“E¸äÿZ”Ûó(ÌV-µ)|^ä™ña cÎ‚.O’Te:âÖ ¦5W;”Q\6Â¬©2>¹]%ëmmBîiY¤1–…q0f‘Àt²êÏ:Èù„û_&Q”ÜRÁ ‰!µÎNåøfxëÏ“ZT2Hˆ“;ËËYÈNÌÛWÙÊ"5×ÖrX:Œ±>tZAÍbåÀAèGj“¤²è®¶m³‰W5ŸÏŞt'5œª«Éøõ°?è«Çİ)~ÜRo†³Wãë™ÂˆIw4{«Æçª;z«~ú-5øëÕd0ªñ›^^]x:õ.®ûÃÑKõ3Gã™º^g;«–´Â†Ì<W—ƒIïdw_/†³·-ˆ:ÎF”{>¨®ºêNfÃŞõEw¢®®'Wãé [èCğh8:Ÿ`Áå`4kc]<Sƒ×øEM_u/.¸¤u¯¡Ã„»T½ñÕÛÉğå«™z5¾èğğÅ »ë¾¸˜Å Zï¢;¼l©~÷²û’;œ¨1äPC4{To^økvñ·7GT¦7Í&øµ]'³rò›átĞRİÉpJ³œOÆ—T“†Å¬ 1˜994ºª<¡á®¡ºÛêº†ƒA_»áíƒe
Äùİ8×úÎ<\q¹gaäÑ ×)‚ü ²†'=ÕSİ«!Q+P‚¯‹È(Œ‹OêƒNcsüø¤y€ñŞ¥7ŒTıÏ™ê|êt;JÁ}I-øë«\Çj÷
VáFù‹ø ³&ıút¥Œ€Î1¤XK-üÜ'µA·,òá:ğ²µŸå:µ¦³ñU]%üØéÈÂ%õòÎ¯G=8Ÿ{ãï²;zI#Úù£ñt°•"8ÿ‡=óí8·ïÁk¯?œxİ~Â©œu²gÖ—V¾'oÔıÉ,ÌùÇ¿`şhìMú^·g§»AmÚí>ZO½×ŞEuz\¿µ9?ÒñM¾=ÚY†iFtøä3¿ËõXazÑ}=(íæ¬ĞyŞyJ)×ÎJ¢‹[ıØe¢Gï¹é²üóÎ³/Ol)ı0
—[+îù è"¢ç!	1›)HÉŞÜÃêĞ!Ænán¡OÕs-7µÔ#¼—§ 7°,Bˆ«éÖ¬?RÈK@Æ_øÀ¡#–èGa~G!“şAP%Ç
yN!½d=c˜}òäÊé³%D5’AŒÀOâèÎ8ãÕ W‰Ÿ¬œ)G¶×¡18’±WM/_ÆñÓõ>MN2®\ı€tayöd6"•bø$S½”]Ãî†8ÚA„ÌB…'·ÎnS!"ÕÍS9Poêh‘y8†wå	7hü£–RW„q~ü¬Ùª½\FşM†·{_Äœ¸ÿå¼XÊË«ñp4LFÂÍ¦HPÛlº¸M=áLTtßCGnM¹¬ŞÍ-b;Ê,ÿô¤\ş öB>hód²øÄéßèÌíñãÇ×y(prà"=€~nRŠTçHX]ˆáwt±§…Cµ7É¦ˆ$ïpø
ùUÎ"Ûè Äù,$H¸=´•b>ã~U?õ×š¼LğeHü"¶QÊÉ‹3ÈÛU¬À'„$—â#!¥á¢@öB•BóÄHÓHL%»„k‹øâJÜƒj×Cìb–«~P:ÒL]³SpÔG?*´Á Ç>P }Ê°Ğd"¨…’) ¯aW3°-;‚éåx¨±¶İ²òÓÔÙ`¿ÎÆ×6iaC¤‘ÓLy\À·ù;i8H¸‘ä~”Ióšd"3¦‰tŒ”=Å1V"Œ‡ñTÜäwáû6]‹¬·~×y¯~ú~.í3¶â¸ã÷{`»˜Ã'ûÀnvÀS3àP’[˜3BÈ4IFcyfl²[«´Ø
e²¶5¥lPŞˆoaWŸÓúG	•Ù¤ğ¤—>Òñ|åçjº$ Ş°Ã«;T2±!L&IÎ„Éœùå”„ğıeÁ9CR2ƒY€„(ºlànõ )¿Ô&BG‚±Eˆ¸œ«'ıñ	àŞı(ÕD€)*¤³€S<%`îy”EËVÎÎFˆ%vë<z ÛDÅúVek‚6L	‡CÈ ‹ŠrÃ2ƒ‡s}±[	ÇÆ„4
EŸsãORÜ»ú“OİÕ±ºÖ`2š”²œ†8Æ†K‘›¡DªÑNÊT É?””XrQ)–„•áÓ2’'Œ­{Y#”ci©¶g{äÆ†.9™–XÇl„¯*_ã{™Ë%Ö<™¤vò"{
;¶4€X MFå‚LŠGÉ°ÍÌK°h¢qy"‰Êõ‚(É4œ¤¶ˆP§û×aêOÀº#°à(„ìœéÚuá‡ê/èP`SR$µ3ÀG¬˜İcãà{Ù*ˆÈ7¼ÜäÂÄ-Ä•ék)Hã¸‰¶MY™ïú qaƒ¡•b7@Ûnéø©lı)‚DÖˆŸÀüæ‡|¾cí]í!£Ä¦ÄÜ/«›$ÇQl¶Ì#gíl/›Ç?v¯ç~HC›~±Å†Á/ãæ´8°W—à…ÒÄ?·7<&°	Wç–°@Nò¸ÕÄóöéõˆeÁô†ùQ•+sáÊğVTrĞ·Şöï*â4\kÆö‘$ĞŸïS©K"Kp•,éSŒÈè ”g^°I#Z&~ª–~6‘éSµÊóMvúäÉ¼¸ÉÚáêv’Ş<A¯¬Ğ(Ëÿ`%eK©3!€ÆQI/ïüã¨NZû¹ølK¥ßÏ‘É•{:ëT² å¸?>U=?GJ3ÒûdğÏW)Bœ‡È™=hyár‰.è[¡ßçÀ—@ØÁÜ¦	ºG°¾•t™Ş¥cNêÂ2–µà!:#ªô'äkÍÌ™PßmU@0(BÒ#Š€ËÁ­o“‚Ìå˜€
%Xªª_Êıšxd‘G,bäw¨RÀÅ°ì£:
¨,ôÚ»àÚsŒBË¥yPÙù6Ø1áÙ6Ä´¬Ğ¤%áúeÖ=˜I'ëu‡ÓiIŠ­²6–m9˜eYÊE‹6!'ôH1Á“ªGæ]&ßªq4«U¥õ7;a7iÜÄ¡¦+²íNfï[CÙ¥ÑÚÂ}Í™ğ8»5= ãá1Öh8ü†\R*<RßÍåß ÃÆà0tTbÁHß6»¼a©0IÛF¢æ ûla*.Š6fCr¾^láı¬‚i âøp,]o—`<¼¥‘A1ñu4«ÉêÖ~êZ½ù­¦±S'lbH¯âfè‚ÔÖ–(¥fæ¬ˆòÚÛê•[ÙÈMõß°p^*˜É^yVE9¯Á£m©NK·\…ÔÀ¦PŞ:2“ÿÕ›4Pëö¯¬I¢\¢£µ#ª4›w¨ä¤ğ‘, ~âe%ì}]ÏK2—Q“$$6´ø3ójU¥ÓwÙ¤iaM±PµÒ–Ì¶˜U'°½[àış0æhÕ8%³æ>ÿ®[rÉ%F	L.1F’4éãI9‚¤#7ÅVA‘‚Ê:İoó:H+Tª¬SÈÓ<iËÅ‘½Ô«àÄ(ºCJ—ç`##¤YåhuÎşqØ~¯:~f‹PZÇ-ı›v«p'ºæÛÎ€³ŠoµÊUÙ£»YoÛ†ãoŞ×æQ|¸‡³á•³3Î€[#²ÊÃv,½¯Íà0ş:)ĞÇB\‘¦…ˆC€]°¶vmPŠ6t	İè|!ÈúX}~W:.ÇØ ®TŸMˆ1ƒÒÃ÷¥ÅTFİ×\BzCÃ¼ˆ‘¸ÀK+ ƒ¡e ©™c \V¢KòQKë­Ü.¥‰`iÉnYoX"úd\SŠİ¼ÊèH?·FM^©H(éê‡8¹E¥‹+ËHhÇf]¨Ó\è}ÃÛS°ªKT–Œdáš@ãp·RRª*“¤~ˆR<8¬z*’›×ËbágöÜ*jÉ—ä¨Yå.ä½Ùª4…Á+İ<å¹^˜ÛÓ)µxx´(hĞğÁñ«"í4·0²+‹ÒŒ÷ÁÃÿ÷Â¹öxİßx¦ k˜ªBòÿ›M[J6Tüu&––f	–ÿf®S!íÔ¿EÈ0÷}üEz…dT Ø¤D¶ã/HÎò½­$60ÿ¨J™n™-z ¨àCÍ·]Ïd”Û…Ù	Üéh²Kt+¹G.Ê¦®4šıøllïãìí2˜ÖÁLYlzo†<ıÍ´Ë4½<„Cõ3K&Ù2¥“®.“Ü‹V~FCÖ6ƒ¾°ËšD¦ÕÌÄĞz°’ÙY”°ò¨iùÕmÛ\#2ÎàDJTVm óš<Š¡^¸-áÕ
ûªÈ\sñ·ˆ…‰+ò|PÎøw&M(GØ`â
)Ú­+Ôä8Øô5à&âkØnñêßğ9·o×ù’U‰
jû‘|Çë¦3j-MóêÒÉˆ¶+Æjp|­1PYpo–÷[Òêe‚ö™Ş'Ñ«gYbiŞı£ÍÂïsi1r9&TRğMg§Êd¶ËÁ_Dk©J+ìv<öÖ™•Lu<´{Tµã‘—Ç_8»C5eBËÈÖÄö0Ëóÿ6zî‚/ÖÕ_Áv9S·%÷]=p(5(Ó¸}E¶¥yg¹°vÅq­Â.…••öÿF…ı«ñ(°èí*¢ÆÑÙ‹Wè¸W”3µx<?¯èäÁQ÷µJz¹ï2èKà‹7ÒûrUfÍu¿	7—¿”H™S;e&\Ìà­¼Ş÷«Õ˜èÒâ‹yÊÍ•ÂLı„ìP}­ 9Kà
Y¾“zœ7o-e¾p-å…µ6\&í…!³j,Ms)¸E¨u§G”ßHF8Å‹r~O¨C÷™‹aÎ¨´ı
Ã!ÛnÈé|¿7•¯÷3Ş©¥¼ì]ç´ú¾AxJTOtjÀ0­Q€Ÿ&ï_ßª8¿‚#ó¡Ê¯Rı|$ŒÙE¨³MŞ+1I“–leù?³—|ôšƒÜEüÆè+1¦¬]7Ü'8Ö?5O|?Š–ˆ€f7VşëĞ©(Š)'¾ÕÛ‰Á&û––Æö"ï·`¾àô|¯H\L(m7há0“Ç%ŠßÜ«š»éÒ=H9Ÿÿ§á>{>ÆáV,eğÁ‚¡ö1®„$V=ö“·òbñ Àf;9®/¦H³Ó¥¡…|G”d¢„š«ÖKošo½êå­\…üı—C¸u2IM,½®š\ø 
5t¨²ê‹aµ†ùºHw}ššYÜù\3ä×tÅE-\6ík¾ìÚ&«Â´ip”WRÿñæùÓ^·Ğğ¾şJí²ÊŒ[ùıÁŞuU7T¿¨•ş[ì¤óó;¹!Úix	owËN‡Zñs{_á˜×ÿ¸D\ã‹ÀÌ„Øä…cí™ÃıˆaÓlX†Ÿär™=gx«™@¿ªçVŒaoÕş	á7x+)JMU014f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U•9™y%EÉ7:£7°¸N1ZÏ\¶jûñ8ñ»€ŠÌMMôJŠË2‹õ*ss¾=?b`õŸ]HóÔÉEÆİÿŸ­™Ò	q“cJbZQifI|@iQª§?ÃÌĞ)…›÷Ô1FnœõşÕÙ »áÓï~ÚêãéìêìÊpA5Xv?cê6¶Õ³26G˜UB J‚\]|]õrSÖöYı}µ¯şº¡lA'ƒË„›vC¥VÅ§–”èT2(¿š¥]·÷íÇ&»Kmë«ÅÎÏ]µª¬(µ°4³(575¯¤X¯¤¢„áÙÜG³7]¼æìİ­¹®<êÆ¡'=Á¡jáæõm~¿äÅ«§Ìk×¶íyş>lÚ×S–¤—3|yæfqÇ²àÇ”Îß¹)k×¶îu~è hÌ®x•Y
1ıÎ)úJÒY:¯ÒYf‘L+ÌíÄøYğŠWeçQ Ñ¤·6ÚXL ¬r)”F˜3¤H9¡Ë…í±ˆêÉ½-%fR¶_£o&xí‚H”Ñy›‘¼ó.*~Écí0qİ¹2\§q^ûı‡—¥ÉŒÇã…lppÖNkU¾qÒşÔÔ&Ü¤ó{ÜàH•]} 9ÚE…x•ÎA
1@Q×=E/ ´i2é€ˆWÉ´	
#5.¼½ ^Àå_<øm[×«GÈ¸ó¡1·…@Cè§Flu®ÙtæÂVŒæ á!Cï‹˜fb`ÁjJĞ–²Â.h)MdS"¡äå—mÄ›ô·t‰ÇÛuİÆù—‡»ú)f‚¹2s¸O˜Rhß9×?Yxºº>ü>k¶C]xİZkoÛÈígÿŠqÔÒ®*ËN6YpE’cumÉä¤A5²¸¦H•(FÑÿŞsîRäÄÛİº»‚Ä&gîÜ¹sî¹á4ˆ¦êøùË^üé@u¢Õ}ìß.RUóêê¤uüRµgî<ÎüTõÃY–¤±¯“½ÕÎÒEŸªIŞ«®ß‰wï Ï¯u¼ô“ÄBå'j¡c=½W·±¦zÖPóXkÍ•·pã[İPi¤\Ì_é8Á„hšº~è‡·ÊU8ŒM”DótíÆÃgÊM’Èó]HT³ÈË–:Lİ”+Îı@'ª–.´z6¶3Õe™™vÈóCÈÓ*©Ö>¶‘¥*ÖÜ™G)ò‚lF=ò×¿ôíœ.¢ –`Ô¶¡–ÑÌŸó-›[eÓÀO5ó)|š¥™ğ¡§CÎÂ^¢X%: jÓš—Ê(®Akª„OÖ‹h¹¹Ÿ:Í³8Ä²0ÆÌ"˜NVıY{)ŸPÿyÑšô¢pæs×É©ßoİiôIË–Â(…Æby9ÑÄ±}•,Ü PSm-‡¥ıšğa¾+l3›&)pà»ZE±,º½Û¦Qâ¢§ÆÃóÉ»ö¨§úcu=¾íw{]õ¬=ÆïÏê]r1¼™(Œµ“÷jx®Úƒ÷ê§ş ÛP½¿_zã± Dÿêú²ßÃÓş syÓíŞ¨×˜9NÔeÿª?ØÉPM°¤Öïaæ¹ºê:İ~İ¿ìOŞ7 ê¼?Pîùp¤Úêº=šô;7—í‘º¾]Ç=¨Ğ…àAp>Â:½«Ş`ÒÄºx¦zoñ‹_´//¹¤µo°‡µTáõûQÿÍÅD]/»=<|İƒví×—=³¶Ö¹l÷¯ªÛ¾j¿¡†#5„îêİE¹f;“şpÀÍt†ƒÉ¿6°×Ñ¤˜ü®?î5T{ÔÓ,ç£á·IÃbV€ÌôŒ]Uœ†Ğp7Øz®êöÚ—†ƒ@_çÃ›{óˆõÒûpî/	õy8÷Â4ÈŸù‘—{v \'óÒ=ÈêŸtTGµ¯ûD­@	¾."?Ì>«;‡: ç¸3ğI}ã+gÒ¨êŸ3ÕúÜj·”‚û’Zğ×U©Õîå-ü•rg3ğAbŒºÕéJ­c
ˆ±–š¹©KjÃŞ’À…ëÀË–n’êØJO†×U”ğc«%*øsîË9¿tà|2ì/«öàhç†ã	ÀVˆàü;æÛq¹Ş½·N·?rÚİîˆS9ëdÇ¬‡Ví¿G=gĞşÉ,ÌùÇ¿`ş`èŒºN»c§»aÛ´Ûcv=êuŞ:—åéqı¶ÍùoÓèÙĞÎÜr¸§ıO Ÿé}ª÷Ä
ãËöÛ^a·Ü
­W­ç”r“à¬$ºÈ±U]&:pôN>]–ÕzùğÄ†ÒŸ #¾·±â_` €. zî’C 4`8‹±x_tp_÷ËC‡«ÂªĞ‰Çê•€–Š'µ÷òà–Eq5ŞĞÀ
ùBŞh„2şÌ]®¡„@7ğÓ{bøN„ŒºïA¥+ä…t¢åÔaöÑÑ;•"Ò'sˆªE!‚…Á½qÆë^§!?Y9?R¨×¡18’±W¯^gÆñÓÍ®œ d\±úéÂòìÉlD+ÄğI¢fz.ZÃî†8š{^€ÌBù'³Lnkc!,ÖõS9Pgîë`–88†Å	×iüÃ†R“ùazü²Ş¨¼œîm‚·;_Äœ¸ûå4›ËËëa0éjFÂõºHÿ¸WQ6­cG8Ó!=Vqì‘ª©|»ïúÆB;Ê,ÿü¤X~öBî´Ãy¢‚,¾qº·:±F{öìÙMêœrp‘=@?5)E¬S$,È.Äğ[{±§…Cm¯¢UHŞ'àpò«”9D²Òó™IÈuh*Å|&ÿU­ÜØ]jò2Á— ñ@P£“f+fë…ï-À'+„$—â#>¥Oş,CöBBÓÈHÓHL%»„k‹¸âJÔÁµë!v1ËU/”4S×ä48ê“dÚàGc(€>eXh2ÔBÉ€‡×°«Ø`zùj¬mUVn» è›ÛÓøÚ*°AØidàôSWğ-F¾ƒ&µÜùHÊ”I5óšdå#3¦‰tˆ”=Æ1–"Œ‡ñTòÉüMºYoù¡õQıôÿê\v´=ÎØŠã?î u1‡Nv€İì€çfÀDk˜ÓBÈ4I	Fcyfl²[»i±#6”ÈÚÖ”¢ ¼ß‚V_ÓúG	•Ù¤ğ¤ç.Òñtá¦j‰ºÄŞ áõ=*™Ğ&“¤œÎ„kÑ”ùé”„ğãeÁ)CR2ƒY€„({YÁ;óÕ=¤üR›	Æf>ârªfúÓàŞı$Õ„ç)J¤³€S%`ê85”EóVNÎˆ%Vu=€D…z­’%a7L	=‡CÈ ‹ŠrÅ2ƒGîúb·$9oÒ(|N?IqGìêÏ.÷®ÕZXƒAÊì¤•ïğ/ÇP¡?I°J¤
=á¤L­ğCA‰ÒhIX>-#yÂPÍØË¡»Šq”µÃi„¡qrh<ƒhÂ¦c-~H‡†Gù)˜˜ÍhÈW¥s¹vÃê{²9ß¼ÀÏÖ¡Í?£¤sFYŒ3f<gJ& 5aº8ªœ¢Šõ¼ J4¼§²RÇ»×“êÏp7DÄÁ	æ6mV…¨¿¡u¥$ÖHÎg<Õ±bÚÅDU0”k€J…¢w¥é*¹Ií¸~MYšï€ûAFÃâ;uï'eà¹lìñsñú³'Ì‰t?!$˜Òé–µ·w 0%Là—IåØ=ñxD8lµaÁIn{QÿX]Ïİ XÇnºQx(g+FÅ„Êiñ.€²8.ÁKá¸›
‰xâ8÷×œÉÀZò¸ˆáúæéuˆeÁôúéa™DsáÒ9ğvúÖ ùöÆQµÆ€kÅóØW’ÌúK=•º"²WÑœ>ÅPÖJqæhb›4¢¥èçjîú I0œ>U‹4]%§GGÓì6i®„Ä›Q|{„&Z¦Q¯½zñ ?‹µŞùgë_‡MÕÒMÅgê0ş~Š¯Ğé¬UÊÂ.‡İá©ê¸)rş°ÇĞ“YAºˆû\8DÊ´BË‹<y°3Ó‰‡†9XàˆG8u¡­Tó› bÉ“já]:t§ä4,cé¢¢JF"W¯ Éœ	qD%ŠM…/ yîû(£'s9f¦ÂC–*›B_¨,òÈƒYˆÄEA
¸úİ¯¢ğ—Ê²ns\4Ø6--.äà-vdçÛ(ÈLhÓã¢t“^EŞH³îÁ;Z.³Ğ÷˜gK¶l7kƒÜ†ƒI´–¥òhÑ$äÃ¨†æ)&8R£É„Ì$bfë°æ~PÙÛ$ÈŸàp$5í’Mw2ºo(†zL£I´a°Š3á¯qvKz  ÆÃc¬ÑpùI¦”~¤¾%ºBÊ½EêÁ~ºX`ÁHß4»¼a©0Šg›FâÎ vÙÂ”bmÌ†¬}9Û<ÂÇYÓ@Å·ğàXÚáyæñô–:@jÅŒ8/­Y®Hº·tã¼œ®5]ˆ-<aCz%7c/ÈymíR£Q*fN² ­¼-_å+¹±şN«BåSü/KÒ²Z§óÕx´Õj¨ãF^:Õ ê^¾.ş¨w± Ví_.ÈaVıã
­®-ÜJ½ÎqJNúØ Éâ'^–Â>V÷yEæ2Û$	‰-şÌ¼JyFéßô]voXS,T®´!³)•gÇ	lg¼?Æ­j'²É¤¾Ë¿«–ÜBrA“KŒ‘$M|R§ éHM–‘F$‚ äöA÷ÂÛ¼'Ò
%,ËŠÈTø4Oœ…r£dco…,81î‘Ò¥)ØÈ©—9Z•óŸ„rl?W¿´Õ)­“/ı»v«p'Úé5Ûç€³Šo5ŠÎUÑ£»YoÛ„ãïŞ×¦Aäİ=ÂÙ®Qı#ÃcvÆpkDV¹zØŒ¥ñµ	Æ]F\ˆ+ÒÍq°3vÉ–y”¢M‹]B7Zb².VŸŞË16€+Õe·bÇ $ƒô 1â¾ôÊÓ¨úZŞ„Øaš…H\à¥%ÁĞKÔ,g Üb¢}òIKO®Ğ7Ò]°4Šd×¯·,]2Šd±›SÉã—Ö¨È+6âKºzFkTº¸Ë„vlÖ…z1N…ŞW¼VK¡ºDeÉA®4·–’
P½+M»>Jğ`¿l¶Hn^-‹…ŸÙŒ+·PI¾$×@Í*—$ghÚ–¥)^Bè±à)ÎõÒ\»˜şH±€‡G‹‚ı—O°*ÒNs=#ë°²(Ìø<üq/lj‡ß„·)Èjæ€Êü‡`c£´¥dCÅ_gbéu`ù_æ:ÙÒŒİ5B†¹ä/ÒD$£À&%²W‚ä$ĞÛJA"aF`óûeÊ´f¶è€¢¼»Š+nºÉ(7!²¸3ïD¢û.Òä¹(»½ÒvÃ[°±½¨³×Î`Z1e±é½òtW+Ğ.ÓôâÔÏ,™DeJ&óºLr/v`ù}YÛz@ËŠD¦ÕÌÄĞz°’ÙY”°²_·üš«mîgp5"%*«6yEÅp_¸Fá®Èò6æâo
—äù¤œñ[&M(G¤Ë$/<¤h·,wø¤ş#ÇÁ¦¯7_Ávƒ×S¿ÀŸäÜ¾]çKtV&*¨íDòï¡Î¸ki‚œ—·QF´õ\1Vã+Ò‚;³¼¯Ø’V/´/üğ1‰^5ËzKó£ ´Yøá!-æBy‰-H)ø¦‡³Se²Ûåà/²k©JKìq<ö:š•Ly<´{T•ã‘—Çœİ3¡¥&²€5±=Ìâü¿Ç‚àÁºú+ Ø,gª¶¤ŞeğØ‡bE·«È¶4ŸAn²óâ¸RaÂŠJûQaÿj<ÊìÆ£zs…Š¨vxöú÷ƒr¦çç%<9ê¾V)`_ùô%ğÅ;é}åUfÅu¿	·<)2¦¶ÊL¸˜Á[qï)îW©1Ñ¥Å§ò”ÊÂL}Dv(?cœÅËY¾“¯}roŞXÊ|úZÈó+m¸*MÚCfÜ±4Í¥à¡ÖYò]pDññ„`‰S8+á‡†ÚÏ¿ß`1Ìån¿ÂpÈ¶kr:ßïEÅëİŒwj)/ùĞ:-?|’-È·;`˜Ö(À‹o–w…¯oUœ_Á‘ù‚åW©z>OÆì"Ü³MŞ+1I“–liù¿²—|ø–ƒò‹øÙ¯Ä8š²rİğ˜àXı=ğa)Z"šíXùŸC§¤(¦œøˆo+›ì[Z›‹|8Ş€ø‚ÓWò!#q-x2¡´–İ¢…ÃL—t(\s¯jî¦÷ å|ùGœ†wúìù‡[°”Á—|N<†ÊWV¸:Ì%<!±Úè°Ÿ¼‘‹6›ÉqÙx1Eš.-ä;²I&J¨¹*½ôºù¬Z¾ÑÊeÈß}9„['“Ô„ÒëªÈ…¢PC‡*)¿hV«™ÏŞ€ô¼OS1ë“;_Şù5]qÙ.›v5_vGm“‚•aÚ48Š+©ÿzóüùV¯[hxW¥rY•Œ[úıá‹ª_ÔJÿ=vÒù]Üm5<¼ˆ·»E§C-ø¾«pÌë\"û.ŠñÅV`æBìòÂ±öÌá¿™ŞgcØ4æşg¹\fÏŞj&Ğ¯ª9„cDØ[µÄ=ŞxSÑª1íó~Å@Váv©Ş–‚p¡öZè‚EA
¥HLf54›„$ë½Û¯ï$«»
Ò‡æI“sÎ™9³Wf“ÉÇé›àÚYtŞÂÖµĞx©€vCc!Ú¦¤‹`Œò +Ğ& S™h/Eªœ©Y[ãéb'™îöj4Îğ•£P&ÆWçŒ»8+Ú8„³Æ'`Z ó¾©Öm8ğr”üØû:2åº3g‰’eÉâuAÉtó •ÔbgÿÍH`®ˆ#+‰ÎÃüÌxBel:À&°Ğx˜Íà¼ƒ/XşŠ‹=Ÿ|eÑ±ûºi}À:Â×«Mù#şXJİ¼Ş!-%Gí1B
sk9¡ˆÿ¿—[¢¥ç;ÄRÔ‚óFHÔ<Iœ=S	wkgÕut¸dúĞPİÉc×Vúâ´øô_¼Ç;¬­±’Gù©Â£±^5ôŸø¾yß˜‘™ÿÊ²4³‘fƒ›óù\°Ê52ìÖÃrÕkŸ¨’ò2¿/¦Å¤‡°†å Ğäó­Ñ-,ä³QÃ”;àk&U'`’è3;(¸©{i;iÃà€Ñ!Ø®ß#Y`AšBsBÀWh4ìÇÀ8GïãZ¦Ü@¹¢íãŠ&M³+§Ïi+6ë² X8céZÅ8¦¸VT“¯÷”Ø¸=ŞJ'¨hú¢w¨ÎÑÊ'‡ºp½—¢¯î.pY¡k›İÇÙ_ËÖWx]J1„}Î)úQ–Îæg6 ¢è¼@ºÓƒÁd²d"ËŞŞ{‚­‡‚ú àãVkp<é‡ÑEÀ²áƒ¶‚ZĞXr1° øWÒNSŠ+²:Ç.Û .Z"“„‹w0úå„£Ş¦¨Wt¤Uüß­ÃWÛ®ğ™?Z‰ğ2æxû¯”y‚·ú
Úzô‹1K€gœQ“NÅ!wÕ{)í—‡ •Æ?0ì²%z×{ÜD’$X§âŞª@ÉÔcÏ²?Ô³¯[HxNKjÅ0ëÚ§˜}áá‰?±áQ
-=A÷Åq&¼$6Î¤íëéë^¡Z$!¤\¶†Ñ?H#‚àl¤DVS&ë0{ƒhâ2$œ|ğsòfJÎ©šízñYOd'‹ãÂ„±Ç3å%úàæE“µC4*r+ŞË~‡W~)k‚«tñüG3çn\rÙ íè#º =<êÕİ~Qè_eõÆßPï}{•+ğ~HZWàã8	¾Xn@?ÉY¡Ñš„?	x«¥ÉEıÂWZx+)JMU022d01 Ç”Ä´¢ÒÌ’ø€Ò¢TO†i.>ÕµÌ÷üú¿ÄëŸèÄS†|ÌLL|<]ı‚].¨ËîgLİÆ– zVÆ¦à¨³JTI«£‹¯«^n
ÃÚ>«¿¯öÕ_7”-èdp™°£aÓÑn¨¢ÔªøâÔ’Ò½‚JåW³´ëö¾ıØdw©m}5£Øù¹«ÖB•ÁÕ<“k2ÖÓ¸ôöEXê£šæ{gpn€8¾$µ¸¤˜áË37‹;–?¦tşÎMY»¶u¯óCw Cl[x+)JMU02µd040031QĞKÏ,ÉLÏË/Jex$Æ»£x>ï“Ù*Ó›ê8Üf¹/­l11 Ç”Ä´¢ÒÌ’ø€Ò¢TO††ÿom¾Y¿ïã´öÅ·Œì…¬ æùx:»ú»2\P–İÏ˜º-Aõ¬ŒMÁQf•¨’ WG_W½Ü†µ}V_í«¿n([ĞÉà2aGÃ¦£İPE©UñÅ©%¥z•Ê¯fi×í}û±ÉîRÛújF±ósW­…*ƒ«‘şºLvıQÅ‹Õkv}œkÏRóF¢âø’Ôâ’b†/ÏÜ,îXü˜Òù;7eíÚÖ½ÎİXÄj`x]SË’¢J¼k¿‚]/ˆnDEÔˆY ˆŠˆˆ¼ds£„yXUPÅË¯Ÿ¶gV³ÊÈ<™'Î"Ï½Äwn)‰ÿÑ&Æ+.%…£8£lÅ±º¡l• ¥HáŠ#{`4ú«Ñ'÷1ù’?Ş8ıšŒ2D(Ë÷€d„ûK¹Ïš«aÕd5|BÄèëÙ?2”b#Õa?ñSbÔMÆş·šÎ}ŞúE†QI‰‡ÕˆãHÛ,†õû8’}}ğ7ùÉjĞfôm”v¸ß!£0ú^¹â|OMå$Úz,Oõn?Á Ÿ_‹„(e²}8òyxËäÈÕPöÆNë;-5Ã4Êu¾Î%lë1êaÚ½{ ã£Vu’Ê¶éØƒcO^bQâƒx˜˜ÅUöõîÚ~. Ûş9Ô÷½Ê-¨ 3ƒ™ªyÄ½éTAz‘å~âë×ŞírŠšİLöq\ÜïÃµ‡«ŒfPi†±PÈ1Ùìì+7\ñÄòà¢˜²Ùë¹º³:Zãùlc°Æ;	Ğ„ÚeÊJ#[äÀÙF^QÜNNt§GÀ/“¢}Ê?­4¤ ·?«~Ó„Haâ€£qD§^ñö5Õ½*Ş‡{ÛÔğÖyë› jß¥ûâíkƒHTÉ¨["#(´EÃ›¯ÚÌJ`İíã>ßKúyÏò¶*Ô6fªÊò½ªô¤•·ÃÃ_‰è¸ÄÑ-FMâ(3s¬Ë‹€ŸEQ¼¹ŞÚ™p–‹X0ÁÂŸàù1&;>]©mä“åÖ¼¯ÔÛ‹àÛ9—½\v‚á¼£lÔsõ”ÃVÛ‡F½:/›ë<^n¢\³XàoÓÓi
C›UUAş²–>JNõæ~ÕCı1	o¸;^¼!¬BA‚›+dNsXN-uzîÓW5tÛ
x³±~÷Ğ‡ÏŠ1ÛåšÖ)¼ŸçVÌgèØ~Hâ¬øõ]\ŒşÔ—”şü'ıÚAB¡x+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤ÒbšÊİ­±–üşÚ±—I	Å[;lîœ -= xx[jÄ0EûíUè¿0Ø©-ÇPJ¡¥+èüĞLÌ$vId¦³ûj¶P}î]rß¶Ê0ÿÄ;„³))Ût¶è]šKÈˆîeòèZoIÅho´ú‰;5†€ÑEëÑ8kílœv³EŠÅÓLA™‚š²Šƒ—¾Ãwowø¬}ğÊŞ«Ô,à”ûöÆ¢ÆGßÏZF	E¦«¯úi\àVy]Ì ­=_¡u–Ècoµ] ®«¤c¬|Àm¡mIw¦äQ –ûhâ@å¤ş ”x`Ñx+)JMU067c01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U%E‰e™Åz•¹9U$&<x.É²%hK½Š-‹ñœxˆu)‰iE¥™%ñ¥E©şUky–,úÁµÿŞÆr»]s¡úx:»ú»2\P–İÏ˜º-Aõ¬ŒMÁQf•¨’ WG_W½Ü†µ}V_í«¿n([ĞÉà2aGÃ¦£İPE©UñÅ©%¥z•Ê¯fi×í}û±ÉîRÛújF±ósW­…*+J-,Í,JÍMÍ+)Ö+©(ax6÷ÑìM¯9{wk®+ºqèIOğD¨Z¸yÍ÷´ãN'}ú»s‰eù§P—3^-…x´$µ¸¤˜áË37‹;–?¦tşÎMY»¶u¯óCw «šxS]‹1íóüŠ}Pa;íêÂ‚°P»:`QĞ‡B)“;šIB>\í¯ïMÆñ¤Í“&çœ9÷Şs7Êlàññyô.¸ã¸ :ïaå½Ô[À?k!Z¤ö)ù"£<È´	À”C&E™…jgš‹‚l¬qt±•Ì
w{ÕxàhT™ñÕ9ã:gÕV‡pÒÂôL`ŞÇaq;£ao;Éwg_;æ¯\·æ,QŠ"[¼.¨5™o –Z¬-ã¿Ù	Ìqd-ÑyxŸ½)îQÛ °,Dã1<Áø‚õrq©£§Ó›[t,¤¾.>`“à‹ù²ú‘~Ì¤‡;¤™ä¨=&Aab­3{éÿ÷jE´ü|‡Xé€Zr…DÍ³ÄÉ3•p‡±pfëXÓ$‡3¦·‘êÎÛ¶Ò‡åóñFwX+c%OòKS‡7Fc½jè?ñçæ}cN$fïWQä™õ5£ÜœèM«]”a½ˆ«ùY{Om”—Ë!ğ§rX»Ù±Hr—w Á÷VFa*_bğ:q¨´ˆ>8‰—Ö¶ô56LªV„è>Ú´	ŸÙÉUÉMs¶$Ğs'm¸Ø"F²¶B_–XÒÖ¦$íğ@SNUø0ÎÑû´«9LPÍi%¹¢ñÓ@«ák^•å¢*¦ÎXz‡V19Ã5Uê›Å8­”·Rà#¢B_ªS/M!‡”Ä3àzMº¢¯îºÖv{u­s³pıÁ ø_¡x5AKÄ0…=çW<ğ ^*z[Vq.xN“Ù6˜&!“¬İï´"ò†÷¾7CHŸ¯®±sæTš¯è/uJ}+Ô”Z'òßß­×¤¢©şL ¥RdŸ"ßÁXKÌ¨	ï>¶İ>ÚĞœ#º‡=Ltøì;¨×’²¨(”ƒ±4S¬8¥‡ÆÛ"gïèŒ9¹ˆµR‡ãÛ“gÈ3øIå{µÈ%eL½a«¸Pkã.›inCğV(Ûœ«Ğjµë;°¥†´cÑZp°“‰#mñ&ÈIùK?ç°±’“_FnµBu¯½€©xñ*È0a 	2ÅírÓºâÛäH«_T‚@x+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤ÒbÇ{ùÎÚ.Üà:/(ıÁù_ÿ8^ú5 EN#—xm’Ks¢@…gÍ¯è½•¤y	T%Si@"u\v7o°ieô×f¶¹ËsÏ=u«ÎGûÓ©æ@“Õ_œå9€T¤ªnPJå‹Ê¢A2]ÕDM5ƒŠT%I0Ë;”\¢b¦ÉXË¡)3]š«™b–ëj¡@s_xÕ3ĞsTx¢¬/8xŸÂ'Ç]—Oüµgåo ª²¬©š&àå
úı$Ïpjî^xïz–íí³¬yu!¯ÃgåPu	^c./gÏ	Qºßº 0&52-„"3ZÌŠM_«åë*3oB(s=™|j*5ë–µÙU=×—:ú*`Ã˜­‚Ö>$.ìçX‘Œì^ás¸ia¦ûør6>Jñ ›€Y¥(GËév‘L8‰ \äH¾Ò9»<§%«œÄs©¿4Öj;mwŞe²úñ´›úYíß®|Ûx5¼µ;²Î#!$MÚÒûË#f7kufŞ`èÍıuìŸËP¹Şwvì8í}Qxkn‹rÕ…òÁ·i²Çƒ ñósHÌ··®ZX©$;´ešhïÅ:fŠC_uõ~Ô¥NŞ\äZ·§‰yÑz‰úßGğØ/Ú’DÛÒ9E×T7Ù€Ì?£Új¼4ËYKbí×ğxHğÎÚ·İ}(ƒ³ãö'’ÄGú!€yï4ÂÿÎ¡ısc‚]˜´9nmı€V9=‚±S(î yn¸ux1`^?Ìÿ Œ—èYxS]‹1íkçW\èƒ
Û±ë¶„…n×B¶(èC¡‰ÉÍ$!îÚ_ß›Œ:c‘>4O3É9'çŞÜ³Qf·“·¯‚;L õVî ÑK½ü½ö¢…`@j˜R7‚1Êƒ¬A› L9dâpB (³PíLÓ)ÈÆH[É¬q—[ÃQ/m€*3¾8gÜÉYµÕÆ!µ0Ó˜÷±AXÂÎh¸ƒçä»³¯ó=×­9K”¢Èûµ&óÎÔR‹µeüÛ"¹"¬%:÷ğc0Ã=*cÔ–…èa:…÷ğ>c`ƒ›\\êèqæ©¯ËƒØ$øb¾¬¾§'©ãËÒ“ä¨=&AáÁZgö(Òÿ·jE´||…Xé€Zò!
‰šg‰£g*á
cáÌÖ±¦IŸ˜ŞFª;{lÛJ7NÊÿÅ»»ÂZ+y’_š:<3zÖ^Cÿ‰?7ï+s"1?‹"¿ÙP3ƒ‹uƒÁjeX/¢Ãj~ÖŞS$ÍK·ü®œ”Éîk€èTw”¿è|‚õÓñx+Ã.nJnš1;ê»‹rÇş¾EO×—$½•Ñ˜ÉG£Œá¤ •Ñ'±{¨–¾Æ†É£/¢ûhS®><$Cçzî¤]‘ÄHM Û>éP–XR†AÓ\îğ…f&õÄ€qŞ§äçÑ„jNçŠ†‰Æ£š<æà-U	0sÆÒ!8´ŠqÌ‰¨©Rßl() ŞJ{hŒˆ
}yv¨Óİ5…Ò\ŸıĞµ {èíBvJi_ç"¾ÃÑ¨øeòw0xİZkoÛÈígÿŠIÔÒ®ªÈÎîfaÀINÔµ%C’“A@PÔÈâ†"U>âEÿ{Ï¹3CRŠ’x5v‰MÎÜ™{çÜsÃy”ÌÕñÓï¿ÿş/‡ª—lîÒğf•«FĞT'ãTwá/Ó"ÌÕ0^Y†:;8Tİ"_%é©š%ñê‡½$òñüJ§ë0ËÂ$Va¦V:Õó;u“úq®-µLµVÉR+?½Ñ-•'ÊÇüN3LHæ¹Æa|£|`#‡±ù
‚²d™ßú©Æğ…ò³,	BÕ"	Šµs?çŠË0Ò™jä+­OíŒÇMYf¡ıòÂò´r/Õm5Š\¥šš”ÒÂ  *Ü‡{…ëĞ®Áéb!Zû/2èÁİ¶Ô:Y„Kş¯E¹M1ÂlÕR‹ÂçE‘:æ,èò$IU¦#n2`Z£qµCÅu`#ìÁš*ã“ÛU²ŞÖ&ä–EcYc	L'«ş¬ƒœO¸ÿeEÉ-’xRëìTo†·ş<ù E%ƒ„8É±c±¼œ…ìÄ±}•­ü(Rsm-‡¥Ã;áC§Ô,æY„~¤6I*‹îjÛ6›x9PÓñùìuw2PÃ©ºšŒ_ûƒ¾zÜâ÷Ç-õz8{9¾)Œ˜tG³7j|®º£7ê§á¨ßRƒ^MÓ©O°‰áåÕÅp€§ÃQïâº?½PÏ1s4©‹áåp±³±šaI+l8ÀÌsu9˜ô^Bv÷ùğb8{Ó‚¨óálD¹çã‰êª«îd6ì]_t'êêzr5°…>†£ó	Ö\F³6ÖÅ35x…_Ôôe÷â‚‹AZ÷:L¸KÕ_½™_¼œ©—ã‹ş Ÿ°»îó‹Yªõ.ºÃË–êw/»/¸Ã‰C5ä@³Gõúå€¹f{³áxDezãÑl‚_[Ğu2+'¿N-Õ§4Ëùd|I5iXÌÁ
ƒ™£‘C£‹¡Ê³Áîª»ı¨ş {i8¨dñµŞ>X¦@lßm€ópM¨oÌÃeç‘{&AØp"È kxÒS=Õ½µ%øºˆŒÂ¸ø¨Şë4Ö8Ç_€Ošï]z³ÁHÕÿœ©ÎÇNç¸£Ü—Ô‚¿¾Êu¬æp¯`n”¿X€2+`Ò¯OWÊèS@ŠµÔÂÏ}RtË"®/[ûY®S+a:_ÕePÂl!\R/ïüzÔó€óÙ¸7¾ğ.»£4¢?Og [)‚ó¿Û3ßsû¼òúÃ‰×í÷'œÊY'{f}nÕá‹Ñx2ğFİŸÌÂœüæÆŞ¤ïu{vº±Ô¦İî£õdĞ{å]T§Çõ;P›ó#ßä+Ğ³¡e˜fäğ@‡@>ó»\ˆ¦İWƒÒnÎ
g§”rá¬$ºÈ±Õ]&zpô›.Ë?ëüğù‰-¥? Fáò`kÅ=¿À  ]DôÜ1$!†`Ó€á"…é#Ù;€û|X:ÄØ-|Ç-t@â©z& åÆ³–z„÷òà–Eq5İÚò=…¼Ğ	dü…¿\:b	~æwÄğ{2é¿Ur¬gÒKÖó0†Ù'O^«‘>[BT#‰Äü$îŒ3^z•ùÉÊù‘rdûpƒ#{Õôòya?]ïÓäD !ãÊÕH–g`Of#XÉ †O2µĞKÙ5ìnˆ£}DÈ,Txxëì¦1â)Rİ<•õ–¡™‡cx[pãˆÆ?j)xEçÇ?4[µ—ËÈ¿ÉğvïK€˜÷¿œKyy5fƒIÃHø±Ùéïj›M·©'œé‘Šî»qèÈ­)·‚Õ»¹¥@lG™åŸ”ËÀ~@È{íqlA_ƒ8ıY£=~üø:N\¤Ç ĞÏMJ‘ê	²1ü.ö´p¢ö&Ù‘ä}_!¿Ê™Cd„8Ÿ…	·‡¶RÌgÜ¯jã§şZ“—	¾‰_²À6J9y±ay»
ƒødƒ0€äR|$D¢ô!\È^£Rhi‰©d—pmñ_\‰{0Bízˆ]ÌrÕwJGš©kvêúàG…6øäØ
` OÖšLµ@2àá5ìj¶eG0½ü5Ö¶[V~šú ì×ÙÓøÚ&M  lÈƒ42pú‚)+ø#ß`'g	7ƒÜ2©a^“¬BdÆ4‘‘²§8ÆJ„ñ0Š›ü6|×¦k‘õÖo;ïÔ_AÿÏÎE£İqÆVwünï ls8àdÿ ØÍxjªQrs†@’&©ÀhŒ#ÏŒMv`k•;B¡LÖ¶¦”Êñ-ìêScZŸà(¡2{€ôôÒG:¯ü\­Q—Àvxu‡J&6„É$ÉÑ™0c#™3ÿ¯œ’¾¿,"gÈBJf0ĞE—¼Ó­ å—ÚDèH0¶—sõd¡?<|À»¤š0E…TcpŠç¡Ì=¯²hÙÂÊÙÙ±ÄnG`;ƒ¨XßªlAĞ†)a áp`QQnXf°àp®/v+AâxÃ˜F¡(àsnüIŠ;bWô©»:V·ÂRF“R–ÓğoÇØÂp)’`3”H5zÂI™
4Ùà‡’K.*¥Ñ’°2|ZFò„±5c/k„r,-Õö¬aÏ€ÜØĞ%Ç!Óë˜ğUåk|/s¹DÃš"“ÔîA^dOaÇö‘¤É¨ÜAI‘â(¶™y	M4.OÄ1Q¹^%™†“ÔVêtÿz LıX÷c…3]».üPı
lJBŠ¤vø(‚³{l|/[ù†÷€›\˜¸…8ğ¾2İa-i7Ñv )+óR$.¬±s0ô£ò@ìhÛ-?Ö€­?BÈñ˜ßüÏw¬½«=d”¸Á”8ƒûeµs`“$àá8ŠÍ–yä¬íeóøÇîõÜ ihÓOâ# ¶Ø0øeÜœ'öÊã¼Pšøçö†Ç6áêÜÒÈI—¡šxŞ>½q!£,˜Ş0?ªre.\ù ŞŠJúÖÛ>ò]ÅQœ¦€kÍÁØ>’úÓ}*uId	®’%}Š”òÌÑ«6iDËÄOÕÒÁ† 2}ªVy¾ÉNŸ<™7Y{#\İNÒ›'è•eÙ³ïL ä±l)u&Ğ8*éåßÿµÁIk?Ÿm©£ôÛ92¹rOgJ´÷Ç§ªççHi†ãAšbŸşù*Eˆóá9³-/\ Ñe¡³ }+ôûXà;8Û4A÷¨¶Á·’!£ ÓÁ»tìÏI]XÆ²<DgD•şˆ|­Y’9ê»¢
EHšbDp9¸õMRĞ“¹Pá¡KUõK¹_,òÈƒEŒüµ A
¸–}TGá/•…^{\{Qh¹t!JC#;ß;&<Û†˜–š´$\¿Ìº3éd½.â0`:-I±UÖÆ²-“ ,K¹hÑ&äã¤)&xRõ¢ãÈ¼Ëä[5fµê±´şìf'ì† M‚[À‘8ÔtE¶İÉì}kc(»4zA[¸¯93şg·¦`<<Æ'ßKJ…Gê[£ù£üdØæJ,éÛfƒ—#,&ébÛHÔ`Ÿ-LÅEÑÆlHÎ×‹í#¼ŸU0T|ÿ ¥ëíŒ‡·Ô!2(&¾®‚fU"YİÚO]«7¿Õt!vê„MéUÜ]ÚÚ¥A£ÔÌœQ^{[½r+¹©şÎëBå3ùO+Ïª(§ó5x´-Õi©ã–«ØÊ[Gfòÿ¡z† jİşÕ‚5IôKt´vR•f“ã•œô±>’ÄO¼¬„½«ëyIæ2j’„Ä†f^­
£ô¯ú.›4-¬)ªVÚ’Ù–³Šã¶w¼ßÆ­'¢dÖÜçßuKî ¹„À(É%ÆH’&}<)Gtä¦Ø*H#APY‡ {ám^i…J•ÕCb
yš'-b¹8²±·zœEwHéòld„4«­ÎùÂ?ÛãUÇ?Ø"”ÖqKÿ¡İêÜ‰®yÃ¶3à¬â[­²AU¶ÀènÖÛ¶áø‡÷µy”ïïál¸Ee†ÇìŒ3àÖˆ¬rÃ°Kïãk38Œ¿N
ô±W¤i!â`l†­]”¢M']B7:_²>VŸß•Ë16€+ÕgSbÇ $ƒô°cÄ}i1U§Q÷5—^ÇĞ0/b$.ğÒŠÈ`hHjæ —•è’|ĞÒz+÷‚Fi"XE2„[Ö–ˆ>×”b7¯2:’ÇO­Q“W*Jºú>NnQéâÊ2Ú±YêÅ4zßğö,…ê•%#Y¸&Ğ8Ü­”T€êûÊ$©¢T «Šäæõ²Xø™=·J…Zò%¹jVŸ¡1[Õ¥°v…Ÿû"§<Ô„uÓ )õ lx¨(eĞğ»ñK"á4÷/²kŠÒ€÷AÂÿëÂ¹öxÑßx¦kàhªHü§ aìø×Ğ°ô3K¼üñ[æxˆ%x_s mŸ1yàvùBNã¹6!ZãÒ½ÜJÉ‘A²+ía?¾‡Ú[4{'L¦àÿ›)fMÇÌP¿Ù€,™\—Ö;T?³Ğ‘-S*ğäª)É˜ØåÇ/äZ3è3»¬Id2Ìü	+™ı@	š–İ¶Íå£î-¤°d­
®É£ê…;^ˆ°ŠØíš'˜‹¿E,üYQŞƒúûï™ê ˆ`ñÎÊÁ•Rj[V>(ğå8Øª5à&C×°İâİÑïğ9·¯Wç’¹œUé*ò‘|ÇK¢3j-­‹óêªÈˆ¶+Æjp|­œ¯,¸77û‚-%SriÕ'~xŸô¬=ˆ¥ycæ¿ª1¤Å¦¦‚ä}‚oz8ûK&²ÛŞ­¥–¬°ÿÉñØ»bÖÕñĞ"ì,ÕG^æìÕ”i(w"XÛÃ,Ïÿëè¹/>[ÛEHİ–Üw<öÀ¡Ô Ì¿ö•Æ–æäšÙ•´µº¸VÖÇºø7ãQ`?ĞÛÔ1£³ç/Ñ'¯0(gjñx~^ÑÉƒ£îKù=ôr_SĞ—À¯¥cåjÃšë~n.)‘2¦vŠC¸˜Á[y))îW«Ñ[Åwò”›+…™ä÷	Ù¡úÆ@r–À•Ÿ|'Ÿâ8oŞZÊ|—ZÊkÍ³:MÚk>fÔXZİR&‹Pë,N(¿lŒ qŠå"ü
P‡îã
–°œQiû†C²ÜÓùvo(*_ïg¼SKyÙÛÎiõU‚ğ”¨ ÖÔ€aš />(Ş¾¾V'~Gæó’ß¤úù<H³‹P+f›¼b’&ÔÊògøè¹ëøÑWbMY»$¸Op¬ &øêÍn¬üõĞ©(Š)'¾°Û‰Á&û–FÄö"o·`¾àô|eH\L(m7h¼0“ÇÕŠßÜ†šåÒ=H9Ÿş§áM<;5ÆáV,eğ™‚¡ö	.üœ„$V=v·òbñ Àf;9®:&¦H³Ó¥…|G”d¢„š«Öoš/´êå­\…üıW:¸+2IM,ªš\ø 
5ô•²ê;aµ†ù&Hw=–šYÜù\/ã·ô²E-\íkœìÚ&«Â´½(q×Lÿó–÷ÓÖˆĞğ¾ştíŠÉŒ[ùıÁŞPU÷J¿¨şGìó£9¹×Ùix	ïdËN‡Zñ#y_áÚ–—ö¸ú\ïâËˆÀÌÏ„Øä…cí™Ãıˆí\ÓlX†åJ˜bx«™@¿ªçVŒaïÂş¾ŒxİZıoÛÈíÏş+61PK=";×ä`ÀINÔÚ’!ÉIƒ  (jeñB‘*?âEÿ÷¾7»KRŠ’øzW÷®AØäîìÎì›7Ëy”ÌÕñÓ??{ö‡CÕK6wix³ÊU#hª“Îñ3Õ]øË´s5ŒE–§¡ÎU·ÈWIzªfI|§úa/‰üƒC<¿Òé:Ì²0‰U˜©•NõüNİ¤~œëEK-S­U²TÁÊOotKå‰ò1£Ó’yî‡qß(_ØÄal¾‚ ,Yæ·~ª1|¡ü,K‚Ğ‡DµH‚b­ãÜÏ¹â2Œt¦ùJ«ÇS;ãqS–Yh?‚¼0†<­ÜKuB"W©¦f¥´0(ˆŠ÷á^Gá:´kpºXˆVÀş‹zp·-µNá’ÿkQnSÌ£0[µÔ"¤ğy‘cdÆ‡9º<IR•éˆ[ƒ˜Öh\íPFqØ{°¦Êøäv•¬·µ	¹§e‘ÆXÆÁ˜EÓÉª?é çî™DQrKƒ$^„Ô:;•ã›á­?O>jQÉ !NrìX,/g!;1Gl_e+?ŠÔ\[Ëaé0ÆNøĞi5‹y–¡©M’Ê¢»Ú¶Í&^Ôt|>{ÓÔpª®&ã×Ãş ¯w§øıqK½Î^¯g
#&İÑì­Ÿ«îè­úÛpÔo©Áß¯&ƒéT'ØÄğòêb8ÀÓá¨wqİ^ª˜9ÏÔÅğr8ƒØÙXÍ°¤6`æ¹ºLz¯ »ûbx1œ½mAÔùp6¢ÜóñDuÕUw2ö®/ºuu=¹OØB‚GÃÑùë.£Yëâ™¼Æ/júª{qÁÅ ­{&Ü¥ê¯ŞN†/_ÍÔ«ñE€‡/Ø]÷ÅÅÀ,ÕzİáeKõ»—İ—ÜáD!‡r Ù£zójÀ‡\³‹¿½Ùp<¢2½ñh6Á¯-è:™•“ß§ƒ–êN†Sšå|2¾¤š4,æ`ˆÁÌÑÀÈ¡ÑÅPåÙ`wÕİ~TĞ½€4Ô²øÚo,S 6Èï6Ày¸&ÔŸÌÃeç‘{&AØp"È kxÒS=Õ½µ%øºˆŒÂ¸ø¤>è4Ö8Ç_€Ošï]z³ÁHÕÿœ©Î§Nç¸£Ü—Ô‚¿¾Êu¬æp¯`n”¿X€2+`Ò¯OWÊèS@ŠµÔÂÏ}RtË"®/[ûY®S+a:_ÕePÂl!\R/ïüzÔó€óÙ¸7¾ğ.»£—4¢?Og [)‚óØ3ßsû¼öúÃ‰×í÷'œÊY'{f}iÕáËÑx2ğFİ¿™…9ÿøgÌ½Ißëöìtc7¨M»İGëÉ ÷Ú»¨Nëw 6çG:¾ÉW gC;Ë0ÍÈá?‚|æw¹>+L/º¯¥İœ:Ï;O)å:ÃYIt‘c«»Lôàè=7]–Şyöå‰-¥?Fáò`kÅ=¿À  ]DôÜ1$!†`Ó€á"…é#Ù;€ûbX:ÄØ-üÀ-t@â©z. åÆ³–z„÷òà–Eq5İÚòg
y©Èø¸"tÄı(Ìïˆá"dÒ#ªäX!Ï)¤—¬ça³O¼Q9"}¶„¨F#ˆøIİg¼ô*ò“•ó#åÈöá:4G2öªéå‹Â8"~ºŞ§É‰ BÆ•«.,ÏÀÌF$°’AŸdj¡—²kØİGû ˆY¨ğ$ğÖÙMc*ÄS¤ºy*ê-C-2Çğ®<áÆÔR*ğŠ0ÎŸ5[µ—ËÈ¿ÉğvïK€˜÷¿œKyy5fƒIÃHø±Ùéïj›M·©'œé‘Šî»qèÈ­)·‚Õ»¹¥@lG™åŸ”ËÀ~@ÈíqlA_ƒ8ıY£=~üø:N\¤Ç ĞÏMJ‘ê	²1ü.ö´p¢ö&Ù‘ä}_!¿Ê™Cd„8Ÿ…	·‡¶RÌgÜ¯jã§şZ“—	¾‰_²À6J9y±ay»
ƒødƒ0€äR|$D¢ô1\È^£Rhi‰©d—pmñ_\‰{0Bízˆ]ÌrÕJGš©kvêúèG…6øäØ
` OÖšLµ@2àá5ìj¶eG0½ü5Ö¶[V~šú ì×ÙÓøÚ&M  lÈƒ42pú‚)+ø#ÂNÎn$¹eRÃ¼&Y…ÈŒi"#eOqŒ•ãa<7ù]ø¾M×"ë­ßuŞ«?‚şŸŸ‹F»ãŒ­8îøıŞØ.æpÀÉş°›ğÔ8T£äæ2$MRÑG›ìÀÖ*-v„B™¬mM)”7â[ØÕçÆ´>ÁQBeö é#<é¥t<_ù¹Z£.	€7ìğê•Ll“I’£3aÆF2gş_9%!|Y0DÎ…”Ì` ¡Š.x§[=@Ê/µ‰Ğ‘`l".çêÉB|ø€w?J5`Š
©Æ,àÏC	˜{^eÑ²…•³³b‰İ:ÀvQ±¾UÙƒ SÂ@Ãá2$À¢¢Ü°Ì`Áá\_ìV‚Äñ†1!BQÀçÜø“wÄ®şäSwu¬n…5¤Œ&¥,§á÷ÇØÂp)’`3”H5zÂI™
4Ùà‡’K.*¥Ñ’°2|ZFò„±5c/k„r,-Õö¬aÏ€ÜØĞ%Ç!Óë˜ğUåk|/s¹DÃš"“ÔîA^dOaÇö‘¤É¨ÜAI‘â(¶™y	M4.OÄ1Q¹^%™†“ÔVêtÿz Lı	X÷c…3]».üPı
lJBŠ¤vø(‚³{l|/[ù†÷€›\˜¸…8ğ¡2İa-i7Ñv )+óR$.¬±s0ô£ò@ìhÛ-?Õ€­?BÈñ˜ßüÏw¬½«=d”¸Á”8ƒûeµs`“$àá8ŠÍ–yä¬íeóøÇîõÜ ihÓOâ# ¶Ø0øeÜœ'öÊã¼Pšøçö†Ç6áêÜÒÈI—¡šxŞ>½q!£,˜Ş0?ªre.\ù ŞŠJúÖÛ¾ ò]ÅQœ¦€kÍÁØ>’úó}*uId	®’%}Š”òÌÑ«6iDËÄOÕÒÁ† 2}ªVy¾ÉNŸ<™7Y{#\İNÒ›'è•eÙóL ä±l)u&Ğ8*éåŸµÁIk?Ÿm©£ô»92¹rOgJ´÷Ç§ªççHi†ãAšbŸşù*Eˆóá9³-/\ Ñe¡³ }+ôûXà;8Û4A÷¨¶Á·’!£ ÓÁ»tìÏI]XÆ²<DgD•ş„|­Y’9ê»¢
EHšbDp9¸õmRĞ“¹Pá¡KUõK¹_,òÈƒEŒüµ A
¸–}TGáÏ•…^{\{Qh¹t!JC#;ß;&<Û†˜–š´$\¿Ìº3éd½.â0`:-I±UÖÆ²-“ ,K¹hÑ&äã¤)&xRõ¢ãÈ¼Ëä[5fµê±´şâf'ì† M‚[À‘8ÔtE¶İÉì}kc(»4zA[¸¯93şg·¦`<<Æ'ßKJ…Gê[£ù£üdØæJ,éÛfƒ—#,&ébÛHÔ`Ÿ-LÅEÑÆlHÎ×‹í#¼ŸU0T|ÿ ¥ëíŒ‡·Ô!2(&¾®‚fU"YİÚO]«7¿Õt!vê„MéUÜ]ÚÚ¥A£ÔÌœQ^{[½r+¹©şÎëBå3ùÏ+Ïª(§ó5x´-Õi©ã–«ØÊ[Gfòÿ¡z“† jİşÕ‚5IôKt´vR•f“ã•œô±>’ÄO¼¬„½¯ëyIæ2j’„Ä†f^­
£ôoú.›4-¬)ªVÚ’Ù–³Šã¶w¼ßÆ­'¢dÖÜçßuKî ¹„À(É%ÆH’&}<)Gtä¦Ø*H#APY‡ {ám^i…J•ÕCb
yš'-b¹8²±·zœEwHéòld„4«­ÎùÂ?ÛãUÇÏlJë¸¥ÓnuîD×¼aÛpVñ­VÙ *[`t7ëmÛpüÍûÚ<J‚÷p6Ü¢2ÃcvÆpkDV¹aØ¥÷ñµÆ_'úXˆ+Ò´q°6ÃÖ®JÑ¦“.¡/Y«ÏïJÇåÀ•ê³)1†c’AzØ1â¾´˜ªÓ¨ûšKH¯ch˜1xiEd0´$5s€ËJtI>ji½•{Á£4,"Â-ëKDŸkJ±›WÉãçÖ¨É+	%]ı'·¨tqe	íØ¬õbš½ox{
–Bu‰Ê’‚,\hîVJ*@õCe’ÔQ*€‡UOErózY,üÌ[¥B-ù’\5«ÏĞ˜­êRX»ÂÏ}‘SêÂºi€”z 6<T”2èøŒİx‚%‘pšûY„5EiÀû áÿ‹uaƒ\{¼èo<SŠ5p4U$ş]0vüŸĞ°ô3K¼ü/’}lü0)O-u¿eºçc‚5_Úv“nW2¤Ÿë¢K.Ì­ìÉ$»²Ò)öãĞ©½P³×Ã`jÿïM]kšg†ıüÍ¼É<»4ä¡ú‰5l™R-WXIòÄN)¿ƒ!íšA_ØeM"ób¦RèXÉlJ\xÔ´é¶mî(p…!5&Ë.°qMÅP/\wğn„Q„q×GÁ\ü-b¡ÒŠıÔõÍ¬õëx®rªÛZ°ÒğA}@ƒ][nú@Û-^#ı: sûv¡.IÌY•i 8/Éw¼/:£ÖÒÅ8¯nŒhë¹b¬ÇF´àŞ4í+¶äœ2ÃúÌï“©ÕÓ¤±4/ïÑ'á6†´˜Ì¸$*H
(ø¦‡³Õd‚¼mSğÑZÊÊ
ûŸ½6f)R-Â&SíxäåñÎîPM™‘r'²€5±=Ìòü¿û‚à‹…ñW@°]ÔmÉ}WÁcJÊTl_•liŞAnœ]u[+‘Kae©üû(‘1å öãÑ ½½AIÓ8:{ñ
-ó
ƒr¦çç<8ê¾–êC/÷a}	|ñFšW®L¬¹î7áæò—)3`j§N„‹¼•÷“â~µ"mV|2 O¹¹R˜ÉƒŸªÏ$g	\%ÊwòUóæ­¥Ì'ª¥¼°ÖG«Ó¤½ñcÖA¥ë-³µÎâ´àˆò#Á§xQ.Âuè¾³`5Ë•¶_a8äÍ9ïö†¢òõ~Æ;µ”—½ëœV(O‰
òM¦·	ğâÛâ}áë[%ãWpd¾4ùE@ªŸÏƒ„1»µb¶É‹!&iÒS­,ÿ6ƒ^s»I€ß}%ÆÑ”µû‚ûÇú·âi‚@ÑÓĞìÆÊÿ:E1åÄÇv;1ØdßÒ“Ø^äİñ¬Àœ¾‘‰kÁ“	¥â=fò¸eCqà›‹Qs¹\º)çó?â4¼”gÓÆ8ÜŠ¥¾¸Cpâ1Ô¾†ÂİŸ“ğ€Äjc Ç†ğV^,Øl'ÇUóÄivºt¤ïˆ’L”PsÕšáMó±V½|£•«¿ÿv×F&©‰¥YU“D¡†SV}’ ¬Ö0Ÿ§é®İR3ëƒ;Ÿkkü’¶¶¨…Û¢}=”ıQÛ¤`U˜¶w&îÆé¿Şı~ºÓ%Ş×ª®İ6¹‚‘c+? ?ØËªêŠégõÂ‹­p~?'W<; áõlÙéP+~/ï+Üàòş·Àa‚›^|$±˜ù»¼p¬=søo¡±³kšËğ“Ü³io5èWõÂŠ1"ìµØ¿ !BxmRÉr£0œ3_¡Û\™ B,UÉT ÛÛ,Şo Äf³	ƒùúq2×ô±û½ª®îÆuYæ(úÅZB€€T‰‹BC‘D0’a‡¡„¢^Ä² U‘kÂ–T„Ô’I²Š‚(ÆPI"	Å±€$óXE¢(c‰;–Õ-pÍ²°Çm0ğF¿ˆVéÙŸºMÿ>=@¨ Aƒ¼ğ
ÏsøÛ$#-°r¶è"ğVÕ-in4gYıyüğ–6)ÍSğòcfÙàZ.lk£ïöşì›ç zj`C×S×=Ã[Fá¸ÔLßX)Y!mï°µ{]¶­›Ç‡u\¬­¼ò»îT5…Øu'›ÈK²ß@+¾ÍiÂW¹‘%…‘¯ÌcÒRõêuÅlv5æŠŒxÏ0ª^84^@EGŒ‡#áÀÄ£{7LÒ@ß÷	“VîÃÕöóR/¥*NÆÕ|ª›òöyÊ•À,}“ZÅ3Nš]ë*àn<qÀVÏVìõI44ª²»ˆ.?½OªZ‚ÌÒõÔ1¼¤]Êkw½º^¶ÓmMFGŞ±:°rÆ±7†®BÁ|œ¿"3÷=ÿÓ­/Öc©.Ï÷1¨:»©Ò:S?“hq~]Ñv´R^n·‘ã&8<|Ñm@:ß.Z§ğBÑ°No¿,œC¦ªâêgMõ¬(8à‰/ÛîEß.Nö;Şûa#pÿ;›m¦?7Æù¤¬ï¡¹åø9ß:*f ¯2ÒæÏ-aÂq6ûMAU3P“ø)‚æñ­‚ÿ €ëéx+)JMU0²4f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-sSÓŠJ3KâJ‹R=ıªÖó,Yôƒkÿ½7&ä4v»çBÍóñtvõve¸ ,»Ÿ1u[‚êY›‚£
Ì*!P%A®.¾®z¹)kû¬ş¾ÚWİP¶ “ÁeÂ†MG»¡ŠR«â‹SKJô
*”_ÍÒ®Ûûöc“İ¥¶õÕŒbçç®ZUWÓ|O;îtÒ§¿Û8—X–
uY0ãÕRˆãKR‹KŠ¾<s³¸cYğcJçïÜ”µk[÷:?t ápx~x+)JMU0²4f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-sSÓŠJ3KâJ‹R=ıŠî9sı	Ë‰—ö¾º*y¬ç½/ßf¨y>Î®~Á®Tƒe÷3¦ncKP=+cSpTY%ª$ÈÕÑÅ×U/7…amŸÕßWûê¯Êt2¸LØÑ°éh7TQjU|qjIi^A%ƒò«YÚu{ß~l²»Ô¶¾šQìüÜUk¡ÊàjÒY5r®ÜQcmİ_±üÉ¯Y—ïüHÌƒ8¾$µ¸¤˜áË37‹;–?¦tşÎMY»¶u¯óCw úWyİx-M‚0…]Ï)^â¢+š(A#§ğ
­Ø¤¶u:¨Ü^¬Ş÷~’çcö8t—]tiİÀ=Ê¤ÏœˆVí	h`ölVjíÉ…TÕÅ¸¶%lğ{Â/NZ­ş”¨Ş$İÆ“rUì‘e¾²‹yÌ|]nña©!§ŠÖvpéÏ1é²°4 x“ËŠÛ0†»öSœ˜1é´´ÌÀ@ÓÉ¢†”’E¡” HÇ©¨nèâNúô=²;ĞEµ’åï?üç¶Wvfoo5àŸ]À˜Hí¬öÑZŠëÏÉ´èD¢Î²îåiÄÎ1ş‹0W,ÙHôá{¹À•uM„Md1xz‚÷pŸ1²ò®€ëS®z¥9Àæ"êŒ¯W›ú[¾,¥I¯7DKÉÑÌ¡0wÎÛEşşZoIÖı¾!¬MD#ˆœ'!Ñğ.ÄÉ3¥pC±ööà™ÖÙá’™C¢¼;ÇøÓš|{¨>ş—îİÕÖ:ÉsĞmâoæ.
úO~(ŞæEV–?Š¢ëÙÄ0×U†r.Xã“Œ»uòX¯†Ø-•ARbã!xVÍª·Â¥îG ¨óåÖš#,ä‹Uc—{p‡šIÕãF!9AŸØÉ@Å­BÜKG¤ÈÁõõÈ
+0M‹€¯ÔĞl8Lq!@´ıÜ@½i¸¢NSïê‡`FÀf]W oixtŠqìÆµ¡œ‚ŞÓÄf.8)°mERªÁ¡:Ş˜>9¤¡€Ë8'}ñvŞ€ó
]Æ¹Ú­ÉtZü¿i¸x+)JMU02µd040031QĞKÏ,ÉLÏË/Jex$Æ»£x>ï“Ù*Ó›ê8Üf¹/­l11 Ç”Ä´¢ÒÌ’ø€Ò¢TO¾Ì•Ygâ=›fòØä	É]ax0Ùj§³«_°+ÃÕ`ÙıŒ©ÛØTÏÊØU`V	*	rutñuÕËMaXÛgõ÷Õ¾úë†².v4l:ÚU”Z_œZRZ WPÉ üj–vİŞ·›ì.µ­¯f;?wÕZ¨2¸šçarMÆz—Ş¾K}TsÁ|ïÎÇ—¤—3|yæfqÇ²àÇ”Îß¹)k×¶îu~è ßfx+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤Òb­	ş^İ&Ì;Ëö´Äµ½I +ü½ -ó!Çxİ[koIİÏşåXZÃCÀÉ&‘%À€vl° ÇEQ«i
Ó“¦›íGlkµÿ}Ï¹Uı€Ä³3ëÉlMìîª[uo{î£zfA4Síg¯Ú/şr ºÑú>öo–©ªyuuÔj¿P¹»ˆ3?Uƒp%iìëdï@u²tÅÇj…÷ªçw£Àİ;ÀóK¯ü$ñ£Pù‰ZêXÏîÕMì†©7Ô"ÖZEå-İøF7T)ó×:N0!š¥®úár•‡@Æ¦KJ¢EzëÆÃçÊM’Èó]HTóÈËV:Lİ”+.ü@'ª–.µz2±3Ôe™¹vÈóCÈÓ*©n}¨‘¥*ÖÔÌ£”yA6ç>ò×¿òíœ.¢°ÿ,ÜmC­¢¹¿à¿Z”[g³ÀO–5÷)|–¥™ğ¡§CÎ‚.O£X%:àÖ ¦5—;”Q\6Â¬©>¹]F«Mm|îi‘Å!–…q0fÁt²ê/ÚKù„û_DAİRA/
ç>µNåø¦xëÎ¢OZT2H£;ËËYÈNÌÛWÉÒ5ÓÖrXÚ±>Ìµ‚šÙ,IßÔ:ŠeÑmm›foúj2:›^wÆ}5˜¨Ëñèí ×ï©'	~ÒP×ƒé›ÑÕTaÄ¸3œ¾S£3Õ¾S?†½†êÿãrÜŸLÔhŒM..Ï}<»çW½Áğµ:ÅÌáhªÎƒ)ÄNGjŠ%­°A3ÏÔEÜ}ÙÓÁù`ú®QgƒérÏFcÕQ—ñtĞ½:ïŒÕåÕør4éc=†gc¬Ó¿è§M¬‹gªÿ¿¨É›Îù9ƒ´Îts—ª;º|7¼~3UoFç½>ö±»Îéyß,ÕºçÁECõ:×ÜáX ‡r Ù£º~ÓçC®ÙÁßît0R™îh8ã×tO‹É×ƒI¿¡:ãÁ„f9.¨&‹9Xb0sØ7rht1Tq6BÃ]Aõ|?ª×ïœCjY|oî-b ÖKï×À¹¿"ÔæáÂÓ æG^ìÙpÌK÷ kpÔU]Õ¹µ%øºˆü0»Suê œãÎÁ'õ=Œw.œi¨ªNTë®Õj·”‚û’Zğ×U©Õîå-ıµrçsğAbŒ{ÕéJ­6ÄXKÍİÔ%µA·$pá:ğ²•›¤:¶&ÓÑeU%¼jµdş‚z9gWÃ®œOGİÑ¹sÑ¾¦íüáh2Ø
œÿ|Ç|;.ßwÿ­ÓŒN¯7æTÎ:Ú1ëK«^Gã¾3ìülæüö¯˜?9ãÓéÚéÆnP›v{ˆÖã~÷­s^×oAmÎtx“.AÏ†v~œÃ=íùÌîS½'V˜œwŞö»åVh½l=£”«g%ÑE­zì2Ñ£wóé²üËÖ‹/Ol(ı	0ò{+îø è¢ç!	1›ç1ˆ÷eï îé <tˆ±[xÎ-´@â±z) åÆ“†ÚÇ{y
pË"„¸šlìÀ
ù…¼Ö	dü¹»\:B	nà§÷ÄğG2î]‚J9VÈK
éF«™Âìã§×*E¤OU‹B1?
ƒ{ãŒ—ın)B~²r^Ql®Ccp$c¯š\œfÆñÓÕ.M2®X}tayöd6"•bø$Qs½]Ãî†8š{^€ÌBùG³Jnj!,Öõc9Pgáë`88†÷Å	×iüÃ†R“ùaÚ~QoT^.÷&ÁÛ/bNÜır–-äååh0œöÇ5#áU½.Ò?ìU6ÏocG8Ó!=tãĞ‘[Sù
Vïú†¡e–vT,¿û!µÃy²Y|âtotböäÉ“«Ô8åà"=z€~jRŠX§HX]ˆá·t±§…Cµ×Ñ:$ïp¸
ùUÊ"YkÏÇùÌ%Hä{h*Å|&ÿU­İØ]iò2Á— ñ@ØF!'ÍÖÌ o—¾·Ÿ¬\ŠøH”>ùóÙaTM##M#1•ì®-^àŠ+qF¨]±‹Y®z®t ™º&ÇyÀQŸÜ Ó?‚û@ô)Ãz@“‰ H¦ <¼†]ÍÀ¦ì¦—á¡ÆÚvËÊcdƒıæö4¾¶#(ò œ¾`ÊáŠ ¾ÅÈØI-·€D>ƒòeRÍ¼&YùÈŒi""eqŒ¥ãa<•|ò{ÿC“®EÖ[½o}Pı¿<¶Ç[q\ûÃÎØ.æpÀÑî°›ğÌ8PÃèæô2$MR‚ÑG›lÁÖ*-v„B‰¬mM)”7â[ØÕçÆ´>ÁQBeö é#<é…‹t<]º©Z¡.ñ€7ìğò•Lh“IRNgÂŒµhÆü¿tJBøá²`ˆ”!)™Á,@B]ÖğÎ|u)¿Ô&BG‚±¹¸œª§sıé)àŞı$Õ„ç)J¤³€S%`ê85”E‹VNN†ˆ%vë<z ;7ˆ
õ­JVm˜z‡!åšeÜõÅnHrŞ0&¤Q(
øœ’âØÕw.uWmu+¬Á e4)dåşÔÆ‘›¡DªĞNÊT Ñ?”XpQ!–„•áÓ2’'Œ­{Y#ci©¦c{ä††.9™–XÇl„¯J_ã{™Ë%jVß™¤vò{
[¶4€˜!MFå‚Œ²GÉ°ÍÌK°h¢qq"9ëyA”h8Ie5¡w¯ÂÔwÀº"°à(„ìrÓ5«ÂÔßÑ¡À¦$¤Hjg€"X1»ÇÆÁ÷²U‘kx¸I…‰ˆKÓTRZ»¶MYšï€ú qa‚¡÷‹± m7t¼« [ßyBÈñ˜ßüÎ¶¬½­=d¸Á”0û%•s`“Äãá8²õ†yä¬sÛËæñ»×37 ¤¡M/
ØlÍà—psZœØ+KğBiâŸ›Ø„kî–9aœäqª‰çÍÓë2Ê‚èõÓÃ2WæÂ¥à­¨”CßzÛ@¾­8ŠÓp­8ÛG’@¾O¥.ˆ,ÁU´ O1"£ƒRœ9zUÀ&h™ø™Z¸>ØD¦Õ2M×ÉñÓ§³ì&i®…«›Q|ó½²L£,{ùÜJË†R'B µÃ‚^şÕú÷aœ´rSñÙ†:Œœ!“+ötÒ*eAËQot¬ºnŠ”f0êÇ1öÉàŸ.c„8‘2{Ğò"Ï$ºÌuâ¡o…~_¸Âä6Ğ=ªùMğ­¤CÈ(Ètğ.º3R–±¬Ñ	Q¥ï¯Õ+@2gB}7ATÁ ISˆ(.·¾‹2z2—c*<a©²~)ökâ‘Ey0‘ß¡ HÃ²ûUş:PYè5·Áµã…–r 44²óm°cÂ³iˆIQ¡IK"ï—Y÷`&­VYè{L§%)¶ÊÚX¶á`”e©<Z4	ù0ª¡GŠ	T½è82ï2ùV…£Y­:,­¿¸Ù1»!H“àp$5]‘Mw2{ßØÊ.^Ğî+Î„ŸâìVô@ Œ‡ÇX£áòrI©ğH}+4”{ƒƒıtÿ°À‚‘¾iv1x1ÂRaÏ7DÍ vÙ"©£a‡Í£ vİÿyR=—¦ÃdH»bJPÎ08Bµ²šï°È7a‚iˆM7 8¶\ä×ãCç )%+¼¥À2MÒÜ•ç½ïôV“SØºz5Q VĞ¹¾­Ùj4JwI¤•·å«|e#7ÖÿÄÂiU¨<`ióy)^v)ÈF5b½¡ZÕnä%c›B½Ÿ³»ü{ ®c[µ¹`E	ã-¾-T¥^ç¸%Øoà#{BB—¥°U=/HåFM²²ØĞ:¤™W)K)ı›dÆ®UkŠ…Ê•6d6¥â.‚Û¹<Æ­jG¢dRßExUKn!¹€À0‚É%èJÖ*M©Ï…¥¦úÌÈ«RÑjğÿ$ñ~L+”î,§"ÓÙ yâ,”›4›ŒÔPÀ#HÁ=rÜ4=!õ2i­ÁG!äÛãUí¶*§uò¥¿k·:wâ¡fû;pVñ­FÑ±+z‚t7ëm›püî}mDŞÇ8®•™ò2]å¸5R¹rÙL.âkS8Œ»Š24öW¤‹#âqÌÙ\å}aŠ6W’Ë ˆ¬ÃÅê³ûÂq9Æf4JõØ%‚Ã1ÈQ@zØ1!é¹•§Qõµ<C¿
¡aš…Èäà¥%ÁĞC‘\5g ÜŞ¢môIK/²Øn\¥«biÙ!®oX3»dÜÛŠİœÒèÈ¦?·FE^¡ˆ/ùûÇ0ºEé;Ü@hÇ¦¡( ãTè}Íëd°Êm”ÚŒdáŠ@ãp·RcªK“Ä®Ú	<8(›LR¬TûÂÏlB–*l$`8~ñr9t‚fuY«Ãà%„
â\ÏÍu“Éz
m -*<4L\Fp<ÁªÈÃÍµ”¬ÃR«0ãCğğÿÅ½°Aª~ÿŞ8¦B­™*CòŸ‚Í¦-%*ş:K· Ë™ëdCH3vo2Ì(‘æ) 6)‘½$'i„f_
	3˜ß/S¦[f‹(ÊûXqÅM×3åfÊOvwæXÜ:Hcx#¹G.Ê.·tŞİğll/(íu;˜^ÊO¦O`š‘†<İõ´Ë4½8„õkHÙ2¥“y¡*¹;Ïü®ˆ¬m}a—‰L«™‰¡c%³Õ*ae¿nù5ß¶¹WeœÁ•Ôì,cAæyC½p}Ä»&6š‘ä})ÌÅß,&.ÉóQ9ã÷LšP°/Â$/<¤‹a-Xjø¨ş#ÇÁ.¸7_Ávƒ×r¿ÀåÜ¾İøè¤LTĞì(Éw¼;¡ÖÒ:+oá6:b¬ÇW¥wfy_±%­^$hŸùáC½j–õ(–æÇè;ñƒ%CZÌ…ò*H)ø¦‡³ug²Ûåà/¢µT¥%ö?;{ÏJ¦<Z„M»ÊñÈËöÎî@M˜Ğr'²€5±¥áâü¿‡‚à‹uõW@°YÎTmÉ}—Ác
Š4nW‘mi>7‚ÜàçÅq¥Â.„•öŸ£ÂşÍx”ØGôæQíğäô® JÊ™Z<•tòè¨ûZ¥ ½òUèKà‹ké}åUfÅu¿	·<)2¦¶ÊL¸˜Á[qß+îW©1Ñ¶Æ'ò”›+„™ú)Ù¡ü|Cr//dùN¾rÊ½yc)óÉo!Ï¯´áª4ioP™uPc¹E‚[„ZgÉµàˆâ£Á§p^,Â,µŸ·Âb˜3Jm¿ÂpÈ¶kr:?îEÅëİŒwl)/yß:.?øä›¥
0LkàÅ·Ú»Â×·*Î¯àÈ|¹ó›€T=Ÿï&ŒU¿’#|úŠæ…ïvTûï¹$&‡øÌp+Zš<Yš›‹¼oo  ÍékùÔ’”“7A¯–İ ÙÂœ÷‹Hã]s%l®Õ “>ÿ#ğæçìÎ×X²èÀ·†#Èj«ßáÖ3—ğˆh£•ÃÎïF+Xl7ÓØ²EbÊ);]ZOÈLDI¦4¨*]ïºùL­ZhÑÊepŞ}ƒû!“~„Ò•ªÈ…· ¤B/))?Æş©™ó*¶ŠYÿ 7ùí·B¢®…vµIvÇW“,•Õ´"ŠË£ÿy›ûÙVWZsW'¤r­”—v[úıÁŞJ•wI¿ªéı=ö¼ùå Üålµ&¼ˆÓEOB-ù
¸
w×ür÷ß~„;n|²Bùí„|ZašˆÂ±öÌ%äî³…kÚÿNîÅÙ†·š	ô«j´·bŒ{ÿõÎÑsaxmTKOÛ@îÙ¿b8I…Ô^z£Bm= qŞØ“xï£»³ş}¿ÙØ*NQ¼ö|ÏÙı÷tûåöë§‡Ñ…½ÄJ‡˜©ÏìTÂ‘¥:M”ùOå¢¤‘ú4Ë¾*Û¿»Ár½,ôSôWİã|à‹î;c·y1q ùuHšØûû$<·“Cœ¦8Ş±ÊÀ“.äÂ@*© ¦yJ$J{&os1@¦’ |ÌNyøÖu[Úlî¹ô jÀ+= )Œ$Aà‘·[ÙñæÑAŞ9?¥!.€í ¹¬¥#û´½E43`}ä <ì6¢‡Q
Íw»Z¨†sQ#îÂe)§bCVšˆ©ëÈİ”í“Sˆs I¼(üÁ t|+ Aÿ@Düì<œ$YH6yoRÂ¥’K	!"G¥¦3\¢49E0~•6É>»ü‚ç-ÏÁPáôBî÷UM‘¢Pô
lÌÈŞĞáÜbmf¯Fµ64ÊnÍyj½	a¢d'ª­|¬<-ø\C°>4ÄÏ‹ÖÒœ^<QØ‘)ÇKßvG'áÜãµ¬˜uAôˆ-0…d8cÃÚĞ¹7çNt®P‰0¿3ŠâÂ¡õVA7;”G5Ş‚[ÊŸ9Å"³ O@À™;6E ñAc‘Mæ’¢•<?1(-[¶³nYİĞ¯)0‚Ã;ûê“yßÜŸĞ©Î¸½_Ï+¬HØOU•sëÚ ¥¯¥X®K¡œk˜v7•ˆÊ5›cóaíÔºõàÑO±à ğ–Ü«_Ãv[¢gozGîRˆW“°oºâ¡ö­ß7¶ÉmGQƒkòrµ!x§ıøÁD[·7¼ºoì™õ¦ém÷MÁÊ÷H-z_ƒ(â­z`:, öÒ¶tIÍ»NàÈ´bœ˜ÓÛ¥Ã¡ymÂÙ¬;˜Ãç[¬UÔŞ^_ûˆrØ…jëKíÆ´;CùYé£otß©éşgKø%xİ[ksÉÍgıŠ¶UA#$;ö–ªô²ÉJ dÇårMC#f5Ìy«Rùï9çvÏ„l9»Q¼Ùr­é¾İ÷ö¹ç>z<¢©:zñ²ÕúÓ¾êD«ÛØ¿^¤ªæÕÕqëè¥jÏÜyœù©ê‡³,Ic_'{ûª¥‹(>Q“(¼U]¿îŞ>~¿ÔñÒO?
•Ÿ¨…õôV]Çn˜êYCÍc­U4WŞÂ¯uC¥‘r1¥ã¢iêú¡^+WyØÄalº€ $š§k7Ö>Sn’DïB¢šE^¶Ôaê¦\qî:Qµt¡ÕÓ±ñ´.ËÌ´@BVùCµö¡F–ªXS3RäÙŒûÈşÒ·kpºXˆVÀş³zp·µŒfşœkQn•M?Y4ÔÌ§ği–bdÂ=rt9Œb•è€[ƒ˜Öh\îPFqØ{°¦JøËz-7µñ¹§y‡XÆÁ˜YÓÉª¿j/å/Üÿ<
‚hM½(œùÔ:9‘ã›à©;>kQÉ !ŒRìX,/g!;1Gl%7ÔT[Ëai?ÄNøc®ÔÌ¦I
øn VQ,‹nkÛ4›xÛSãáÙä}{ÔSı±ºßõ»½®zÚãûÓ†zßŸ¼^MFŒÚƒÉ5<SíÁõKĞm¨Şß/G½ñXGØDÿâò¼ßÃ¯ıAçüªÛ¼Q¯1s0œ¨óşE±“¡š`I+¬ßÃÌ3uÑuŞBvûuÿ¼?ùĞ€¨³şd@¹gÃ‘j«ËöhÒï\·Gêòjt9÷°….úƒ³Öé]ô“&ÖÅoª÷_Ôømûüœ‹AZû
:Œ¸KÕ^~õß¼¨·Ãón?¾îawí×ç=³Tëœ·ûÕm_´ßp‡#5„jÈfêıÛäšmüéLúÃ•é“¾6 ëhRL~ß÷ª=êi–³Ñğ‚jÒ°˜ƒ 3=#‡FCgƒ!4ÜTÏ÷£º½ö9¤á ÅÇùğæŞÓ§OûÇ€#ÕñÜ¦Ò…›ª%œË¢½Ë[¸c¨Æ¯³Dµ/ûMÌØÛ›Ç º—Ş®àş’ØQ“AÊÏğ<ùpô2ÿôüŸÜ$m c²NC]ûƒ	,µKL¬A#İ3¼v¦Ù|®ã†§qæ¥Y¬Í”¹¦A¾°yi°gwy¸=©V‡;¦G	ÌÁC²`à‡Ùu£ãPàCw®«cÆêOÒ’ƒ;ôéÔ=[/üT'+XfgÒ¨ê§ªõ¥Õ:j)î!/â«Rª)¸Á[ø+åÎf ³Ä
u«Ó•2ZG İA nê’—aá$pá÷ ˆ%ì§c+a<^VePÂÏ­–lÁŸSqçìjĞqà¤“agxî\´oˆ ;0Oà)…Î±c¾—ï»÷ÎéöGN»Ûq*gï˜ußªı7ƒá¨çÚ¿˜…9ÿè;æ†Î¨ë´;vº±Ô¦İ¢õ¨×yçœ—§Çõ[P›ó^§ÄÃ™s?N€<ísNoS½'VŸ·ßõ
»åVh½j=§”«„îÃĞ(ÇV=v™è€¥:ùtYşUëåıJŒüùŞÆŠ;¾À  ]@ôÜÂ• ±iÀpCø‰ìÀ}İ/bì^p-D X½ĞrãIC=Ásùà–Eq5ŞØòW
y£Ï®fî
pEÜ%~»ŸŞÃ7"dÔ}/*åX!¯(¤-§~³ß«iJPµ(D&ğ£0¸­‹œË^§!Ÿ¬œŸ)G¶×¡18’‰ƒ¡1™B»Ú¥É± ÂĞ]¾z…t¸‹È7–ao¦Z’5‚!%j¦ç¢ÎÅ0+S5„`ZîsWX×Xb-)Ç1Î¨	ÛŒå‡ŸaëÙ³Ğ]êFEÏæzıL’ïÙRƒÈgÉÈTş±ç,“ëZA¬õØı\èÑ°ûÖ§‰¹¯ƒYâ <\Ö™ƒœğ^Ö•góÀ½Nî{Ï»ï¸l¨¨ÙğR¯‹äO{=âÙ:v$
8äÎªNê«&º£±pïU†õ¨U¾?k¯ú†ê¡d6ÿü8ß|±+§‡œÛºÑ—EÛ%B‹{­“ò ¯R_.w?OÂªdŒ±F ñQ@°e<«<#-{­²@ÒzqW!}N™"&+íùÀÂLâl¾‡¦RLWó¯jåÆ@"#…%ÈëĞ)¢“f+³ŞŒ»B Dí ,â#şìÏ2$§t¤Bhiu‡ ?ñTWÈ†{0Bízÿ,bÔ¥ÍÊ$9ÉC²‚»dÚ€U`jP&ï°q¸6™Å`ÇĞ®f`3G’ü3Ö¶[Vn» cì7·§a£UAAØid 0b‡+ÂÉ,¬ş?©å0(ÊGbPşQ&ÕÌcÒ¹ÏÂGĞACéuYŒÃ,ŸçÙä">úŸštfJ5S?¶>©?#V¾:å¶³•£>í†ıWDïcV=7ƒöÕ ZÃÎ> Cj¤­J”«ÉoÆX[x¶ÖCÇ¤b-Ù§<7Å“»F¶¾ÂQäx{®t‡'Ì–©$¤Ô¢)«¾ÒW‰ì‡Ë‚RÆz$»ÊÀSTYÁiótİC¡'©Ğ¢@oæ#¡IÕáL>ª>Kéy8çÀÆ* ÇAáŸ:NÅğ¼•“ÓÂ•İ:a€X‘D…z­’%A&Û†²d`f‚>ÂŠÅ%ËÌœ$¦PÉéÄÔ4
E°SÄ~Ä‘Òú‹KİÕ‘Z™0ºM
Y¹†Ï°…ş\$a(Œ+¬$™¾C´Â‡‚)Š*¤Ñ’°2ö #‰@lÍØË¡KK5kØSà64,ÊqHQÅ:f#|T:ŸË\.QÃ°úÈ$ã;ØSØ²} aÙõú5àÍ(‹q”Ìw˜²Š¯˜4¦8–n\‹ÿÉz^%.RYü¨ãİëGõ‡nˆxƒ£àÈÂtE†@áûêoèKaSi$'6ÀGëC±,ÂÆd«`&×Ğ!p“
A7nJÓíWr·ÚQÍ&š²4ß>—Äšì¬¤(ŸJÚP×¿T€­¿xÂ›H·ñ	Á|H§[ÖŞÖ2
å1%Là~IåØóxD8lµaÛËæñ?»×37 ¤¡M7
€ØlÅ˜˜psZœØ+KğBiâŸ›Ø„kî–8-©ğQÍËÏE'«Ğ Ï2Ê‚èõÓƒ²ÈàÂ¥à©¨”CßzÛ= ÏA—+48\+Æ¦a‘
çÔ PcŸJ]Y‚«hNŸbƒ ­‚âÌÑ¡6iDÛºx®æ®6‘éµHÓUrrx8Í®“æJšÍ(¾>D‡4Ó¨g_½0ñ“»ÛPêT vPĞË?[ÿ:h‚“–n*>ÛPñOS¤„ÅN[¥,h9ìOTÇM‘éô‡=Iæ™¤‹Î…C¤t(-ò¸-™ÿL'º•èò–6[£OƒYÇz†5¿	¾•,	‰™ŞerËÍaY¢¢JAW¯ Éœ	õİQ	ƒ"äR!¢¸'ñ!ÊèÉ\y©ğP„¥JR(ökâ‘EÎQe!Ò>I)àbXöI…ß*½æ6¸v£ĞráB”†Fv¾vÌ€61.J[éåä]Rë ¯-—Yè{ 0CWVYË6L‚²,•G‹&!F5tÆ1Á‘vúÌLÄLîUáh–ù{÷nvÄ6’$¸‰CM;iÓíÍŞ76Æj­¼ÜWœ³[Ò0c†È7$—Rú’ú–h«)÷‰7ûé“ƒFú¦ÙÅàÅK…Q<Û45G Øe‹¤bŒ†M6OPŒ‚Øu+Iş©LS¬aR¤]1µ0g ¡ŠYÎv˜ä›8Á4§k0<[nò”ëñ±³œ’…@Şlaù&yîÒó+t­I*ì
KâkÂ@­ r}[ËÕh”
ğ’,H+OËGùÊFn¬ÿ…ÓªPùåÅİ½ì”j{Cµê¨h‰×°)´rz—¿÷ÕûÍg[aÿrÁŠ$2Æš£[©J½ÎqûJÀd¨ é2
<,…}ªêyA.7j’–Å†Ö#Í¼J¹Jéßd3öûXS,T®´!³)•x™ÙÜÎğps´ª÷®ïòïª%·\@`Áäu%m•–°hHÃRS|f$V‰©hAø€Éx-ªJzÖS‘éxĞ<qÊªÍFj(ì%‚àInš‚Ÿz™µV£à£0ríÇñª£—¶(§uò¥h·²X5{gß*›Es’îf½m?¼¯MƒÈ»y€³ámæ¼ÌW9n\C.«6³‹‡øÚã.£?Äiâˆ8¤3v—yÇœ¢Í¥Œ$3h"íp±úô¶p\±)R]6‰ Æp’vŒLHzqåiT}-OÑ¯Bh˜f!R9xiId04Q$YÍ —öh}ÖÒ£,ö‚‹vi«XEzˆëÌkÍ.×õb7§4:Òé»Ö¨È+ñ%¿	yi ÃùĞÍCQAÇ©ĞûŠo€¥Po£Öf„ W‡[K‘	¨Ş”&‰]Åx°_v™¤Z©6
„ŸÙœ,UØÈÀpü¨âåZí}ï²X‡ÁK=<Å¹›‹:“õÚ <<Z”xè˜¸Œàø«"7z²k­ÂŒÁÃÿ÷ÂÛ÷ê5s@eHşC°±Ù´y§ÀRñ×™Xz¼Xş—¹NA@vßÍØ]#d˜«c~‘î) 6)‘½$'i„n_
	3˜R¦Lkf‹(Ê»©¸â¦ë™Œr3å';;Ë>ËÂ¹(ß‘Æ»^ƒíÕ®}QL3å™i˜n¤!Owµí2M/a_ıÊ"R¶L©•JUr/¶ù:YÛºg—‰L«™‰¡c%³×*aåIİòk¾ms#Í8ƒ«")ÚYÇ‚Ì+ò(†záZ‰wPì4ã5–¼1…¹ø“…ÂÄ%y>*güIÊ6FXƒä…‡\ùY–>ªÿÈq°nÀMÄW°İàuİïğG9·ow>$:-t;
Dò/ãN©µ´…ÎÊ+¹Î€«Æñ•Æ@iÁÍ^	º•»LXé”ÜãzM6:å~§Üo5úALºÃ2Ty›7	­éïW@Æ9EæzÇJÉ€İ^|¿9¾$gØœIb|CI­ÅñI}ljš´É¶øE´–r½$…;¸µ¯:°Ä+qK‹°YÁ­<<ºÔûjÌLŸ;‘¬‰m|*ãÛnµx÷6¾‚Í:¯jKî»Œª;àPhPä·»º6şåFWò®A¥õP+ZŒÖÃoÆ£Àn< 7ñúæMíàôõ[\Î””3µx<;+yöÑQ÷µ
zåoöĞ—Àï¥)˜—ß×ı&Üòò¸@Ê˜Úª¿áboÅM¸¸_¥øFCï¬È¯Ü\!¶—’Ê÷]$™óò
ŸÏäÅ¸Ü›7–2¯ÀòüJ²J“ön™é5–ûéDˆPë,¹Q¼e#áë³b¾³«ıØVªìpF©íWeHMNç§1ºx¼›ñN,å%['åË0ÂS¢‚¼äU†é¼ø·»˜ë[¥øWp$7¨ßÅ[w€T=ŸG	û	cÕ5Gx›]9Şí¨öŸrI&ÌšñæêV´4„te6ùx´ x6§¯äí]"PNŞ½Zv.‹Ü¼¢¾qÍe¹yá  2Éáîo¾¨Á¶•q«1¼Š0‚t¿úâîƒs	H6Z9l‰o¤ö‚uÀv39-{G¦Î´Ó¥'‡ÌD”dJƒ²±rP7ïõU+PZ¹Î»ï·pqfÒPÚu¹ ]Ôšh²%åk*Â?5ó&c¥õX1ëÿÀM~ûu™¨…û²]ı£İñÕ$Ke@µ·FùÛ½ÿÿÜö†òv½æ®Qå¾-¯y9¶ôúƒ½®+/Ù¾ë6àG¼à•rÉµÕ³ñ"^ÙÍµà?>qnõùNŞğ#ÜşãÅ™­Ê·Jä¥Ó]µg.!÷	{Û¦_2÷¿Èl›Ã[ÍúU5Ú[1F„½ü7÷É€xm‘Ko£0 „÷Ì¯°z]µ1á¤vUC „¼ÉÍØBÁ!_¿}\;‡9|š‘Fr-ËœÊxÃ±L5J5QruªC‚I"C¬¨l2Ö5(&Ë2jÜ°Š
5B¨.R“D:ıDeEO°Ì4•PSUÄ	œh¾ñìÚ ?/?ıÉÇtÀ?Y“3
^/_øıòC_*ÆÿQ‘ T5QÑÀ3”!È÷TÎ`çÜ¹%àµº6¬¾ïiÎ³[òòø¥–Öi›§àùK†e»°´—`íÚ´Ù®¬o. Ü[ƒ&B‘Í“ +væÊğ´¬ÃNjÜ;BÔq]äù8Ê$-%xšú¸Bwî± RnÛfíİy3K¦aŸÒÎhm±[ŒJõ°½(¥$™ç	÷¹¹êxyàçá7ßë­Ù&^¹ "ÿ¼±7=Šı®„EaösÑÛmµŞ.Çáe‘.V}Íúj{é›:Ş}°üï(«j$€À4cg:7ÉQ?H¨¦R$gÜRI´0ãÄ¹>ÂG‡œÇi?˜nG)µ%Ú]÷™ã+*Y
`%çÕì¸ÆŞ£›©ñ¶/ËªEG»')âºğGQpœ¨·¤
ç:ãå0bívË4EÓA–­ud…hÚq˜‹ñÇú°Çóİåìê¹¡O§9Kõ[“¹š'4`ìH·ŞğV¥UøùÌZLLØÖsZÆoõK=üpİdx+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤Òbš¥×ƒEÖ$ÉÿÑÌÍ¾bóFÌüzÖ- 5:!üx“ËŠÛ0†»öSœ˜1é´´ÌÀ@ÓÉ¢†”’E¡” HÇ©¨nèâNúô=²;ĞEµ’åï?üç¶Wvfoo5àŸ]À˜Hí¬öÑZŠëÏÉ´èD¢Î²îåiÄÎ1ş‹0W,ÙHôá{¹À•uM„Md1xz‚÷pŸ1²ò®€ëS®z¥9Àæ"êŒ¯W›ú[¾,¥I¯7DKÉÑÌ¡0wÎÛEşşZoIÖı¾!¬MD#ˆœ'!Ñğ.ÄÉ3¥pC±ööà™ÖÙá’™C¢¼;ÇøÓš|{¨>ş—îİÕÖ:ÉsĞmâoæ.
úO~(ŞæEV–?Š¢ëÙÄ0×U†r.Xã“Œ»uòX¯†Ø-•ARbã!xV½­fÂ¥îG ¨óåÖš#,ä‹Uc—{p‡šIÕãF!9AŸØÉ@Å­BÜKG¤ÈÁõõÈ
+0M‹€¯ÔĞl8Lq!@´ıÜ@½i¸¢NSïê‡`FÀf]W oixtŠqìÆµ¡œ‚ŞÓÄf.8)°mERªÁ¡:Ş˜>9¤¡€Ë8'}ñvŞ€ó
]Æ¹Ú­ÉtZü¿k¸x+)JMU067c01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U%E‰e™Åz•¹9¿Ê¤ßTÖßèû¦-ºu3;_¡:×GMˆu)‰iE¥™%ñ¥E©şUky–,úÁµÿŞÆr»]s¡úx:»ú»2\P–İÏ˜º-Aõ¬ŒMÁQf•¨’ WG_W½Ü†µ}V_í«¿n([ĞÉà2aGÃ¦£İPE©UñÅ©%¥z•Ê¯fi×í}û±ÉîRÛújF±ósW­…*+J-,Í,JÍMÍ+)Ö+©(ax6÷ÑìM¯9{wk®+ºqèIOğD¨Z¸yÍ÷´ãN'}ú»s‰eù§P—3^-…x´$µ¸¤˜áË37‹;–?¦tşÎMY»¶u¯óCw  M›cxİ[koÇígıŠ‘TdÂĞ”ìÚ } IÊf#‘IÙ5c±\Å–»ì>,	Eÿ{Ï¹3û¢i[iR%i`ÄÒîÌ¹wÎ=÷1ëyÍÕÑó£ÎË¿¨^´¹ıëUª^Sw^¨îÂ]Æ™Ÿªa¸È’4öu²w ºYºŠâ5‹Â{Õ÷{Qàîàù¥×~’øQ¨üD­t¬ç÷ê:vÃT/Zjk­¢¥òVn|­[*”‹ù'˜ÍS×ığZ¹ÊÃF cÓ%Ñ2½ucáå&Iäù.$ªEäek¦nÊ—~ ÕHWZ=™ÚOš²ÌB»äù!äi•¿T·>ÔÈRkjæQJƒ¼ [pùëÀ_ûvNÑ
Ø–@î¶¥ÖÑÂ_òo-Êm²yà'«–Zø>ÏRŒLøĞÓ!gA—§Q¬pkÓËÊ(®aÖT	ŸÜ®¢u]Ÿ{ZfqˆeaŒYD0¬ú³öR>áş—QD·TĞ‹Â…O­“9¾Şºóè“•Â(ÅÅòr²sÄöU²rƒ@Íµµ–öCì„s­ f6ORàÀwµ‰bYt[Û¶ÙÄ›šÏfïº“NÕådüvØôÕ“î¿?i©wÃÙ›ñÕLaÄ¤;š½Wã3Õ½W?Gı–üãr2˜NÕx‚M/.Ï‡<zçWıáèµz…™£ñL/†3ˆÕKZaÃf©‹Á¤÷²»¯†çÃÙûDg#Ê=OTW]v'³aïê¼;Q—W“Ëñt€-ô!x4M°Îàb0šµ±.©Á[ü¢¦oºçç\ÒºWĞaÂ]ªŞøòıdøúÍL½Ÿ÷xøj€İu_ÌbP­wŞ^´T¿{Ñ}ÍNÔr¨!š=ªwo|È5»øÓ›Ç#*ÓfüÚ‚®“Y1ùİp:h©îd8¥YÎ&ãªIÃbV€ÌŒ]Uœ†ĞpWP=ßêºç†ƒA_çÃÛ{ËˆõÒûpî¯	õy¸ôÂ4ÈŸù‘—{v \'óÒ=È÷TOu/‡D­@	¾."?ÌîÔC€sÜø¤¹‡ñÎ…3ŒTõ¿SÕ¹ët:JÁ}I-øãªT‡j÷òVşF¹‹ø ±&ıêt¥Œ€ÎÄXK-ÜÔ%µA·$pá:ğ²µ›¤:¶¦³ñeU%üØéÈü%õrÎ®F=8Ÿ{ãsç¢;zM#Úù£ñt°"8ÿùùv\¾ïÁ[§?œ8İ~Â©œu¼cÖ—V¾'gÔıÉ,ÌùG¿`şhìLúN·g§»AmÚí!ZO½·Îyyz\¿µ9?Ğáuº=ÚYúqB÷´ÿ	ä3¿OõXazŞ};(ì–[¡ó²óŒR®œ•D9¶ê±ËDŞË§Ëò/;/¾<±¥ô'ÀÈ_îÕVÜñ ĞDÏ=Cb6.b(ïËŞÜWÃòĞ!Æná9·Ğ‰Çê¥€–OZjïå)À,‹âjZÛò7
y­Èøw¸"t„İÀOï‰á2é¿•r¬—Ò‹Ös?„Ù'Oß©‘>YBT#
Äü(î3^z¥ùÉÊù‘rdûpƒ#{ÕôâUf?]íÒäX !ãŠÕ÷H–g`Of#XÉ †OµĞKÙ5ìnˆ£½çÈ,”ì9ëäº1âÉbİ<‘u–¾‰ƒcøPœpãÆ?l)å9™¦G/š­ÊËeà^'x»ó%@Ì‰»_Î³¥¼¼G³Á¤a$üØlŠô{•ÍÆ‹ÛØÎtHEİ8täÖT¾‚Õ»YS ´£ÌòÏ‹å÷`? äF;œ'[Å× N÷Z'ÖhO<¹J}S.Ò£è§&¥ˆuŠ„Ù…~K{Z8Q{m²@ò>‡«_¥Ì!’ö|œÏB‚D¾‡¶RÌgò_ÕÆİµ&/|	¿ dmrÒlÃòvå{+ğÉa É¥øˆDé“¿È½F…Ğ42Ò4SÉ.áÚâ®¸÷`„Úõ»˜åªçJš©kr’õÉ2mğ#È±À@Ÿ2¬4™j!d
ÀÃkØÕlË`zùj¬m·¬Ü8vA6ØonOãk›8‚‚°!ÒÈÀé¦®à[Œ|‡4rHä#1(ÿQ&5Ìk’•Ì˜&Ò!RöÇXŠ0ÆSÉ'ğ?¶éZd½õ‡ÎGõWĞÿË3Ñh{œ±Ç}Ü9 ÛÅ8Ş= v³™jİÂœ>B†¤IJ0ãÈ3c“-ØZ¥ÅP(‘µ­)eƒòF|»úÜ˜Ö'8J¨Ì }„'½t‘§+7UkÔ%ğ†^Ş£’	a2IÊéL˜±Í™ÿ—NI?\‘2d!%3˜Hè¢ËŞ™¯î!å—ÚDèH0¶ğ—Sõt¡?=|À»Ÿ¤šğ<0E‰TcpŠã L§²hÙÂÊÉé±ÄnG`çQ¡¾UÉƒ SBOÃá2$À¢¢Ü°Ì`Á‘»¾Ø­ IÎÆ„4
EŸsãORÜ»úÎ¥îêHİ
k0HM
Y¹†?aÃ¥H‚ÍP"Uè	'e*Ğhƒ
J,¸¨FKÂÊğiÉÆÖŒ½¬Š±´TÛ±†=rCC—‡LK¬c6ÂW¥¯ñ½Ìåkî‰LR»y=…-Û@Ì&£rAFYŒ£dØfæ%X4Ñ¸8‘œ‰Šõ¼ J4œ¤²ˆPÇ»×aê;`İXpBv¹éÚUáêïèP`SR$µ3ÀG¬˜İcãà{Ù*ˆÈ5¼Ü¤ÂÄ-Ä›Òt•¤qÔDÛ¦,Íw@}¸°ÆNÁĞûÅØĞ¶5ï*ÀÖw$²Füæ7?¤ó-kokn0%Là~IåØ$ñxD8lS3œun{Ù<şg÷zæ€4´éGá!›münN‹{Åq	^(Mü³¾á1M¸æn™ÈI¡šx®Ÿ^¸QÌ@¯Ÿ–¹2.} oE¥úÖÛ¾ òmÅQœÆ€kÅÁØ>’úó}*uAd	®¢%}Š”âÌÑ«6iDËÄÏÔÒõÁ† 2}¢ViºIN>g×I{#\İâë§è•eeÙËç&PòXjJ
4zùWçß‡mpÒÚMÅg[ê0ş~L®ØÓi§”-Çıñ‰ê¹)RšáxÇØ'ƒºŠâ\8DÊìAË‹<Gè²Ğ‰‡¾ú}9Xà;8Û8B÷¨á·Á·’!£ ÓÁ»tèÎI]XÆ²<D'D•¾C¾Ö¬ Éœ	õ­ƒ¨‚A’¦Q\n}eôd.ÇTx(ÂReıRì×Ä#‹<ò`"¿C-@.†e÷«(üe ²ĞkoƒkÇ1
-.ä@ihdçÛ`Ç„§nˆiQ¡IK"ï—Y÷`&­×Yè{L§%)¶ÊÚXVs0	Ê²T-Ú„|5Ğ#ÅGª^t™w™|«ÂÑ¬V–Ö_Üì„İ¤Ip8‡š®HİÌŞkCÙ¥Ñªá¾âÌ@ø+œİš€ñğk4œ@~C.)©oær¯‘ac°ŸîX0Òëfƒ#,Fñ¢n$j °ËIÅ-›8ÔOPŒ‚Øu/Iş”©L[¬aR¤]15(g ¡\Y/v˜ä›8Á4§k0<[îò”ëñ±s€œ’¥@ŞS`&yîÚóæwz«I*ì]
¿š0PF+è‚dßm¥¼$ÒÊÛòU¾²‘ëbá´*T°¶ù¼/Û¤£ÁŞR–:jå5c›BÁŸÓ»ü} ŞÅ>\·jÿrÁŠ$2Æz|[©J³ÉqJÀd¨ é2
¼,…}¬êyA.7j’–Å†Ö#Í¼J]Jéßd3¶­ZXS,T®T“Ù–’»Ìlnçğps´j÷nîòïª%·\@`Áäu%m•Î¦hHÃRS~f$V‰©è5ø€ÉxA¦jwÖS‘imĞ<qÊUšÍF¨à%‚àInš‚Ÿf™µV£à£0ríÇñª£¶,§uò¥ÿĞnuîÄ=BÃ6xà¬â[­¢eW4énÖÛêpüÃûÚ<ˆ¼›8î•™ó2_å¸5r¹s©gñµÆ]G:{ˆ+ÒÆqH9l®óÆ0E›»IfĞDÚábõù}á¸cS¥úlAŒá$) =ì™4İÊÓ¨úZ¢_…Ğ0ÍB¤rğÒ’È`h¢H²š3 ®oÑ7ú¤¥YìW®ÒV±4Šô÷Î×,š]2.nÅnNit¤ÓŸ[£"¯PÄ—ş&ŒnQûã7Ú±y(*è8zßğ>,…zµ6#Y¸"Ğ8Ü­™€êMi’ØõQ<‡e—Iª•j£@ø™]ÈR…Z†ãG/·C§èV—Å:^Bè¡à)ÎõÜÜ7™¬§ĞàáÑ¢ÄCÇÄeÇ¬ŠDÜÜKÉ:¬µ
3>ÿ_Ü¤ÚááµcJÔ†9 2$ÿ)ØØlÚR²¡â¯3±4y°ü¹NA@6„´c÷!ÃÜ€òé’Q`“Ù;Ar’Fèö¥ ‘0#°ùı2eºe¶è€¢¼›Š+Ö]Ïd”õ”ŸìîÌ[°¸vÎp-¹G.Ê6·´Şİğllo(í};˜fÊ¦Q`º‘†<İÍ´Ë4½8„õ3‹HÙ2¥“y¥*¹[Ïü°ˆ¬m}a—‰L«™‰¡c%³×*ae¿iù5ß¶¹XeœÁí¬cAæyC½pÄË&vš‘ä)ÌÅŸ,&.ÉóQ9ã·LšP°1Â$/<¤a-Xjø¨ş#ÇÁ6¸7_Áv‹÷r¿ÀåÜ¾İùè´LTĞí(Éw¼€;¥ÖÒ:+¯áj1Vƒã+Ò‚õ^‰	»¬Xi–|ÁûÚ¶×)·<å®«IÕÄ°;ìcß&Pblgü´qN‘Â~f«‡¤Ân2~/‚Ö¿é2´Îl1ÏÂ¡‚äØÂ ä@v7Mşdû@üE´–º½d‡Ï l¿T`­W˜a_³`yyôt¨)S~îD°&¶ªğoû×PàgnòÅÎÃW@P/øª¶ä¾Ëğº…E¢»«aanùÈ!oTz…°¢ñçèAüj<ÊìÆ£z{ƒš±qxúêniJÊ™Z<•„ûè¨ûZ-½òoyèKà‹wÒÌëğŠë~ny†W eLmâp1ƒ·âJ\Ü¯R…£³¯Tä)7W3%ÆS²Cù…‹du^^êó|–{sm)óUt!Ï¯4*«4i/™™—Qc¹h‘–„µÎ’kÁÅw5‚¤–á¢X„ß j?ÿ´‡íÎ(µı
Ã¡iÈé|¿3X¯w3Ş‰¥¼äCç¤ü&FxJTÏº*À0Íc€Ÿ³ïb®oÕä_Á‘ù¸éW©z>ùÆªÿ ğu0Ú;r¼ÛQí¿?ä’L˜>ãKÌ­hi*	iÏÔùpT <›Ó7ò5*('o‚^#»F;ŠU	®`Qè¸æÖÜ|yP ™äğùo~±Áş•qË2|‰0‚¼¿ú©.†s	H6Z9ì×r|Á:`[OQË&’)8ítiÎ!3%™Ò ~¬Ü4Í—|ÕR”V.ƒóî‹.Ü ™ô#”¾]E.¼E'ºmIù½ŠğOÃ|»XéAVÌú;¸É¯¿7µpq¶«‘´;¾šd©¨¦YS\¯ıÏ/mõí…0wõŠ*oyñË±¥Ğì½]yÛö‹®şˆ·ü¸Rn»¶š7^Ä»û¢k£VüÇ®Âõ>?îÀ'~„Ï ğÍVåç%òõ‰i³
ÇÚ3—»Ï&·iœ,ı;ùt€ısx«™@¿ªF{+Æˆ°7„ÿ—ŒÑdxQŠ1DıSôVÒIwL@Äe=€H&=pŒŒ={{ãüyT=(¨±ÍsU°.nt¦P„’d?‘qq“ñ3ÉÄEwÖçÄÏ´ÈC!ÙX"wFÎd1†¬ØŒaêÉ¡Ol1â!­zk\ÛãNõ¯İìµ—ã¥]lÇ6 É“†‘áÇìŒºíU¾¿¥À¹êeÍP_¯U@e~Ş“Ê§L(x“ÉÎ£H„çÌSÔİê¦Šiz4€Ìbãß7(
ŒYÍb?}»{4·9MR_(¥)÷m[Í !†ûc	|!"’‰Dr‘b>å!be,C	§(#ˆr‰Ãr!SC:’n)›IğÃxsaˆ’I™Œ B¬”!B0&<Ì •.óµAˆûyá5}â±/fğçôü=§]Gó÷~,ÿˆg!äN`Á7(BHáß_Îä—C9U%øökTİÜ»À7}îMW‰â@ÿÍ)@ê¸«Š¢jŠ’•®gâİsÑ¬X†Vß(°êN‰çŞPšihIÑÊúø/§@<ßƒç‘–4ØŞÙ¦¥)~åğÒçÈ³×GvškV¹/5Â½<Ô²]D4~;îu
Ç`öŒzg9:ŸÒè!ëaNÓNèŞ~İµZ‰ˆiANnœÆoéŒ©§”Q£İŸ4Fr5ªÃaXnVUiwÁ¶­B<\ïül‡…#*Ï¼y`m»*U›$>[®rÇëzÒ›“Pë‘"Ve&í·ó¦Ø¬"1Ûîˆu™ßNÆèÂçO‹-ccØV‹Mİ¥‹„-D„=>‹Ò§À3»Ğ“p¾é7Ş®¡-äÏ0kyàumr-ãœLrA–øhßV&"ìÆ•îOyeü®¤À=F,WĞœdÏ…!{è…Ä·‡ÛCV£QLÃƒã¿noÖ¬L&QJ›ç`ñzpmjbq$´:Sà¢V±xø²œğæs_!MÓÖ÷“œŒÌ¾àeëãß_ÙzÇ»I_^#kÕ³#LÚ/VŞœPÀ™?ùÍÖ»Ü‹aÔÛÍ;¬ØrÏGÕˆÏ–êlÚBpC3œŠuzËÉËaœjjh“{ñT
l.øè‘3e¤ö|9[Ú9mH«„‚Û¸ê4òÁœèv•åË—)Çİº£kZ½	â«µ÷ÜÇE­n[´ÄÍİQ¤c,CÿµcãÉ´¬.›Axã|Ixš3¼’¶…—mì-Î¥qòJ’™P ¿¥Fwqº±Å’“ïw/î3¿3N–Ö¤ùçÍÊÒî6ø®ÆoëiNÒ
ü`„dKıÓİİşWc(½K³†€a™®`îÁ°è;0’†¤i—üY»eøhMÕÍß©Ÿ•ıex+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤Òbš¤í­ËN‰ó3yËıúÓ¿%‡:NUİ  MÒ$¼xİ[koIİÏş•XZÃ&ØÉ$#Kş@ 'ìØ`N6Š¢VÓ¦ÇM7Ûkµÿ}Ï¹Uı ãÄÙ™õÌì(š ]u«î­sÏ}TgDSuôâå‹ÿ²¯:Ñê6ö¯©ªyuuÜ:z©Ú3wg~ªúá,KÒØ×ÉŞ¾jgé"ŠOÔ$
oU×ïD»·ß/u¼ô“ÄBå'j¡c=½U×±¦zÖPóXkÍ•·pãkİPi¤\Ì_é8Á„hšº~è‡×ÊU6q›. (‰æéÚ5†Ï”›$‘ç»¨f‘—-u˜º)WœûNT-]hõtlg<­Ë23íç‡§UşP­}¨‘¥*ÖÔÌ£”yA6ã>òÇ¿ôíœ.¢°ÿ,ÜmC-£™?çßZ”[eÓÀO5ó)|š¥™ğGO‡œ]E±JtÀ­ALk4.w(£¸l„=XS%üe½ˆ–›ÚøÜÓ<‹C,ã`Ì,‚édÕ_´—òîA´¦‚^Î|jœÈñMğÔFŸµ¨dF)v,–—³˜#¶’…jª­å°´b'ü1×
jfÓ$|7P«(–E·µmšM¼í©ñğlò¾=ê©şX]†ïúİ^W=mñıiC½ïOŞ¯&
#FíÁäƒ©öàƒú¹?è6Tï—£Şx¬†#l¢qyŞïá×ş s~ÕíŞ¨×˜9NÔyÿ¢?ØÉPM°¤Öïaæ™ºè:o!»ıºŞŸ|h@ÔY2 Ü³áHµÕe{4éw®ÎÛ#uy5º{ØB‚ıÁÙëô.zƒIëâ7Õ{‡/jü¶}~ÎÅ ­}FÜ¥ê/?ŒúoŞNÔÛáy·‡_÷°»öëóYªuÎÛı‹†ê¶/Úo¸Ã‘B5ä@³Gõşm?rÍ6şt&ıá€Êt†ƒÉ_Ğu4)&¿ï{ÕõÇ4ËÙhxA5iXÌÁ
ƒ™ƒ‘C£‹¡Š³Áî
ªçûQİ^ûÒpPÈâã|xsïéÓ§ıãÀ‘êxîSéÂMÕÎåÑ€Şå-Ü1Tã‹×Y¢Ú—ı&fìíÍc İKoWpIì(ÏÉ å'x|8z™z~ŒOn’6€1Y§¡.‡ıÁ–Ú%&Ö ‡î^;Ól>×qCÓ8óÒ,ÖfÊÜÓ _Ø¼4Ø³»À<ÜƒT«ÃÓ£æà!Y0ğÃì‹ºÑq¨ğ¡;×Õ1cu‹'é	ÉÁútêÎ×?ÕÉ
–Ùƒ@çÂ™ôªúß©j}iµZJ{È‹øãªT‡j
nğşJ¹³È,±Fİêt¥Œ€Ö@w¨›ºäeX8	\ø=(b	ûéØJO†—U”ğS«%[ğçTÜ9»t8édØ;íÁ"ÀÎÇxJ!‚ó_ì˜oÇåûî½sºı‘ÓîvGœÊYÇ;fİ·jÿÍ`8ê9ƒöÏfaÎ?úùƒ¡3ê:ínìµi·‡h=êuŞ9çåéqıÔæü@‡×é±ÅpæÜ OûŸÁœÓÛTï‰Æçíw½Ân¹Z¯ZÏ)å*¡û04Ê±U]&:`©N>]–ÕzyÿÄ†ÒŸ#¾·±â/0 @=·pe@l0œÅP ~"{p_÷ËC‡»…ÜB(V¯´ÜxÒPOğ\~¸eB\7v`…üH!o4âÃÕÌ]®ˆ{¡Äo7ğÓ[bøF„ŒºïA¥+ä…t¢åÔaöÑ³÷*Eš’€T-
	ü(në"ç²×)EÈ'+ç'Ê‘íÃuhdâ`hL&ƒĞ®vir,€0t—¯^áî¢òeCØ›©–d¤ CH‰šé¹h…s1ÌƒÀÊTM#!X‡–{ÄÜÖõ$V XKÊqŒ3*DBÀ6cùágØzvºKİH£èp®×‡’ôx‡K"Ÿ%{"SùÇ³L®k±ÖOf`÷s¡G;Àî_XŸ&væ¾f‰ğ|,pY; drÂ?zYoTÍ÷:¹ï!<ï¾Gà~<²¡¢fÃK½.’?íUôˆgëØ‘(à;«:©¯šèÆÂ½TÖ£Vùş¬½êª‡vÙüóã|óÅ®,œrn{@|èF;\Jtm—-îµNÊ¼J}q¸Üı@<	«’1Æ4ÄGÁ–ñ¬òŒ´<îU´ÊIëÅ}\…ô9eŠ˜¬´ç3‰³ùšJ1]Í¿ª•‰Œ\– ¯@§ ˆBNš­X  Ìz0î
µƒ°ˆ<ø³?ËœÒ‘
¡id¤iÔR<€üÄS]!îÁµë!ü³ˆQ/”4+“ä$É
î’iV©ıA™¼ÃÆàÚd:ƒyC»šÍIò78ÌXÛnY¹qì‚±ßÜ†VqaC¤‘Àˆ®'³°úü¤–[À (‰AùG™T3Iç>A¥CÔe1³d|g“‹øèjÒ™)ÕLıØú¤şŠXùêL”ÛlÌV>ú´sö_y¼{ŒYôÜÚWƒh;û€©‘¶*Qj¬&¿cmáÙZC“ŠµdŸò@ÜOîÙú
G‘ãí¹Òu0[¦’R‹¦¬úê'PÛä@WHÍC?D©7DêI£w¦›¥LÜhôb‘¶‚‡ç¹½‡ªPÊWáPÁéÌGö“ªg3ıù ˆèõY
NÏÃK´‚—]‚ÔqjĞaŞÀÊÉé ±Ír’İ~n=êµJ–323÷4œ–õÓ4V¬DY“æô!P£¨œ{LBn ( {ŠDÁD|äÏÀ¿şâRwu¤ÖÂ<LŒ&…¬\ÃÃ#l¡?IØªèbiRD+À¸ Õ‚Ï
i´$¬Œ=ÈHÂ[3ö²F(ÆÒRMÇö Í9sòY±Ù•Êç2—KÔ0¬¾'2Èì)lÙ>Ğ°l†bÍl”Å8J&GÌoÅ±LÎSœë<®Åÿd=/ˆª¬2Õñîõ@ºú*I7DpÂQpdaº" ğ}õw4±°)	K’@@ŸD±†ÂÆ3d« 1×p'p“
›7KnJÓíW½ÚQ)š²4ß>—ÄšlÃ¤¨.ŸJÚP×¿T€­¿xB²ÈÍñ	ÑÃ|H§[ÖŞÖ2
å1%Là~IåØGóxD8lµaÛËæñ?»×37 ¤¡M7
€ØlÅ špsZœØ+KğBiâŸ›Ø„kî–8-i ô—Ÿ‹pO<W¡R$.d”3Ğë§eEÂ…KÀSQ)‡¾õ¶{@ƒ.W9s¸VŒÆ"oÎ© Æ>•º ²WÑœ>Ånú
Å™£	lÒˆ¶Ïñ\Í]l"Ó'j‘¦«ääÙ³iv4WÒ	iFñõ3´S3â÷Õl¹»¥N… j½ü«õïƒ&8ié¦â³uÿ0EşXìé´UÊ‚–ÃîğDuÜiQØ“ÌŸ	Dºˆ]8DJ‡Òò òR&Ìtâ¡µ‰–pi³5š:8u¡ÁXó›à[I©•éà]&Ñ–µà!:!ªôä|õ
Ì™PßM•@0(Bâ"Š€Ëq¢ŒÌå˜Ä
EXª$…b¿&YäáU20N\Ë>©¢ğû@e¡×Ü×cZ.\ÈÒĞÈÎ·ÁéÒ¦!ÆE,Ÿ¼¥jİàõ¢å2}fèÊ*kcÙ†ƒIP–¥òhÑ$äÃ¨†6:&8Ò[@SšY›IÔ*Í€ÃÆ½›±ç„Œ
nGâPÓ{Út{³÷±4Eßo÷gÂ_ãì–ô@ Œ$ÀX£áò™¨ÔÉ¤¾%zpÊ½F–Á~úä À‚‘¾iv1x1ÂRaÏ6DÍ vÙ"©£a‡Í£ vİŠA’?¥EªÓk˜i—ELáÌH(y–³&ù&N0ÁéŒÏ–«¢<åz|ìì#§dÕwfXëI»tãü~$]köØØB–Ä×„2ZA¶ğ«Ñ(à%YV–ò•ÜXÿ§U¡òk‘»õ|ÙV!Õö†j5ÔQÑ?¯aSè3äô.ï«÷(DTì_.X‘DÆ¸@'uK U©×9n_	ø }BF‡¥°OU=/ÈåFMÒ²ØĞz¤™W©m)ı›lÆæ`kŠ…Ê•6d6¥l/3‚ÛYƒcVµcãŞõ]ş]µä’"˜\¢®¤­Ò?–ÊiXj*ÕŒÄ*1ı
P"ïPµBıÏz*2íš'ÎB¹mµÙH] D‰ ¸E’›¦àg#¤^f­Õ(ø(Œœcûq¼êè¥­ài|é?´[ÙÛ®š½ì‚³Šo•Â¢“Iw³Ş¶	Ç?¼¯MƒÈ»y€³áÕæ¼ÌW9n\Cn¶6³‹‡øÚã.£İAÄéøˆ8¤3¶—y{¢Í$3è'"íp±úô¶p\±)R]v” Æp’vŒLHwåiT}-OÑ¯Bh˜f!R9xiId04Q$YÍ 7üè1}ÖÒĞ,ö‚[yi«XEzˆ»ÏkÍ.wûb7§4:Òé»Ö¨È+ñ%¿	yÃ ÃùĞÍCQAÇ©ĞûŠ¯€¥Po£Öf„ W‡[K‘	¨Ş”&‰]Åx°_v™¤Z©6
„ŸÙÉ,UØÈÀpü¨âåîMò²X‡ÁK=<Å¹›[=“õÚ <<Z”xè˜¸Œàø«"7·²k­ÂŒÁÃÿ÷ÂÛ—ğ5s@eHşS°±Ù´yÁRñ×™XÂX~Ï\§  »ïfì®2Ì=3¿H÷”Œ
 ›”ÈŞ£’“4B·/‰„Ì?)S¦5³EåİT\qÓõLF¹™ò“ÀeŸeGaˆ\”/‘H—Ş¯ÁÆöØ¾Õ@¦™rh¦iÈÓ]­@»LÓ‹CØW¿°ˆ”-Sj¥R•Ü‹­g¾{FÖ6ƒîÙeE"ÓjfbhÆXÉìµJXyR·üšoÛ\_3Îà^IŠvÖ± óŠ<Š¡^¸ƒâ…;Íxç%oLa.şd¡0qIÊ¿eÒ„r„Ö yá!÷ƒÖ‚¥†ê?rlƒpñl7x·÷Û üQÎíÛÉNËDİ‘|Æ›»Sj-m¡³òşn£3 Æªq|¥1PZp³W‚nå.V:%÷¸^“N¹ß)÷[M§ş &İaª¼Í›„ÖÎô÷+ ãœ"s½c¥‡dÀn/¾Œƒß¨3lÎ$1O¾¡‚¤Öâø¤>65MÚdÛ?ü"ZK¹^’ÂÜÚ÷"Xâ•¸¥EØÎ¬àVİê}5f¦ÏÈÖÄ6>ñm·Ú
¼‚{_ÁfWµ%÷]FÕp(4(òÛ]İÿr#Èûy× Òz(„-ˆ?GëáWãQ`7Ğ›x×ó¦vpúú-.gJÊ™Z<•<ûè¨ûZ	½ò×€èKà‹÷ÒÌËïŠë~nyy\ eLmÕßp1ƒ·â&\Ü¯R|£¡\äWn®[ƒK‘Ê—c$™óò
ŸÏä-ºÜ›7–2ïËòüJ²J“ön™é5–ûéDˆPë,¹Q¼’#áë³b¾à«ıØVªìpF©íWeHMNç‡1ºx¼›ñN,å%['å›3ÂS¢‚¼V†é¼ø‡»˜ë[¥øWp$7¨ßÅ[w€T=ŸG	û	cÕbGxõ]9Şí¨ößrI&ÌšñšëV´4„te6ùx´ x6§¯äU_"PNŞ½Zv.‹Ü¼¢¾qÍe¹yá  2Éáîo¾¨Á¶•q«1¼ËŠ0‚t¿ú–îƒs	H6Z9l‰o¤ö‚uÀv39-{G¦Î´Ó¥'‡ÌD”dJƒ²±rP7/V+PZ¹Î»ï·pqfÒPÚu¹ ]Ôšh²%åk*Â?5óÚc¥õX1ëïà&¿şºLÔÂ}Ù®şÑîøj’¥2 Ú[£üÎíŞÿn{Cy»^sW‹¨rß–×¼[úıÁ^×•—lßuğG¼àë—rÉµÕ³ñ"^ÙÍµà¿TqnõùNŞğ#ÜşãÅ™­Ê·Jä¥Ó]µg.!÷	{Û¦_2÷¿Èl›Ã[ÍúU5Ú[1F„½ü4u‘dx•ÎM
1@a×=E. ôwÚ‚ˆWI“TÓ)u1·Ä¸|‹í½·	ÖêÓ"S¤hˆ]ö¦2ùkN\BYl5‰#£x½¨Ù&-Ù²WŠu„lD;G\(G66†Š¡±¢ğ=Ÿû€ù@F¸®­ïãşËË&ó&ØœbL)ÃY{­}ç¦üÉTÇ£ÌqÀÚ¶Ù¶‡ú G3xİZkoÛÈígÿŠqÔÒ®*ËN6YğE’cumÉä¸A5²¸¦H•?Pô¿÷œ;Ã‡%ñv·ŞİAb“3wæŞ9÷ÜÇpDSuøò‡W/ÿ²§:Ñê1öo©ªyuuÔ:|­Ú3wg~ªúá,KÒØ×ÉÎjgé"ŠÕ$
U×ïD»³‡ç—:^úIâG¡òµĞ±>ª›ØS=k¨y¬µŠæÊ[¸ñn¨4R.æ¯tœ`B4M]?ôÃå*8ŒM”DóôŞ5†Ï”›$‘ç»¨f‘—-u˜º)WœûNT-]hõblg¼¨Ë23íç‡§UşRİûP#KU¬©™G)ò‚lÆ}ä¯éÛ58],D+`ÿY=¸Û†ZF3Îÿµ(·Ê¦Ÿ,jæSø4K12áCO‡œ]¢X%:àÖ ¦5—;”Q\6Â¬©>¹_DËum|îiÅ!–…q0fÁt²êÏÚKù„ûŸGAİSA/
g>µNåø&xëN£;-*$„QŠ‹åå,d'æˆí«dášjk9,í‡Ø	æZAÍlš¤ÀïjÅ²è¦¶M³‰³O'×íQOõÇêr4|ßïöºêE{Œß_4Ôur6¼š(Œµ“jxªÚƒê§ş ÛP½\zã±°‰şÅåy¿‡§ıAçüªÛ¼So1s0œ¨óşE±“¡š`I+¬ßÃÌSuÑuÎ »ı¶ŞŸ|h@Ôi2 ÜÓáHµÕe{4éw®ÎÛ#uy5º{ØB‚ıÁéëô.zƒIëâ™ê½Ç/j|Ö>?çbÖ¾‚#îRu†—Fıwgu6<ïöğğm»k¿=ï™Å Zç¼İ¿h¨nû¢ı;©!äPC4{T×g=>äšmüíLúÃ•é“~m@×Ñ¤˜|İ÷ª=êi–ÓÑğ‚jÒ°˜ƒ 3=#‡FCgƒ!4ÜTÏ÷£º½ö9¤á Å×ùğæÎ<b½ôqœûK‚@}gÎ½0òg~ä¥Á ×É¼t²úGÕQíË>Q+P‚¯‹ÈÀ³u«ãPàw>©ï`¼sáLzUıs¢Z­ÖaK)¸/©]•êPMá^ŞÂ_)w6$VÀ¨[®”Ğ:¤€k©™›º¤6è–.\^¶t“TÇVÂx2¼¬Ê „[-Ù‚?§^ÎéÕ ã ç“agxî\´ïhD;0O ¶Bç¿Ú2ßË÷İ{ïtû#§İí8•³¶ÌúÒªıwƒá¨çÚ?™…9ÿğÌQ×iwìtc7¨M»=EëQ¯óŞ9/Oë· 6ç:¼I gC;s?NÈáöï@>ÓÇTïˆÆçí÷½Ân¹ZoZ/)å*ÁYIt‘c«»Ltàè|º,ÿ¦õúËJßFş|gmÅ-¿À  ]@ô<2$!†`Ó€á,†ñ®ìÀ}Û/bì^q-x¬Şh¹ñ¤¡vñ^ÜÀ²!®Æk;°B~ w!Œ?sW€+BG(!Ğüô‘¾!£îµ ¨”c…¼¡N´œú!Ì>:¸V)"}2‡¨Z"ˆøQ<g¼ìuJò“•ó#åÈöá:4G2öªñÅÛÌ8"~ºÚ¦É‘ BÆ«ï.,ÏÀÌF$°’AŸ$j¦ç²kØİGsÇY(ÿÈs–ÉMm,Ä“Åº~,êÌ}ÌÇğ±8áÚ>¿ßPÊs2?L_×•—óÀ½IğvëK€˜·¿œfsyy9ì&½QÍHø±^éŸv*›g÷±#œéŠºqèÈ­©|«w}MĞ2Ë¿<*–ßı€[íplA_‚8İX£½xñâ*õN9¸H Ÿš”"Ö)dbø]ìiáDíU´ÊÉû®B~•2‡HVÚóq>3	ùšJ1ŸÉU+7v—š¼Lğ%Hü¶QÈI³3Èû…ï-À'+„$—â#>¥;–!{!Œ
¡id¤i$¦’]ÂµÅ\q%îÁµë!v1ËU¯”4S×ä88êÎ2mğ#È±À@Ÿ2¬4™j!d
ÀÃkØÕlÊ`zùj¬m·¬Ü8vA6ØonOãk«8‚‚°!ÒÈÀé¦®à[Œ|‡ÔrHä#1(ÿQ&ÕÌk’•Ì˜&Ò!RöÇXŠ0ÆSÉ'ô?5éZd½åÇÖ'õWĞÿ›SÑhsœ±Ç~Ú: ÛÅ8Ú> v³^š{jİÃœ>B†¤IJ0ãÈ3c“ØZ¥ÅP(‘µ­)eƒòF|»úÜ˜Ö'8J¨Ì }„'=w‘§7UKÔ%ğ†^>¢’	a2IÊéL˜±M™ÿ—NI?]‘2d!%3˜Hè¢Ë
Ş™¯î!å—ÚDèH06ó—Su0Ów€x÷Nª	ÏS”H5f§8JÀÔqj(‹æ¬œœKìÖyô vnê{•,1Ú0%ô4!C,*ÊË¹ë‹İ
ä¼aLH£Pğ95ş$Å±«\ê®Õ½°ƒ”Ñ¤•kø·Cl¡?I°J¤
=á¤L­ğCA‰ÒhIX>-#yÂØš±—5B1––j:Ö°'@nhè’ãi‰uÌFøªô5¾—¹\¢†aõ‘Ijw /°§°aû@ˆÒdTî È(‹q”ÛÌ¼‹&'’3Q±D‰†“TVêxûz Lı ¬»!BÈ.7]³*|Oı
lJBŠ¤vø(‚³{l|/[¹†÷€›T˜¸8p[šn¯’‚Ôëh;Ğ”¥ùö¨ÖØ)z·8»ÚvMÇ‡
°õƒ'‰¬?ùÍétÃÚ›ÚCFL	¸_R96I<#[­™GÎ:·½lÿØ½º mºQ¸Äf+¿„›ÓâDÀ^q\‚Jÿ\ßğÀ&\s·Ì	ä$‹PM<¯Ÿ^‡¸QÌ@¯Ÿî—¹2.} oE¥úÖÛ¾ òMÅQœÆ€kÅÁØ>’úó}*uAd	®¢9}Š”âÌÑ«6iDËÄ/ÕÜõÁ† 2}¬iºJ¦ÙMÒ\	W7£øæ ½²L£,{óÊJËšR'B µı‚^şÕú÷~œ´tSñÙ†Ú¿Ÿ"“+ötÒ*eAËawx¬:nŠ”¦?ìÅ1öÉàŸ.b„8‘2{Ğò"Ï$ºÌtâ¡o…~_¸Âä>Ğ=ªùMğ­¤CÈ(Ètğ.ºSR–±¬Ñ	Q¥¯Õ+@2gB}×ATÁ ISˆ(.·~ˆ2z2—c*<a©²~)ökâ‘Ey0‘ß¡ HÃ²»Uş2PYè57Áµå…–r 44²óm°cÂ³nˆqQ¡IK"ï—Y÷`&-—Yè{L§%)¶ÊÚX¶æ`”e©<Z4	ù0ª¡GŠ	T½è82ï2ùV…£Y­:,­¿¸Ù»!H“àp$5]‘uw2{_ÛÊ.^Ğî+Î„¿ÅÙ-é ±FÃ	ä7ä’Rá‘ú–hş(÷6ûéî~#}İìbğb„¥Â(­‰š# l³…©¸(Ú˜Éùr¶~„O³
¦ŠoàÀ±t½óãù-µ‡Š‰o^A³*‘¬néÆy«7½×t!vê„Mé•Ü]ÚÚ¥F£TÌœdAZy[¾ÊW6rcıO,œV…ÊfòŸWeQNç«ñhªÕP‡¼BªaS(os2“ÿ÷Ôuì¨Uû—V$Ñ?.ĞÑÚHUêuÛSrÒ‡øH?ñ²ö©ªç™Ë¨IZü™y•*ŒÒ¿é»lÒ4°¦X¨\iMfS
Ì2ØÎ=ğşts´ª‰’I}›W-¹äƒ&—#Išôñ¤AÒ‘šb+#HAeíƒî…·y¤*UV‘)äi8åâÈÆŞêUpb<"¥KS°‘R/s´*ç?ÿäØ~¯:|m‹PZ'_úíVGàNtÍk¶gßjª¢Fw³Ş¶Ç?¼¯MƒÈ»}‚³á•³3Î€[#²ÊÃz,}Š¯Mà0î2ÊĞÇB\‘¦…ˆC€±¶ÌÛ m:éºÑùBu±úô±p\±\©.›"c8!¤‡#îK‹©<ª¯å	éUÓ,Dâ/-i€†–¤f9à²]’;-­·b/¸`”&‚¥Q$C¸e½a‰è’!pM)vsJ£#yüÜy…"¾¤«·atJW–ĞÍºP/Æ©ĞûŠ·§`)T—¨,!ÈÂÆáî¥¤ToK“Ä®R<Ø/{*’›WËbágöÜJ*É—ä¨Yå.ä½Ù²4…ÁK=<Å¹›ÛÓ)´xx´(hĞpÁñ«"í4·0²+‹ÂŒOÁÃÿ÷Â©vxİŞ8¦ «™*CòŸ‚Í¦-%*ş:KK³ Ëï™ëdCH3vï2Ì}‘^! 6)‘íø’“4Bo+‰„Ìï–)Ó=³EåİV\qİõLF¹^‘ÀyÃMvéƒ®%÷ÈEÙÔ•F³Ş€í}œ½]¦ Ó:ø›)‹MïÍ§»Zv™¦‡°§~fÉ$[¦T`2¯Ë$÷b£•ŸÑµÍ /ì²"‘i531´¬dv%¬ìÖ-¿æÛ6×ˆŒ3¸‘•UÈ¼"b¨nKxµÂ¾*²€¼ƒ¹ø›…ÂÄ%y>+gü–IÊ¶Xƒä…‡íÖ‚¥†Ïê?rlúpñl7xõÛ üYÎíÛu¾ä@'e¢‚Ú¾@$ßñºé„ZKä´¼t2¢­çŠ±j_i”Üšå}Å–´z‘ }æ‡OIôªYÖ³Xšwÿh³ğûCZÌ…ò*H)ø¦‡³Se²Ûåà/¢µT¥%ö?;{ëÌJ¦<Z„=ªÊñÈËÃ/œİ3¡åNdkb{˜Åù=OÁëê¯€`½œ©Ú’û.ƒÇ8iÜ¶"ÛÒ|n¹°Î‹ãJ…]+*í?G…ı«ñ(°èÍ*¢ÚşÉÛ3tÜKÊ™Z<–tòì¨ûZ¥ ½òï2èKà‹ké}åUfÅu¿	·<)2¦6ÊL¸˜Á[q½)îW©1Ñ¥Åò”›+„™ú€ìP~­ 9‹—²|'õäŞ¼¶”ùÂµçWÚpUš´†Ì:¨±4Í¥à¡ÖYr-8¢øFB0‚Ä)œ‹ğ{BíçŸi°æŒRÛ¯0²íšœÎ÷[CQñz;ã[ÊK>¶Ëï„§DùD§Óxñiò¶ğõ­Šó+82ªü* UÏçÆª…Ç¾ôDóBw3ªı÷‡\’	“C|U·-M,Í‡õE>® Íé+ù²”“7A¯–İ ÙÂœ×iHã]sjn‘ “>ÿ#ğæí;»3Æ5,:ğiÂ²ÚêgO¸äË%<#Úhå°ó»–Á
ÖÛõ4¶l‘˜rÊN—Ö2Q’)ª£J×»n¾ÊªZ´rœ·_ãà~È¤¡t¥*rá-(©ĞKJÊo„jæ;´J‡­bÖßÁM~ı­¨…k¡mm’íñÕ$Ke@5­ˆâòèŞæ~¹Ñ•ÂÜÖ	©\+å¥Ç–~@°·Rå]Ò/jzÿ{ŞüPNîr6Z^Ä{Ø¢'¡ü0ŞU¸ªåE=®{ıWºøb#„òSù’À4…cí™KÈİe×´æşƒ\³;o5èWÕhoÅöşë?cöCx“ËŠÛ0†»öSœ˜š––4,jHI Y”é8Õ]ÜIŸ¾Gvb'º¨V²üı‡ÿÜÊàÓ‡Ù›Æ[øg0&R;ë#¤€ıC´V…âös2-:Q§è€‹¬{y€F±wŒÿbGEÁA6}€'ø^.±EeFaYLá=¼…/YùPÀí)×=‹Òa{
uÆ7ëmı’/+iÒëÑJr43B(,œó¶E‘¿¿Õ;’u¿ïkÑ"IH4¼qöL)ÜQl¼=z¦uv¸bæ˜(ïÎã)ş´&ßæÕÇÿÒ½»£ÚY'yºµMüÍ<ÂUAÿÉÅûÊ¼ÈÊòGQt=›¦ñ¶êOP.k|’q¿Iëõ»¥2HJl<Ïªy5–(u?@/wÖœ`)Ÿ­»Üƒ{ÔLª'0
É	úÌÎ*nõZ`à^º8: Ev®¯÷DVX±`hhZ|¥†fÃa
Œs¢íçê5HÃušzWÏŸÛM],½¥}0àÑ)Æ±×†r
ú@›¹à¤À´Ia¨‡ê<zcúä†n ®7â’ôÕÛe.+tçf·&ÓiñÀá¹x[jÃ0EóíUÌZFÒx$C	-$èôƒ9îø£»¯³…ü¸.œÜæyT°Ä]E€$sí¹rˆ4 çÁ™(qèÑ×<°	ÅD¾[â*…‚4!û¥R²Œ½uäz4	ÉûÂKéâ¦÷¶ÂO{üÁ÷øÕ¦GİÇù…2æ]|æ6ŸÀ“Èlà=b·Û=Qå­sw)®£Ş¶Ë6M°Ês“_•y™¢Ê?jeN›x•ÎMªC!@á7vn %j¢JéVâ5Ráş<ÄB»ûBé:<ƒÎrl[ŸÖ;÷7‡ªE• M½xt™[ñÎ7% D‰É»„ÕªÁüËĞ}Ú
¹32`Ì˜ËµQ"N!åBÈ16ò˜÷cØUêKªØËÚ·cÜ¾yŞu^­#Ÿ9q°'@ ³|æ¦şÈLëO»ö]ÍÀ;@qx+)JMU014f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U•9™y%EÉ7:£7°¸N1ZÏ\¶jûñ8ñ»`ŠJŠË2‹õ*ss¦‹‰[èÎ¼¤ì®hyjÑòi›<Ì!nrLIL+*Í,‰(-JõôgXÃ|"ø|óæ9»®ÿdãWh¿4G.j §³«_°+ÃÕ`ÙıŒ©ÛØTÏÊØU`V	*	rutñuÕËMaXÛgõ÷Õ¾úë†².v4l:ÚU”Z_œZRZ WPÉ üj–vİŞ·›ì.µ­¯f;?wÕZ¨²¢ÔÂÒÌ¢ÔÜÔ¼’b½’Š†gsÍŞtñš³w·æºò¨‡ôO„ª…›×·ùı’¯2®]Û¶çuúû°i_OA<Z’Z\RÌğå™›ÅË‚S:ç¦¬]Ûº×ù¡; ¢ÿ¨Òx+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤Òbšêí—×ïö¼bsúšIn—Ÿ¬~1‘ UÍ$Kx]SË’ªHœµ_Á®D7¢jÄ,PDEDD^²™(¡PVTñòëoÛ·W³:‘y2OœEæ­Ä7n!/ş¡M‚—\
J
GIFÙ’cuCÙ0*º7à—Ø£Ñß±}r“/åã=§_òÇ(C”²|/HF¸_È}Ö\«&«á"F¿XÏş§ C™!6¢qöcÿ!85iİdì?»©áş$Ğç­¡_d%”xX8Ô¸ÍX¿Ÿ#Ù7ÑĞ7 ¿ÎOVƒ6£o! ´Ãuò6q…ñ÷É%èüİR¢c$ÊÔèvğé5O‰Z¦›‡«œäÔ_¤¯P©†zpÖÎ=´Ï‰ÛR+ºÇ¹Á×y¡Fí~5#æAÛO"§÷ötÜaÔjnZ9[cpèéÃ",J|˜«¸HÂî±Ú#âC'È¥b”qÛ?‡úÖ¡W¹tg0ÓtŸxWƒªÈ(²<HãÒ›¢SNQ³iÂNçÏ®‡û]´òqu†ñªÍ0
%!›q
“íõŠ‹!™Ø>œò>›½±×i[»£Å0–gk“5ØJ€!ÔÏSVšÙ<î&ö‹âztã°;>B~‘èï,vÓJG*òú“4Iˆ¥.8˜tì•ï\î†¿ÕÄÛp+cpšş*¯ÂC}@xtWC¼™ae‰ªõJd†…>oxëU›‚UlxkŞädœv,o¡Bmcİ5E¹U•‘¶Êfx‹"]¸†Í¨E\ufµSy"ã“(Šg37Z'.Âb˜,Ba2°ÃÓ“ZÑA‰QnË}¥]__O¹âçú°L·à]u­ª§Ô˜Ö>tê×yÙ\äd±sİfa°¹ëd_˜ú¬jì
òç•²Pz¬×·‹ItÅİáìQ	\_ s›ıbjkóÈ÷¦£ëFÀëµ­òÛ‡°={*&l›ëz§úÊNÎíXÏÈu‚6”ÄYñïwp1ú_îô§Ÿğ'Í¿…ü­áØîGx+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤Òb£|!ÏùÓ­îÉ~ã«¼uó!‹ '‘ Ëx+)JMU067c01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U%E‰e™Åz•¹9Ú’v7./ì2•ò)}¢Xû5ôÙˆu)‰iE¥™%ñ¥E©şUky–,úÁµÿŞÆr»]s¡úx:»ú»2\P–İÏ˜º-Aõ¬ŒMÁQf•¨’ WG_W½Ü†µ}V_í«¿n([ĞÉà2aGÃ¦£İPE©UñÅ©%¥z•Ê¯fi×í}û±ÉîRÛújF±ósW­…*+J-,Í,JÍMÍ+)Ö+©(ax6÷ÑìM¯9{wk®+ºqèIOğD¨Z¸yÍ÷´ãN'}ú»s‰eù§P—3^-…x´$µ¸¤˜áË37‹;–?¦tşÎMY»¶u¯óCw ÑÜ›5x+)JMU02µd040031QĞKÏ,ÉLÏË/Jex$Æ»£x>ï“Ù*Ó›ê8Üf¹/­l11 Ç”Ä´¢ÒÌ’ø€Ò¢TO†¢£û_Î\Ârâ¥½¯®JëyïË·j§³«_°+ÃÕ`ÙıŒ©ÛØTÏÊØU`V	*	rutñuÕËMaXÛgõ÷Õ¾úë†².v4l:ÚU”Z_œZRZ WPÉ üj–vİŞ·›ì.µ­¯f;?wÕZ¨2¸štVœ+wÔX[÷W,òkÖå;?ó /I-.)føòÌÍâeÁ)¿sSÖ®mİëüĞ <–lax+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤Òbš³ÖËïÿ8äò¦é¥aïáıh™õº Rm"×xQJ1DıSô§",I&ÉdAAñ^ Óé¸Á™É’éAçöf¯`}Tñ

Šê²Üƒ4fPÎÛqÌ˜Ï#YOÙüt*Ù0ÆI[­ÒpÃÆ« jËätNlÍ>FŒÚÑiòÙ›`L6¤ŒÃw¹ÖŸu=à½¼ÕáE:¼Ş-êÅ‰êrm“ÎÀ³êzÛ/
ÿk<|”_(Û¶3ü¹Bœ+}CcL°2§²~ÔÎ²·æ²	ÔñŞàñØO§á \çx-Š1Â0E™}
o™D+©#Ü %Š%7MGjnÏNÿé½ïyõxÆ»87‡	SÕßÚN€Ø¡éíÕ4ìh (fuÌ­&Jxì%l…$,!j¶º+@~%=Î•)*Ş>î+…ôõ,îs^|É6Õ?T'-¼x+)JMU01e040031QğuqõğqqÕËMaHvÙôuÉ®¿–Zå‘‡ãâV,ºrï ºá‘xİ[ksÉÍgıŠ¶UA#${íªô²ÉJ dÇårMC#f5Ìy«Rùï9çvÏ„l9»Qv³åZÓ}»ïísÏ}ôxDSuôâÇ¿ÿi_u¢Õmì_/RUóêê¸uôRµgî<ÎüTõÃY–¤±¯“½}ÕÎÒEŸ¨IŞª®ß‰wo¿_êxé'‰…ÊOÔBÇzz«®c7Lõ¬¡æ±Ö*š+oáÆ×º¡ÒH¹˜¿Òq‚	Ñ4uıĞ¯•«<lâ06]@PÍÓµkŸ)7I"Ïw!QÍ"/[ê0uS®8÷¨ZºĞêéØÎxZ—efÚ Ï!O«ü¡ZûP#KU¬©™G)ò‚lÆ}äéÛ58],D+`ÿY=¸Û†ZF3Î¿µ(·Ê¦Ÿ,jæSø4K12á9ºF±JtÀ­ALk4.w(£¸l„=XS%üe½ˆ–›ÚøÜÓ<‹C,ã`Ì,‚édÕ_´—òîA´¦‚^Î|jœÈñMğÔFŸµ¨dF)v,–—³˜#¶’…jª­å°´b'ü1×
jfÓ$|7P«(–E·µmšM¼í©ñğlò¾=ê©şX]†ïúİ^W=mñıiC½ïOŞ¯&
#FíÁäƒ©öàƒú¹?è6Tïï—£Şx¬†#l¢qyŞïá×ş s~ÕíŞ¨×˜9NÔyÿ¢?ØÉPM°¤Öïaæ™ºè:o!»ıºŞŸ|h@ÔY2 Ü³áHµÕe{4éw®ÎÛ#uy5º{ØB‚ıÁÙëô.zƒIëâ7Õ{‡/jü¶}~ÎÅ ­}FÜ¥ê/?ŒúoŞNÔÛáy·‡_÷°»öëóYªuÎÛı‹†ê¶/Úo¸Ã‘B5ä@³Gõşm?rÍ6şt&ıá€Êt†ƒÉ_Ğu4)&¿ï{ÕõÇ4ËÙhxA5iXÌÁ
ƒ™ƒ‘C£‹¡Š³Áî
ªçûQİ^ûÒpPÈâã|xsïéÓ§ıãÀ‘êxîSéÂMÕÎåÑ€Şå-Ü1Tã‹×Y¢Ú—ı&fìíÍc İKoWpIì(ÏÉ å'x|8z™z~ŒOn’6€1Y§¡.‡ıÁ–Ú%&Ö ‡î^;Ól>×qCÓ8óÒ,ÖfÊÜÓ _Ø¼4Ø³»À<ÜƒT«ÃÓ£æà!Y0ğÃì‹ºÑq¨ğ¡;×Õ1cu‹'é	ÉÁútêÎ­~ª“,³Î…3éTõ¿SÕúÒjµ”÷ñÇU©ÕÜà-ü•rg3YbŒºÕéJ­#
€î P7uÉË°p¸ğ{PÄöÓ±•0/«2(á§VK¶àÏ©¸sv5è8pÒÉ°3<w.Úƒ7D€?'ğ”Bç¿Ø1ßË÷İ{çtû#§İí8•³wÌºoÕş›ÁpÔsíŸÍÂœôóCgÔuÚ;İØjÓnÑzÔë¼sÎËÓãú-¨Íù¯Ób‹áÌ¹'@ö?ƒ9§·©Ş+ŒÏÛïz…İr+´^µSÊUB÷ah”c«»LtÀR|º,ÿªõòş‰¥?Fş|ocÅ_` €. znáÊ€Ø4`8‹¡@üDöà¾î—‡1v/¸…"P¬^	h¹ñ¤¡à¹ü
pË"„¸oìÀ
ù‘BŞhÄ3†«™»\÷B‰ßnà§·Äğuß‚J9VÈ+
éDË©Âì£Ã÷*Eš’€T-
	ü(në"ç²×)EÈ'+ç'Ê‘íÃuhdâ`hL&ƒĞ®vir,€0t—¯^áî¢òeCØ›©–d¤ CH‰šé¹h…s1ÌƒÀÊTM#!X‡–{ÄÜÖõ$V XKÊqŒ3*DBÀ6cùágØzö,t—º‘FÑ³¹^?“¤Ç{¶Ô òY²'2•ì9ËäºVkıD`v?z´ìş…õibgîë`–8 ÏÇ—µBæ 'ü£—õFåÙ<p¯“ûÂóî{îÇ#*j6¼Ôë"ùÓ^Ex¶‰¹³ª“úª‰îh,Üû@•a=j•ïÏÚ«¾¡zh™Í??Î7_ìÊÂé!ç¶Á‡n´Ã¥DgÑv‰Ğâ^ë¤<À«Ô‡ËİÄ“°*c¬HC|lÏ*ÏHËã^E«,´^ÜÇUHŸS¦ˆÉJ{>°0“8›ï¡©ÓÕü«Z¹1ÈÈEa	òú t
‚(ä¤ÙŠÂ¬· ã®(Q;‹øÈƒ?û³É)©šFFšFİ!ÅÈO<Õ²áŒP»Â?‹õBé@³2INò¬à.™6`˜Ú”É;l\ ®M¦c1˜ç1´«ØÌ‘$ƒÃŒµí–•Ç.èûÍíiØhGP6äA Œ€ØáŠp2«¿ÀOj¹Šò‘””I5ó˜tî³ğtĞP:D]ã0KAÆçy6¹ˆş§&™RÍÔ­OêÏˆ•¯ÎD¹íÁÆlåè£O;‡aÿ‘Ç»Á˜•AÏÍ }5ˆÖ°³èi«¥Æjò›1Ö­5ÄÀĞ1©XKö)ÄMñä®‘­¯p9Ş+]çá	³e*	)ÉÑ—õSÆx$¹ÂÀRTXÁYó4İC'•¨Ğ¡@næ#‘IÕáL>šˆ>Kíèy8ß¸Æ ÇAÁŸ:NEğ¼•“ÓÂ”¥?bDnêµJ–m˜d{şÇR	ú+•,/s&XV@$§SkĞ( NóMğF*(ë/.uWGj-$Â¨n4)då>;Âús‘„]  ®°dúÑ

†,¨©FKÂÊØƒŒ$ò°5c/k„b,-Õt¬aO×Ğ°'Ç!5ë˜ğQét|.s¹DÃê{"“Lï@^`OaËö†e3ÔèÓ€/£,ÆQ2Ïaª*>bÒ—âDX²q-ş'ëyA”h¸Fe5ğ¢w¯şÔ_Pº!â‚#Ó™…ï«¿¡…MI„‘\8šJ›#‰Ë!lô/[#¹†›Tˆ¹°pSšn¿’³Õêh2Ñ”¥ùö¹$ÖdG%E¡ø¤PÒn€ºnèø¥lıÅ¾DšOæC:İ²ö¶öQ()a÷K*çÀ–˜Ç#Âqd«ólØ^6ÿÙ½¹ mºQx Äf+ÆÂ„›ÓâDÀ^q\‚JÿÜÜğÀ&\s·ÄiIe*^~."7ñ\…ø¸QÌ@¯Ÿ”Å.} OE¥úÖÛîyº\q¤¿1àZq06‹8§€ûTê‚È\EsúhgÎ$°I#Ú–Ås5w}°!ˆLŸ¨Eš®’“ÃÃiv4WÒÔhFñõ!:£™Fûê…‰›Üİ†R§B µƒ‚^şÙú×Aœ´tSñÙ†:ˆ˜",ötÚ*eAËawx¢:nŠ§?ìIÏ\ ]Äl."¥CiyÇkÉøg:ñĞ¥Dw·´ÙıÈ:Ğ+¬ùMğ­dGH0Ètğ.“SÎhËZğUúÒ·zHæL¨ï&ˆJ !‡
EÀå8‰QFOærÌG…‡",U’B±_,òp*‘î¡8"HÃ²Oª(ü>PYè5·Áµã…–r 44²óm°cæ³iˆqQÒJ'ïZ÷ x½h¹ÌBß…º²ÊÚX¶á`”e©<Z4	ù0ª¡#	´	Ğ_ffr®
G³¼wØ‹¸w³#¶Á-àHjÚH›noö¾±1V™hámà¾âÌ@økœİ’€ñğk4œ@¾!©”’—Ô·D;M¹×H¸1ØOŸX0Ò7Í./FX*ŒâÙ¦‘¨9À.[$c4lâ°y‚bÄ®[1Hò‡´Hõ`šb“"í²ˆ©9Ã 	ÕËr¶Ã$ßÄ	¦!8]ƒ1àÙrë“§\}ä”, ò&Ë6És—nœ_u¤kMRa7X_Êh]ãÛ®F£T€—dAZyZ>ÊW6rcı,œV…Ê,+î–æe‡„tT#ØªÕPGE+¼†M¡eÓ»ü½¯ŞÇh:óØ
û—V$‘1.ĞİHUêuÛWş#CHŸQàa)ìSUÏr¹Q“´,6´iæUÊTJÿ&›±Ï×Àšb¡r¥™M©ÀËÌ†àvÖ`€‡Ã˜£UíØ¸w}—W-¹…äƒ&—¨+i«´‚¥@C–š¢3#±JLEëÁG ”HÆëP­PÊ³ŠL§ƒæ‰³P.Nm6RCA(·HrÓül„ÔË¬µ…‘sl?W½´Å8­“/ı»v+{qU³÷VpVñ­²éW4%énÖÛ6áø»÷µiy7p6¼EÀœ—ù*gÀ­‘kÈ%Õfvñ_›ÀaÜe”¡Ñ‡¸"Í‡”cÆná2ï”S´¹Œ‘d­A¤.VŸŞË16¥QªËæÄA’ÒÃ‘	I®<ª¯å)úUÓ,D*/-i€†&Š$«9à²í¢ÏZz“Å^pÁ.mK£HqyÍ¢Ù%Càš^ìæ”FG:}×y…"¾$ğ7!/`8?Ú±y(*è8z_ñí°êmÔÚŒdáŠ@ãpk)2Õ›Ò$±ë£xöË.“T+ÕFğ3›’¥
U¼\§¢ß]ë0x	¡‡‚§8×ssAg²B€‡G‹—¿`U$âæ"OÖa­U˜ñ!xøÿâ^Ø`û>½f¨É66›6ïX*ş:Ko· Ëÿ2×)Èî»»k„seÌ/Ò=%£À&%²W"‚ä$ĞíKA"aF`óOÊ”iÍlÑEy7WÜt=“Qn¦üd'pgÙgÙQ"åû ÒpwÃk°±½Òµ/(P€i¦<3Ó4äé®V ]¦éÅ!ì«_XDÊ–)µR©JîÅÖ3_##k›A÷ì²"‘i5314c¬döZ%¬<©[~Í·mn¢gpE$E;ëXyEÅP/\'ñî‰f¼¾’7¦0²P˜¸$ÏGåŒß2iB9ÂÆk¼ğ«>kÁRÃGõ9¶Á¸‰ø
¶¼¦ûm ş(çöíÎ‡ä@§e¢‚nGH>ã%Ü)µ–¶ĞYy·ÑcÕ8¾Ò(-¸Ù+A·r—	+’{\¯ÉF§Üï”û­¦S¿“î°UŞæMBkgúûqN‘¹Ş±ÒC2àG·ß«AG/Ç6g’˜'ßPARkq|R›š&m²í~­¥\/Iání+,ñJÜÒ"lgVp+îõ¾3ÓçNdkbŸ
Çø¶[íÀ ŞÁ½‡¯€`³Î«Ú’û.£ê8ùí®îƒ¹äU‡¼kPi=ÂŠÄ£õğ«ñ(°èM¼¶yS;8}ı—3%åL-ÏÎJ}tÔ}­„‚^ù=ô%ğÅ{i
æåwÅu¿	·¼<.2¦¶êo¸˜Á[q.îW)¾ÑĞÇ»*ò+7Wƒ­Á%‡d‡ò=Iæ¼¼Âç3y!.÷æ¥Ì«ï…<¿ÒŸ¬Ò¤½[f:Få~E:"Ô:K®Go×Fø:Â¬X„ïêj?¶•*»œQjû†CR“ÓùagŒ.ïf¼KyÉÇÖIùŒğ”¨ /wU€azÆ /şÍÂ.æúV)şÉêwñÖ UÏçQÂşCÂXõ_‹ÄŞ¢FWGw;ªıç‡\’	³f¼±º-M!]™ÍE>m  Íé+yk—”“7A¯–]£Åb7¯¨o\sYn^8(€Lr¸ûŸÀ›/j°me\cÁj¯¥"Œ İ¯¾0‡ûà\Â#R V[â©½`°İLNËŞ‘©3ítéÉ!3%™Ò l¬\ÔÍû|Õ
”V.ƒóîû-\œ™ô#”v]E.hµ&šlIùšŠğOÍ¼ÁXi=VÌú?p“_]&já¾lWÿhw|5ÉRPí­Q~çö_ïÿ?·½¡¼]/„¹«ET¹oËk^-ı€ş`¯ëÊK¶ïºø=^ğMJ¹äÚêÙx¯ì‹fZğ¸
·ú|§oønÿñâÌVå[%òÒ‰é®
ÇÚ3—û„½mÓ/™û_ä¶Íá­fıªí­#Â^şÇÆ}Ğx+)JMU014f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U•9™y%EÉ7:£7°¸N1ZÏ\¶jûñ8ñ»€ŠÌMMôJŠË2‹õ*ss¾=?b`õŸ]HóÔÉEÆİÿŸ­™Ò	q“cJbZQifI|@iQª§?ÃŞàÁç›7ÏÙuı'¿Bû¥9r)P[}<]ı‚].¨ËîgLİÆ– zVÆ¦à¨³JTI«£‹¯«^n
ÃÚ>«¿¯öÕ_7”-èdp™°£aÓÑn¨¢ÔªøâÔ’Ò½‚JåW³´ëö¾ıØdw©m}5£Øù¹«ÖB•¥–f¥æ¦æ•ë•T”0<›ûhö¦‹×œ½»5×•Gİ8ô¤'x"T-Ü¼¾Íï—¼xõ”9píÚ¶=¯Óß‡Mûz
âÑ’Ôâ’b†/ÏÜ,îXü˜Òù;7eíÚÖ½Îİ‹ó¬rxŠÍ
Â0=÷)>ğ¢—€‚àUôRZğJšlu!İù)õíı9ÌÌtÄátŞlqñvJ•ËĞ¿ËKeèk¢¶k~@ü+ìØ(Ä^´’Ì*yëåŒ¢¸³Ômªgy¢=^aÅãÑ·¸%ßˆD1XG3IÁ¤	ykş9²§³ú(›æ¾9xMRMoÛ0İY¿B@w
jû2,À]/Š!ÀÖÓ0²LÛjdQé4Ş¯ß³“n»Ğäã‡©×Fní~¿ÿ ¤sVæ(ÕÎÜÙ‡E©ò<å©³å¬a
¿7ÿñùÙöÀÅyñÎt<6fWçå§çî—Ù}ÌKí£1õÕÒE)Ià$(^ÁÇ ZB;+PŒÏÎŸÜÒ`êÃ¢#'CéÜ˜v±kLGgŠœ+A„VX~K‘]à
××Omc`>jLvE‘—kÇÙ••$ÊªznL’¨‹X°öıpM­ÜËÓ-QÙ™Q´XIèº¸u…ì[	Š½l»XgóÆÚŠ/!«íO •¦Ò:¥¥Ñôßl»m'ë\\ˆî­°uÙ†ôJ^m‡Ö†‘.@zØ5©5¨N.…D×ƒfò+í¿¤mäAL¹‚SëE7¿£HxSƒT](ø—eË¢÷%]Q¼…ç37-”4£N ¦|}/øçÕ;ø«Lb	s¤¾LÑ¼WnÁî~M=.yİJŞÿşQ\œé¦‰±
6•¼º4°ûş`ì³ÂßóÒÅvìç‰’n­„—æxSŠËÃª*F]’1wO·gúÆJ-ó	ÈKj`îO™q_1 ø	@xMŒ=Â0…™}
o™İ™à(P,¥©q‰Ü©éÀô¾÷ããäq³?­¢KCqCè‘«¾§Ğ´ÄÍÖMs;{0 ”²º[ÊÄ¸ ì%|
ICÒlõ«óî¿Ã5RR€üb]>f†ç§{I!½ßŠ„ËuG_²åúºs5xx+)JMU0²4f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-sSÓŠJ3KâJ‹R=ıŠî9sı	Ë‰—ö¾º*y¬ç½/ßf¨y>Î®~Á®Tƒe÷3¦ncKP=+cSpTY%ª$ÈÕÑÅ×U/7…amŸÕßWûê¯Êt2¸LØÑ°éh7TQjU|qjIi^A%ƒò«YÚu{ß~l²»Ô¶¾šQìüÜUk¡ÊàjîïêS®uìª±ØüÜ&§gıì“gÄA_’Z\RÌğå™›ÅË‚S:ç¦¬]Ûº×ù¡; ûyx+)JMU014f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U•9™y%EÉ7:£7°¸N1ZÏ\¶jûñ8ñ»`ŠJŠË2‹õ*ss¦‹‰[èÎ¼¤ì®hyjÑòi›<Ì!nrLIL+*Í,‰(-Jõôgğú}è|ü‰ë_—nü¢ì¦÷`ŞIFÑßP}<]ı‚].¨ËîgLİÆ– zVÆ¦à¨³JTI«£‹¯«^n
ÃÚ>«¿¯öÕ_7”-èdp™°£aÓÑn¨¢ÔªøâÔ’Ò½‚JåW³´ëö¾ıØdw©m}5£Øù¹«ÖB•¥–f¥æ¦æ•ë•T”0<›ûhö¦‹×œ½»5×•Gİ8ô¤'x"T-Ü¼æ{Úq§“>ıİÆ¹Ä²üS¨Ë‚¯–B<Z’Z\RÌğå™›ÅË‚S:ç¦¬]Ûº×ù¡; )¨Úxm’]o¢@†÷š_1É^š­#$í¦ VPÅÚïfP>â¯_ÛîŞõ\¾yNrNŞ'*ó<m.Ã­`U&
Çrh`ªÙàLÃ„QCGÑ„NBÄCEªˆ`E™a1dˆà‰,3ÕÙDá$DŸP«²Æ##ÄÿùHÖ=Ò°l(
Ä”ëCÕ`S
‰¬é
ÔQˆ5U"]›”ì£²mÁ>!}$JŞ‚Çæ#xnIQ°¾}(EüÜ¯DX…‚à—ŒeYŠ>Ÿj™ ‹´µ»<¥`U6<Çi›táÃøf-®â&Á¯±æg¶‹-Ø;‹ùzğçŸ¹$Ğ7Vd™¦55Íµ[†äö²úÖ
'ç‰wEÂéM“Úcš•»QĞ´¦×ãjš}]ŒÕC«I vEùæŞĞáKÒ®oÛQé³pt†ÃmjÅU™öèÂoêêàv1ì±£”í×·çãt!hü‘š]uûPo“ãÚé7êif “V;µÏ.oú­oş(—ç®ğ+d{CÍù+ïh5ç1”À%œã¥6Ù»¶¨ÅT½TWGTß’Òª¹’CŠÒ‹ëôpê<«S_úëÁÑ³Ä¹\Ãy%äLFãí†|ïa¹PqêwÙŒ‚~Ó)3-Ş{ŠB™	%
^K›Šü…Ö:»Ù‘†eÔ06ŞvAQ»d¾Æ^ÏÇnï‰±,*v²o»²rÿì½½EëŠYŞÚĞ]oÑ{y~-Í'	<õq&}u6ßÌ¾oLr™ˆ¨º,‚ÕkZğS\”9øgÒ8'Í]IòŠl ô.K9|èAa—fôá/³åüšxÅUß‹›@îóşy8… z?h”’kBÉC¹#	¥PŠŒº‰Ë©kw×KÒ£ÿ{gµùuñB*>È:ß|ß|3£Q&#ŞßôŞuàµˆAçQ¥Ápm<€Y*4Ğ]*nÌªE¶,È9Œ„ˆƒª
ÀŠB@§Á*¸c:NËœƒ¬LY €’Ç†'Q˜bÆ‘C&DŠfë_\YÊ‡áC&|±‘ŠPFR2›È¤¢X€IÑ@ŒE-–Â¤”RTÉÿÈD^Je êX¶9$8W•0ác¥øøÁkêDİÌ¾?ÂÁp8à¯n{l2ú<ÎF ËùÅu`Fæ€,9ÕM^Ä™ÔÜcâ:¦˜:«7ır_iÇµgs—=cFïí‰â˜„ÑÚpgÒe¥¢Z«í[˜+™é‹ß÷¿ıîÛ§À>]ys©r4ÎF](·Û°Õbˆy£RÂÌy[+nÓùßÄ=£’†-Aƒ`ëÖ³=p1pšD¾õ™mÃYmĞ?[ùSh•îw­›&¸µº×Ä5àâF¶°/¥J.bßÚÙoOÌQ=ÙF™ŒŸNhèÂõ±	‡À6-mó¼Y^/å«LÌ×N=à»©>œ¥ôµ:?9võêØ£İ{İÅÃÈ“%û«Ş]Sõ´µ¾}Rº´É½›cØ¡Uoa¿[Æ&Å†¸³c>ß¢cøı³ñÓ>omø£’1×š>¹YÖü.ØÑ²‡¼Ÿyçø¡÷gÖ63}ÿÔüş¬	JxNK
1sİS¼½0ôõ3mADĞ{/ğÚ¾bÁ™ÊPŞŞŠ70‹’Ú²ÔJË]ß˜Á²aB[
g
y*;¯,ê¬™d2Cg)Hñ¤×hC‰Ò9‰*`ÖÆÇlÌ³AM„¡(uŠ3	zõ{ÛàÖÖ7\ê¹=}˜Ó—rM#˜R[€ÆZïL@{9 F:.vş«,®kí•ğ[™Ä¾HÙx+)JMU014f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U•9™y%EÉ7:£7°¸N1ZÏ\¶jûñ8ñ»€ŠÌMMôJŠË2‹õ*ss¾=?b`õŸ]HóÔÉEÆİÿŸ­™Ò	q“cJbZQifI|@iQª§?ƒtÓÉI^=K58ß‹>‘ıùÏıçô ¶úx:»ú»2\P–İÏ˜º-Aõ¬ŒMÁQf•¨’ WG_W½Ü†µ}V_í«¿n([ĞÉà2aGÃ¦£İPE©UñÅ©%¥z•Ê¯fi×í}û±ÉîRÛújF±ósW­…*+J-,Í,JÍMÍ+)Ö+©(ax6÷ÑìM¯9{wk®+ºqèIOğD¨Z¸y}›ß/yñê)sàÚµm{^§¿›öõÄ£%©Å%Å_¹YÜ±,ø1¥ównÊÚµ­{º †=­–xA
Â0E]çsešN&)tãŞ$ÓM%.¼½oàæÃğş—ZJn08<´=F -QóÄÄNË˜¼„!0ZÒ’ôè­õTşÕu‡GİŞpË×ºz˜[/—o,Y:8I-gÈg‰Á¢ê´_¶ø—¬î[nÙ¯ğ[ù ø|;x]
1ƒ}î)æ]étû³ "è	Ä´©.¸V–*z{ëÌC $$×y1«¶ˆ içp,œSN±ÖÈ5{cmà
FçÅyõˆ‹Ü¤‘8è¥ ¡e&²Æ“Š)õ¹±Ø‚^Åg»ÖÎõşãt¨·ÛÖÃşg<å6¹Î;ĞƒCçõ kìRö‹Mş*«“Ìõ%À’hònõÔ’Iœxí[msÛF’¾ÏüSJª"Å -ÙI®Öw¼”"SêdÙ%ÉÙì93@10x‘Doö¿ßótÏ  D%rjó-©Ø&€ÁLwO¿>=˜fÅÔ|uğô«ÿxûòğâr|şn0øÄš¨X.mX%+[Ú:‰M–Vµ)ffe£÷v˜¢4Ë"n²Ääv™TfVKs½HÊÄ™ä¦Nò*-òÊ,íóM“6Nâ¡wÏ,óvšÏMš×…©‰±Q^%æõº^9o'åªLğ·±yì¦+›ÜØršÖ¥-× 5Ní’áêı<¼^¤uB’GÂM›YšJP§eÕE™âÒ-9ÍÀGÍå"Y›jQ4YL¢§¶r&/jp²²õ¢Òy^”Éèè»‹ß\`iëhAöÈY™Ì“N f ™­‹c&o‚D;·iÑß¢d“ĞO*ì:ÑQ,\$¹I¢¦NÓTÍ²µ™A
Õº’4OWMfkì–©šhalE6×óúı°L~i ®İ½áà“4OëpQïe7Ë²ÉêtX•E”T•
´Z%P—f…Ì°{xÓü\L«ÑÁ@şyByzeÊš9¸3»¶R…3Â]Ù¬áAåTTİ*Õ·=rFİ	0g· <ÌMe‰ã”<ÙÌD‹$zŸ”Ø5¾®tQUŠO°v–A)@wlk+‚D0¬ VĞäá`…98y^ÖIE>.VI”ÎÖÆb`>Kçl…r¤²ñ2âUÁ,+®[eSúöÍåy¤ËUQ’0oXõw-ÄÜµá É+;KBÍ×ak0£¼o_/._Œ/ÌÑ«³ËóW§ïÈà«ús¸6×¶Ì¡È•¹N¡5TgÎã$p'¹J²jhNN–«zÍmâû$;Ë†æ;›¥p&2ğ™ùöäÅ·99;ŸÏÆ½Ÿ“ãÃ“Ó7ç¸õæìùøøälü|Ğ­$"}VvŠÍ#-ğ@¼R€ı§¼aûæœtİíGù®%Ş­ö†æEâ"››œaÏù´Óí¬Õé,ÅŞ÷”sJ¯ivƒ=.±jjĞ‘ÒrŠ•¨@kuJ÷¸[P’PR+¯Â™Á>@2ü
v×=èiæ¢ú8§šÖŞ-ÙÕ*±%æ’	£do„›UŒ!1;a«tFú6“¹;²/aQôJ³´„k¡_Y9„—ä"RØ0ô:TtØÑcğ˜ÜØ%¬=0é³­±æµÍÁ6ŒîXÈ!sUºL3ØLMëDÈpÊø.u˜+uİQÿİ¡9™İ¿L”Yñ8í
SlÁz‡ùòÂü]ÕU5Í«GE¬2»NbzÃdSLnn¡ÌËñï;¸ôj•aR–E¬JØfXÕĞ¸%t%`Ä\2`…MÎh	Aí¯0ÍayQ²ªƒ"‹ÃÒ¦UVë¼¶7Áƒk8¤ +òyX5³Yz#£ò$,à|,¢–\Qm³0Cˆ+m8b@@ªÅ¾‚Ò^‡N<áÌB•b,ƒêf¤b­ˆAÁëKÜŞĞ-‰ê`¨á.ªf…`ÁÇ¡79È‘µ½úˆ“Æ	FÑámK;_Ú J‹E¦MŠ‘ƒ‹r›w·À.DæGDËU÷»HÊ(i/Ï„(?vãBdçŸ@“4‡q¶/—IÜôæ‚ĞòØ–±ìd;¨ÉSÏöú¦´ù¼»Œ”ìñ¢ˆÁkVe)æt×ó¤Ş¸®n]çEh§U‘!$‡ºu²§qz•2c
â4ªCn­ŸPn\¥Éµ¿‘Ãu»ß!7ûŠµ­hm«Àf‰"¦yœÜPÆªpœœúÆ;*ü L$xqA¯ü‹äÆÿÌ‹üCRş’;ãX½%Ú¢ÉãVf’¸åí%Eºè¶wiÛíáÿ„_„NXÊ‡ô¾'›pë-¨ %æ¹õ°–I·-çˆ&ù%d+ [- ô«–©Şï²÷»"J°	‘È•)ÜN¤9²•4¦XCjN ¿
—öÆV‹ÑióÔïxÏ@œÌš‰ï¦íp:¤¸yÅdD¶zà=Ğ_Nç/§ó—ÓCûËéüéNÇgšî´^/Œ“‰8„­&Ã×¥5‹†±&‘L}’ğÇòr&µ˜ïwòò¤å.)Ç\iùÉÊ{99¦û­¬Ü\$@3˜’S]®¹ãKÖá.©FuéR`–bçã×¯Î//¤sÅ|r#yê„R_ iJ€!¬"X€UÀÈ³öÍ.ş¤¼LÌ"/p`Ó¢G’eÔ’¬Ü™ÄsÜòv •‘½F±§it`ÚôV—ÇLHQ%«A‚Ò¬N!“äÍrŠ2
5®›ä±Ÿh†NÀZs`a¤²¤«}©]‰ƒl¶ş@Ğèµ™A²	\U%ˆºBuŸ(Ğ²[‹?Ì¶{şzÿÀİÓÑÁşpß„fww†¤§ŞıÒ|®šG>ü*“ÊklÌ#ò„2‘1yÏ<î°‡÷ö÷¨è—(qš•,ÈĞ•-›áÖ£9ò¸ª^£®ÃöäÁÄÌƒ1›ğ†IÜ}²èÄ…òPo‚–¡¨U\D‚R û31r¿4Cé¹¬æ!j!I*ä‹„U)°º¦fªsÍáÆK§w h q5²Ê °RY%|†ºÈ€’Aüù ( ®ºB5‹\Xhoâ´¸U€JılÅCa¥˜„<.×?.×Z«_®Ï¥fOÊ#”ÚPi‘,•u–AHº1gOÖ€kHA÷µx[‰zeè³J€`›TZîEÓé‡©" zÃü£ -ñøğèòÕùÉÙ±Æ—ö&]6Ëºæ°+ê$ê¨÷@A±¾Ïä 4š'›i¯Ìup¨ƒG_ÒÖO_½xág?-æ€ÃæX«”ú”BQH®*‹WŸÎêÂü2 ‚n‰h«Q÷00YÄ•ŠÕÈ¿Z.^OO=1À¶2Šs(µ$¦DZ	õöõ§}„Zÿ|K§—0Å÷	]ãuQ²ú9„0©«š£Üà¤jh›€Éº[eh¤˜­‡fé`AÌ‹kñâ'€jµÒ{siÑÊb‡‚šRy 4„VD®ÎwU€1U/Z®Öÿe ƒ%êoÁkzó»ñBsÈùd‘KˆmCQ+¸¸ˆü}^\Ã{+ıD‚u †˜úÎºx¡…a+–;KùBÁ&6¦·uµxsŠß#Uh !48‰8Øïäâ»~x6~õF#—¼D”ÚòƒÀjÙÒœN‘±^qN„…¶? §L˜€O	3Õèøäû—ãàûï¿._=5à„½›ÔşË¼};>ú_±.¿2
¨BĞ·ÑÀ—YµsqºbÖ ûJ8•°vÏ²t:t?İ(è+à²ÀBĞ’-N\ˆ?¹µ"8ğkJawgå!ÁHÒâA.äIİK	İ˜gq™0HROÌé˜xƒV¥g›jaÀ[	˜Î@€°VL…Ş>H2´i‘öÊtñ˜ñÁÁş]&ò	óŒ¤.Ÿ ÿ ıKLÓeêF8tµæIÎ¬G¨İ¢ßKP(.Ëñã¥f™}P÷ïÓØ©ƒ’°-X¼?»ƒP¦0|:ƒÿP¨ß$9^Pç¾cv#¶e úl21A wÆ.#P¡+½¦—ìa–Ù¹ìcYôìÓÉÕu|˜î;E‚»YT¾
j‚bq3bß9T<…)Ú_DÙéÏ YŠ&eØ8‘½ìc<³’İm!Q—Áµ‰é
V‚¬Ñ:,¢#ğU>RÁ#[¿‹ºd` BP!Š%:VÀ@#R-ä|dCœ£{™±\5ÎÏB„åZÂ ¼Òı¨s„¤øÂæd:ìÒ\ÚPU§péÉO7¥¥6å$…(“±ÿ¥-D2
D¤, ì»,r “”'Ê	'(ßmñ¶#	…o;"à*Gºç¦-O ×ko3>˜]e 41XË\–èWßühİ\H™E‰r¢¿@¿$’€ßÅD¿ b‹ V¢</qèfk•ÄjˆöšZA½(á´‡_ƒÉÆå†—Øè°~,« Ì1+¬ºşÙcx6*ªè0ü´oˆ!º¡¶nâ†jKxŸML§Y{ƒòà~´³û¤X³9‰£İ¯-î‹I=Ú	’Ğ£‡…õÒì¨D*Qpm á”ÿ¾ÉÓ¶w
"µ­ÚIÚ1'ê‚ı*‹¢†ìëª€“b«H[Õê%¥Ná= p60•áµS+å˜FhE+MjîºL#'†õEÛFfş€’#äÎ#:ïr¸W`šÿU23È·@­á4–m:P¤
šë2½qkZå:%*	Ù^„ı_,3n%‡X¿‹,¦"UR†õ²Z?½
L<£¤0`g¾¥I«/Š•”AúÔ·4²Û¤İ¡Š¹q´( h±OŒ¼à»Ãó“ÃoNÇ›I¯§«„‰9rà@˜$HšC‚¡içèÊÈF“ĞÇÆ•ãÅ^hFâ]}Ñ 6k_Tßí5g8èÖö(sµ%6¹Tq®4íÊéğ`ùLú pÖ\¥E&ÂÃül‡ú"5N¶ï{òPË ‰ÈE\›R’0LÅVRW  ¼r1VB¢qË>ÚPâpĞTåb1L{¡÷@ÈhİjÈyÜËÕ(šN‚I4¥úÂ¯K.ÑË$Z?)a¶¸Y.×=Œa7‚&äó3¡’utİ‰ ,ç7£É£Oİ¼µá‡ÃğÿöÃ¿MŞ}Ş]¼{ôõ§{¿Êk¿şè²ŒÉ¯?ª,'Bªƒÿ…u—[Š+™°è.‚àu Qm²ò¸ ‚1•…ì€T‘S7Ne‡×@6ÇÒÅ±¸í5„_&ÃÏï¡j³`¸†¼5nIüÓvZ¥İ"j÷]­´L¤ŠaìäÙ}ìŠ\¯)Û=«™Tñ5.C¨35)Q“ Ÿ­%¡Œ–›à·5¶Š¬Ò›á²¸Bl›5@¤’¡Ö|üêüåá¥¤øc·Ûä‹èÔ‚İHjæJ0Dš¤'vqJ¡ÿp/0§ÇÔÒ£óÓc^sĞ	E?Sgğ°Î©Zm{xzLm8çqœ•óB„°E[l½
;ŠtÃ„Õ 2ä‚8Öâòé7òíjôãÕç»Ÿ˜½¯ÿûëE]¯ª¯Ÿ=~üÃÅ£ÿùúS.wÖ!\mÁ:;tRî˜y°¸¢ëDÃ‘zEvYO¤yz¸7›/…vÆÒŠ$}Á.HR	ŞE‡©kF÷MÎ67üïËìü‡lúS	Er’aç‡·0_m§Ì«u5õ£ÏøÊg\í.‚’¾vÆªQÑ"DåsÄ\%š¿ĞšÎçõ`ÜşöYD”ÔqÉ~8ÑŸ2"°=¾ìu\;Ù<èƒY—s†Íñ7ÊN2¨¹;Å
!¸F‚ıO¬÷CÌçŠÙ¢ü©…aî¢†?$Úø!­:>3ÿ<0æ™9~ÈŸ<yòÌ<ùuó'ôíRğ2G?5ñO:}¾’2Mêkœ¶ Éx*yU”RI!Çi¥úE€¹Ä„ùv™%¨K$6Du¸ \jË´¹¾v•[)½CQhÂS4DÔïDà\0ugU*¦G\‚‹êJ…£êÊ4Á¶P) Œ¤[w	Ÿ‡ !wt÷eàŸËÚƒqw©@0Cä‘€~ØPZŒO<oˆİ–UÄïzË¥³n-À['/ON‘X\¸¼âDñÉÀ¢$!–XŠIÀJw’¥µwnûìæ  ëÂ¤&ö[³tÃoÍ£Nüa¤¸±N’/]b©Ôáé4DÇÇš‰Wv×Î à>o¿9¼89}ìK¢+éÛFØxÔQ›æ·»»Ãïø—Då>	îÿkÏÅjÔ{{âáu	<ôƒ­Ïæ±%Ïf¢Ñ6½ÆénA¦ ±Ô>|¿ŞÏ‹ë?‘‰m«}$ß ÙóI KZÔ©ù6»¶k”"¬­gÌ›¶#rûÑ4dV8PâÏ‡ IÔ×ŒÕÒ'Ü–˜úƒ¶vrS#nïöEøy”`òÎıèi”9Ğdòzğ°åE¦_x;"H@yã•j6ç7mÆùîÑ§ƒß3á ÌõUW7W'C÷¯»í©_ñoˆÚu‰ıíÚuË´Ù4Mö£wiÛ"NÑUz÷Nß÷Yh^23Èí»Õc‘ 	IÍ\d:ï	}_ğ|,!&Ô,
aà€¢‚ğ>9¤×s‰G(5ïmAù üå¦¬ş.Î¯p{A'·‡.õ¢(ê!<®{‹øÄÌ1—óiğsğ>Hn‚ó&&ƒŞ“2˜Óà:Ğyp¬ƒY¼wƒ±'y”5šÇƒaaæàİ;”‘ñÅU RGùTÔS¤œò:iÁ8µC6+îú'=ÊxÒ5$œ4õ6goÿ¶:ˆÏl§¿»’7Ë;ŞO×¸­p®3H~«^ôˆıˆ ÷'³m±T´;ô÷ÉËÎÉL?P¿é¢ÿ¯âk6<éGD]Ám¯[®ãà¡¡£S#Ê)ÌdŞ+› †ˆZ‡‚ÔY û3éCHB(}{‡sQ£ù&áxW5bRt¤5?JsÊÇ”VmÙ®ˆ.½b­‹`(‰yŸP&¼DK¼O´W”Z s~”Ó‚ø‚©kV)×¾×…ÑæäÁí¶³†nH4ÄyU”Qí¯¥¥†õ‘¤DSíVK­[_VèÂë0ß¶ê6°™üåŸgJ~§ŠşRĞ©[íàíÉËî„b@œâ'‘¯ äƒ*UuşJ9™ $E”v¡Q´†xä++a›L¾ 13<TP¸~±dZb7]{E±ë>auŠÍ~Ê:	Ÿ	ÎC®¾•´LpBU‰6!ó»v‘€Kú‘%éÈ7üvu´ÀŒì¡iÇÁÂì Phdv0,Vš}®8Ò^û”îÎ¸+‹ş|…ÆŒçíYôö\Å†ÅÑˆœî	½Ãºn?Ú†NPã€ˆÖéõóHĞ]TÒóÒ®à?p
Ÿ»•ü
	³ ¢Bï–ßE€wÊJ?D‘£»î N.}±ÿçÔüq-çÁŠ=~ææ€¾P–§²eU~ãa`I»7œ½mô€ß¦H<Î=ª]¿IK»ş¿G˜î®|!àU½m› ˜,æ90µ`Aö;¹3Ü fÇ<ÿÎ½vµÁgK8G€o±UÃ™ğ#Q2óÉZÿG–µô™<P2ü:(ÌuyDP¯^Ü!ÖæG§‡·š!ı Ş°‚3‰Ûyı`ÚFê! ¶f[-–Ë›èVñcÀÔY&tC&“ AòÍŠªíƒG¯m†0±aJĞœ’gê‡ï-ù=(Eßîšúz6 S¹S…8§£ñ‘ˆ3šØŠàZ0A;5‹«`³À×™I0©Š{Lx¸¨OĞĞĞè3M÷]“‡MÔª|)x^_îé-àÁ·PDíGÓõ~è˜G¿ÁpÑzs©öé=‹.#,:xû||qòâL`˜»«ÇEî9g&H)ÆT<Y¶¡í¶_rr÷íV8¨z¾ÿ·ı'7ªíFşS§õhàW© îR7-
ølôCÛ£ªâç,:èŸÂ2Gâ£”Uy¡zˆa£ÜršNG±e(•Ş¥HÚë÷«;”§£F÷Mv‡(ß‘Ø$Fy¹AÖVÁ¯š)>rÇ• ;Sñ´ªL%c[ƒ|rNî<6kÊï‰JGW£¯¶Ó×nìX›xŞ=ÀØ}©„9Ô±ÃÂëSòŠš\Ç¶¼JëwüıÑøõåÉ«3íıåc9|u)†tæäÌ‰õ~D×iÂ=²½Ísí×á%&Ê;í,;4©J=ÙDäY'N>jGşs B*x+)JMU014f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U•9™y%EÉ7:£7°¸N1ZÏ\¶jûñ8ñ»`ŠJŠË2‹õ*ss¦‹‰[èÎ¼¤ì®hyjÑòi›<Ì!nrLIL+*Í,‰(-JõôgXÃ|"ø|óæ9»®ÿdãWh¿4G.j §³«_°+ÃÕ`ÙıŒ©ÛØTÏÊØU`V	*	rutñuÕËMaXÛgõ÷Õ¾úë†².v4l:ÚU”Z_œZRZ WPÉ üj–vİŞ·›ì.µ­¯f;?wÕZ¨²¢ÔÂÒÌ¢ÔÜÔ¼’b½’Š†gsÍŞtñš³w·æºò¨‡ôO„ª…›×|O;îtÒ§¿Û8—X–
uY0ãÕRˆGKR‹KŠ¾<s³¸cYğcJçïÜ”µk[÷:?t Là¦Öx+)JMU0²4f01 ½ôÌ’ŒÒ$†»3Ïù³¿4ı¯_æj°½?ÂD¶k¯¡™‰	XIfz^~Q*Ã#1ŞÅóyŸÌV™ŞTÇá6Ë}ieÄÇ”Ä´¢ÒÌ’ø€Ò¢TO†¢£û_Î\Ârâ¥½¯®JëyïË·j§³«_°+ÃÕ`ÙıŒ©ÛØTÏÊØU`V	*	rutñuÕËMaXÛgõ÷Õ¾úë†².v4l:ÚU”Z_œZRZ WPÉ üj–vİŞ·›ì.µ­¯f;?wÕZ¨2¸štVœ+wÔX[÷W,òkÖå;?ó /I-.)føòÌÍâeÁ)¿sSÖ®mİëüĞ |ay[xíZ[oÛFŞgıŠ©CTW¦“İ¨ØÖq c‹$ˆ“Øl@SäHâšâ°3¤µèßïœ9Ã‹liÑ·]£$ÎÌ™s¿rUš•zúä«¯ıåä‹óÖÙóUQëêNÕ‡fkªÉt:ıÎ˜Æ56­•ÓM[7Æ”N•kÒ²L››&ïŒj¯«ƒi­ªÓì6İè™ó‹q}XàlV¶¹VÍ¶p“uQj<ÁœOwZå…ÕYcìA¥U®Ò<ç}ª1¼¥1µ2k›ÑÄçÏ'…¿µ5;¥Nø¹*vµ±áå0Ş¼oü(š3şVÿÔâf•*Wë¬X™ºÓÖ<º¯§|Aß±+7ûª4i>ÙÖ»PÆ2ÒJ¥e£m•6 E6õDá8+Êµ5>&DvZ×ÖÔ¶ ¦&:"÷ææÑ››¸‚kŠ¹–ñ]Î¨•V¶Å½°ÏlQ7t^DÄˆÕ›‚ã=1Iv"<2.|sÛ¶)Êî×¡[hô®¦KÃÒÏÅè'Ğ®Sëºe×®@S¦] †®¬İ şÔì¡Táwf*zT«É„™®!d k^’¥ÙL&=<ï…í
°L–ß__¾M®¯Ş]Nô§LƒW|ì’¤ãt;ÔR½2•L^\¾üöı÷ï’.ß^_½~…çÓ¯â¯ã§ÓnåıÛïéé¶ij÷üü¼>Ô4L#6vs.êíÎ”=ÓçøÒÙÈùt2ÉõZ%~’íòèËÔnÜÜ£C µ}‹¶RïlZÖ¬å™ÙíHû]›eZç:yg8A@€Uä.ÖŸtÖ6éªÔ‹¹ú«¢%Şk=Ô^q{ø~µ\ª'ÁNÔ+Ù¶¸Ó	I¹‚!’²'tfÍí}Ñlqß,R»wXöy'NQm3zYÆûÔVÑìÊ_‚Euİ±n6ïv‚#•iFLœ1!†ÙBÍI|ırˆï ñ}×f§áxpİ^WÚ[ƒ¯yké	£ aÇğ8‚¢É}i¥I»Ôz'§Ò•¹ÓÇ‡N”şT4™ùí‹²$c}ÖQGPERÏ‚@VmQæ‰Şl"ü¿èXİË¥1	œäÃ'rá>pC‡K/“ïŞ1	íwÔ©¯…îìPÇGâ9û‰„´"c&’èÇÙıÂ?öĞ‰°"ˆÂj×–ßÑá^7D/Œ‹ë´ÙÂ ÓÇ’·i¨tõš}@4»0m™³61¼ 7˜·…n8¶$+Sç"Œîš¶Ş‘Òü«¨_RØâ}äjÉ™S°sP0^èƒUpxê{õ,şSÀù³Şëµi)0#q¬±üPÃ¾$ÁıÚ&Iät¹,‰V:ÁÈ!h œì5Œû.-[| ®gz… }‹€ÄYiàÒ #wµM]Ú4öoÈ9IHñ“d6Wº„şİ!ujğÿÂ;€X¾
Ù‰;œ`‚6‘Òİ‘ı|e³«¡lp˜!ˆÅ»Ûœ¾#ôqrÍ.{ ¦óa¿ÑÀ.÷9 Aë +Ù>]T"pXÌ¶¸0ò÷ö®Œ=ç‘E!¾½[õñ`ÑŸg
É‹Caı¹×!¢%…Â½>{ê6 xêƒ©üû7d-..a9t?<ùØ£ÜÑâ¡ô=Ï^™½Ú{+H°{8Ş}(t™K’VT @‚8Ñ]á¹Û_ás‘Øî«uÇL‰Z9| $W‘äi‹.İJV©#İf?9xœë2=ˆÆ7cA²ûğ<‘ıŞq¾xvêÎêÃiã?r_WûåóTõXPT”’¢Z0YßñÃ§çÔÏqd¢@8=Èiû›»E¦ÿ1\P„KİéäáxØë‰ ò˜‘ŸÚ6Ñ“…QÓ¤8;DFU[}W˜Ö•‡3Ÿ´é\Õ·›Ó'¤zkÚäÈÉÂÃyßs¢Böµ*šU›İêÆç^‡:¦[u[–g”Æk×œÿıœo®›)äÜçO€>İ7#³!Üw&oKízÃƒª>ûè•YRÏ>çc®õ?ãU¨ 	>™âÜvÉ×«òQ’/š³<JMZLÂí–‘Ÿ.:QyQ.É¢Z“bÕ_>ıZ´ßï@ºr$¿È/x¡Z]'Âì<â |O§·‹N¦K*48;•ãó¸ °åàšPİDÀş¦‘ÿ¦Å$>–×“BK§ğ‡ıß1Âd„B,b4íéşf9EÎ-"ó¤ôÈqCzk‹ªS½2ÍKÓVy¯z)Â®ñÕ?øšx]
Y§~¸HÆö÷ÃJ‚$û‡DÖÎ‘Ë…[Œ²v…„†v„¿wH…]y`Ï¸ŒVÑ7Ë_„q¿ÎJZÊòÓ;X+×2NT¡à5”@‹1Á}ì·”ˆQ'!T¾ø†b¸B8ŠÕ›RÃXîÁ’ã¨–w%?"&9ÁµµuÍÅ<@Ü;:ÀC0fuö~PRÏPœlÃgtÑZà(øúÅs;¦š
áûk¯6á8:©VN›Èo_údm^|KùŸ%G†PaÆ{‹Ê8‚Àîï ¤,z6Ê J»G®¼ /¨©¡ÌmG
yÂ‘ù`&–}ß1*ş5öõs)VI¶ÕÙm„"‘ÜÓ¸² oÑ¡’,ÔÎHËC<”±º—×kŠ¤ñ€¯Úš®‡„÷ŒªJjº:o\„<Å°Ì&<.¶¬ç¿˜â`×’ ¿ñ=®Oz[ƒÂ…§(ıQ…xZ9Q{™¼ş§˜Œ}mUÕ­ìëÅÍµ0\Ú'µÙC‰¶idkËG˜ù"4®ˆxJQUŠVš-©Øñ‰>¿é ©¶˜m}‘‹ê¢ÈÑÏb-jlëšy¬Şr9FU'7h¨µR‡2ƒ“€Qj5úˆá,õ‡b–W¾,ÇöÎzrg} œ]øËàÙ4ªôşÌ¬şƒ ¥®Bü
©ÆzuQ°áy¸BÅ_tJì›#ÆŞÛùT¢°²¨ı]Ô“+°*¨¡PDÂàLh™Å0l`ÍÕÃ?êf½¾ˆ¥½LQe™0¢uwG³šélA"Qšys}W!}"æÖºŠ VœÍÉcÄúı
U2iİHíG?hu ál¯Ài4¹i›eÒ{ªğ»W\±•Ë #=tÁ=Z×Çõ„\à‹W©ÏäµØÀsÑícsˆï

=àÁX"ò«‡ÌG´oFËhnà_îw8èKÕàzàAİÒwoFŸ­!|£èÆÑ5€*ñà^šÄ¥±éÉCÜ#‚<à kiy AÌøw'À³Üd-5ƒ~¿$ùæ#IÊuÿ—$’o—Ä‘±$éÉC’¤’RÖH3äïÑ~’>Ü(-à†bõNSö`ÚÍV@>¥-‚SÕMfğÕ;WSU¾9
Oa2AnŠ«<hu³¤$s
<%Ë°Ä×]O*@<{è¬³\UîüËÓ:4rÈ~‡ÜÇÑŠ/¥}T’§ù9§‰˜W•Tc"¢V¥Éná«ºãHŸ(İÎ¬&òSDek1şãt` HBxğª”Ês±G{Ãà‚®D:U ¤¡sÆ+LíL÷«i@¤d´Ä?¿ç÷`£]ÆML‰töŞx]öÅ‡ ]½.–én•§Ïy`ãõŠ™¬L»ÒSÛĞ=lAÊâû¼$<?B}2ŞAnì±52ŒÇÖú!aÁQ[:g™‡K€^ÏâPğ¢âıI$Í}j_‡vT×¢áÚ ñ»:Ô³Cã¢?ö÷^Lˆ—0^k°ü!‘íôÆÙÍyQDBéyŞÃg¡°hü”•Fa¾®»‘ {£&	(DSê£Ôu£«P¢©ªİ­0h¶Èœa]iË Q-O_|—* ‰> Ñê&H†{™7Šæ’`ËíºÊ”ŸÇ©Ùù)öïßÜĞ”Xwí`Ê¥.=£Îg˜D…[‚¡ŞpŸ¨;.4ğ MùœçÒuŠ–•ÔJDdùEWlyúê¯7RßtÔô²»³qİVÜBZÄäÊĞ(“#,±Ê“êEC5Yªº¬ÌÂ@¿D¼‚›OCÙÇ…8Áp†opäåˆb:`¦láé(óå#ŸÕ$ÃH$!uCèÇXázÀ—ìFŒ}é,ZôŞâÒ;äiM‡­ŞÂP©\
ÙºÌÀ<„ùsòòßŞh'úmäÃóîf?"&{îúøÓ`)ÄÃS7åìuà‚…ÃPÏ€^šÿ¨ƒ$Ÿ…—:ˆ Il+ Œ8Pr×1ìñõ¾o8K“†§Ï‘¼qdÜ<§ôÂët¼›ù»7JŒ‰C»h†Ç»Ö*ü‘Š–A9ìì#ÅÁ ¦']ÿ‡çZĞös~zÂã{„èZá«Cw5;
køa;B€_¥ F‡×*â×üZƒAháÍ~SŒd#âÇ$Ô€8|&¢Òr6Äù*ÉLµœ9øP :×x
RL[—\EöÑ}‚z†ì”%,¼ÃÂvÂ¯ö(´sùÕR,Œ:é¥¼ğ¡í\ÊÆßÆ6èÌEF†ĞOÙNğƒ{xQ»œÂÀ§=ŠóĞ1µÄ=şá¼ßÀ”Ó3ñˆÃ6ÜÀ}İø,
Bœ½‡|o#XsxOÿ^†ô¢£Ú/¤qœäö‚z öõ <Ùï¡tœ‹aä¶€«¨Î¤/C6àCÁYq>G«B™¹P|Áôš_•:PY%ß€ÿ†˜BZ0¸\lŞyà\DiøCìŠwŸ¨Ú@¡Äˆ;ƒ0‡^l*(õ0\tÆFºK1üì­óÊOe~GŠÓKô{eW!‚&ì3¹‡ÚoOê:V-T˜ödİï¶ŞßÜëÚ½ı’?6òÇÁŸ…×xJ†~Ğ:zËoìƒÑ:†?L8ê%	½K„Q?ñ£~ŸDR#šÛÌÛóÉ½	å£x+)JMU0¶d040031Q(I-.‰÷4rÖ+¨dX¿Nñ·›ŠëuÕ¥¥—M{¼Šç* c3Íx+)JMU067c01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U%E‰e™Åz•¹9Ú’v7./ì2•ò)}¢Xû5ôÙˆu)‰iE¥™%ñ¥E©şùÊF)ó4wºKRpKÙ›9!õÁ¨>Î®~Á®Tƒe÷3¦ncKP=+cSpTY%ª$ÈÕÑÅ×U/7…amŸÕßWûê¯Êt2¸LØÑ°éh7TQjU|qjIi^A%ƒò«YÚu{ß~l²»Ô¶¾šQìüÜUk¡ÊŠRK3‹RsSóJŠõJ*JÍ}4{ÓÅkÎŞİšëÊ£nzÒ<ªn^ó=í¸ÓIŸşnã\bYş)ÔeÁŒWK!-I-.)føòÌÍâeÁ)¿sSÖ®mİëüĞ =™x•ÎM
Â0@a×9E. L2™ü€ˆW™¤,4­ÄTğö¢x—oñÁ+[kóĞÖĞatml"á‚Æ!ÛT²8	ŒÈ![Ÿ+ª;wY‡N(à’õÑT˜¸øğ)XşPª¡FŠŠ÷qÛº^xzñÄú¼Ìmë×_VmÈ¦H>ÓGp ª|ç†üÉTŞÛ]?¥?æmUo?«CxmRÛ›0í3_aµ«î°HmU’%ÀnHØ\–4o¶q¸ÄÂ%	ùúf[õ­3Òhtæœ‡£3¼®ª¢¶	?õ­ #N¡N8ÆÔB©iéº8 “¤0…¦a1D²LhÛZC[¡z@MfÃÔFÂér"˜Íêºi3]Î†şãcçŞç˜ƒëÌ0LHÂá†0eŒ0‡ËĞèĞçuæEuŸŸç4iJ?ƒY[ˆ|“ğOù}T¢ÿtlBH,èğZjüµ^´À/ú``à›ª[ÑÈñgVôùÀï„ÿÈ²&ëŠ|ı¨‰ç‡û1X‡şÂİlWŞ\¸t>qİÉÔuß&o/,:¿¦«É«•—hy6Ûğâºi†®[KZ.ß¯<Û%Ø^ÍK/’Ğ·£qlvÛD-Cöê¸çÛC2¢ÈËEûxÏÙ.„1‘+ïäÙÇ06d’W²Wjñ®Òû×Y‰•_*o˜‡m^lË×`ue©™)ùØ®³Ãôv¬ìı2°G_·rˆ÷H¯:gxÖÛHÊ==ÀÛeÌlY´–~§Ìó	íİjSÓ[yÍ.ao
nW[k‘ËÜŞxÏ¤L8Õ€UM§y‡nI™¢İUš»åî¥òO¤i×fÍŞp¢xøµŞìoÌp’÷Ó±‡•¿gÙªvç¹íh ?M§·ƒÅçÃK×F{C7¦>Gb<gÑE•Î­R–W/E°Æ*\n’ÊØk}×À÷M\µ¿™y‹çÿ'¦E¢Íh)A+NƒèzğƒC[W §J‰KÿTÑîş0šæ)Êä·ËA_ƒfl
P«»L
Ú	@U
ø}UCs¿ÉBõ¿	x]RK›0îÙ¿b”Ó®„¶»=TUo˜U‚‘q6Í‘‡	®°i´ÿ¾c’¬ÚJHÈã™ï5®[ÃËó·¯ŸT¯aËd¦Ñ£Óğ€‡GBb{~ŸÌ±÷ğĞ<Â—ç—¯@Ûª›fãíìüd´#¤ĞÓÉ8gìÆA¯']¿ÃqªF¯ÛºIk°4}5uŞB5¾ÃYOlí+3šñ4ÈG°Ó÷ãlç/Õ¤±¹…Ê9Û˜
ñ µÍ|Ò£¯|àëÌ <x4°*o«Ç…¤ÕÕ@ÌˆhîWp1¾·³‡IñMÀˆÀŒÍ0·AÃız0'scãK òÙ¡ƒ 3‚“mMşz±uëÁ¸>‚ÖèzöØéBqÉ4
>>Û	œ‚˜\HåouKOÈ³Aş[D.T.½=ıÓ‹I“nF¤ÄP°£µÙÂøK7>Ttg‡Á^‚µÆ­	~İwB^Uµı­/×Ö£Ô%îe‹ˆëVoW®¯†j}y1^,}ØAwsí<.ŞTœí´ğıoó	ù7J‘ª=•x	…o<a	¬h‰çU{®6b§ ;$ÍÕD
4?À'°Ÿ…de	B¾-2Î°Æó8Û%<…5ÎåŸ3ÇwŒ J@ ¼Aq†s)l™Œ7ˆL×<ãê‘”«<`¦B…‚JÅã]F%;Yˆ’!}‚°9ÏS‰,lËrõ„¬Xö†(74Ë¡;T/ƒ>ˆEqüu£`#²„aqÍP]gìJ…¦âŒòm	İÒ× N‚@IBÛUì7,”Å/V\äÁF,r%ñ¡K©>F÷¼dPÉËH*Å6"!Nœ@tÁ¹œ]QBÔK@Á–ØMßµ@Âh†X¸|±xo~" ˜Ã\‰x+)JMU°4g040031QğuqõğqqÕËMaHvÙôuÉ®¿–Zå‘‡ãâV,ºrïTq@¨O|k`¨kpŠê¹Iâ„ò¾ÍP’ÿ·¯ßøT ‡å&ÈxeV]oI¼g~E¿Å‡HÉ):ùÍq6‰%Û à.‰N'yØ`âÙ™Í|˜ğï¯ºgÁà{‰ÃîLTUWïÊú½}ÿşÏß–[åhï3­} ßigÜ†”#cÖäÿÿºQëM¢Ù>mñÈšUPaOAw>šäÃ~L´ôÓvÁ?kJ[M±Óº!¿Æ¡èmN÷:«UÔxòlôNN­½µ~Ç)7Ù4Ú§#26ƒÚ·-n¤àóÊê¸õ>ñ©˜ti¥q	ÿ¢dMuĞJŞqV©új0ÑpøÑ“ó‰22~6éK^•·Q:}…ÿĞu’äı¹ñpHtëR5e@}É!·8—h›Rw5™ 
<«¤1J§äIÅ'ú™uäÎKØÓœ´Ûî0úV§-wf¢{“hçÃ“IÿêPn í­£V¹=Õ@/J(°´¸EŠz¬¤w)µ1£;c-µŒÑÏlê'Ë„ÕÚ€ ­¶­
Ğ¤‰’IÌå^©£ÕÊ%ÁîÉù£F¯0–¤öæR×’ºñÜ$³æ÷ µ–[yrß;P« 0iû?ÖYÇ:×&Ä4.#Û‹‚¥-e	R=A#3r3i¸¨84V3|ƒŞÖÙZf£Şêú‰Pƒn9c‘ô(èà/Ğ÷²£­Œ+ºKÂÓ˜Î6ñUD+°¢}$ƒ2^âj“Ë'ÚXùœú\€E•Ú'‡nú^?áb™¿É\Ån¥&pfè¨ÜR=rCğÏ/Ou!…ëRì©0¤ºÎî‡CLÑè@³]”"Rt˜¥Û¶ó!U!øpEªj²ÕäT‹ÆÇŒ#ÊAŒ&G"îÁ&¤À£i0\@»`'ØóáCß“B¡n^]¼¯ş¾¦T€<FÊ$#»Sq)£#dùWÌH´ï™!7wp².­¼„*:D5é‘ÖÛKZ¦#Ê¯ê”"A¹¡©GáaĞÒx‡Ã'rd”cfüåFÿÌ*iêüN#ˆ—8+¯B#>ts„ÆZÄµ$ä»f™5äàI‡a(K*Ğ33ù‘c’HÍ›TÒÇ3EH|ôÑe;Ğ¦ÏL©?äK’Üƒ¼ÂU§ƒéğCÙñ²²ØÙÈOF[¡Á9ğÃ#W±ÈÚ;(–)m²ê	b=y,ÅÖŠ]]<±İcHƒñ9ò$°)2ß]¶Ğ?EC¬š_µ†Ô`aÇÄÿ^°ƒGX8öRpg>9ØùH"Œ×GÇëEü],„·ØnÌm¼oú$}k ¡ø"Û€˜ <?N^±'¶xfŠâ:Ì:Ö(EïE+,ØA¿H×lğ½‘¾øàÚh[Œ
€<c«bb
a¯–©qĞk‹åéİxğãÔ*ø‚¶2äŒÒ9¯d¡7AP¤8=3Ïº!ÀÖoû—ìNÊØ(;xfUâ|W„²¤#ÓÕÒ…c[œù˜Lœ<1Pïë—àı«qßEz÷v´2éòøûıå÷½ªiºøF‡ß:Õãß¯ˆíëaQÍ—4»»^~šÎï'ÓY5¿^Ş>|FÔÅ÷Å²º§/Õ¼y­ô9°ĞÈ-l÷]ùòõOÙÆû‡ïèøô<Û÷å—é2ü]Í·Ó‡“b¤Ø¨0ªMYNg{	Rk›Gìı¾"Ö`'R)(¸ÜIkÈRÍçÓ9İW‹ëÏÕ¤úvSÍ–œt9¿¾©}néïÎ€ºEL|Çz]hïÇ~È_YX`øÊ‹†§W¥¤êm±s Ğ\Dv’úïnKšW³ù”€ìlAª»éW`û®Ijx+)JMU02µd040031QĞKÏ,ÉLÏË/Jex$Æ»£x>ï“Ù*Ó›ê8Üf¹/­l11 Ç”Ä´¢ÒÌ’ø€Ò¢TOÉK×K'?İXüöKSæ·çÏKb—hBÍóñtvõve¸ ,»Ÿ1u[‚êY›‚£
Ì*!P%A®.¾®z¹)kû¬ş¾ÚWİP¶ “ÁeÂ†MG»¡ŠR«â‹SKJô
*”_ÍÒ®Ûûöc“İ¥¶õÕŒbçç®ZUW#ı;u™ìú£Š«×ìú8×¥æDÄñ%©Å%Å_¹YÜ±,ø1¥ównÊÚµ­{º şJk`x•Î=Â0@aæœÂ(ócKq'uU¡¨5·GB\€ñŸôÚÒûÕ ÜÙª
)abŠS!n%#EÖ€Cl\²çBY5$$÷”U„ƒ¢æ\3Ö\EkŒ>3)i‰c^GŸ&vò²yYá.ã[FÓıÚ—õòËãCíC
L1 |ôŞµïœéŸÌİ^›Í
õmºA—½t÷K(E”xS]‹1íkçW\èƒ
Û±ë¶„…n×B¶(èC¡‰ÉÍ$!îÚ_ß›Œ:c‘>4O3É9'çŞÜ³Qf·“·¯‚;L õVî ÑK½ü½ö¢…`@j˜R7‚1Êƒ¬A› L9dâpB (³PíLÓ)ÈÆH[É¬q—[ÃQ/m€*3¾8gÜÉYµÕÆ!µ0Ó˜÷±AXÂÎh¸ƒçä»³¯ó=×­9K”¢Èûµ&óÎÔR‹µeüÛ"¹"¬%:÷ğc0Ã=*cÔ–…èa:…÷ğ>c`ƒ›\\êèqæ©¯ËƒØ$øb¾¬¾§'©ãËÒ“ä¨=&AáÁZgö(Òÿ·jE´||…Xé€Zò!
‰šg‰£g*á
cáÌÖ±¦IŸ˜ŞFª;{lÛJ7NÊÿÅ»»ÂZ+y’_š:<3zÖ^Cÿ‰?7ï+s"1?‹"¿ÙP3ƒ‹uƒÁjeX/¢Ãj~ÖŞS$ÍK·ü®œ”‚¼ˆNuGù‹Îw!X?·2ìâ¦ä¦³£ş¸»(wìïûX¤ñt}IÒ[}€™|4ŠÁN
Pi}p»‡jékl˜<ú"º6åêÓÉC2t.P çNÚĞIŒÔ°í“e‰%e4Íå_hfROüçè}J~M¨æp®h˜h<ªÉcŞrQ• 3g,‚C«Çœˆš*õÍ†B‘ê­¸‡Æˆ¨Ğ—g‡ê8İ]SÈ!ÍõĞ]º‡ŞŞ)d§”öu.â;Š?dw/x•ÎK
B1@QÇ]E7 ¤¥IZq+ı¤Xx?J¼İâŞÁ[÷uj=¤‹NëR{cé•|BÙS%©B™;Á›#OÙÔrjàBLHØùÆİ1ìR§I¹¢Éo}íÓ.¹¹e{_ÆºÏç/o›èÃ:ô)2'D{… `êwNåOfs›š}A@x+)JMU066b01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-0U%E‰e™Åz•¹9¿Ê¤ßTÖßèû¦-ºu3;_¡:×GMˆu)‰iE¥™%ñ¥E©şUky–,úÁµÿŞÆr»]s¡úx:»ú»2\P–İÏ˜º-Aõ¬ŒMÁQf•¨’ WG_W½Ü†µ}V_í«¿n([ĞÉà2aGÃ¦£İPE©UñÅ©%¥z•Ê¯fi×í}û±ÉîRÛújF±ósW­…*ƒ«i¾§w:éÓßmœK,Ë?…º,˜ñj)Äñ%©Å%Å_¹YÜ±,ø1¥ównÊÚµ­{º T:‡Rx“IÏ£F†sæWôİšÌf¤LÀ,ög³ƒo,Íb³´¡Yıx&Ê-§Ô©ôª[õ¨JOÚ5M…MSì¸‡plS4Ÿr\,°#Ğ4ÌY†Ï¨ŒböBÂò	+0Ôá@ ¸‡-
ŠTÎeqÌ%Y"ğŸwœpØC6‡|3i&ftœÆ¸ìzà¥ÆÀ+ã9í»ƒ?‡_Áß8n[8ãï]_üh¡(–˜=øF	E¤¿)1üŸßTU¾ı*YÕO&°ux'İ”ü›«şÎ	@€Ê9m²$ÉŠ$eZ¥ª‰ğ¶LWÙ+ç›ê£F=æ´{~µÒwšTëÛ™%¥x9ÿæ¸adIæLuh¿9¤µkÍ™´Aò,/óLl)ÃüÔŒ,r"&µİÍ1pPvôıH€¡ÎëC'±Ê–yå„Å0Ï.´àÌÊ‡:™y—u¢Åô…h±}böº”§“G
,ö	àÃ@ÌÅÒÇge™lÅ­@ÃÁp~=÷|è¤ÆHl˜ ÁİøèoŞƒ£fUü—şåÍ°ÔVv+gàûÈW—$ÔÒA/äPU¤G¯ê™ìxœJ)Z^¦Z;³Ìœ‚Ï·®®Å¡ò³FRâ¾cé‘òv0oŞ»Ğ˜Ül×ì´i²ğrk#.ã¨A¼¦6Dz†'¦“_vº ç€¶
Ë#C7œS¢÷p3ßhÖŠ¬[üEŸPv2o·‰¿†¹¦OÔôO6á´Ò¯këà5ëöüeK}º[Ê5Íåú€¹d•H¾ŠƒU`J•ªWÊ¾QúŒaq3#hz¥é>µ+¨Û‚ïhº'ÃÎ<ßzFàõÍÛœ€÷"Ş¹{Uš,è>êŸi&øC"×GN4ù;ş\³ä…á´îŠ¦U?ÃâkÎú²RR—J÷õ˜ÑñihlkvGq‹öe`Ã‚'IçÑ"ÀQàëE¹Ì/—ôù*VĞ"™‹Ñ(s[9ÛÛıñdƒùÒ*qÆëzû€Üºw³Ã&m\\„”÷Nš‹TS#<Nì¥ĞğÔ'Ü›ãD]ß’TEòÀÅe¦á°6Gúúƒ ?j%~ÿ8£šÇÿ2†pa7$cÔÄİ¯äÉëªÅß‰Ÿî¾fGx“ËÎ£FF³æ)zoÍ¸0m¤LÀƒ¹ûòï¸s5´ÁøéÇ3QvY¥–§TªO:ú’®iJ
‚è:dˆ60bsŒÒ‰x‹6 ˜g²TÜr	Ÿò1—Ç,ÓGCÖR Âs£Œ‹0a¶ãŒgó(æ„œO¼Bˆ1f¢'½uğ“Ràß¢9ºœ‚?Ç_àoµm6ÓïİPü>_!ÜBV@àÄ2Éï”4ûŸçE_Œe¾ı™ìõ#pöğõıQ
Büæ`@éêoY’dE’Rµ$$Æûè)¬b„$è²Ë‘gT­ÒN•êñmJ¡¤•û/gÀgÃ¥5–µ2r¹ì§¹ˆnäzò×,“g#ÛÜhKe?ğ×Çš›5iƒ{¥¦e3!İ,<.ğ|#5jÎ'xI¶‡Wrã[™¿ò-*ßÇjåæ‡©[Š0»›®%®øWézÁh«¯ed -øFí`u¸	v!V'Zä²1òjğŞK]A¦$WÚİè“ÂJ~–ïË	–h;\bøV?›œ:]…›1gEe=Â÷L[KÁ„¥áÉ>rÓ1&üLHk\ç ¢Ü¬/­<);ÔšæêFx/Š/²_Š!”ÃF²é×ş²ë›Íú,Uk÷4É"Ï^å3+g.|½ü[_IŞÇ…¦mRİ¦ÇóKş%gE)Ié®6ûÁNƒ‰6Y²D:¹kä9U­¦mx=ßğ‰k£Q¼Kå„Vêq¥¿^ECïGÍŞ†ëBÅ½ï¥eƒÚ/‰ã-‡øéØ»$0<ÓX…7®ím¹ı¸_¢Æí›èšEaöõÍ.ÄËƒ[ŞGzôêp½“]t¦Ê¥Ï¥€/ÑeÛ»çÕµ
t·Yì<$Œb[ã‘U¯D{§kÍÁ]€,By•ç Š±Ñ%+º×1‰YÚ|-NoÎõŸÈ<h¥º¨ >™İ=k¯çU)b7–mCåE¶ÍÉòs•7Ù›ÜÕC¥­Çk5»¢qƒz1ÀUÁ¼ÆivL£·{Ú¾À¸¨µd6w"µëgM•Ïlª°ÛøÑ	äÌüÓrÜıWc»­f}İ- ºpß?Ë:ıÎü^›x•ÎAjÄ0@ÑYûº@‹äÈCéUd[fI<x”ÅÜ¾Pz.ÿâÁ¯ã86Ïx³©
)6a’ÅwâÜ±äT;˜RGÅ¬¼rJî)SOƒ 9øêK¬ÕÓª”$ÆØJ×)2ûLeí¹U'—=Æ„]Ú[šÀ}ß1¿ÿòóTû
>‡C&ø@FtõwÎôŸÌIk Ğ¯³Ú6N°S¥Áqí¶=w…ò6}¹‚‰L\x+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤Òbšô4¾Šå¯W'\ñ?ï¿Ò©÷&Ÿ®
 <g!zx+)JMU0²4f01 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÄxwÏç}2[ezS‡Û,÷¥•-sSÓŠJ3KâJ‹R=ıªÖó,Yôƒkÿ½7&ä4v»çBÍóñtvõve¸ ,»Ÿ1u[‚êY›‚£
Ì*!P%A®.¾®z¹)kû¬ş¾ÚWİP¶ “ÁeÂ†MG»¡ŠR«â‹SKJô
*”_ÍÒ®Ûûöc“İ¥¶õÕŒbçç®ZUWÓ˜Å¡éÆ®Pyÿ[Xòf·•Ú‡&A_’Z\RÌğå™›ÅË‚S:ç¦¬]Ûº×ù¡; V3ulx+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤Òbšàv¡_ûœ¸†ï‰á–çù @Ş#x+)JMU07e040031QˆÏÌË,‰×+¨dx6÷ÑìM¯9{wk®+ºqèIOğD¨²âÜ¤Òb¯7s˜vïnŸ­yåœØ!Åõ;şfk  F´#3xİ[ksÉÍgıŠ¶UA#$;öFUú€Ùd%P²ãr¹¦†¡³fÈ<ŒU©ü÷œs»çB¶œİhw³åZÓ}»ïísÏ}ôxDSuôâeëoÚWhuû×‹TÕ¼º:n½Tí™;3?Uıp–%iìëdo_µ³tÅ'j…·ªëw¢ÀİÛÇï—:^úIâG¡òµĞ±ŞªëØS=k¨y¬µŠæÊ[¸ñµn¨4R.æ¯tœ`B4M]?ôÃkå*8ŒM”DótíÆÃgÊM’Èó]HT³ÈË–:Lİ”+Îı@'ª–.´z:¶3Öe™™vÈóCÈÓ*¨Ö>ÔÈRkjæQJƒ¼ ›qùãÀ_úvNÑ
Ø–@î¶¡–ÑÌŸóo-Ê­²ià'‹†šù>ÍRŒLø£§CÎ‚.‡Q¬pkÓËÊ(®aÖT	Y/¢å¦6>÷4ÏâËÂ83‹`:Yõgí¥ü…ûŸGA­© …3ŸZ''r|<u§Ñg-*$„QŠ‹åå,d'æˆí£dášjk9,í‡Ø	Ìµ‚šÙ4IßÔ*ŠeÑmm›fo{j<<›¼ozª?V—£á»~·×UOÛc|ÚPïû“·Ã«‰ÂˆQ{0ù †gª=ø ~êºÕûÇå¨7«á›è_\÷{øµ?èœ_uûƒ7ê5f†uŞ¿èO v2T,i…õ{˜y¦.z£Î[Èn¿îŸ÷'uÖŸ(÷l8RmuÙMú«óöH]^.‡ã¶Ğ…àAp6Â:½‹Ş`ÒÄºøMõŞá‹¿mŸŸs1Hk_A‡w©:ÃË£ş›·õvxŞíáÇ×=ì®ıú¼gƒjóvÿ¢¡ºí‹öîp¤†C9ĞìQ½Ûã\³?I8 2á`2Â×tMŠÉïûã^CµGı1Ír6^PMs°Ä`æ gäĞèb¨âl0„†»‚êù~T·×>‡4Ô ²ø8ŞÜ{úôiÿ¸p¤:»ÀTºpSµ„sy@4 wywÕøâu–¨öe¿‰{{ó@÷ÒÛÜÃ_;Ês2Hù'^æŸã“›¤`LÖi¨Ëa0¥v‰‰5hÄ¡{†×Î4›ÏuÜPã4Î¼4‹µ™2÷Â4Èö#/öì.0÷ 'ÕêpÇô(9xHü0û¢ntê |èÎÀuuÌXİâIzBrp§>º³gë…ŸêdËìA sáLzUıïTµ¾´ZG-¥À=äEüqUªC57x¥ÜÙd–X£nuºRF@ëˆ ;ÔM]ò2,œ.ü±„ıtl%Œ'ÃËªJø±Õ’-øs*îœ]:œt2ìÏ‹öà`ç†ã	<¥Áù/vÌ·ãò}÷Ş9İşÈiw»#Nå¬ã³î[µÿf0õœAû'³0ç}ÇüÁĞuvÇN7vƒÚ´ÛC´õ:ïœóòô¸~js~ ÃëtØb8sîÇ	§ıÏ`Îémª÷Ä
ãóö»^a·Ü
­W­ç”r•Ğ}åØªÇ.°T'Ÿ.Ë¿j½¼bCéÏ€‘?ßÛXqÇ  ˆ[¸2 6Îb(?‘½¸¯ûå¡CŒİÂn¡…«WZn<i¨'x.¿ÜÀ²!®Æ;°BşJ!o4âÃÕÌ]®ˆ{¡Äo7ğÓ[bøF„ŒºïA¥+ä…t¢åÔaöÑá{•"MIÀ ª…ˆÀ~·u‘sÙë”"ä“•ó#åÈöá:4G2q04&“AhW»49@ºËW¯pƒwQùÆ²!ìÍTK²R!¤DÍô\´Â¹æA`eª¦‘¬CË=bî
ëz+P¬%å8Æ"!`›±üğ3l={ºKİH£èÙ\¯ŸIÒã=[jù,Ù™Ê?öœer]+ˆµ~"0»Ÿ=ÚvÿÂú4±3÷u0K€çcËÚ!sşÑËz£òl¸×É}áy÷=÷ã‘5^êu‘üi¯¢G<[ÇD‡ÜYÕI}ÕDw4î} Ê°µÊ÷gíUßP=´ƒÌæŸç›/veáôsÛ‚àC7ÚáR¢³h»Dhq¯uRàUê‹ÃåîÇ âIX•Œ1Ö¤!>
¶Œg•g¤åq¯¢UHZ/îã*¤Ï)SÄd¥=X˜IœÍ÷ĞTŠéjşU­ÜHdä¢°y} :ArÒlÅaÖ[€qW”¨„E|äÁŸıY†ä”TM##M£îâä'ê
ÙpF¨]áŸEŒz¡t Y™$'yHVp—L°
LíÊä6. ×&Ó±ÌóÚÕlæH’¿ÁaÆÚvËÊctŒıæö4l´Š#(ò  F@ìpE8™…Õ_à'µÜEùHÊ?Ê¤šyL:÷Yø:h(¢.‹q˜¥ ãó<›\ÄGÿS“ÎL©fêÇÖ'õgÄÊWg¢Üö`c¶rôÑ§Ã°ÿŠÈãİƒ`ÌÊ çfĞ¾DkØÙtH´U‰Rc5ùÍkÏÖb`è˜T¬%û”â¦xr×ÈÖW8ŠoÏ•®óğ„Ù2•„”Z4eÕWú*‘ıpY0CÊXd×@Ø¡cŠ*+8m®{(ô¤"ZèÍ|$4©:œéÏ‡@Òg©!=ç\ØXTã8(üSÇ©¡7°rr:@¸²['+rƒ¨P¯U²Ä hÃdÛÓğC–ÌLĞGX±¸d™™3‚Ä´*9˜šƒF¡( vŠØo‚8Rb@Zq©»:Rk!Fw£I!+×ğÙ¶ĞŸ‹$ì…q…µ€$ÓwˆVøP0eAQ…4ZVÆd$ˆ­{Y#ci©¦c{
Ü††E9)ªXÇl„Jçãs™Ë%jVß™d|ò{
[¶4,›¡¾@¿¼e1’ùSVñ“Æ'ÂÒkñ?YÏ¢DÃE*«u¼{=ğ¨ş‚âĞopY˜®È(|_ı})lJ"äÄøh}(–EØ8Â€lÌä:nR!èÂÃMiºıJîV;ª£ÙDS–æÛç’X“•ã“BI»êº¡ã—
°õOxé6>! ˜étËÚÛÚCF¡<¦„	Ü/©œ[cÇ‘­6Ì³a{Ù<şg÷zæ€4´éFá›­nN‹{Åq	^(MüssÃC›pÍİ§%>ªyù¹ˆàÄsà9âBFY0½~zP\¸ô<•rè[o»ä9èrÅ‘Ç€kÅÁØ4,Ráœ jìS©"KpÍéSl UPœ9:”À&h[ÏÕÜõÁ† 2}¢iºJN§ÙuÒ\Is£Å×‡èfõì«&~rwJ
Ô
zùWëßMpÒÒMÅgê şaŠ”°ØÓi«”-‡İá‰ê¸)2ş°'É<s‚t#À¹pˆ”¥åA·%óŸéÄC·]ŞÒfkôip ë8BÏ°æ7Á·’%!Ñ ÓÁ»Ln9£9,kÁCtBTé/Hãê ™3¡¾› *`P„\*D—ã$>D=™Ë1/Š°TI
Å~M<²ÈÃ9ª,DÚ‡"‰ \Ë>©¢ğû@e¡×Ü×cZ.\ÈÒĞÈÎ·ÁĞ¦!ÆEi+½œ¼Kjİàõ¢å2}fèÊ*kcÙ†ƒIP–¥òhÑ$äÃ¨†Î8&8Ò.@Ÿ™‰˜É½*Í2ßaOâŞÍØFB’·€#q¨i'mº½ÙûÆÆXm¢•·ûŠ3á¯qvKz  ÆÃc¬Ñpù†äRJ_Rßm5å^#ñÆ`?}rP`ÁHß4»¼a©0Šg›F¢æ »l‘TŒÑ°‰Ãæ	ŠQ»nÅ ÉÒ"ÕƒiŠ5LŠ´Ë"¦æ$T1ËÙ“|'˜†àtÆ€gËíOr=>vö‘S²È›-,ß$Ï]ºq~å‘®5I…]aI|M(£tA®ok¹R^’iåiù(_ÙÈõ?±pZ*?°¼¸[¢—ÒQ`o¨VC-ñ6…ÖANïò÷¾z£ùÌc+ì_.X‘DÆ¸@stK U©×9n_	ø }BF‡¥°OU=/ÈåFMÒ²ØĞz¤™W)W)ı›lÆ~_kŠ…Ê•6d6¥/3‚ÛYƒcVµcãŞõ]ş]µä’"˜\¢®¤­Ò–iXjŠÏŒÄ*1-P"¯EµBIÏz*2š'ÎB¹@µÙH…=¢DÜ"ÉMSğ³R/³Öj|FÎ±ı8^uôÒå´N¾ôïÚ­ìVÍŞ_ÁYÅ·Êæ_Ñœ¤»YoÛ„ãïŞ×¦Aäİ<ÀÙğ6s^æ«œ·F®!—U›ÙÅC|m‡q—Q††âŠ4qDR»†Ë¼cNÑæRF’´‘v¸X}z[8.ÇØ”F©.›Dc8I
H;F&$½¸ò4ª¾–§èW!4L³©¼´¤2š(’¬æ€K{´>kéQ{ÁE»´U,"=Äuæ5‹f—ëz±›Séô]kTäŠø’Àß„¼4€áü@hÇæ¡¨ ãTè}Å·ÀR¨·Qk3B…+Ã­¥ÈToJ“Ä®â	<Ø/»LR­TÂÏlN–*ld`8~Tñr­vŠ¾wY¬Ãà%„
â\ÏÍEÉz
m -J<tL\Fpü‚U‘ˆ›=Y‡µVaÆ‡àáÿ‹{aƒí{õš9 2$ÿ!ØØlÚ¼S`©øëL,=Ş,¿e®Sİw3v×æê˜_¤{JF€MJd¯FÉI¡Û—‚DÂŒÀæŸ”)ÓšÙ¢Šòn*®¸éz&£ÜLùÉNàÎ²Ï²£0D.Ê÷B¤ñî†×`c{µk_T  ÓLyf¦iÈÓ]­@»LÓ‹CØW?³ˆ”-Sj¥R•Ü‹­g¾NFÖ6ƒîÙeE"ÓjfbhÆXÉìµJXyR·üšoÛÜH3ÎàªHŠvÖ± óŠ<Š¡^¸Vâ;Íx%oLa.şd¡0qIÊ¿fÒ„r„Ö yá!W~Ö‚¥†ê?rlƒpñl7x]÷ë üQÎíÛÉNËDİ‘|ÆË¸Sj-m¡³òJn£3 Æªq|¥1PZp³Wbº•»¬Xi–Üã}MÛë”[r×Õ¤êwbØö±Šo(1¶3ş
Ú8§HaïØê!©ğ£›Œ/Ú 5Ç·å­3[Ì³p¨ 9¶0 9İM“?Ù>¿ˆÖR·—ìpÀöÖz%€iö5+ –‡G÷ {_™òs'²€5±T…‡|Û¿vÀ€ï¸É½‡¯€`³à«Ú’û.Ãë8‰î®6„„¹äİ‡¼}PéAÂŠ^Ä£ñ‹ñ(°èM¼ÇyS;8}ı·4%åL-ÏÎJÂ}tÔ}­–‚^ù+>ô%ğÅ{éæuxÅu¿	·¼N.2¦¶
q¸˜Á[q%.îW©ÂÑÙÇË+ò+7Wƒ­Á%‡d‡òÅÉê¼¼Ôç3yC.÷æ¥Ì»ğ…<¿Ò¨¬Ò¤½df^Få¢EZ"Ô:K®G¯ÛFø^Â¬X„/ïj?¶%+ÛœQjû†C=R“Óùag°.ïf¼KyÉÇÖIùVŒğ”¨ o{U€ašÇ /şÃ.æúVMşÉUêwñÖ UÏçQ"ÿCÂXõŸÄ^«F{Gw;ªı÷‡\’	Óg¼Âº-M%!í™ÍE>m  Íé+y—”“7A¯–]£ÅªW°(t\sknŞ<(€Lr¸ûŸÀ›ol°e\cÁ²ï©"Œ ï¯¾A‡‹á\Â#R V{ã9¾`°İLQË&’)8ítiÎ!3%™Ò ~¬ÜÔÍ~ÕR”V.ƒóî‹.Ü ™ô#”¾]E.hE'ºmIù¾ŠğOÍ¼ÒXéAVÌú¸É/¿7µpq¶«‘´;¾šd©¨öú(¿|ûŸ_<·M¢¼o/„¹«WT¹xË‹_-ı€ş`ïíÊÛ¶ïºø=Ş
ğÕJ¹íÚjŞxïî‹®Zğ_¡¸
×û|¹¯ø^À4[!”¯—ÈÛ'¦Í*kÏ\Bî6¹Mãdî‘WØ?‡·š	ô«j´·bŒ{Cø Ò„NxKÊÉOR0`  	°ğ#!/bin/sh
#
# An example hook script to block unannotated tags from entering.
# Called by "git receive-pack" with arguments: refname sha1-old sha1-new
#
# To enable this hook, rename this file to "update".
#
# Config
# ------
# hooks.allowunannotated
#   This boolean sets whether unannotated tags will be allowed into the
#   repository.  By default they won't be.
# hooks.allowdeletetag
#   This boolean sets whether deleting tags will be allowed in the
#   repository.  By default they won't be.
# hooks.allowmodifytag
#   This boolean sets whether a tag may be modified after creation. By default
#   it won't be.
# hooks.allowdeletebranch
#   This boolean sets whether deleting branches will be allowed in the
#   repository.  By default they won't be.
# hooks.denycreatebranch
#   This boolean sets whether remotely creating branches will be denied
#   in the repository.  By default this is allowed.
#

# --- Command line
refname="$1"
oldrev="$2"
newrev="$3"

# --- Safety check
if [ -z "$GIT_DIR" ]; then
	echo "Don't run this script from the command line." >&2
	echo " (if you want, you could supply GIT_DIR then run" >&2
	echo "  $0 <ref> <oldrev> <newrev>)" >&2
	exit 1
fi

if [ -z "$refname" -o -z "$oldrev" -o -z "$newrev" ]; then
	echo "usage: $0 <ref> <oldrev> <newrev>" >&2
	exit 1
fi

# --- Config
allowunannotated=$(git config --bool hooks.allowunannotated)
allowdeletebranch=$(git config --bool hooks.allowdeletebranch)
denycreatebranch=$(git config --bool hooks.denycreatebranch)
allowdeletetag=$(git config --bool hooks.allowdeletetag)
allowmodifytag=$(git config --bool hooks.allowmodifytag)

# check for no description
projectdesc=$(sed -e '1q' "$GIT_DIR/description")
case "$projectdesc" in
"Unnamed repository"* | "")
	echo "*** Project description file hasn't been set" >&2
	exit 1
	;;
esac

# --- Check types
# if $newrev is 0000...0000, it's a commit to delete a ref.
zero="0000000000000000000000000000000000000000"
if [ "$newrev" = "$zero" ]; then
	newrev_type=delete
else
	newrev_type=$(git cat-file -t $newrev)
fi

case "$refname","$newrev_type" in
	refs/tags/*,commit)
		# un-annotated tag
		short_refname=${refname##refs/tags/}
		if [ "$allowunannotated" != "true" ]; then
			echo "*** The un-annotated tag, $short_refname, is not allowed in this repository" >&2
			echo "*** Use 'git tag [ -a | -s ]' for tags you want to propagate." >&2
			exit 1
		fi
		;;
	refs/tags/*,delete)
		# delete tag
		if [ "$allowdeletetag" != "true" ]; then
			echo "*** Deleting a tag is not allowed in this repository" >&2
			exit 1
		fi
		;;
	refs/tags/*,tag)
		# annotated tag
		if [ "$allowmodifytag" != "true" ] && git rev-parse $refname > /dev/null 2>&1
		then
			echo "*** Tag '$refname' already exists." >&2
			echo "*** Modifying a tag is not allowed in this repository." >&2
			exit 1
		fi
		;;
	refs/heads/*,commit)
		# branch
		if [ "$oldrev" = "$zero" -a "$denycreatebranch" = "true" ]; then
			echo "*** Creating a branch is not allowed in this repository" >&2
			exit 1
		fi
		;;
	refs/heads/*,delete)
		# delete branch
		if [ "$allowdeletebranch" != "true" ]; then
			echo "*** Deleting a branch is not allowed in this repository" >&2
			exit 1
		fi
		;;
	refs/remotes/*,commit)
		# tracking branch
		;;
	refs/remotes/*,delete)
		# delete tracking branch
		if [ "$allowdeletebranch" != "true" ]; then
			echo "*** Deleting a tracking branch is not allowed in this repository" >&2
			exit 1
		fi
		;;
	*)
		# Anything else (is there anything else?)
		echo "*** Update hook: unknown type of update to ref $refname of type $newrev_type" >&2
		exit 1
		;;
esac

# --- Finished
exit 0
#!/bin/sh
#
# An example hook script to check the commit log message.
# Called by "git commit" with one argument, the name of the file
# that has the commit message.  The hook should exit with non-zero
# status after issuing an appropriate message if it wants to stop the
# commit.  The hook is allowed to edit the commit message file.
#
# To enable this hook, rename this file to "commit-msg".

# Uncomment the below to add a Signed-off-by line to the message.
# Doing this in a hook is a bad idea in general, but the prepare-commit-msg
# hook is more suited to it.
#
# SOB=$(git var GIT_AUTHOR_IDENT | sed -n 's/^\(.*>\).*$/Signed-off-by: \1/p')
# grep -qs "^$SOB" "$1" || echo "$SOB" >> "$1"

# This example catches duplicate Signed-off-by lines.

test "" = "$(grep '^Signed-off-by: ' "$1" |
	 sort | uniq -c | sed -e '/^[ 	]*1[ 	]/d')" || {
	echo >&2 Duplicate Signed-off-by lines.
	exit 1
}
#!/bin/sh

# An example hook script to verify what is about to be pushed.  Called by "git
# push" after it has checked the remote status, but before anything has been
# pushed.  If this script exits with a non-zero status nothing will be pushed.
#
# This hook is called with the following parameters:
#
# $1 -- Name of the remote to which the push is being done
# $2 -- URL to which the push is being done
#
# If pushing without using a named remote those arguments will be equal.
#
# Information about the commits which are being pushed is supplied as lines to
# the standard input in the form:
#
#   <local ref> <local sha1> <remote ref> <remote sha1>
#
# This sample shows how to prevent push of commits where the log message starts
# with "WIP" (work in progress).

remote="$1"
url="$2"

z40=0000000000000000000000000000000000000000

while read local_ref local_sha remote_ref remote_sha
do
	if [ "$local_sha" = $z40 ]
	then
		# Handle delete
		:
	else
		if [ "$remote_sha" = $z40 ]
		then
			# New branch, examine all commits
			range="$local_sha"
		else
			# Update to existing branch, examine new commits
			range="$remote_sha..$local_sha"
		fi

		# Check for WIP commit
		commit=`git rev-list -n 1 --grep '^WIP' "$range"`
		if [ -n "$commit" ]
		then
			echo >&2 "Found WIP commit in $local_ref, not pushing"
			exit 1
		fi
	fi
done

exit 0
#!/bin/sh
#
# An example hook script to verify what is about to be committed.
# Called by "git commit" with no arguments.  The hook should
# exit with non-zero status after issuing an appropriate message if
# it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-commit".

if git rev-parse --verify HEAD >/dev/null 2>&1
then
	against=HEAD
else
	# Initial commit: diff against an empty tree object
	against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

# If you want to allow non-ASCII filenames set this variable to true.
allownonascii=$(git config --bool hooks.allownonascii)

# Redirect output to stderr.
exec 1>&2

# Cross platform projects tend to avoid non-ASCII filenames; prevent
# them from being added to the repository. We exploit the fact that the
# printable range starts at the space character and ends with tilde.
if [ "$allownonascii" != "true" ] &&
	# Note that the use of brackets around a tr range is ok here, (it's
	# even required, for portability to Solaris 10's /usr/bin/tr), since
	# the square bracket bytes happen to fall in the designated range.
	test $(git diff --cached --name-only --diff-filter=A -z $against |
	  LC_ALL=C tr -d '[ -~]\0' | wc -c) != 0
then
	cat <<\EOF
Error: Attempt to add a non-ASCII file name.

This can cause problems if you want to work with people on other platforms.

To be portable it is advisable to rename the file.

If you know what you are doing you can disable this check using:

  git config hooks.allownonascii true
EOF
	exit 1
fi

# If there are whitespace errors, print the offending file names and fail.
exec git diff-index --check --cached $against --
#!/bin/sh
#
# An example hook script to prepare the commit log message.
# Called by "git commit" with the name of the file that has the
# commit message, followed by the description of the commit
# message's source.  The hook's purpose is to edit the commit
# message file.  If the hook fails with a non-zero status,
# the commit is aborted.
#
# To enable this hook, rename this file to "prepare-commit-msg".

# This hook includes three examples.  The first comments out the
# "Conflicts:" part of a merge commit.
#
# The second includes the output of "git diff --name-status -r"
# into the message, just before the "git status" output.  It is
# commented because it doesn't cope with --amend or with squashed
# commits.
#
# The third example adds a Signed-off-by line to the message, that can
# still be edited.  This is rarely a good idea.

case "$2,$3" in
  merge,)
    /usr/bin/perl -i.bak -ne 's/^/# /, s/^# #/#/ if /^Conflicts/ .. /#/; print' "$1" ;;

# ,|template,)
#   /usr/bin/perl -i.bak -pe '
#      print "\n" . `git diff --cached --name-status -r`
#	 if /^#/ && $first++ == 0' "$1" ;;

  *) ;;
esac

# SOB=$(git var GIT_AUTHOR_IDENT | sed -n 's/^\(.*>\).*$/Signed-off-by: \1/p')
# grep -qs "^$SOB" "$1" || echo "$SOB" >> "$1"
#!/bin/sh
#
# An example hook script to make use of push options.
# The example simply echoes all push options that start with 'echoback='
# and rejects all pushes when the "reject" push option is used.
#
# To enable this hook, rename this file to "pre-receive".

if test -n "$GIT_PUSH_OPTION_COUNT"
then
	i=0
	while test "$i" -lt "$GIT_PUSH_OPTION_COUNT"
	do
		eval "value=\$GIT_PUSH_OPTION_$i"
		case "$value" in
		echoback=*)
			echo "echo from the pre-receive-hook: ${value#*=}" >&2
			;;
		reject)
			exit 1
		esac
		i=$((i + 1))
	done
fi
#!/bin/sh
#
# An example hook script to check the commit log message taken by
# applypatch from an e-mail message.
#
# The hook should exit with non-zero status after issuing an
# appropriate message if it wants to stop the commit.  The hook is
# allowed to edit the commit message file.
#
# To enable this hook, rename this file to "applypatch-msg".

. git-sh-setup
commitmsg="$(git rev-parse --git-path hooks/commit-msg)"
test -x "$commitmsg" && exec "$commitmsg" ${1+"$@"}
:
#!/bin/sh
#
# Copyright (c) 2006, 2008 Junio C Hamano
#
# The "pre-rebase" hook is run just before "git rebase" starts doing
# its job, and can prevent the command from running by exiting with
# non-zero status.
#
# The hook is called with the following parameters:
#
# $1 -- the upstream the series was forked from.
# $2 -- the branch being rebased (or empty when rebasing the current branch).
#
# This sample shows how to prevent topic branches that are already
# merged to 'next' branch from getting rebased, because allowing it
# would result in rebasing already published history.

publish=next
basebranch="$1"
if test "$#" = 2
then
	topic="refs/heads/$2"
else
	topic=`git symbolic-ref HEAD` ||
	exit 0 ;# we do not interrupt rebasing detached HEAD
fi

case "$topic" in
refs/heads/??/*)
	;;
*)
	exit 0 ;# we do not interrupt others.
	;;
esac

# Now we are dealing with a topic branch being rebased
# on top of master.  Is it OK to rebase it?

# Does the topic really exist?
git show-ref -q "$topic" || {
	echo >&2 "No such branch $topic"
	exit 1
}

# Is topic fully merged to master?
not_in_master=`git rev-list --pretty=oneline ^master "$topic"`
if test -z "$not_in_master"
then
	echo >&2 "$topic is fully merged to master; better remove it."
	exit 1 ;# we could allow it, but there is no point.
fi

# Is topic ever merged to next?  If so you should not be rebasing it.
only_next_1=`git rev-list ^master "^$topic" ${publish} | sort`
only_next_2=`git rev-list ^master           ${publish} | sort`
if test "$only_next_1" = "$only_next_2"
then
	not_in_topic=`git rev-list "^$topic" master`
	if test -z "$not_in_topic"
	then
		echo >&2 "$topic is already up-to-date with master"
		exit 1 ;# we could allow it, but there is no point.
	else
		exit 0
	fi
else
	not_in_next=`git rev-list --pretty=oneline ^${publish} "$topic"`
	/usr/bin/perl -e '
		my $topic = $ARGV[0];
		my $msg = "* $topic has commits already merged to public branch:\n";
		my (%not_in_next) = map {
			/^([0-9a-f]+) /;
			($1 => 1);
		} split(/\n/, $ARGV[1]);
		for my $elem (map {
				/^([0-9a-f]+) (.*)$/;
				[$1 => $2];
			} split(/\n/, $ARGV[2])) {
			if (!exists $not_in_next{$elem->[0]}) {
				if ($msg) {
					print STDERR $msg;
					undef $msg;
				}
				print STDERR " $elem->[1]\n";
			}
		}
	' "$topic" "$not_in_next" "$not_in_master"
	exit 1
fi

<<\DOC_END

This sample hook safeguards topic branches that have been
published from being rewound.

The workflow assumed here is:

 * Once a topic branch forks from "master", "master" is never
   merged into it again (either directly or indirectly).

 * Once a topic branch is fully cooked and merged into "master",
   it is deleted.  If you need to build on top of it to correct
   earlier mistakes, a new topic branch is created by forking at
   the tip of the "master".  This is not strictly necessary, but
   it makes it easier to keep your history simple.

 * Whenever you need to test or publish your changes to topic
   branches, merge them into "next" branch.

The script, being an example, hardcodes the publish branch name
to be "next", but it is trivial to make it configurable via
$GIT_DIR/config mechanism.

With this workflow, you would want to know:

(1) ... if a topic branch has ever been merged to "next".  Young
    topic branches can have stupid mistakes you would rather
    clean up before publishing, and things that have not been
    merged into other branches can be easily rebased without
    affecting other people.  But once it is published, you would
    not want to rewind it.

(2) ... if a topic branch has been fully merged to "master".
    Then you can delete it.  More importantly, you should not
    build on top of it -- other people may already want to
    change things related to the topic as patches against your
    "master", so if you need further changes, it is better to
    fork the topic (perhaps with the same name) afresh from the
    tip of "master".

Let's look at this example:

		   o---o---o---o---o---o---o---o---o---o "next"
		  /       /           /           /
		 /   a---a---b A     /           /
		/   /               /           /
	       /   /   c---c---c---c B         /
	      /   /   /             \         /
	     /   /   /   b---b C     \       /
	    /   /   /   /             \     /
    ---o---o---o---o---o---o---o---o---o---o---o "master"


A, B and C are topic branches.

 * A has one fix since it was merged up to "next".

 * B has finished.  It has been fully merged up to "master" and "next",
   and is ready to be deleted.

 * C has not merged to "next" at all.

We would want to allow C to be rebased, refuse A, and encourage
B to be deleted.

To compute (1):

	git rev-list ^master ^topic next
	git rev-list ^master        next

	if these match, topic has not merged in next at all.

To compute (2):

	git rev-list master..topic

	if this is empty, it is fully merged to "master".

DOC_END
#!/bin/sh
#
# An example hook script to verify what is about to be committed
# by applypatch from an e-mail message.
#
# The hook should exit with non-zero status after issuing an
# appropriate message if it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-applypatch".

. git-sh-setup
precommit="$(git rev-parse --git-path hooks/pre-commit)"
test -x "$precommit" && exec "$precommit" ${1+"$@"}
:
#!/bin/sh
#
# An example hook script to prepare a packed repository for use over
# dumb transports.
#
# To enable this hook, rename this file to "post-update".

exec git update-server-info
ref: refs/heads/master
# git ls-files --others --exclude-from=.git/info/exclude
# Lines that start with '#' are comments.
# For a project mostly in C, the following would be a good set of
# exclude patterns (uncomment them if you want to use them):
# *.[oa]
# *~
ó
$ıú[c           @   só  d  Z  d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l	 Z	 d d l
 Z
 d d l m Z y d d l m Z Wn e k
 r» d Z n Xd Z d Z d „  Z d d „ Z d	 „  Z d
 „  Z e
 j d „  ƒ Z d „  Z e e e j d d „ Z d „  Z d „  Z d „  Z e e _ d „  Z  d „  Z! e! e  _ d „  Z" d „  Z# e# e" _ d „  Z$ d „  e$ _ d „  Z% e e e j d e% d „ Z& d „  Z' d „  Z( d „  Z) e* d k rïe j+ e) ƒ  ƒ n  d S(   s×  Bootstrap setuptools installation

To use setuptools in your package's setup.py, include this
file in the same directory and add this to the top of your setup.py::

    from ez_setup import use_setuptools
    use_setuptools()

To require a specific version of setuptools, set a download
mirror, or use an alternate download directory, simply supply
the appropriate options to ``use_setuptools()``.

This file can also be run as a script to install or upgrade setuptools.
iÿÿÿÿN(   t   log(   t	   USER_SITEs   3.5.1s5   https://pypi.python.org/packages/source/s/setuptools/c          G   s#   t  j f |  }  t j |  ƒ d k S(   s/   
    Return True if the command succeeded.
    i    (   t   syst
   executablet
   subprocesst   call(   t   args(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _python_cmd%   s    c         C   sT   t  |  ƒ B t j d ƒ t d d | Œ sJ t j d ƒ t j d ƒ d SWd  QXd  S(   Ns   Installing Setuptoolss   setup.pyt   installs-   Something went wrong during the installation.s   See the error message above.i   (   t   archive_contextR    t   warnR   (   t   archive_filenamet   install_args(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _install-   s    c      
   C   sk   t  | ƒ + t j d | ƒ t d d d d | ƒ Wd  QXt j |  ƒ t j j |  ƒ sg t d ƒ ‚ n  d  S(   Ns   Building a Setuptools egg in %ss   setup.pys   -qt	   bdist_eggs
   --dist-dirs   Could not build the egg.(   R	   R    R
   R   t   ost   patht   existst   IOError(   t   eggR   t   to_dir(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt
   _build_egg8   s    c          C   s6   d t  j f d „  ƒ  Y}  t t  j d ƒ r2 t  j S|  S(   sL   
    Supplement ZipFile class to support context manager for Python 2.6
    t   ContextualZipFilec           B   s   e  Z d  „  Z d „  Z RS(   c         S   s   |  S(   N(    (   t   self(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt	   __enter__H   s    c         S   s   |  j  d  S(   N(   t   close(   R   t   typet   valuet	   traceback(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   __exit__J   s    (   t   __name__t
   __module__R   R   (    (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyR   G   s   	R   (   t   zipfilet   ZipFilet   hasattr(   R   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   get_zip_classC   s    c         c   sÁ   t  j ƒ  } t j d | ƒ t j ƒ  } zw t j | ƒ t ƒ  |  ƒ  } | j ƒ  Wd  QXt j	 j
 | t j | ƒ d ƒ } t j | ƒ t j d | ƒ d  VWd  t j | ƒ t j | ƒ Xd  S(   Ns   Extracting in %si    s   Now working in %s(   t   tempfilet   mkdtempR    R
   R   t   getcwdt   chdirR#   t
   extractallR   t   joint   listdirt   shutilt   rmtree(   t   filenamet   tmpdirt   old_wdt   archivet   subdir(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyR	   P   s    "	c         C   s²   t  j j | d |  t j d t j d f ƒ } t  j j | ƒ sj t |  | | | ƒ } t | | | ƒ n  t j j d | ƒ d t j	 k r™ t j	 d =n  d d  l
 } | | _ d  S(   Ns   setuptools-%s-py%d.%d.eggi    i   t   pkg_resourcesiÿÿÿÿ(   R   R   R)   R   t   version_infoR   t   download_setuptoolsR   t   insertt   modulest
   setuptoolst   bootstrap_install_from(   t   versiont   download_baseR   t   download_delayR   R0   R7   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _do_downloadf   s    !	i   c   	      C   s!  t  j j | ƒ } d	 } t t j ƒ j | ƒ } y d d  l } Wn! t k
 rc t	 |  | | | ƒ SXy | j
 d |  ƒ d  SWn | j k
 r£ t	 |  | | | ƒ S| j k
 r} | rü t j d ƒ j d | d |  ƒ } t j j | ƒ t j d ƒ n  ~ t j d =t	 |  | | | ƒ SXd  S(
   NR2   R7   iÿÿÿÿs   setuptools>=sO  
                The required version of setuptools (>={version}) is not available,
                and can't be installed while this script is running. Please
                install a more recent version first, using
                'easy_install -U setuptools'.

                (Currently using {VC_err.args[0]!r})
                t   VC_errR9   i   (   R2   R7   (   R   R   t   abspatht   setR   R6   t   intersectionR2   t   ImportErrorR<   t   requiret   DistributionNotFoundt   VersionConflictt   textwrapt   dedentt   formatt   stderrt   writet   exit(	   R9   R:   R   R;   t   rep_modulest   importedR2   R=   t   msg(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   use_setuptoolsx   s(    c         C   sT   y t  j |  ƒ Wn< t  j k
 rO t j | t j ƒ rI t j | ƒ n  ‚  n Xd S(   sm   
    Run the command to download target. If the command fails, clean up before
    re-raising the error.
    N(   R   t
   check_callt   CalledProcessErrorR   t   accesst   F_OKt   unlink(   t   cmdt   target(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _clean_check—   s    c         C   s9   t  j j | ƒ } d d d t ƒ  g } t | | ƒ d S(   s‘   
    Download the file at url to target using Powershell (which will validate
    trust). Raise an exception if the command cannot complete.
    t
   powershells   -CommandsC   (new-object System.Net.WebClient).DownloadFile(%(url)r, %(target)r)N(   R   R   R>   t   varsRV   (   t   urlRU   RT   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   download_file_powershell£   s
    c          C   s‚   t  j ƒ  d k r t Sd d d g }  t t j j d ƒ } z6 y t j |  d | d | ƒWn t	 k
 rn t SXWd  | j
 ƒ  Xt S(   Nt   WindowsRW   s   -Commands	   echo testt   wbt   stdoutRH   (   t   platformt   systemt   Falset   openR   R   t   devnullR   RO   t	   ExceptionR   t   True(   RT   Rb   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   has_powershell°   s    	c         C   s&   d |  d d | g } t  | | ƒ d  S(   Nt   curls   --silents   --output(   RV   (   RY   RU   RT   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   download_file_curlÀ   s    c          C   si   d d g }  t  t j j d ƒ } z6 y t j |  d | d | ƒWn t k
 rU t SXWd  | j ƒ  Xt	 S(   NRf   s	   --versionR\   R]   RH   (
   Ra   R   R   Rb   R   RO   Rc   R`   R   Rd   (   RT   Rb   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   has_curlÄ   s    	c         C   s&   d |  d d | g } t  | | ƒ d  S(   Nt   wgets   --quiets   --output-document(   RV   (   RY   RU   RT   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   download_file_wgetÒ   s    c          C   si   d d g }  t  t j j d ƒ } z6 y t j |  d | d | ƒWn t k
 rU t SXWd  | j ƒ  Xt	 S(   NRi   s	   --versionR\   R]   RH   (
   Ra   R   R   Rb   R   RO   Rc   R`   R   Rd   (   RT   Rb   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   has_wgetÖ   s    	c         C   s¨   y d d l  m } Wn! t k
 r7 d d l m } n Xd } } z8 | |  ƒ } | j ƒ  } t | d ƒ } | j | ƒ Wd | r | j ƒ  n  | r£ | j ƒ  n  Xd S(   sa   
    Use Python to download the file, even though it cannot authenticate the
    connection.
    iÿÿÿÿ(   t   urlopenR\   N(	   t   urllib.requestRl   RA   t   urllib2t   Nonet   readRa   RI   R   (   RY   RU   Rl   t   srct   dstt   data(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   download_file_insecureä   s    
c           C   s   t  S(   N(   Rd   (    (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   <lambda>û   s    c          C   s7   t  t t t g }  x |  D] } | j ƒ  r | Sq Wd  S(   N(   RZ   Rg   Rj   Rt   t   viable(   t   downloaderst   dl(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   get_best_downloaderı   s    	c   	      C   s†   t  j j | ƒ } d |  } | | } t  j j | | ƒ } t  j j | ƒ sv t j d | ƒ | ƒ  } | | | ƒ n  t  j j | ƒ S(   s  
    Download setuptools from a specified location and return its filename

    `version` should be a valid setuptools version number that is available
    as an egg for download under the `download_base` URL (which should end
    with a '/'). `to_dir` is the directory where the egg will be downloaded.
    `delay` is the number of seconds to pause before an actual download
    attempt.

    ``downloader_factory`` should be a function taking no arguments and
    returning a function for downloading a URL to a target.
    s   setuptools-%s.zips   Downloading %s(   R   R   R>   R)   R   R    R
   t   realpath(	   R9   R:   R   t   delayt   downloader_factoryt   zip_nameRY   t   savetot
   downloader(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyR4   	  s    

	c         C   s   |  j  r d g Sg  S(   sT   
    Build the arguments to 'python setup.py install' on the setuptools package
    s   --user(   t   user_install(   t   options(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _build_install_args"  s    c          C   s³   t  j ƒ  }  |  j d d d d d d t d d ƒ|  j d	 d d
 d d d t d d ƒ|  j d d d d d d d „  d t d d ƒ|  j d d d d t ƒ|  j ƒ  \ } } | S(   s,   
    Parse the command line for options
    s   --usert   destR€   t   actiont
   store_truet   defaultt   helps;   install in user site package (requires Python 2.6 or later)s   --download-baseR:   t   metavart   URLs=   alternative URL from where to download the setuptools packages
   --insecureR|   t   store_constt   constc           S   s   t  S(   N(   Rt   (    (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyRu   6  s    s'   Use internal, non-validating downloaders	   --versions!   Specify which version to download(   t   optparset   OptionParsert
   add_optionR`   t   DEFAULT_URLRy   t   DEFAULT_VERSIONt
   parse_args(   t   parserR   R   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _parse_args(  s"    c          C   s@   t  ƒ  }  t d |  j d |  j d |  j ƒ } t | t |  ƒ ƒ S(   s-   Install or upgrade setuptools and EasyInstallR9   R:   R|   (   R“   R4   R9   R:   R|   R   R‚   (   R   R0   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   mainA  s    			t   __main__(    (,   t   __doc__R   R+   R   R$   R    RŒ   R   R^   RE   t
   contextlibt	   distutilsR    t   siteR   RA   Ro   R   R   R   R   R   R#   t   contextmanagerR	   R<   t   curdirRN   RV   RZ   Re   Rv   Rg   Rh   Rj   Rk   Rt   Ry   R4   R‚   R“   R”   R   RJ   (    (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   <module>   sZ   
																			
Metadata-Version: 1.1
Name: Adafruit-PureIO
Version: 0.2.3
Summary: Pure python (i.e. no native extensions) access to Linux IO including I2C and SPI.  Drop in replacement for smbus and spidev modules.
Home-page: https://github.com/adafruit/Adafruit_Python_PureIO
Author: Tony DiCola / Adafruit Industries
Author-email: support@adafruit.com
License: MIT
Description: UNKNOWN
Platform: UNKNOWN
Classifier: Development Status :: 4 - Beta
Classifier: Operating System :: POSIX :: Linux
Classifier: License :: OSI Approved :: MIT License
Classifier: Intended Audience :: Developers
Classifier: Programming Language :: Python :: 2.7
Classifier: Programming Language :: Python :: 3
Classifier: Topic :: Software Development
Classifier: Topic :: System :: Hardware
Adafruit_PureIO
setup.py
Adafruit_PureIO/__init__.py
Adafruit_PureIO/smbus.py
Adafruit_PureIO.egg-info/PKG-INFO
Adafruit_PureIO.egg-info/SOURCES.txt
Adafruit_PureIO.egg-info/dependency_links.txt
Adafruit_PureIO.egg-info/top_level.txt
setuptools-*
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*,cover
.hypothesis/

# Translations
*.mo
*.pot

# Django stuff:
*.log

# Sphinx documentation
docs/_build/

# PyBuilder
target/

#Ipython Notebook
.ipynb_checkpoints
# Adafruit Python PureIO

Pure python (i.e. no native extensions) access to Linux IO including I2C and SPI.  
Drop in replacement for smbus and spidev modules.

NOTE: This is a work in progress that's not yet ready for public consumption.
API signatures could change and all APIs are not yet implemented.  Wait for a
1.x.x series release before depending on this code.
try:
    # Try using ez_setup to install setuptools if not already installed.
    from ez_setup import use_setuptools
    use_setuptools()
except ImportError:
    # Ignore import error and assume Python 3 which already has setuptools.
    pass

from setuptools import setup, find_packages

classifiers = ['Development Status :: 4 - Beta',
               'Operating System :: POSIX :: Linux',
               'License :: OSI Approved :: MIT License',
               'Intended Audience :: Developers',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 3',
               'Topic :: Software Development',
               'Topic :: System :: Hardware']

setup(name              = 'Adafruit_PureIO',
      version           = '0.2.3',
	  url               = 'https://github.com/adafruit/Adafruit_Python_PureIO',
      author            = 'Tony DiCola / Adafruit Industries',
      author_email      = 'support@adafruit.com',
      description       = 'Pure python (i.e. no native extensions) access to Linux IO including I2C and SPI.  Drop in replacement for smbus and spidev modules.',
      license           = 'MIT',
      classifiers       = classifiers,
      packages          = find_packages())
# Basic smbus test.  This is pretty ugly and meant to be run against a ADS1x15
# and some output inspected by a Saleae logic analyzer.  TODO: Refactor into
# something that can test without hardware?
import binascii

import Adafruit_PureIO.smbus as smbus


DEVICE_ADDR = 0x48
REGISTER    = 0x01


# Test open and close.
i2c = smbus.SMBus()
i2c.open(1)
val = i2c.read_byte(DEVICE_ADDR)
print('read_byte from 0x{0:0X}: 0x{1:0X}'.format(REGISTER, val))
i2c.close()

# Test initializer open.
i2c = smbus.SMBus(1)
val = i2c.read_byte(DEVICE_ADDR)
print('read_byte from 0x{0:0X}: 0x{1:0X}'.format(REGISTER, val))
i2c.close()

# Test various data reads.
with smbus.SMBus(1) as i2c:
    val = i2c.read_byte(DEVICE_ADDR)
    print('read_byte from 0x{0:0X}: 0x{1:0X}'.format(REGISTER, val))
    val = i2c.read_byte_data(DEVICE_ADDR, REGISTER)
    print('read_byte_data from 0x{0:0X}: 0x{1:0X}'.format(REGISTER, val))
    val = i2c.read_word_data(DEVICE_ADDR, REGISTER)
    print('read_word_data from 0x{0:0X}: 0x{1:04X}'.format(REGISTER, val))
    val = i2c.read_i2c_block_data(DEVICE_ADDR, REGISTER, 2)
    print('read_i2c_block_data from 0x{0:0X}: 0x{1}'.format(REGISTER, binascii.hexlify(val)))

# Test various data writes.
with smbus.SMBus(1) as i2c:
    i2c.write_byte(DEVICE_ADDR, REGISTER)
    i2c.write_byte_data(DEVICE_ADDR, REGISTER, 0x85)
    i2c.write_word_data(DEVICE_ADDR, REGISTER, 0x8385)
    i2c.write_i2c_block_data(DEVICE_ADDR, REGISTER, [0x85, 0x83])
    #i2c.write_block_data(DEVICE_ADDR, REGISTER, [0x85, 0x83])
    i2c.write_quick(DEVICE_ADDR)

# Process call test.
with smbus.SMBus(1) as i2c:
    val = i2c.process_call(DEVICE_ADDR, REGISTER, 0x8385)
    print('process_call from 0x{0:0X}: 0x{1:04X}'.format(REGISTER, val))
Metadata-Version: 1.1
Name: Adafruit-CharLCD
Version: 1.1.1
Summary: Library to drive character LCD display and plate.
Home-page: https://github.com/adafruit/Adafruit_Python_CharLCD/
Author: Tony DiCola
Author-email: tdicola@adafruit.com
License: MIT
Description: UNKNOWN
Platform: UNKNOWN
Classifier: Development Status :: 4 - Beta
Classifier: Operating System :: POSIX :: Linux
Classifier: License :: OSI Approved :: MIT License
Classifier: Intended Audience :: Developers
Classifier: Programming Language :: Python :: 2.7
Classifier: Programming Language :: Python :: 3
Classifier: Topic :: Software Development
Classifier: Topic :: System :: Hardware
Adafruit_CharLCD
setup.py
Adafruit_CharLCD/Adafruit_CharLCD.py
Adafruit_CharLCD/__init__.py
Adafruit_CharLCD.egg-info/PKG-INFO
Adafruit_CharLCD.egg-info/SOURCES.txt
Adafruit_CharLCD.egg-info/dependency_links.txt
Adafruit_CharLCD.egg-info/requires.txt
Adafruit_CharLCD.egg-info/top_level.txthttps://github.com/adafruit/Adafruit_Python_GPIO/tarball/master#egg=Adafruit-GPIO-0.4.0
Adafruit-GPIO>=0.4.0
The MIT License (MIT)

Copyright (c) 2014 Adafruit Industries

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.#Libraries
import RPi.GPIO as GPIO
import time
import Adafruit_CharLCD as LCD
 
#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
 
#set GPIO Pins
GPIO_TRIGGER = 27
GPIO_ECHO = 12

# Raspberry Pi pin setup for LCD
lcd_rs = 25
lcd_en = 24
lcd_d4 = 23
lcd_d5 = 17
lcd_d6 = 18
lcd_d7 = 22
lcd_backlight = 2

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows = 2
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

#set LCD
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance
 
if __name__ == '__main__':
    try:
        while True:
            dist = distance()
            print ("Measured Distance = %.1f cm" % dist)
            lcd.message('%.1f cm' % dist)
            time.sleep(1)
            lcd.clear()
 
        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
#!/usr/bin/env python
"""Bootstrap setuptools installation

To use setuptools in your package's setup.py, include this
file in the same directory and add this to the top of your setup.py::

    from ez_setup import use_setuptools
    use_setuptools()

To require a specific version of setuptools, set a download
mirror, or use an alternate download directory, simply supply
the appropriate options to ``use_setuptools()``.

This file can also be run as a script to install or upgrade setuptools.
"""
import os
import shutil
import sys
import tempfile
import zipfile
import optparse
import subprocess
import platform
import textwrap
import contextlib

from distutils import log

try:
    from site import USER_SITE
except ImportError:
    USER_SITE = None

DEFAULT_VERSION = "3.5.1"
DEFAULT_URL = "https://pypi.python.org/packages/source/s/setuptools/"

def _python_cmd(*args):
    """
    Return True if the command succeeded.
    """
    args = (sys.executable,) + args
    return subprocess.call(args) == 0


def _install(archive_filename, install_args=()):
    with archive_context(archive_filename):
        # installing
        log.warn('Installing Setuptools')
        if not _python_cmd('setup.py', 'install', *install_args):
            log.warn('Something went wrong during the installation.')
            log.warn('See the error message above.')
            # exitcode will be 2
            return 2


def _build_egg(egg, archive_filename, to_dir):
    with archive_context(archive_filename):
        # building an egg
        log.warn('Building a Setuptools egg in %s', to_dir)
        _python_cmd('setup.py', '-q', 'bdist_egg', '--dist-dir', to_dir)
    # returning the result
    log.warn(egg)
    if not os.path.exists(egg):
        raise IOError('Could not build the egg.')


def get_zip_class():
    """
    Supplement ZipFile class to support context manager for Python 2.6
    """
    class ContextualZipFile(zipfile.ZipFile):
        def __enter__(self):
            return self
        def __exit__(self, type, value, traceback):
            self.close
    return zipfile.ZipFile if hasattr(zipfile.ZipFile, '__exit__') else \
        ContextualZipFile


@contextlib.contextmanager
def archive_context(filename):
    # extracting the archive
    tmpdir = tempfile.mkdtemp()
    log.warn('Extracting in %s', tmpdir)
    old_wd = os.getcwd()
    try:
        os.chdir(tmpdir)
        with get_zip_class()(filename) as archive:
            archive.extractall()

        # going in the directory
        subdir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        os.chdir(subdir)
        log.warn('Now working in %s', subdir)
        yield

    finally:
        os.chdir(old_wd)
        shutil.rmtree(tmpdir)


def _do_download(version, download_base, to_dir, download_delay):
    egg = os.path.join(to_dir, 'setuptools-%s-py%d.%d.egg'
                       % (version, sys.version_info[0], sys.version_info[1]))
    if not os.path.exists(egg):
        archive = download_setuptools(version, download_base,
                                      to_dir, download_delay)
        _build_egg(egg, archive, to_dir)
    sys.path.insert(0, egg)

    # Remove previously-imported pkg_resources if present (see
    # https://bitbucket.org/pypa/setuptools/pull-request/7/ for details).
    if 'pkg_resources' in sys.modules:
        del sys.modules['pkg_resources']

    import setuptools
    setuptools.bootstrap_install_from = egg


def use_setuptools(version=DEFAULT_VERSION, download_base=DEFAULT_URL,
        to_dir=os.curdir, download_delay=15):
    to_dir = os.path.abspath(to_dir)
    rep_modules = 'pkg_resources', 'setuptools'
    imported = set(sys.modules).intersection(rep_modules)
    try:
        import pkg_resources
    except ImportError:
        return _do_download(version, download_base, to_dir, download_delay)
    try:
        pkg_resources.require("setuptools>=" + version)
        return
    except pkg_resources.DistributionNotFound:
        return _do_download(version, download_base, to_dir, download_delay)
    except pkg_resources.VersionConflict as VC_err:
        if imported:
            msg = textwrap.dedent("""
                The required version of setuptools (>={version}) is not available,
                and can't be installed while this script is running. Please
                install a more recent version first, using
                'easy_install -U setuptools'.

                (Currently using {VC_err.args[0]!r})
                """).format(VC_err=VC_err, version=version)
            sys.stderr.write(msg)
            sys.exit(2)

        # otherwise, reload ok
        del pkg_resources, sys.modules['pkg_resources']
        return _do_download(version, download_base, to_dir, download_delay)

def _clean_check(cmd, target):
    """
    Run the command to download target. If the command fails, clean up before
    re-raising the error.
    """
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        if os.access(target, os.F_OK):
            os.unlink(target)
        raise

def download_file_powershell(url, target):
    """
    Download the file at url to target using Powershell (which will validate
    trust). Raise an exception if the command cannot complete.
    """
    target = os.path.abspath(target)
    cmd = [
        'powershell',
        '-Command',
        "(new-object System.Net.WebClient).DownloadFile(%(url)r, %(target)r)" % vars(),
    ]
    _clean_check(cmd, target)

def has_powershell():
    if platform.system() != 'Windows':
        return False
    cmd = ['powershell', '-Command', 'echo test']
    devnull = open(os.path.devnull, 'wb')
    try:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except Exception:
            return False
    finally:
        devnull.close()
    return True

download_file_powershell.viable = has_powershell

def download_file_curl(url, target):
    cmd = ['curl', url, '--silent', '--output', target]
    _clean_check(cmd, target)

def has_curl():
    cmd = ['curl', '--version']
    devnull = open(os.path.devnull, 'wb')
    try:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except Exception:
            return False
    finally:
        devnull.close()
    return True

download_file_curl.viable = has_curl

def download_file_wget(url, target):
    cmd = ['wget', url, '--quiet', '--output-document', target]
    _clean_check(cmd, target)

def has_wget():
    cmd = ['wget', '--version']
    devnull = open(os.path.devnull, 'wb')
    try:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except Exception:
            return False
    finally:
        devnull.close()
    return True

download_file_wget.viable = has_wget

def download_file_insecure(url, target):
    """
    Use Python to download the file, even though it cannot authenticate the
    connection.
    """
    try:
        from urllib.request import urlopen
    except ImportError:
        from urllib2 import urlopen
    src = dst = None
    try:
        src = urlopen(url)
        # Read/write all in one block, so we don't create a corrupt file
        # if the download is interrupted.
        data = src.read()
        dst = open(target, "wb")
        dst.write(data)
    finally:
        if src:
            src.close()
        if dst:
            dst.close()

download_file_insecure.viable = lambda: True

def get_best_downloader():
    downloaders = [
        download_file_powershell,
        download_file_curl,
        download_file_wget,
        download_file_insecure,
    ]

    for dl in downloaders:
        if dl.viable():
            return dl

def download_setuptools(version=DEFAULT_VERSION, download_base=DEFAULT_URL,
        to_dir=os.curdir, delay=15, downloader_factory=get_best_downloader):
    """
    Download setuptools from a specified location and return its filename

    `version` should be a valid setuptools version number that is available
    as an egg for download under the `download_base` URL (which should end
    with a '/'). `to_dir` is the directory where the egg will be downloaded.
    `delay` is the number of seconds to pause before an actual download
    attempt.

    ``downloader_factory`` should be a function taking no arguments and
    returning a function for downloading a URL to a target.
    """
    # making sure we use the absolute path
    to_dir = os.path.abspath(to_dir)
    zip_name = "setuptools-%s.zip" % version
    url = download_base + zip_name
    saveto = os.path.join(to_dir, zip_name)
    if not os.path.exists(saveto):  # Avoid repeated downloads
        log.warn("Downloading %s", url)
        downloader = downloader_factory()
        downloader(url, saveto)
    return os.path.realpath(saveto)

def _build_install_args(options):
    """
    Build the arguments to 'python setup.py install' on the setuptools package
    """
    return ['--user'] if options.user_install else []

def _parse_args():
    """
    Parse the command line for options
    """
    parser = optparse.OptionParser()
    parser.add_option(
        '--user', dest='user_install', action='store_true', default=False,
        help='install in user site package (requires Python 2.6 or later)')
    parser.add_option(
        '--download-base', dest='download_base', metavar="URL",
        default=DEFAULT_URL,
        help='alternative URL from where to download the setuptools package')
    parser.add_option(
        '--insecure', dest='downloader_factory', action='store_const',
        const=lambda: download_file_insecure, default=get_best_downloader,
        help='Use internal, non-validating downloader'
    )
    parser.add_option(
        '--version', help="Specify which version to download",
        default=DEFAULT_VERSION,
    )
    options, args = parser.parse_args()
    # positional arguments are ignored
    return options

def main():
    """Install or upgrade setuptools and EasyInstall"""
    options = _parse_args()
    archive = download_setuptools(
        version=options.version,
        download_base=options.download_base,
        downloader_factory=options.downloader_factory,
    )
    return _install(archive, _build_install_args(options))

if __name__ == '__main__':
    sys.exit(main())
Thank you for opening an issue on an Adafruit Python library repository.  To
improve the speed of resolution please review the following guidelines and
common troubleshooting steps below before creating the issue:

- **Do not use GitHub issues for troubleshooting projects and issues.**  Instead use
  the forums at http://forums.adafruit.com to ask questions and troubleshoot why
  something isn't working as expected.  In many cases the problem is a common issue
  that you will more quickly receive help from the forum community.  GitHub issues
  are meant for known defects in the code.  If you don't know if there is a defect
  in the code then start with troubleshooting on the forum first.

- **If following a tutorial or guide be sure you didn't miss a step.** Carefully
  check all of the steps and commands to run have been followed.  Consult the
  forum if you're unsure or have questions about steps in a guide/tutorial.

- **For Python/Raspberry Pi projects check these very common issues to ensure they don't apply**:

  - If you are receiving an **ImportError: No module named...** error then a
    library the code depends on is not installed.  Check the tutorial/guide or
    README to ensure you have installed the necessary libraries.  Usually the
    missing library can be installed with the `pip` tool, but check the tutorial/guide
    for the exact command.  

  - **Be sure you are supplying adequate power to the board.**  Check the specs of
    your board and power in an external power supply.  In many cases just
    plugging a board into your computer is not enough to power it and other
    peripherals.

  - **Double check all soldering joints and connections.**  Flakey connections
    cause many mysterious problems.  See the [guide to excellent soldering](https://learn.adafruit.com/adafruit-guide-excellent-soldering/tools) for examples of good solder joints.

If you're sure this issue is a defect in the code and checked the steps above
please fill in the following fields to provide enough troubleshooting information.
You may delete the guideline and text above to just leave the following details:

- Platform/operating system (i.e. Raspberry Pi with Raspbian operating system,
  Windows 32-bit, Windows 64-bit, Mac OSX 64-bit, etc.):  **INSERT PLATFORM/OPERATING
  SYSTEM HERE**

- Python version (run `python -version` or `python3 -version`):  **INSERT PYTHON
  VERSION HERE**

- Error message you are receiving, including any Python exception traces:  **INSERT
  ERROR MESAGE/EXCEPTION TRACES HERE***

- List the steps to reproduce the problem below (if possible attach code or commands
  to run): **LIST REPRO STEPS BELOW**
Thank you for creating a pull request to contribute to Adafruit's GitHub code!
Before you open the request please review the following guidelines and tips to
help it be more easily integrated:

- **Describe the scope of your change--i.e. what the change does and what parts
  of the code were modified.**  This will help us understand any risks of integrating
  the code.

- **Describe any known limitations with your change.**  For example if the change
  doesn't apply to a supported platform of the library please mention it.

- **Please run any tests or examples that can exercise your modified code.**  We
  strive to not break users of the code and running tests/examples helps with this
  process.

Thank you again for contributing!  We will try to test and integrate the change
as soon as we can, but be aware we have many GitHub repositories to manage and
can't immediately respond to every request.  There is no need to bump or check in
on a pull request (it will clutter the discussion of the request).

Also don't be worried if the request is closed or not integrated--sometimes the
priorities of Adafruit's GitHub code (education, ease of use) might not match the
priorities of the pull request.  Don't fret, the open source community thrives on
forks and GitHub makes it easy to keep your changes in a forked repo.

After reviewing the guidelines above you can delete this text from the pull request.
PK    2¡yM®i_       EGG-INFO/PKG-INFO•‘ËÛ0E÷ş
ş€cL;À ^5MÔ“púØ8ã°è´şûRÓ]tG‘çŠWW/$hP°üF1±w5<¬Š=ZªamğG–rsÁØl¶Å{F©v´ãTCÃoQ&ò• SvBT†Spt´ZÏŞR°×-‘êªêY.ãÛªó¶Âyquwğzœäâİël¤*Ö£c'ï&ØòÆ8÷J²ÈCb¸Óî§û]ùâ¢á\Ò¥/»S±¥ÔEr{Ñ×ı—ıáû¾8ª¿³öog3`J|fÒu[ºÒàƒ%'Ğ
Ê˜ ®áJø¬9.ĞC ˆÂ®‡vJB6ƒÇC»û‘‹†İøkÏÎòP!X‡ı•L>«×ûx!Ù9!g”Y†Éu7ñìP?jÁ£ï#Z›ı4èúQ£¿9ºåš««§ÿT|\ğ'¸ËíÖŸå'FzÖ?È?Á<c4YSüPK    3¡yM“×2         EGG-INFO/zip-safeã PK    2¡yM’çæ         EGG-INFO/top_level.txtsLIL+*Í,‰wÎH,òqvá PK    2¡yM[5”Øq        EGG-INFO/SOURCES.txt+N-)-Ğ+¨ärLIL+*Í,‰wÎH,òqvÑGÀª(>>3ÈÇ&©—š®›™—–¯àí®ëéçæGI°h³k°^IE	U)©©y)©yÉ•ñ9™yÙÅ”¥–f¥RV’_Ÿ“Z–šR PK    2¡yM<u²L   X      EGG-INFO/dependency_links.txtË())(¶Ò×OÏ,É(MÒKÎÏÕOLIL+*Í,Ñw„2â*K2òóâİ<ıõK‹’srôs‹KR‹”SÓÓmaêtA
tôLô¸ PK    2¡yMğ Õ6         EGG-INFO/requires.txtsLIL+*Í,Ñuğô·³5Ğ3Ñ3à PK    3¡yM&TqİŠ   ¿      Adafruit_CharLCD/__init__.pyccşÌËõöô¯èd(`b .æ)@ÄÈÃÀ’ÂÄ¬ÁÊd ¢DhùAØ@Â1%1­¨4³$Ş9#±ÈÇÙEd‚(¶I¥™9)úI)™Å%z9™y¥º‰E¹ef9ú©ééúèèÇÇgæ¹ñz•%@İ6¹ù)¥9©v +‹Af PK     ‚yM` ãù"          Adafruit_CharLCD/__init__.pyK+ÊÏUĞsLIL+*Í,‰wÎH,òqvQÈÌ-È/*QĞâ PK     ‚yMt¿|?  QQ  $   Adafruit_CharLCD/Adafruit_CharLCD.pyí<ks;²ßı+t“ªÜC&àøuS‡S…ÇÔÁà||S»[Ô ÂÌafv!Şã½¿ıv·4I3ø•|Ø‡J¨¥V«»Õên5ó–uÃè>öî6)«-ëì°Ù:b•»3/eƒ`•%iìñäà-ëdé&Œ?±YÜ³×}÷à-´_óxë%‰ÌKØ†Ç|qÏîb7HùªÁÖ1ç,\³åÆïxƒ¥!sa|Äã„‹Ôõ/¸c.[!€ú¦@”„ëtçÆº¯˜›$áÒs#[…ËlËƒÔMqÆµçó„ÕÒgo¦rÄ›:M³â®ø¼€!4²ËÈRs\Ù±4 ÓÒÏVHGö½­'çÀáÄ!ä ÎXRÛ`Ûpå­ñÓâ¢lá{É¦ÁV"_d)4&Ø¸ä‚µ|c–pIÀZ±â‚Bê…óDÈØT²*Á–İ&Üš«ñ¦u0-§Q«XG³şƒ/SlÁëĞ÷Ã.p+×•|"ñÍ ê.Â¯œ–$4!S XĞ²ˆ
KP²q}Ÿ-¸äLí€óUÅHC’‚x®Ï¢0¦IíÕ:‚ˆË>›/f·IŸ¦ìz2şmĞë÷Ø›Î¾¿i°ÛÁìr|3cĞcÒÍ¾°ñëŒ¾°_£^ƒõÿ÷zÒŸNÙxÈW×ÃAZ£îğ¦7}fç0r4±áàj0´³1M)‘úSDwÕŸt/ákç|0Ì¾4 ÕÅ`6B¼ã	ë°ëÎd6èŞ;v}3¹Oû@B£‹	ÌÓ¿êfÌm¬ÿ|aÓËÎpˆ“áº5LJÖ_™>_ÎØåxØëCãy¨ëœûb2XZwØ\5X¯sÕùÜ§QcÀƒ+Ä‚Fv{ÙÇFœ³ÿº³Áx„‹éG³	|mÀZ'35øv0í7Xg2˜"[.&ã+\&2ÆŒ	Œõdº)è‚ßo¦}…’õú!`A,Q:ŞÏRoËò/¹y™¾Œak3|¯:ƒÃ.v€·jøU÷úğcóÛ7ìŸ«;]ß^!Ş€Àn¸İ‚f'ÃnoŞö;“Ş`z=ì|aòÕfÍoÍ'ıÙÍdt9¾ê3f€	|¹÷úÓşÌ Xâ%QŒ‡øLÌ}3™‚:\.fòV“À7#’‚†›À‡ÍİÏĞ^o¢ƒ eğYyĞÒø­}÷.)"ôÑ\g³ ûe6Ğ:`ÇMhèL,À½¾n
q -¡¯#ÙúgÍfpu|qQI«àª1X§U‚õÁúèsĞä_ÍÁúRØ¬-å
­hiWãßúfg]üT§–Dt. Ø’ˆFÉEĞÉ'MªQtv>˜¡ºÚƒ¤ÆíKŠañÌ\OkXŒ>†YzãÙ´>’à3ª­g¼^ÓJàPÉ"<ÓXîGlÒñíd?Õ†Öplƒ6şmáßã£:é8#†²ÈŸ‚ì²íNZä6ëÏ'±­cxk4`ßR¿ÖGØ;²€‡:ğØ¶tà‰lêÀSø?:±pæé°öyÒ×Èm³Sv>¼1´ó¬‚{àå¤è¸[Ü›‚Vv­T²<°ÕY[ÈAo|;ª ìğàæº
‚0`«µ
Ø‘AëÂ]şÁÿ
aŸwº¿^Ã]ŞH’3XthÂ4IìØ É„h°cvªÁNLœü};=8Xúà‡®ú×Bò ëŸ°ã›7oºÔ6OÌ#ğ~Á‡&ÏG=vÁUD×ZØeïèèô¬I.;´sÁ@piAŞ÷ : Œ+¾fó9xïé|^vİ`qÒ`Üél¶Õ1ü?ÿ§è,û ñ½€ÃJÂG7³=
Ş8¨’|åq: Æˆ½ô¾=‹³==yà.|>vÛö…ë'{zİE^Ø&gàZĞ[0%Û96×êÕC#¸æ hÜ×î¼X^ËiJæKDï_œ\`àªÃØd
îëH8ı½#Çq@ò0~ËóA4â¯ĞÓÆ!‘$
#xòX¸ı!¡[ú!(ºàŒ@¼rS—ø†3İÄav·a§9tË…u&í<áàC´ƒ:Â¼4aGï@Ğ M™pv"äÊ0A"ÂÀ¿‡?¼ 3æÿÌ¼X	Ø´µ	3¶…âÀ¡zÊpMlP
C?ÛBÜ ËPÅŒ24¨p°f÷€wG|ó½ß9Î»”^PjSo–*„Æ±KÌ&%.G°ÏÒ^¶CŸ».8$f^[˜<\—;‘Ç·,ñîŸàà»ë)¿ÊyBØŠnæ§¥‰¿º~†1"£ıÃ<‡;UÊùºb^ƒ±(­%Ø¡XèOçÁœÆ
dfÈ6.zB ¥Xq^JKa[P¨	rLp5¡uë‚Ğ’
²xEÁn’EèŞ'bj_‡_=DMbPûÑu(ìÒ‡üYÅº„‘ı¨›;Á ocêfõ½Eì‚ëlìx@ÙITn/x8*|÷’’R4µü[ä{KØSJê4ˆ,têÀ HšuÊËü‡eŒG4­šWï¥"ñR°KÍl"T4”ÌYA¸V¤7ëua	[B“>¬3ä‰¶î”U'ŒĞÚ¸>˜ˆ|ëé\ ³™N³3ú|ü›»@9<¹µİ Í	WA çßRíEi	Vağ®‚6/õ‹šºÁSSš:§¦äOP*+I¿Pd¡néÕç·lêRj)#Yabv1OOg§$èøfA„½k»gã&R…ô?*½roL4xÜ|³ 1bíiy ­<°ZWGĞº:²[±õØn=ÁÖ»õ[Oí…ªVÉÜ.ºZ}`çÌÅN_éù/wp¹}áƒéH–l©N,O!ÁTÇ˜Z³4ÊRß¨9(øW«vŠ4Ï _('AÄ5× ¡:ã›Y½4¯Zz1lÃ ùè[™S@¯‚!&_Ğè ßã´¦WWYz?_Ş/}^+™†zİÀÆÁŒ–ñk+Ô&(¯Óè/[¦H
VT6S8;q@ë©sÑrÂr·ÖÔ„ˆœŸAùñc}äpV‰1?øl-ƒqáŠ‘÷ó;/IË[TÍÏÌ63ó!ÌLaˆïyR¢U>¹Ä¥B|1TÄìâó¡öYFã•i[‘z(¾›™G·Èº½K—Œ­È›=Tñ¦Z,vŞì¡’ûÇ	½‡Ò²ë¸<OQs8åĞ°ÙD[Äkõ"HÚ„[N’P¶-³8{*Œ§:Ú8„ÕÖ^œ¤âÀ@Í_ÅQRwôSÆ^F‘¶TËI¢0ñÄ¥FÈşÅcûXqXé|ë-ã0áxSÔ>6›MÂB7K‘<e)¸h`ú˜Â¹ˆÙİÿ*Ö+P^pÛ•ËşızV–æVÓ†{¾É^@>~`ˆ%>çQCàÃÓ]³åå«fÎ3eĞ»Ä=‡»Ç¥+Ü/åéhUbqLß"ömDd„®QJß¥ãW²^`ü‹î8˜¶ÁmÃ¯xÏZæ)Ë^ÒÕ×ş-j¤—XÖÃ~bV6î¯0×ßëÚNç¤ZòO4šÜë‹` $AÓG}µŒˆ”CîÍ§yağPz&ªŒíƒemW¹tUÿK›ı_õø×™·Bá6áÎÔ8l1ù5İ N@¨„qE¡uÀ©®P?2	» ‚ò ĞfÂÍª<ÕşJN•†'£ Î¿KÑg“G³,0@1­°VV;Âö—JE_Ë:Ut³øEíÏf˜¼]x%¿ìÑßÉ®-X¨¹Ï×é¾³)7†Ø‡ÔJ+U²İÚ­Öƒ¾£è¦C´ä—657>E¸¢şáôPrºnÚy\ù<÷Ò…“BÀ	´Å"‘&˜…9VrÑK„é>ÔƒåD½Ú+1‰¦™‘ê=²­ Z°¨Æ!+ã¤ÚÍÒ0ƒÙ÷åî-LÒ;ª]$`Ş	Âÿ‘%©·¾'–µe‘„Üá±…™)ä:Ä;B/•¸Hr*@€èªÃzO'zÿ.‰Ù¼$}¦(ó}š×K`Ë“Ä½ã’ı¸n“ñÂu'öb‰‰:‡G!6o\©Q˜â‘!,à;r/u"_¯‚òˆœğö°ˆ´4w—›âêÁ©±™Òµ0™É¯·¬³úŠi¤/@Zh*o­İbxèÑYrŒá²k·Ù»¿ïÊÑ+aû©­yJÅÌÂÕ¥ŒånJğ(63ƒÆ¦sJ˜–ñ5…ÂÚâ·â­_ EºEêè}™6j+¹ª¸”ºÅ<)_Ü4Š]Òå,¹˜øªñuıãUqÕ´ó,¥Âõü¸V©„g¸E„R|˜–•I<õS“i<˜¼ÈjağC-W"òã´ıSé˜éTª=£@Ië«0ÒLŞ®×)’mY´3œJß"²RM§©_4´œfCd`átG½¡„*^Ñ	]%”³?¶g%ËË•’f{d:§äÈMËYóìÉ½,GT¤)óÌÏYTşç©¼Ò:©–BİHÒõ9n/quXeòÎèÆKŞ£Úî@ÄK5Âÿz—ud‹ì¤.ó÷‡ÇÇ"¤æÏ½qÓ^~˜‡ˆ¡ÉV7¥ñûÒĞc°_[P^OF¿*S•aÌ¿âU02ˆÂà0dÿÌ<`««
¯[^[ÑcAÚA°°*mÊÓ¤Š!:J!ˆ,Š áâªÌkKdsLÉÖşP©êO¬VÌÿåvT;Úª£ñ¬¾Ã­PÆÕ±âø5(N'¯Aqj 8-P°[Ù¬y”ºÈ]+3Òw¯d¤˜^¾¾—‘­ïgäá÷3òãYä·bË•UÚ“<_‚Ê)(~`š’<`0`‘Y‘È;cT¿§'Âô/Á3¡6‘u5Ÿ÷Ö®ã
«³àéó ƒæåTÜ	Šd/…K»„tãLĞvÆ÷)O(s-Ë²é:R`pXß09¿Vänrï	¸Çcqak/¸IÓèÓ‡»İÎë¸ˆ q–áöÃfEå&ÙêÎÙ¤Ûât…"SQïş8ã/WNî½¾ûÛ·fë]}¤Â•ÿl:Î)Õ,¸XÍµÚ‚œÁÁò³SS'ÌXQùÀjjÜÏ?ƒZD ßêáÙ»ĞxV¯pô%ZÉè¿z×Ï&Ë}ª²ÂBõ&m–·ì<KîÙÎ¥Ë^X_¢,]ä áµw< Gof¿òøY§¬¶wÙÀ[h#8¶à®brÔÁ?µ:û‰Õô¾ğp€—£»‡^œ6ègDdò¯hµûĞŠgß²k„
×U+{;^Q3Ü–˜ğ³.Aše.ùé	/í„cğŒs°®jYæˆøü>'‹Ö"j^`¿Â‘tÜìk×jJ„üò
–H–ƒ'ÊÁ;³{š%Biês]Ô¦÷(ôZy¿†Ü»!]Ğj¾±°ê`Ç„[MN4¦İbd„Q‡¢b³ÂÒÿV-z¬*¦Tõ5˜m—ÅMF
ŞrC-¿Ûê}yª˜‹ØBJE~“ÏçyŸ]ø÷ƒ+ş¨a„0­ƒ|w-`ŒQÒ]Ì±ãÂ¯¬ñ{¼t•<³vğ…ƒ/*Ìo¢a}aÜ®Q,—ÿ©?U($a2÷ÉÒÀb–j_W¨î+|qq Â¸·Jğ¥ÕEğ½¯J°\hVPé:‡İQït¶‚.#3+áÈZnˆpÅÔ‚Á\½J¬ˆH‡ı^²§"°pŞ0)¥ĞÉBA‘Q³«‘¡
ö¨P¯Tx®;eÕuU–§Ñ\£]1ÍÀ¬ÅÒ‹í,
¡¬¡#D%
Ÿ*$ù…qR—?9ã×ü©R?”OC;‰ªÊü€ÔO”œéqúel^W®*"²ÊEq¢Ù.û,¸-Ğ‰^^qª‚&‚Ô°rˆXâ{É‘à2ˆíkG›H÷Ôu´ì9TşJ/:†^1N\¯©8ÅÇ×ğœúÇ_öi}J:¦ñÏ«xƒLÿ¶WS_¬\é˜¢õÆJF|·`dÎÛdÕÍ¼”^;G–ÃpÙö•Æ½e=Üâ[ºM°í„æY&f‚<^-áÁ?‹ÕRÕ[Äw¼˜«¨¥#[a¦H‹‚<:± ã>¸<Ìîö÷ ß
I):”3°Z…ÍX]›§õ’ó>ÙOÌ^İmOâÉàµ˜œÒâ2W¥z·¨Œ€$	 ¿Õ|ßùÉ
¤	–Õ O³©E¾¶×Š:z·Ğg¢ºq¦IG¤eZZØ!|ë~«5ÑU-#´k)„\İËı¢õ”Ô”;"@ë'ã‹ZeÎ'¯ØÅ•}eƒQ} ˆ(INIüU2[yK¼‚¡z[ÑúlII6üQ˜›OŒé‘›ˆğV•—VR³NŸl4Bˆ/B„*ÑCë¨ÂÃşmU©¡şå|µQ.	ĞîªÈo¡«égUºÌ’×ùÅWaLÕúD··œVxrò.LJP»ñ’ºš×¼05¶uèRn-‹y(u¿GÁd{/½Ä†™2@ßÓ<1H{iãk%æW™À½WlÕÖÿ‰Aû„§®ósNUÇ<1-\1G(Ÿ\)„Yts
üñƒöeÅë‡mÕ½¸_¼{ÿ¼#ÿÑwäŒƒ<k¥J{7ZD¦ªãi}yewA¦±Ø·=±‹*± k«İTW}ïû¹î5ş˜º*zy:O=¿gâ&Ñ‚Çñ=»öŠä¡S¿ß~4‰ç®V0QÒÆ§Nà¯Ê’ Û¶‡]J‰IšC3fâ0¢j·Ndn¯}øhÎËÌ4
BëšÑoñ¥·ë\Æ`;-z0ˆ UHÉ ñÛ7-JUgF’­×øè<¶a’R2Z³C89eš*(x~²I¡«­Š_¶N¾î½™gíİá¯EŒŞ:Ò¿¥öÅvÁ)œ¼c-—|W"oöÅ<å ?Üæ?ÒÄt2#¿ùÇœ\ÅœÒ‰×Ÿ|PåÌıåAÅ€áøÖ¦I<=€~Eåø#*¡Ålé÷Y¤ì„Y&9€¿®Ïh0*ßl0|Œ@ƒİ\7Õ—VÜµiKh$mƒQÕI‰‘­·ycüô\#úƒÌ^i²·rúæ/e;ô'Q4˜şt	óÒ-¡÷ëßNŒoV*~Â	>GÉzV„Ş€ˆh”séfô@¹ÅOí˜ó’92ğò3xlZ‰pÒóú#˜+BÂ$y=U8‘¥‚mù´
ú…ZüÚ*déPìbÑ(•ûôã,ş»›à÷ +ësıÈïÔö¢FÌÎ»R<Vèí©ru,KÌ÷Ùw†œË‡\ü€+¡âp`i?°éõ@êQY‚fƒœÉ#ÿ	ç¢GDóì™gIóìgÉ°x¹ªV=í‰,ÂØha)[*í9,VïÜ jO\±¬ä±q;YzèJ•¥³ŒÛÿPK    3¡yMp#æ"¸  I  %   Adafruit_CharLCD/Adafruit_CharLCD.pycí\KlÉy®î9|J¢DQ+iÕÚ]¯(›;z¬DÉk{WâC»ŒùPš”å{1N÷M»g»{DÒ!“µµyÙœ8ÏCHœÄ@€ä` HnA€ >H€äÀ’K '‡ |Ë%ù¿¿ª«{Z¯brˆ5œšêêê¿ªşúë·rßü¿ù¯/Ô„ú—§ïúFÿ`áĞŸ!B”uİe3©çÄv^”óÉeŸØ.ˆrr9 ¶‹¢\)ÊƒÂÉ‰òp¨ÿ°púDyD8ÔyT8ı¢<&œQ>&ê\8ƒ¢|‚ûó³'¹å?;ÁõÓ|w’ëg¸Ïs\?ËÏqı<÷ëx,‹ë¹Ï\‘û¼Äõ	Çå—…3"Ê—„3*ÊSÂåËÂ9&ÊÎqQş„pNˆò´pÆEùáœå’pN‰ò†y•á\ãù\ç¾*œ	Q¾Á£Üäön¿Åí·¹ı“Â9-Ê¯1´O1´OgR¸ŸuC8gÄûB<âíòëÂyN¸¯sëYİú†pÎ	÷n=¯[ïçù¤ïİz»²6u‘6×ûoú·â¨š(°ëŞ Šc(, ï= ï$Šuc(FQŒ F1„bEEE?ŠŠ>*b@¾ëTëaË‹+s[Õpin^“úÎ‚ì¾K…Kg€Œ@j§„›nŸpb»+q™°0‘Nß/(ò¢uJ
C…‰¦3T˜ÔPajC…	¦9Tˆì†¸B”7Ì•“ TN&P™ Y r³"âxß`Z<Îg@"¨<*Aå,¶•sÂ^›šÀïQ1×¨F‘Vè6C7rıØªúåù±Vk±µëÅ[Ôb½5ãÆ­ÛW­!ŒÚİĞ"´Y5ÕıÒ¦ÄŞ¾QÃ¦ ÃÀüùcÚİƒ~q D…*\1ÄÁ0WLq`p%'L®äÅA+}â Ï•‚8èã
)p…€¹BåWÅÁWèrP£6,ö^eè&CÌ3”‚¨Äü;gÄá¦°M‰xTl‰'¦0ŞıºxH iE8nôğ» ½}\¹}BŒŠ'†ìN=$bšÆ¹û¨û<4,|Æ U†ÑÅ|u¤C°uaòE|JÄb6>-f±IŸñsÔp–¾çdãy?/âòÂRÀâ‹\™³)Ìøn;ßÖö"·YiÛK cƒ–½6…}Ê¢ïÅ^µá}Éµâ-»]²,{mÚZX™f™¿Q*•æoYM"ˆ—("²¢­ Õp¬ùHÓó£AKı«¾ïİ8 5ÁÕAí‘åúÕ†+;Õ¸j5<ßµnPÏ0hmnY· ^àG%u]ÚõÛŠ\Ğ®åÅ‘uã•/¶vÇµ"2r­†YÕPN1ğûT¸é<C÷İ–Êi´ÌÚßZÖN+¢óÑ xM	÷ıÖÎˆ N“l´vüËĞåˆŸ5¨o.Ö­}‚»Ëxkx\ŒKKÃ ÁlTkŞæV<İ6$á¶¥`Û3òô¶7éí*Iôyşc7Œ+Í Q½xßÚ‚†[õ³‡ÉĞÈõHVå*a-­>´"oÓ¯6¬ ´ŞZ|ó-u©ÆÑ ·^m5â®W-@×ÃQ‚WrK½Tãipé¸mˆÅnÕˆoIÂ²î?\Æşt È¬­êc×ªÓ.…ój·4´Ğ>FXM…ºS¥M‹ZDP´‘!]WÔj6ƒè‡î€×ƒÇC;×>PäÆ
|¥¹»ƒùÖ×¨‹¬{D…îåö“PmÜfèUc9µ†·VÃıöÓá¸M×w<3™1ğ¸„;ÓÖF+ÖğöşÔL!Ü½fÃ«Ñ™Ò»ÎÓ$Sšl›'yˆÅ˜Rşi«+<¬«§hÕt¡aé‘Ûê9¨æJ*·¦®2İÔëÓÜ5IIWê-à…·ör©›t‚&¸MµA,"9zY,¼yq•¸İI!©Cu§IÄá©£]õã„™ĞãËs÷¯¿zuoO>îîÅ´|'pÿRº™q¹?qÔ¸ê×èxdÉoah4†-ßÇî&ÛÊ»Ÿ²¤‚”n¼W¡]§beêcP #UˆE1Dx…¹—lÜlzA=ªFò—´şun¨ß›êwFıŞŠ¡‹¥ûCI]W$‰;q^5ÈÑ6Äx4"„V“ïbunõÁ:7¬ıÉ>q5Œã±¤ÓŠ÷+µıZÃe`A+n¶b®îƒqoÇP‰Wæ×î/İ}{uE·Ì=°×VíÕ{÷x‚h™]Z\ù, `*5GqİçÆìâúòêüB\T×è¡ôê:_©«›{·çW××xº
^½å³@ÓÓXXY·ß^Z¸·NÂ?Ó²öÖâ½õù…9{a™®¢‚ éŸh_ÖÜ*=³ºÄ¡ùŞƒ•¹õÅÕ•µ…uÖ}5XL@%!­Ná6£8rõ9í4~h£ñCûÌ?7åÏŒü¹Å0É ”¤ !İvVÕÛù=SFÊè†¦04çg:¶¼ëùSP7¹ˆîb¤–×p®lVâßÚ{¥î<i\q77¯t*û]¥æ~££RÁx•Š°¯øE£hÒ7ı¨«Aó‚qÚ6
Æ9sÜxÙ1FÌãÆ)*OøÔ`Óàk&zğóB*}„áTé3t¿µ)¬-zƒŠåà±Ô<j­0¢såƒ‡@­Ù
vHÔ=Ú©$AhÈK©}\.y1„ãpö)lé¨Úv{aı½òÖêòB<ÎçÓ%ªìxµ0ˆ\¢n'šÂœí—ä>Kcƒ1ù?H\ÂÚGÇÓ(/DµZ¯êZvBísKwmu:ìÛXÖ‘­ÒıvÛ
1|û’~+4Õ"åExAÕi“‡¦PÖ!b6b¶Îœm_ÿ­t"Å¦–P’˜@Â`×j‘vSbƒ{…U}ÛìÂ±„ùyûîò]*5±WVˆÒ=9<##Â¿4Â3'™A)*ry+°s‘3™5S‘M.Aì Öá$ğ——´j’ÙéË´Œ-£IRUœS¨—È…_£ÏP± u<B+­€«,s•ÅkYkZQÓJZœh†%…İ3(&Û/ ?¦F_AsÀg¹Ñ”¹ªÿ%€0QŒæ1ã(ñæ¹¶E4GØÛ‚ú˜)anNR«Çã®M	•D÷Ï"OËZ%¡Wz"’EÖÖà¬(ğ;ÿ›8„wf½úĞÓX—u-h1HÇSDÈ—İ4˜vËâ3QG¤~ÓàTüğ3çXÓßu!1‘‰g²2€¸à,á¨;ö§ÈÛj¸ui™h6§–ÍÌ-ác’ŒX¡ÒmJ2,¯~nA“. ˆ¡<„†´C+¨`æÿ¸&#å#¡ÃêD[5OÅ‡ı&Š·€™‘ÌŠm²ÚrÉƒÉ’yvÿôAk¾$×œ=A|\àOÆiˆÉ¦",„ÒW$ÉîMŒ˜  }í/‰£T	X‘…ÃT*q ÿ/Bëc=NÀTÛò?»xÊú%0úÿíúy*@ ¦ò¯éú–Rq·)¹dî³/ä’ÄÊv+Š½úş%‰³zìd•)H%Â'{£´¹P‡p×#[Ş‹,¦° ¸ÔÂÎà¼‡Y·¸¢ÌºÌV¤œ¦ª'ÿÌÙñ}‚òïšç32" ŸlÆ{‚uSRM÷"ìÊü;ÄanuRG™"Ü€†êäÄ­C3eTwèh·³xÖTÛD½&Ù±¿-½ò¦t¥³û~;áCpiI;R7:yÚL6ø¡:?„1/·ŒÈ:ÕÇV4oUÕ€Çóki¾»ËVi‰CHH}P)ÁıíçOÁZl€ƒPz)@<‹TçÀ@\tiríÏÅ)ÂDwÜ(ªnºßÊş!	j:h¾lŒçô)Ò·-DjZ ¤QW»¾¦v`;¯: ìÃæ&±Ù•ƒ]ªÇÏs} 	gèpFzŞ>f<MuÖF¼ôvÁCIŸ$j´cM)ÖåéŒƒ×üW¾ä†AÆq(]Å|üb¥!µ{aòT-~*í›úÈñü˜õzÛTÔ4¦3€@E°±ÿ4s‰«¥«YŸûµÒÕiéŒ¤u‡û}‹ˆ¢ù{ÕõÚ3|€#nƒEÚPÍl( ¬½ƒc¦-öºÍ– öHŸ°¯Å¨Yè¹›FÂ*
cFÑxÁÔ¶­¦¸ÓF†âëİ É©/»jÍ#â{ÀáÓ7ˆ1Ü¡ƒş(¯Hqí}íÙ^èlï—íıíb&™Çj»Fî5jî)£<eÔâÕ¤ãÁÆÄ_iv›ãS*êág«86Á¹Gôù9î‘†Ö˜¯¥.â,Y¾rıæMC´
Ç¾”Qq–Áği"Ğ­¶ÃÖÑMÊŒÓøßrI°c÷ 	®gîÏÏ1e¿İNÀÌ>é¦­ Xhãi›92¨ÌÆù`*¬4[4Oå3Îø0$¯Ÿ•i½æg.'!FAü“Lü#æ„ù’1IŸsÄz-U«%A;z~\*1t–T0J‚õ”½O@¡wXâÍ¿sÅªä¶¶>C4ã¦a¼;M‚°ÈHŠZ4›{àĞğU`E:o[soÚw—­FP«r´Tr¦)(D"zo;‚¨IïLà$¥¸7Şu]ßºÊ¤u‹Ëf5¦N¾êÕØ‘VÃìšÛmkc?v#®U=NpàHB(Y%²d“ [öû™`!b{2´Ö¹‹DıV7_»reww·ônËó«M¢†¨Tv®l9œ°Ğr6K[ñNÊü×élèQ—¦Ó¨9%%m§.—.§¤Ÿf“0~QhWZ§÷½h ˆ°êoº¶ÊÌkˆõ,áRb>VGâÎ¨…n5v+XòKšŸ§Œq©ú%<IøfÉù$¡åS§¡NdšI	¤õM‹wO‰
¥¬pNÈ{ï—î²i!õ%o'{|!ë²ÎgV·\ßyæç¼çš‘xÍ“´Øn“kG+KÛFjS$Ò*ŸhÙ.}?¸K()š˜ƒò¡ÎpÇ¾„»1ƒ–¼“Içè×e‚r8fM#†üjµR»èa¤8ÌÇNj¾Yªi’š|¦•,ñö9ùvÍ…·V“ù¢ 5İÑTnšEZÒÊÔùäìU*>q»JE†)!<Z\öó¥Ô*©›ùv¼FlÒn’j”YÓØ(©’ÌÚî6wwì<üIH‹´çQÀ1fÿŠ%Ë(VPÀD³?‡âó	±7D"O±i¼ÈsÏ} …Á"Ä‡FÁÌø  6<Wì£Ï€úäéƒëÁâXqxx¢8R,‹dÒpí7gŸšm‡f³í\¶LdÇ	wn?t*¤Úõsª]çsÊT»Á$Õn(IµNRíFé†m~B<£L7îÅÂ€zÒŠ2Š}šêÀ1OÌÁ\4æÃB¼`Ûì‘™†$¹>D£X$­Vx0‚åpáÁ˜x2Ğg¨Ü·<2İT¢ÜP’(7*Â?SšéÁ10š/æÄáqqxBãùm™:w\2$yMPNd¯	Ø8_û6çÈ9½mPléô¶"êjÊ6q²Û¶´êGÕd˜ñˆ/`ß£|Ï$3¹í˜ıygZ:w' }´Ä3ğih?tæ™†øÔ´6õ¬-å«g
ZwêY{zN[w3$ÕN®–D­¤ø•»[^m‹'®‘šNB"7›‚”ZÑKóÑSÒÍR}“•ÔèWYhÒŸÓ™‚p<ÆY`]ig³Y=²wÒÙ¥›u“æô‘©‡YlOôÉfœuú%äRu8ß¬3ÉNí_F—yCğğ&”é<2ìOê¥ìCFS½çÉ|¦lºU6bœäWégfHÓêÎ¸’Í9…)¶%8ÙËK³,‰’ˆ@¦h.%ïÿo–›=8öUµ6²²V¦Æ5öŞmwX€„‘©St†eêŸc™¨…sÌYA•ps÷Œ	Íöh¢ÈØÇ´Şù¶PyòHjêd¢¨ÙÈØP.ìË(>â(¦Q¼‚¢$”Ë“ÂLäœ0OLI®Œ×x-Y#›÷mÄ$85şİT¿Ní™+7@ä²¡b-âìERl
úÓ¯²}
æ¤qŒ>ãæ¸1XH}"cäÿ´`e‚Ö„ù~˜‡¨'1³™/^ôGwÛÚsI{®½=Ÿ´ç•ùpÀiáªËÔó¨×s*!$Ñ³	i‰"ÂíŒ¿êüõ|©.¦~lF÷æ†İBËc»G¡JFå=Cû­ÇÌIv›ÓGãT›bÛİ8õØw^Tæ†Ÿx¥‡¥Co†0¾Şó¦I7ó"üBÏ›91³6•I‡9ÚMï¢ÛpeÿŠ#FƒøZj²Œ–qŞ¨å•¶¬­x?E®#TºV)ë¹DõË‹Ã>qXP³SAIdF[kÔĞ®Ö4SV7•^I*"öÂáW…tp*Œ%Fó„nÚ¨oõ¼Ù'7ê¯{Ş,H¯iJøg!Cšw<âåZğõÔaØ'iß~ê¼Ñ>~0j_«;MRÀ|­Êİ/ŸÏúú¥_Gÿ2bQ?›êw¨«œLJ‡0¸ÑÏÆ Ø7ÊœvÿÛ»‰0åÑÒ€î×4ÙNö>Š/¡øÉ# N6×9#˜ûÈDôÍ‹Æ}Îä.ƒ\»"Q§5¹êïI.»×ÑÂF6²¬U?±9[4ŞÊ¨TI2±\»öµ!7ñoh^Yd§„Ø‡“ØñM#Iùègá¤EUweŠ•”-ˆ/Ø	Rgy$Ú2pŞIÕˆQœ,ŠG=ç´±E¬:RÁ,äŠÊ92\*û‹Çc8k:Ÿ¼OJ¡« -ì jÔöº¡‘ú@ÀË‘å¾ÄËQ€sƒcp|XçF2Ë®FM²Ã}ë¾—º:˜.`ÖBwuKòL~›VÃt1ä±äX#m)fáã$q¨+Â</÷%¢$æÀşv!+`ú“Önİ»g`<ˆ¨é¡¤ÖûÄü;W ÁR‘ÔÇOŒfáŒqë1µ~G<ŒR~•£e\Ä'…|£.>-b~™N:]âçD|VÄç€Û˜ßÒ•ğ™Fg6ºœí~!‰(Ëšk7W¢¦[óêûÄM"ÖQœŠŒÅësVÕqh—"°ºV¤¬wù&LÆ¬Ğ2%jÕë^Íeñ±D±å»®“‰à`pvô˜Á‡÷hpS™÷Œ®Íì]ÏDşØ3ªfÏvMŸ K…^¾E‚nÖ*ÉĞb'«4¸®É×*;µ&Û:ÕîşÒİõ…Šı0cœL@YÏ£¬-,-ÌÉ78GAÍ¯>\á7Üçk~q×‹+üP“xi«)9E€â½„It½ÖÑ°°ÒÑ0£³áfgÃLgÃ-Z§FY˜×)‡²åM{Fmk›]z°À|M†˜ÅWD›™%qÇÁ3‚1ôí„±‰ş³&	vó	÷Óæ)ã}´xïOøÀ¢`Á'Šqräé“N÷¨_„W1gıøŠ‘ä¸³:)“Nèğo"›H)ì wYæ&ñë6‡\<H/‚ü•Ñl­¤•"¸Ûø|$ËşÓÒF²Y’Ô´Åô4m˜¦­÷§q&AI%×3’0µÓù_Eñ5¿(TŠ‡èÂ0íŸÊd÷üf+–4ıs¢MºşæH#†U.¾“».c†TÛe)¯ŒxÓ$¢êĞWèDKIú[G&:qÿ4™"‰Nóì©x²‡°œ%í¥IßnyyùÃËK[å}$1	f}ÅZ»¿¨%ã†š“ÕŠ °Q‡bßÑäx|ñƒÅ¤<-Jbõáœ›%Ö©å¡’XÃ,«F2²ªø#YõtY•á›ñÄjå¡€R6]½ÍçVJ‰ßÕR"áÖ³wç>{Ÿ¾]mÄÁ»ÚH\t·İìÑ6Ó£íGÛÚ–×•PH}=„Â‘H‚¿×¾’§ŒaC
¦Åü·QüN‚¹£áØ˜¿5TÚ0¸»ldòÑ‘ı¯A¦À#lp–ÁÜ´i ·­¹D¤Î«ˆ'ºn%ãÅìíIê†CF¡4IğŒ·´8©—ß±i÷/¢xÅ§Dæå<Î	fi$SQWQ€³ğDº[òòê½{6¯–µ½€Tæô'}åÛœÙÿYÜ„˜ÖjÊmõöªınCq6{ÿæŞµ«xcÕF´ÜFæ­ıu?‹â—Pü2Šo ø¿Šâ×Pü:Šß@ñ4±iÿŠßGñM€âQüŠo	¥âÛn-æ@´t¿—Ñ#¡1ŞáOË4€×a¾Eğ¬›Ã$Dé“/mŸ\ÇïÓÛrO¶÷h¿kN|oÂ°şPK    2¡yM®i_               ¤    EGG-INFO/PKG-INFOPK    3¡yM“×2                 ¤  EGG-INFO/zip-safePK    2¡yM’çæ                 ¤À  EGG-INFO/top_level.txtPK    2¡yM[5”Øq                ¤  EGG-INFO/SOURCES.txtPK    2¡yM<u²L   X              ¤ª  EGG-INFO/dependency_links.txtPK    2¡yMğ Õ6                 ¤1  EGG-INFO/requires.txtPK    3¡yM&TqİŠ   ¿              ¤{  Adafruit_CharLCD/__init__.pycPK     ‚yM` ãù"                  ¤@  Adafruit_CharLCD/__init__.pyPK     ‚yMt¿|?  QQ  $           ¤œ  Adafruit_CharLCD/Adafruit_CharLCD.pyPK    3¡yMp#æ"¸  I  %           ¤ä  Adafruit_CharLCD/Adafruit_CharLCD.pycPK    
 
 Ì  ß3    from .Adafruit_CharLCD import *
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time

import Adafruit_GPIO as GPIO
import Adafruit_GPIO.I2C as I2C
import Adafruit_GPIO.MCP230xx as MCP
import Adafruit_GPIO.PWM as PWM


# Commands
LCD_CLEARDISPLAY        = 0x01
LCD_RETURNHOME          = 0x02
LCD_ENTRYMODESET        = 0x04
LCD_DISPLAYCONTROL      = 0x08
LCD_CURSORSHIFT         = 0x10
LCD_FUNCTIONSET         = 0x20
LCD_SETCGRAMADDR        = 0x40
LCD_SETDDRAMADDR        = 0x80

# Entry flags
LCD_ENTRYRIGHT          = 0x00
LCD_ENTRYLEFT           = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# Control flags
LCD_DISPLAYON           = 0x04
LCD_DISPLAYOFF          = 0x00
LCD_CURSORON            = 0x02
LCD_CURSOROFF           = 0x00
LCD_BLINKON             = 0x01
LCD_BLINKOFF            = 0x00

# Move flags
LCD_DISPLAYMOVE         = 0x08
LCD_CURSORMOVE          = 0x00
LCD_MOVERIGHT           = 0x04
LCD_MOVELEFT            = 0x00

# Function set flags
LCD_8BITMODE            = 0x10
LCD_4BITMODE            = 0x00
LCD_2LINE               = 0x08
LCD_1LINE               = 0x00
LCD_5x10DOTS            = 0x04
LCD_5x8DOTS             = 0x00

# Offset for up to 4 rows.
LCD_ROW_OFFSETS         = (0x00, 0x40, 0x14, 0x54)

# Char LCD plate GPIO numbers.
LCD_PLATE_RS            = 15
LCD_PLATE_RW            = 14
LCD_PLATE_EN            = 13
LCD_PLATE_D4            = 12
LCD_PLATE_D5            = 11
LCD_PLATE_D6            = 10
LCD_PLATE_D7            = 9
LCD_PLATE_RED           = 6
LCD_PLATE_GREEN         = 7
LCD_PLATE_BLUE          = 8

# Char LCD plate button names.
SELECT                  = 0
RIGHT                   = 1
DOWN                    = 2
UP                      = 3
LEFT                    = 4

# Char LCD backpack GPIO numbers.
LCD_BACKPACK_RS         = 1
LCD_BACKPACK_EN         = 2
LCD_BACKPACK_D4         = 3
LCD_BACKPACK_D5         = 4
LCD_BACKPACK_D6         = 5
LCD_BACKPACK_D7         = 6
LCD_BACKPACK_LITE       = 7

class Adafruit_CharLCD(object):
    """Class to represent and interact with an HD44780 character LCD display."""

    def __init__(self, rs, en, d4, d5, d6, d7, cols, lines, backlight=None,
                    invert_polarity=True,
                    enable_pwm=False,
                    gpio=GPIO.get_platform_gpio(),
                    pwm=PWM.get_platform_pwm(),
                    initial_backlight=1.0):
        """Initialize the LCD.  RS, EN, and D4...D7 parameters should be the pins
        connected to the LCD RS, clock enable, and data line 4 through 7 connections.
        The LCD will be used in its 4-bit mode so these 6 lines are the only ones
        required to use the LCD.  You must also pass in the number of columns and
        lines on the LCD.  

        If you would like to control the backlight, pass in the pin connected to
        the backlight with the backlight parameter.  The invert_polarity boolean
        controls if the backlight is one with a LOW signal or HIGH signal.  The 
        default invert_polarity value is True, i.e. the backlight is on with a
        LOW signal.  

        You can enable PWM of the backlight pin to have finer control on the 
        brightness.  To enable PWM make sure your hardware supports PWM on the 
        provided backlight pin and set enable_pwm to True (the default is False).
        The appropriate PWM library will be used depending on the platform, but
        you can provide an explicit one with the pwm parameter.

        The initial state of the backlight is ON, but you can set it to an 
        explicit initial state with the initial_backlight parameter (0 is off,
        1 is on/full bright).

        You can optionally pass in an explicit GPIO class,
        for example if you want to use an MCP230xx GPIO extender.  If you don't
        pass in an GPIO instance, the default GPIO for the running platform will
        be used.
        """
        # Save column and line state.
        self._cols = cols
        self._lines = lines
        # Save GPIO state and pin numbers.
        self._gpio = gpio
        self._rs = rs
        self._en = en
        self._d4 = d4
        self._d5 = d5
        self._d6 = d6
        self._d7 = d7
        # Save backlight state.
        self._backlight = backlight
        self._pwm_enabled = enable_pwm
        self._pwm = pwm
        self._blpol = not invert_polarity
        # Setup all pins as outputs.
        for pin in (rs, en, d4, d5, d6, d7):
            gpio.setup(pin, GPIO.OUT)
        # Setup backlight.
        if backlight is not None:
            if enable_pwm:
                pwm.start(backlight, self._pwm_duty_cycle(initial_backlight))
            else:
                gpio.setup(backlight, GPIO.OUT)
                gpio.output(backlight, self._blpol if initial_backlight else not self._blpol)
        # Initialize the display.
        self.write8(0x33)
        self.write8(0x32)
        # Initialize display control, function, and mode registers.
        self.displaycontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.displayfunction = LCD_4BITMODE | LCD_1LINE | LCD_2LINE | LCD_5x8DOTS
        self.displaymode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT
        # Write registers.
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write8(LCD_FUNCTIONSET | self.displayfunction)
        self.write8(LCD_ENTRYMODESET | self.displaymode)  # set the entry mode
        self.clear()

    def home(self):
        """Move the cursor back to its home (first line and first column)."""
        self.write8(LCD_RETURNHOME)  # set cursor position to zero
        self._delay_microseconds(3000)  # this command takes a long time!

    def clear(self):
        """Clear the LCD."""
        self.write8(LCD_CLEARDISPLAY)  # command to clear display
        self._delay_microseconds(3000)  # 3000 microsecond sleep, clearing the display takes a long time

    def set_cursor(self, col, row):
        """Move the cursor to an explicit column and row position."""
        # Clamp row to the last row of the display.
        if row > self._lines:
            row = self._lines - 1
        # Set location.
        self.write8(LCD_SETDDRAMADDR | (col + LCD_ROW_OFFSETS[row]))

    def enable_display(self, enable):
        """Enable or disable the display.  Set enable to True to enable."""
        if enable:
            self.displaycontrol |= LCD_DISPLAYON
        else:
            self.displaycontrol &= ~LCD_DISPLAYON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)

    def show_cursor(self, show):
        """Show or hide the cursor.  Cursor is shown if show is True."""
        if show:
            self.displaycontrol |= LCD_CURSORON
        else:
            self.displaycontrol &= ~LCD_CURSORON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)

    def blink(self, blink):
        """Turn on or off cursor blinking.  Set blink to True to enable blinking."""
        if blink:
            self.displaycontrol |= LCD_BLINKON
        else:
            self.displaycontrol &= ~LCD_BLINKON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)

    def move_left(self):
        """Move display left one position."""
        self.write8(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVELEFT)

    def move_right(self):
        """Move display right one position."""
        self.write8(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVERIGHT)

    def set_left_to_right(self):
        """Set text direction left to right."""
        self.displaymode |= LCD_ENTRYLEFT
        self.write8(LCD_ENTRYMODESET | self.displaymode)

    def set_right_to_left(self):
        """Set text direction right to left."""
        self.displaymode &= ~LCD_ENTRYLEFT
        self.write8(LCD_ENTRYMODESET | self.displaymode)

    def autoscroll(self, autoscroll):
        """Autoscroll will 'right justify' text from the cursor if set True,
        otherwise it will 'left justify' the text.
        """
        if autoscroll:
            self.displaymode |= LCD_ENTRYSHIFTINCREMENT
        else:
            self.displaymode &= ~LCD_ENTRYSHIFTINCREMENT
        self.write8(LCD_ENTRYMODESET | self.displaymode)

    def message(self, text):
        """Write text to display.  Note that text can include newlines."""
        line = 0
        # Iterate through each character.
        for char in text:
            # Advance to next line if character is a new line.
            if char == '\n':
                line += 1
                # Move to left or right side depending on text direction.
                col = 0 if self.displaymode & LCD_ENTRYLEFT > 0 else self._cols-1
                self.set_cursor(col, line)
            # Write the character to the display.
            else:
                self.write8(ord(char), True)

    def set_backlight(self, backlight):
        """Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.
        """
        if self._backlight is not None:
            if self._pwm_enabled:
                self._pwm.set_duty_cycle(self._backlight, self._pwm_duty_cycle(backlight))
            else:
                self._gpio.output(self._backlight, self._blpol if backlight else not self._blpol)

    def write8(self, value, char_mode=False):
        """Write 8-bit value in character or data mode.  Value should be an int
        value from 0-255, and char_mode is True if character data or False if
        non-character data (default).
        """
        # One millisecond delay to prevent writing too quickly.
        self._delay_microseconds(1000)
        # Set character / data bit.
        self._gpio.output(self._rs, char_mode)
        # Write upper 4 bits.
        self._gpio.output_pins({ self._d4: ((value >> 4) & 1) > 0,
                                 self._d5: ((value >> 5) & 1) > 0,
                                 self._d6: ((value >> 6) & 1) > 0,
                                 self._d7: ((value >> 7) & 1) > 0 })
        self._pulse_enable()
        # Write lower 4 bits.
        self._gpio.output_pins({ self._d4: (value        & 1) > 0,
                                 self._d5: ((value >> 1) & 1) > 0,
                                 self._d6: ((value >> 2) & 1) > 0,
                                 self._d7: ((value >> 3) & 1) > 0 })
        self._pulse_enable()

    def create_char(self, location, pattern):
        """Fill one of the first 8 CGRAM locations with custom characters.
        The location parameter should be between 0 and 7 and pattern should
        provide an array of 8 bytes containing the pattern. E.g. you can easyly
        design your custom character at http://www.quinapalus.com/hd44780udg.html
        To show your custom character use eg. lcd.message('\x01')
        """
        # only position 0..7 are allowed
        location &= 0x7
        self.write8(LCD_SETCGRAMADDR | (location << 3))
        for i in range(8):
            self.write8(pattern[i], char_mode=True)

    def _delay_microseconds(self, microseconds):
        # Busy wait in loop because delays are generally very short (few microseconds).
        end = time.time() + (microseconds/1000000.0)
        while time.time() < end:
            pass

    def _pulse_enable(self):
        # Pulse the clock enable line off, on, off to send command.
        self._gpio.output(self._en, False)
        self._delay_microseconds(1)       # 1 microsecond pause - enable pulse must be > 450ns
        self._gpio.output(self._en, True)
        self._delay_microseconds(1)       # 1 microsecond pause - enable pulse must be > 450ns
        self._gpio.output(self._en, False)
        self._delay_microseconds(1)       # commands need > 37us to settle

    def _pwm_duty_cycle(self, intensity):
        # Convert intensity value of 0.0 to 1.0 to a duty cycle of 0.0 to 100.0
        intensity = 100.0*intensity
        # Invert polarity if required.
        if not self._blpol:
            intensity = 100.0-intensity
        return intensity


class Adafruit_RGBCharLCD(Adafruit_CharLCD):
    """Class to represent and interact with an HD44780 character LCD display with
    an RGB backlight."""

    def __init__(self, rs, en, d4, d5, d6, d7, cols, lines, red, green, blue,
                 gpio=GPIO.get_platform_gpio(), 
                 invert_polarity=True,
                 enable_pwm=False,
                 pwm=PWM.get_platform_pwm(),
                 initial_color=(1.0, 1.0, 1.0)):
        """Initialize the LCD with RGB backlight.  RS, EN, and D4...D7 parameters 
        should be the pins connected to the LCD RS, clock enable, and data line 
        4 through 7 connections. The LCD will be used in its 4-bit mode so these 
        6 lines are the only ones required to use the LCD.  You must also pass in
        the number of columns and lines on the LCD.

        The red, green, and blue parameters define the pins which are connected
        to the appropriate backlight LEDs.  The invert_polarity parameter is a
        boolean that controls if the LEDs are on with a LOW or HIGH signal.  By
        default invert_polarity is True, i.e. the backlight LEDs are on with a
        low signal.  If you want to enable PWM on the backlight LEDs (for finer
        control of colors) and the hardware supports PWM on the provided pins,
        set enable_pwm to True.  Finally you can set an explicit initial backlight
        color with the initial_color parameter.  The default initial color is
        white (all LEDs lit).

        You can optionally pass in an explicit GPIO class,
        for example if you want to use an MCP230xx GPIO extender.  If you don't
        pass in an GPIO instance, the default GPIO for the running platform will
        be used.
        """
        super(Adafruit_RGBCharLCD, self).__init__(rs, en, d4, d5, d6, d7,
                                                  cols,
                                                  lines, 
                                                  enable_pwm=enable_pwm,
                                                  backlight=None,
                                                  invert_polarity=invert_polarity,
                                                  gpio=gpio, 
                                                  pwm=pwm)
        self._red = red
        self._green = green
        self._blue = blue
        # Setup backlight pins.
        if enable_pwm:
            # Determine initial backlight duty cycles.
            rdc, gdc, bdc = self._rgb_to_duty_cycle(initial_color)
            pwm.start(red, rdc)
            pwm.start(green, gdc)
            pwm.start(blue, bdc)
        else:
            gpio.setup(red, GPIO.OUT)
            gpio.setup(green, GPIO.OUT)
            gpio.setup(blue, GPIO.OUT)
            self._gpio.output_pins(self._rgb_to_pins(initial_color))

    def _rgb_to_duty_cycle(self, rgb):
        # Convert tuple of RGB 0-1 values to tuple of duty cycles (0-100).
        red, green, blue = rgb
        # Clamp colors between 0.0 and 1.0
        red = max(0.0, min(1.0, red))
        green = max(0.0, min(1.0, green))
        blue = max(0.0, min(1.0, blue))
        return (self._pwm_duty_cycle(red), 
                self._pwm_duty_cycle(green),
                self._pwm_duty_cycle(blue))

    def _rgb_to_pins(self, rgb):
        # Convert tuple of RGB 0-1 values to dict of pin values.
        red, green, blue = rgb
        return { self._red:   self._blpol if red else not self._blpol,
                 self._green: self._blpol if green else not self._blpol,
                 self._blue:  self._blpol if blue else not self._blpol }

    def set_color(self, red, green, blue):
        """Set backlight color to provided red, green, and blue values.  If PWM
        is enabled then color components can be values from 0.0 to 1.0, otherwise
        components should be zero for off and non-zero for on.
        """
        if self._pwm_enabled:
            # Set duty cycle of PWM pins.
            rdc, gdc, bdc = self._rgb_to_duty_cycle((red, green, blue))
            self._pwm.set_duty_cycle(self._red, rdc)
            self._pwm.set_duty_cycle(self._green, gdc)
            self._pwm.set_duty_cycle(self._blue, bdc)
        else:
            # Set appropriate backlight pins based on polarity and enabled colors.
            self._gpio.output_pins({self._red:   self._blpol if red else not self._blpol,
                                    self._green: self._blpol if green else not self._blpol,
                                    self._blue:  self._blpol if blue else not self._blpol })

    def set_backlight(self, backlight):
        """Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.  On an RGB display this
        function will set the backlight to all white.
        """
        self.set_color(backlight, backlight, backlight)



class Adafruit_CharLCDPlate(Adafruit_RGBCharLCD):
    """Class to represent and interact with an Adafruit Raspberry Pi character
    LCD plate."""

    def __init__(self, address=0x20, busnum=I2C.get_default_bus(), cols=16, lines=2):
        """Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        """
        # Configure MCP23017 device.
        self._mcp = MCP.MCP23017(address=address, busnum=busnum)
        # Set LCD R/W pin to low for writing only.
        self._mcp.setup(LCD_PLATE_RW, GPIO.OUT)
        self._mcp.output(LCD_PLATE_RW, GPIO.LOW)
        # Set buttons as inputs with pull-ups enabled.
        for button in (SELECT, RIGHT, DOWN, UP, LEFT):
            self._mcp.setup(button, GPIO.IN)
            self._mcp.pullup(button, True)
        # Initialize LCD (with no PWM support).
        super(Adafruit_CharLCDPlate, self).__init__(LCD_PLATE_RS, LCD_PLATE_EN,
            LCD_PLATE_D4, LCD_PLATE_D5, LCD_PLATE_D6, LCD_PLATE_D7, cols, lines,
            LCD_PLATE_RED, LCD_PLATE_GREEN, LCD_PLATE_BLUE, enable_pwm=False, 
            gpio=self._mcp)

    def is_pressed(self, button):
        """Return True if the provided button is pressed, False otherwise."""
        if button not in set((SELECT, RIGHT, DOWN, UP, LEFT)):
            raise ValueError('Unknown button, must be SELECT, RIGHT, DOWN, UP, or LEFT.')
        return self._mcp.input(button) == GPIO.LOW
    

class Adafruit_CharLCDBackpack(Adafruit_CharLCD):
    """Class to represent and interact with an Adafruit I2C / SPI
    LCD backpack using I2C."""
    
    def __init__(self, address=0x20, busnum=I2C.get_default_bus(), cols=16, lines=2):
        """Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        """
        # Configure the MCP23008 device.
        self._mcp = MCP.MCP23008(address=address, busnum=busnum)
        # Initialize LCD (with no PWM support).
        super(Adafruit_CharLCDBackpack, self).__init__(LCD_BACKPACK_RS, LCD_BACKPACK_EN,
            LCD_BACKPACK_D4, LCD_BACKPACK_D5, LCD_BACKPACK_D6, LCD_BACKPACK_D7,
            cols, lines, LCD_BACKPACK_LITE, enable_pwm=False, gpio=self._mcp)0000000000000000000000000000000000000000 c126e6b673074c12a03f4bd36afb2fe40272341e pi <pi@raspberrypi.(none)> 1543162861 +0000	clone: from https://github.com/adafruit/Adafruit_Python_CharLCD.git
0000000000000000000000000000000000000000 c126e6b673074c12a03f4bd36afb2fe40272341e pi <pi@raspberrypi.(none)> 1543162861 +0000	clone: from https://github.com/adafruit/Adafruit_Python_CharLCD.git
0000000000000000000000000000000000000000 c126e6b673074c12a03f4bd36afb2fe40272341e pi <pi@raspberrypi.(none)> 1543162861 +0000	clone: from https://github.com/adafruit/Adafruit_Python_CharLCD.git
Unnamed repository; edit this file 'description' to name the repository.
ref: refs/remotes/origin/master
c126e6b673074c12a03f4bd36afb2fe40272341e
DIRC      [úËí&VM,[úËí&VM,  ³ \  ¤  è  è  
lcD²õ¤¼Šı9*wYÃ^^¨¢ÔŞâ .github/ISSUE_TEMPLATE.md [úËí&VM,[úËí&VM,  ³ ]  ¤  è  è  ‡{d¸bÀ^nö˜"ş¾3ìZ  .github/PULL_REQUEST_TEMPLATE.md  [úËí&VM,[úËí&VM,  ³ ^  ¤  è  è   *‰3nbn²ÓYTù©-4ŠãC¦Î 
.gitignore        [úËí&VM,[úËí&VM,  ³ `  í  è  è  QQ¹ y•L4u_‡6û•”bdÎ $Adafruit_CharLCD/Adafruit_CharLCD.py      [úËí&VM,[úËí&VM,  ³ a  ¤  è  è    Ji¢EW9'xÃ›‘zÒçıôöRù Adafruit_CharLCD/__init__.py      [úËí&VM,[úËí&VM,  ³ b  ¤  è  è  =5£]2½V™lĞ|-—’À@·w  LICENSE   [úËí&VM,[úËí&VM,  ³ c  ¤  è  è  `×¥4r„E ,˜û7mn¹(œ 	README.md [úËí&VM,[úËí&VM,  ³ e  í  è  è  2§àç³cşí“8eüìQù÷ examples/char_lcd.py      [úËí&VM,[úËí&VM,  ³ f  í  è  è  ¸<$”‘€bS$5V—¶Wç f` examples/char_lcd_backpack.py     [úËí&VM,[úËí&VM,  ³ g  í  è  è  bX¸×¸—³%WE¬—™Á8†Ñ examples/char_lcd_mcp.py  [úËí&VM,[úËí&VM,  ³ h  í  è  è  T¾|ÍÖH†Á­»ùıì÷U«î examples/char_lcd_plate.py        [úËí&VM,[úËí&VM,  ³ i  í  è  è  ò1*Mh{9‰&&¼{¬ø´ examples/char_lcd_rgb.py  [úËí&îã[úËí&îã  ³ j  í  è  è  	oÂ±±õºğÉÏJ¹ŸËùDÍo? examples/char_lcd_rgb_pwm.py      [úËí&îã[úËí&îã  ³ k  ¤  è  è  (\#êš+~½íñ‚>Ò†¯{Ïª­ ez_setup.py       [úËí&îã[úËí&îã  ³ l  ¤  è  è  (\‚ô…kiïxf	„áºêOĞÍ setup.py  TREE   „ 15 3
1^¡íæÖ†ıY»¾BhR›.github 2 0
Ğ)½
8W"‘gÔ–Ì}yÍ¯w£sexamples 6 0
›ÜclO½°ç;ğøÄ–uNŠ­Adafruit_CharLCD 2 0
yĞ­ñ‰+<_ÁOá×èSídŞqAöÚë§º=Ğ9'28²l—wÌ[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = https://github.com/adafruit/Adafruit_Python_CharLCD.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "master"]
	remote = origin
	merge = refs/heads/master
# pack-refs with: peeled fully-peeled 
c126e6b673074c12a03f4bd36afb2fe40272341e refs/remotes/origin/master
PACK      x—xœm»nÃ0Ew‘ÎMEëaŠLm‡ô
R¢#~U‘†ü}UÙ: ///˜“:+ª³­(ç;k­r±ëXĞŠê™Ä£ôÍFI–ƒ%£‡>hè‰H‚wº·½	ÔEa§ñáÆ{#ŒÄÚ+6ÆJkZ…ˆ‘-‡–„uÄĞPÉ—5Áiœkß(Ş)ÒŞÒ(Ó¯|œşÔı"ù°‚*TÚ8xVF©&¬ó<æ,	ŞÇüQËšd›îÇó˜/…÷ÕğÏYó)é,°•i‚$ßEntCZgTó–r[——±_LáºÕjŠ±rİÊ¶­©~¥2?v?:«k•xœKÂ Eç¬‚hâã“ãVpMMmK(èêeîàNÎéĞ0A/ ç’ñÌL®xŸ`ŠI¢ªÒ°vıd¹ÚgÌÖH Œ“ƒ³‘¥„k_œ5J>mMgéhë±o«¾-èÓñ}Ëc¯²Î+ú]›¡$Šƒ>‘'Ry[–Wà¸’RPô~Ôºµ‘<2’ä¹©aM””xœMJ1„÷9Eï…Gşc@‚â	ÜK~zx3“éQŸ§7^ÁZÔGÅr•9…\cŠe‰¨lò©>zm‹.R—ı"—€Yô4pg@Ælg½˜êjN1‡R”A‰YU[ŒA%ÒÉ·6à½íwx¥—¶&xâÿ¬R™àRÚveƒÊy­áAN‰I7bÆÅ}C¿Ïïtê@ûÁi]ãDø"¾ş|Èg‡kbúD ­·ÁñíÙXË–xœ‹AjÃ@ ï~…>Ğ kW»6”Ò@ó€~@Ñj©ÁG>ä÷q¿ËÀŒ¯fPUˆÉZµ>Q¯FÜ!ÖšCeä^RÉÚ,²ÚÍCÌ%i«Ä¬mŸ

µ‚DÊ•j*Lµcldó¿y…ßùö„ópšGOßåûeĞ=t¾ )†SHğ±Ùë4¸Û[ss,~¿lWX¶q„Õî›=Ü¦e·İL3Ÿxœ‹[
Â0 ÿ{Š½€’M6‚ˆ¢ ğÛdƒk¥n?¼½õ
şÌÀè,}rÕï¤FCÁõ)fCÑ—jÉqÀÁ¹Ø½x–§†«5Œ)‰Ç@BÖf›mäØ3ù\99[:^ô>Íp›8·Óô`Øé*‡JËkØæiÜR —õéÖ:6Uùkî¥À¥éu ½ß‹€Êøz°ÊÕÍHD’xœA
1ïyÅÜ…%“Ílf@DPğ~`ÜDèFb<ìï_°]ĞP­¦4^ˆd¢YƒN-&ÖÆ‰˜[/#I¼zóÒš–1‰$"Ç‘#‡#†à#+
^¼r`Åè§İK…sYV8æCy(l[û_Å<w0Ìå¹ô"#{†í1>ské¯³9åù¶”šàµv…b~wï\ó*HGšxœ‹QjÃ0DÿuŠı/ÉZËY(!4=B/°Ò®ˆ ¶Œ+|ûªWÈ|<˜ÇLÛUÁùL1*yr£äiòD"‰»Æœ)I˜Eg6ŞumàÆKbŠVGÓØè4xV²V"ešâÌ†ö¨;üÔõ„ïr¯O†ÏÖËíRRCªËæyö¶Çt»”Öô­³ù:–^ºÿ–º¯,Û¹X´±pãÁü[Mn‘xœKj1D÷:EïcŒ>­Ï€	ç Yø­é6Ä#3ÓÆñí#ç©EÁ{P”®"²/‚x²ìc¶èÃt®‘|AW†‹"‘QØÜh•E!‹w…‰j˜j)<¹J¡Æ˜‘¢ÃÊSÉÎºë¥¯pêË>Û±tÀÇ«¸ÍCìç~}‡É¦œ¬ÍğfGÌ°×¦*ÿ›¯çø] À¹ıÈ¶ƒÇ¥©l7š”êÚá¶½ù“fN¹šxœ¥ŒÍJÄ@„ïyŠf=¯öüôü€ˆ'OëCÌ¤{4ìÄÙ	˜·7‹øBQUÕ›0êÂ‘¼%dm’‹Æ¹0ydSô):§í°¦&×Ñ»hYTÖ!*äœÑ;ÇÁ‡1˜Ñ¨C}#INÅ†Œ£cu&çÓÑÌÚ«Å)ÒÖ?kƒË´~º$Ş§¼µIç;~éãUú(K*4ÁÂ	që²L½Ë¿N†wië6ÏĞäk“[‡EPZ]`¯õ6=•éûÜ÷µÃ‘à~ Ÿböšxœ¥ÌM
ƒ0@á}N‘T&æJ)tİC$™±´‘©Ş¾ö…·z‹¯U"ĞèµU°—Áx©RP[@LÁ[	ÚÓ+¶„JïÆ½5^!‰Ø;G  ck:«µ4àLRœ±°µ±TşµQåÏ°hšøõ(eÍ÷m¥ºvïRi™î•Û¸Å.•ùÆ…ÒÂ-…âp ì¼sn?ãoŠyçíXÊûM}xœÍJÅ0…÷}ŠáºV“L~ADĞ­ñ¦ÉäŞBÓÔ4õé­>€›çã|œŞ˜Á2*&ÙYXX&Xy-ËÑ)ƒÖ‰¤‡•/ŒD.	NÑÃZ¹À•2£MNºQF™mÒño¯“Æ[9FŒÙ)²™|ÖŒ†0:géPeŒíıR¼Öå¦Ç:Üõ£<üDšânb-÷ µV> –×B1´L½ó¿äá™Û™aİç¿í¼u¸’r«f*¼ğo·…¶ã`^¸ÔwŞ`_öœ¦²ÖÖ¡P¿œ~ş ²Î¼},Cm&™xœŒMjÃ0÷:Å»@ƒşeA	=@³ééScğ³Œ,‡’Ó×Ğt93£äa4’‰5x!=’‹Ğ“U!Ô´3ŞGe’[êX9eŒE¢ä):X"&£µ»ûT¸«¬ª/6‹tŒGëôyÌ/ºaÅ;½/']øêÇ7§y¹äÆWRÖjœ4–Ş¤‘Rœ–ç1ğÿƒø·çÙë±£ĞÌ[ëƒ8ÕŞ˜ğ“x[°‹_¼R|•xœ‹MKÄ0E÷ı\«ùn"Jg©àÂ}Iß{™	´“1MıõVÄ•;7î¹ç¶ÊÉöA$N¨"	çÉ–Æ")ëI›~JŞu—XùÜ I½ÒÒ¥UM(ƒeÁ¨¥ˆ}L‘ƒ‰¿¾7^ú5¥à8x1ÚˆBR’†r:M½¦.níT*¼–óòPæwm/ßAwpƒe¹i”PV%àZx!º.¹5ş×¹{æzd¸ló•ß6^\YHµ,PÕ|,”ùó6¯ëÆ£ÙıòÎ€•cãO±ş¨Sİr‡=‡—yß¡•?Ã@uİxœ­ÁJÄ0†ï}Š¹Û¤MÛ­ˆ¸ì^ešL¶6)ÉDpßÉ§ğÅ,¸
¢GOÿÇÿó1‰À6]/UİK£Èê
h·F)’ªÑ¦j¶¦Vİ`·m±`$Ï`¥]UË¶¯ê¶©3hÙ7$H×R
­;´H½Â3!Âc0ÑŞßèOnšpÎnâ'¹»\ãè¼Yb¸©*!k©Ú®„¢Ğa3ıÏZñ^t$dzÖ#F°1Ì°3hcvü¼_£ûıá8­8üE±K°ç™8#ó’®ËòäxÌÃf•-ñR)¿»Ç×õşk¢t)eJ¥ú©‘½f<¤1äÉÀ@Sğ§¿@O˜ÒÇ€—¯”xœMJ1„÷9Eƒk5édò"‚nİyNÒí˜yyf2oo\x7U|UÔèÌ@\%SœÅä\S$„°ÙÅD’eñI¸¨u¾*:„’ª.ÁùÈÕh‹dbÆXÓ‚)XIR#şñIÚj‡ÎOZ²³uÍE|´6cò’UtKëğÑ®ßğ¶¾¶àiLóò+u-3x(mãŒC­Ñ'¸×Ak5Ó}ƒÿUVïÜ?nç¶Aç¯“w¤·.ÜÛVÏãq§cÎ+µóüXa4(i0”ó,êT&rü aqië”xœ­±jÄ0D{ÅöáI–-	#Eª4ùƒõj…–uHëÏCÚ”©fx3#pFQ“M°Ö%MÉ979íÙú€iIÓÓğÀÆ»@ŠI9G!*rvöµj¿Ãd‚SHÑ›Ykƒ•[İâÑáÖyÁ.÷ë¯÷’K©KŞ2ïê!Æ^#?ƒ¶zœ¼WÁÀ“2JTKÉ"ü]Ã¨1
Cáó^©Ğñ“.µ ­ØÎ­y?³×·ûû	ñ—ğOÁòØ¸ÿ`Gÿƒ¾Œ5næ›xœ½NÄ0„{?ÅJÔw¬gKîJè FşÙ%‘ò‡qŠ{{LÁĞŒ4£ofja†ìâàƒô]²D^D‡†ŒP“µäYº˜­6j…×
ƒr/Cö^QÃ™ŒakMÒGq˜´§ş'LÖuAH¤sÜ'×À€9ºrš­ØèQ…£[·m½Áuºls€‡ÚÌÓ¯ä)µàœ¶å´E×64œÚ;ª–.S­ü¯²zåòÉ°ó…¿ş®pg@Ê¶À:¥1÷{¨i<i¥Ş÷*ÃsR©~\ÆP^.×ó~ûˆcdÀxœ¥Ë
Â0÷ıŠì…çM"J]ºu-ircöAš,ú÷üW†a8µ ’hë|Ò2( Çc†	Ê2JÃ$‡¨¸èV_p®ÄŠÄlÔÉFç8 :‚¨„åôÜî|«ãRÈœÃ9ÿöÚ6,—‚ëg§ï\Ç6Ğ°LÂ3ZI	’œØq£;è”kÅİs¾"¹EŸJËõÕ¾<ú;]÷/EMÊ“xœ‹ÁjÃ0DïúŠ½ÂÆke%(¥ĞÒ[¡‡BÏkíŠˆØ–qU’ü}Õ_èÌ¦ífNBˆ†˜£÷Ù'ñœtPîHDn“İÖy’É“*Ê<!fñäÇtä$(HSÔÌ'?í\wø¬ë^ËK[/ÏĞ’º8¤º<ÁqDEFxÀ×íRZ³İ[¹ÁÇ×;ØM–m6h®u¿Àµ´3Œ0—Õ@Ë÷6Ëıà~ËOĞ˜xœ‹KjÄ0D÷:EïF²e} Á	9Aö¡[İÆÛ2Šfnå
©ÅƒzEµ*Ö˜`u¼ÆÙ‘MšD„uò×‘µI³ÌnDRV9°'™b—´’ëYöè¢·LšB\ÑŒZ…ßm+>Êù€·üZv„çÖËË8§.†T«çFï&xÒ=ªÛ#·&ÿ:«÷|‡´aıÜ×äÇµ´ş¤R«¤Ë²À•Ï¯AıÆR‚™xœ‹K
Â0EçYÅ›%æÓ—€ˆZÁ‰‚ˆÈç+­‘š‚îŞ¸ïàÀ9pËDÑkgœt‚4
…Q¤¤¥JÈ­áˆFq+„eO7Ñ£@k½	Ê;Š2qµ”‰¨õ^h“DŠ©EïQ¢¹¹Üò×üøÀ¾ïòà`Uªl~ˆ}¨¡	y\ÃRqm¥0°àu¬Ö±/…ş:³m¼Ï¯§îôvãs (æÁå°ƒc·oØKÕ•xœÍJ1„ïyŠ¾«Ëä?EDEO‚ˆà¹“ô¸‘™d˜ÉàîÛ›}ëPPEµ•jÉZëÜ;+<©Qx®y´#%#ƒJÂ¶àJ¥Aò»($….‘Ğ£wJ…AiC
µv@Épo§ºÂg-xÎOuB8¶®–rìàë|\Ú[Ã…‚›¡‹u:çÖè_eö’ÏöoøÍí¥–»÷¯7øx}„”·eÂË-`I€égßĞçe"¸NöwÛıÄQU7’xœ‹Í
Â0„ïyŠ½%i²M"J{ôè$»	ôAßŞø
ÌóÁ”#F0œ’ãŞ:ì:dM}HÜZ¥3¦Ê±‘
SÇb÷G\ ÄĞ2ÊVYƒ¤]ˆ©Z£ôŠ’JdPËÖ’şU¦í€Ç¶~`ÌÃ6{8—:®¿àL4´-PF¢³XN²JTºäRâ_gqc†àŸ™€&À}!¾ı²Ï±_ ìH¹–xœ‹K
Â0 ÷=Å»€ååÓ¼<Q¬K7¢È¶)%.¼½ñ
nf`ê–x´:T9³l½±Ò+‘Hjğ9S`e²éV·¥¥‚d6$”g¯cv„2DiE
	­“:;&¥±ìÜ»>Ë÷²|`œÎåå`_›ˆSh¡e>€Ğ8°Q8HØ!!v­ÎS­é¯¹{¬ÑÕ·Ëi¼^ú9~ÕÑDß”xœ‹K
1D÷9Eï™ü&QtéÒ´If&!Aoo¼‚µ(ê=¨V™Ğ„àÔˆé!=YV>INìb°R&ûÔ?-
U^x›FZJ¬H&G^!¢NÑ’ó½½Ú3W¸çõ×é’g‚CëpúUœBû—#H3Xg¤=ì†Ñí2µÆÅ9FOªp»\¡ÌÔ¶W)¹6 5Â’+¿i)3o{ñ5•PT–xœŒK
1D÷9Eï…!Éä"‚nÜ{NO7æ#C\x{#ŞÀZÔ+ªÚÎFÖ†]ÎÉ°¸ “$R1É»rˆ½POÜymŠÍ(E¼7äÉ[‰:±%ŒG)vB.6’ÂW{l;Ü·õ×zÙf„cëáüµ©RmË	ŒÓ>Z7úİ¥:]jkü×XİÖÚ*Îğ{Ô•ôF’•xœÌK
1Ğ}NÑP:	ˆºqï2I‹3Ú…·7âÜÔƒ*İ˜Á‡©‘ÄSAÌôhÍGG™¨$?cj$S^úìÜûú†«\ú\à¨£œ¿Ñ¤Ø×¾œÀzÑæèìğ€h†.¢ÊÍm•2ÃïÅ| ¥Ì7œ¡xœ340031QğuqõğqqÕËMaHvÙôuÉ®¿–Zå‘‡ãâV,ºrï‘!Dq@¨O|k`¨kpŠê¹Iâ„ò¾ÍP’ÿ·¯ßøT  à$ˆ¼¦xœuVMoÛ8½ûWÌ­©ÛÀv±‡ÜÒDm$±a{·-„–(›µDªüHêß7CÙQì%±(Î¼7óæCë²{:¸Dµóä:mİ’²dBHšœåß—•ª}2‘‡¸ÃQc6^ùyİ¹`¢ó‡)ÑÚLÛy÷¨)î4…NëŠ\KÁ5)ØuVAãäÑè'¹U»¦qO¹M¦Ò±: ±•®ma½K›F‡s‘o…¨»@#üeM¥×JŞ±?a}1Mh<¾vd]¤ÄÏ&~I›ü6H¤¯ƒø]FïïMÇc¢HU±—õ”}jq/Ò.Æîb6ËSÕ'i
ê©°§ŸpÃ‘g·CLzÚà0¸VÇ0Á¾Ã©ó{ şÕ®¦L‚ZeT"{AH€.<µ°"E}®„µ7VôÉ4µœ£ŸÉ”û†+µ@;İtT{&zŒH¼$k"kù"_p©à£ÕÊFÉİŞº'K•®%aÆŠ“ÒUš©Ö]9†/’©ù½×™k¶‚Ëÿ°Vy$ÀÄİqœğ¬qš%Ús)Š	µhTC )õ„¡€-œLÅ¤ZD…»\I¬ğb«SÓ°åN—{RÈš«sK¹±vœü¬¬O–vê‘½ƒw& :]AéÔD6…·L×HBŞC²BÜÄxP—b…´¨Ì}vŒ¦õsÿÍ–*tíÑó\¹™=°Qğ/‡u!Äuf€+‡^!ÕuÍa<FÇMâ±Ú¹RúY€D·ó±ğŞùºw¨ª*5š¬jø”ó¨ù]VRÁ†ÄIåJcº ƒBIZÓ ¹íœ»#û“Š³,¡óânY\^ßƒ(˜©$òäE¬-ˆ‡ÀÀ™€A#ı®zeHŠ€ƒ;’,åfè*×!ü=t¦{ ¬kÎi™Êÿá)nëœô®*ã±f ŸÓ;”#g9$Î¿d¹Ò?“ŠèlÔ’ç0ÙÏÆ)_ÉzNk‰$ÖG>ß’*ÍÆF†¶şµ·h†|˜¡Ş“)DñÔ5i»Ím”ıâqt)²ã,›¶.mwÌ±Ç‹î¸Í³/íM‡Õ„é1ôkiéA‹a+T¸ÄXÇ6³PÚBÂşÔ¨½> T<Õ%Œö€ÆñÆ¥pŠ¬÷Jç-ôo®!®š_¥†²a'àÿÎx‚Œpì%o_LğÙña"&'óÉÉ|ÆEŞ‹è¼Åvc]hë\Õƒô¡!	7§1Ğ· r™Wì`,¾Š’ÎV_Øı,Ú`ÁúEZó€7öÕ&­nò âmÌá{5VõVqZ§£ï(ÉVa.èFÇœ¼ÓJÎÛ•áÙ5×E¿íŸÑ+•i‚ìàE£"CÌğ]áó’,WKgfŠmñbIÇÉ‰Aõ¾¶8‡î_­ÜS L6&Ÿÿú3?ß©’æ«o§gËéûâñu¿*–kZÜ^®?Í—w³ù¢X^®oî?Ãëêûj]ÜÑ—bYŒÇÂ:ä`„şh9ãqÿĞåÃIúÀc¼?üğ|úíûúËüÿËÕÍü~ !ƒƒj«ßÎÜsHS6©Êã÷pdÄ5ØÉ‡Tô
Sn ”b¹œ/é®X]~.fÅ·«b±fĞõòòªXõØ~kBT/4J©R©_|[ä¯¬3,0|åÃİ«bTå.×§ó§¥È²ÿx|{³Zc\/–sBf+úXÜÎ¿û7²d›ÕºxœKÉ,.ÑçJ*ÍÌIáÒÒKMO×ÍÌKË2*“¹ŠSKJJòósŠuµ¸ +øç°xœK+ÊÏUĞsLIL+*Í,‰wÎH,òqvQÈÌ-È/*QĞâ ½{
ò»£	xí\mSI’şÎ¯¨³#ÆâVÖ ãsœ&KÂ(!Äp»E#µ w$µ®[2fgö~û=OfuUuK²=ÌÜ·UØÕKV¾UVfV–_šVºxÊ’û‡¥©vÍÁŞş¡9G“l•,Mw>^åË,‰ó—ædµ|H³÷fÎŸL;i¥Óhç%Ú¯âl–äy’ÎM’›‡8‹ïÌ}Í—ñ¸n&Y›tbFQv×Í25æ/â,Ç„ôn%ód~o"3" ‡±Ë ÊÓÉò1Êb›(ÏÓQ¢§£Õ,/£%Wœ$Ó87µåCl^\Û/ve™qM/™^lŠNó˜€ŒÕÒd1)JƒFÓÕ˜xİÓd–Ø58]8D. ÿU:ˆmİÌÒq2áÏXˆ[¬î¦IşP7ã„ÀïVKŒÌÙ8ŠçœZ~L3“ÇS¢`­Rì1”Q\<–U9[ÒY™š„8MVÙË‚93NÁ:YõoñhÉâ?I§Óô‘Òù8!Õù{ß ½Ñ]ú9’TæéçE‚‰ŠØvåÑtjîbË9,Ì	ª@æê._B’hji&‹V©m(gsİ;Üô;¦{m®ú½Ÿ»íNÛ¼8¹Æ÷usÛœõn#ú'—ƒO¦wjN.?™¿v/ÛuÓù«~çúÚôú@¢{quŞí µ{Ù:¿iw/?š˜yÙ˜óîEw °ƒ`I¬ÛÁÌSsÑé·Î ûäC÷¼;øT¨Óîà’pO{}sb®Núƒnëæü¤o®núW½ëPhğe÷ò´u:ËAë¢Ít~Æs}vr~ÎÅ íä4ô‰¥iõ®>õ»Ïæ¬wŞî ñCØ|8ïèb ­u~Ò½¨›öÉÅÉGbØ7=À!…¨8šÛ³¹æ	ş´İŞ%‰iõ.}|­ƒÖşÀM¾í^wêæ¤ß½&[Nû½’IÆbV Ì¼ì(2]ådƒ!dÜH/ğ1íÎÉ9 AP—€Åîbxc'™Qğf™ÌââKa^†¯º=lmÃŸ;İƒàÇæş‹ÖÕÁ›½/_8¿otu{Á~üØÙ‚­t6Ã>ÌwÎ[íaë¼sÒow¯¯ÎO>ûiš½/{ûÒİïnú—g½‹NÑiŒtH7ÜÿtÑkw®;ƒb€tJ·…+¢èë é~§kßô¯¡gİS7Y€ïïI÷éÍ¥H!€-İÚæÖÇ>t£İî‡kºnt¬w¿Û#:óeöd&Óè^Ù „¨>°”N&İç Ïu6Øq}Ù:[™(³¥»İ)u*­¸¤Ó Ë6è±ÿ¬sµwzZéV\[ÂÕÒdEFEf»ÃÉ!¥ É-OIÑîÒäb6¸zA+ê™jé¸èıìµgMü¥Ş5“‰h·ê»+)f“ÓÕ\N6œ4Ë £wºª«gœÊÑjÜá–î=åìxSš
0=ûÛºuöÑ—ı½vop]]{Oé9úò®ÚĞÓ›L„œ«Ï´C“¥yC6J¿w;„6`CxàMSÃ&Ş«c+Ê¿û‡üıèpWL œ&›Å>…Ø3_Íîà”(H˜ƒAg«|šfÿHÖ³·APİW:´³ê.;ß3Û‡•™ª™:³}TéÔ=d;ßV:•µ¶ó¸ÜùoÁ’}œyşÓ4oƒ¾ıN€nÓ}Îo‰7Í»Üƒ—³„'6f1¸w­ly{æ…¢ìTÕ¹èvÚ½ÛÏ|ßÁÎÍUñ­ü³iÀÖ²Uršæpgg4…ãèÜÙab‡Ôké]£İ÷;ıâÅ‹–ƒVeñn!œKq}x°YŠ>!ZÌYûğğøİø²hU‡àëA ´#ÇñÄ‡pk—Ãa®Ş¤n²¼nbø™cháøßâï1½È)z¦É<Æ»hôË”xó2Çuåè±¿$óÏq¶.à|gÉò©9ÈV[FÆóèn³æi4…ó¹Şı"I›<÷1Àb;LÒl6dsmwóBÄYZ€ÆmãÉx€COŞ~cÏ2ß
 «C’¿Çâ¬BFcú×ğë.Õn6ö±YDÔœG| /~:¦Jÿv‘ÌsG \Ü9¬ş0{¹Õ	n4MG¿@äŒGËHø‹²|ÈÒÕıƒ9¦L t’*ezLÔóE@¯×$ËÜ¾¾ƒ§h †óM„òØ¼U¹Æ0D"OŸğb©B¨Yü?«$S4MF)íŸÒ•™!ô‚Cxj±cÔLID•NW³yNUuE“°H Ju’Kv'æ	p…oÓä,˜’T9~‰¡“P½´$x[pDpu«•æè.)79qAœ,PÑ^s—¦Ó8š;€Ë 0@ˆ‘%Xgw¢9ïİš<¹Ÿ#®À‰p?Ú~µë8€ØŠÑjº\[øs4]ÜÈş1I#nlZĞ®çÀùu±g,¥5‚}PÅ¢£YD9£TP²û!¢‹€ı9Î[i¹Eî$ƒä¤&¡Î"-_A¡ ÈÀ²±„ÈùjA7[|ÜBúŞ"K?'cH®ŒÃj©ŞN?òCÃiÇºÜˆıØ-ï„h¸‹Œ1¹<Mî²>eiwŒãEŒhQ§%²000v«¥ÃZIşYLijã/ÍØSNêÔXo^ ª[bf"N $Y„Šõ`L°¬l.Gê±¨Æ‡Œ[ÙÚ-PÎ â°fÎ<Fğ9DQ'o9÷Uuœ¬h5D´à¤[­PtAkƒğ©»ÛC.H¤$§™‡C6E³ÅHÙ­`›ôĞ˜`º‹dzüe	aÄ´ÊZ‚q:å¥¬+ãaQ¼`(Iv¡ÒÅ¥Ù˜­æ’¼)Ä*Òw´Á4ÓFz½á	YØ¾—æš[ Œm˜Za‘ŸÁÓ³1ä)	'Š?Ü|íQ{×TKëú,lAUÕğ¹“W ¡`xÜaşp@´M§w¥5£5övKÇÑ:>¬Œ±õ¨Úú–­o«­Çl=v­–¿q7²Çw7ıw07ìœ¡îô1–ğ{~}º1¸Ò~7…Çdª¶Ô²ñŞ9s@<s#Ñ¶X-ƒC”šCAàOm³SxeÒÀN]-j˜W_½|ÅîÚº^}°-\+÷!Ñ§o¥_¡åRîâpÃ"à`!½&ŠI®WË§áèi4kk¦a×cIH1Ü°uø…ÁTŞ2„ÀŒWÆÖ‚	Š‘

­á"«‚‘?¤ÍÊNXáÖ:>Ë´Gxñ;ÄVoŞø¹•ßS‚j!rÃ6JUWL¼§,¾GêTâ0¥Ö(«íÜÂ[iÒúDÁoòİÇöú½ˆÖË$XPÅâĞjÂr±¯NÕ`V×¸W·aêFˆB€Bó	¶!â@¼4·d*‚Í¤[–	¥ß6ñÆ3?g‡	¥òÔ‚Ûç
E¦«<™dïóRÎS
ˆŸà°ÙÑ(¨`‹DY8%Ë 	ÙìX¤`ÏãŒ4
V¸$ÈdóT££Í)¦6I2øÆ4şrrèW=Jv%+éNÀ@ŸÏsÛEi.Yq.ô÷8«ã!Şp–Œ²4¡…ã¼öfooO HŠ|¤YE³„‹Óg¦)¼¦=ÿÅÓ« /Ê·È9P!¦¯â¦+em·,<ybµ»Ìùá×Ğ'& ÌäÓ8^0XVôİäø× w<OŒôP™iƒ^‘oúX&¶*]u¿œ×¥R±b*®T,%® ‡;…ßCØñC¿”ïÖñ³l(ş“µÜâ8”m1»›a·y¼D¡IrºAª#¹wòp«›Y(Ÿwıwj87ÿ"&HSı'Öúon'ØóÇbmù§eîu$veÔƒ±cCéÀ³Ãl3rF¼yüTH%ºC¯Ì!Ç¢QÛß*ÖÖñdı<Û4ı‡¦ùßÀxõ.İü*ï*ùò²™±ØLCà±¬ql)óë-äÖ" a•j(8ÕRãÂ›FŒG2‘_Š °Ê,únV9hGéïãÔÚô?È(Ü?Î±J%¿—y4Àõ!4°)à¦ÖZ]NÂö·J%óÖuÊH;‡…Î=x)íßÍ0›v&¿ª³ÿ »fHã§ñd¹íl²ûÃpŒ¨­T•ª^÷¨W^hK‘Õ´\°‘¸ñ[èèİ-æ?ÉÚÑÎ“òá2nÃ‹fh‰€V*ÓDš2¶H¦”´Eey*>”58Î‰rjQeé·¼o`‰´¬L¬·ÈvÒÊR`Í)_Gº0s&ÖÑj™æp9¦S»{}Cy£6ÃÔÌ+EüoH!¢>á•Êb’Ùê»Ãiñ §r
9Åiš=&H  5"ÉœW¢æN[ŠÖ•ïqÜ¾ı×Ä\¾=tÿºİ(%¾oó|½ÁFİ«—ŠDè.3^]wQuh‰Ub˜ÌËıò!²Û€é&­1‰Í<~ï£¤Nl÷±ç(GäÄÛ¢ié8=ø«Ï~†Ô¬®aLMDÊ\GÕÁø3Ó8´İsnIY
²ç½ÅÀ-éò€éúØq¦Ù4¯şkşª›Ú_xƒÃoáÇŞ‡ÚÍÃÓE•2çQ\Î-g)Ê"}(ğFhÆİ¡­øA|+·éààíi¤+2—ÔÑëuÜ¤“6A·½4½†ñ.B3	F»@Qà—Ñ]WXÂ	õ/ÍÆ5²EJÜyÃêúâ¸.î„Êj·Ùt“¡€İ‰¤emÒCÀ±©Ù4œÀæéü5C W¢ùqÙşKëd·€øç‘JÆue“·“I	‹FpÕ%y_$
Y¦€ÄJí5ö ¯.Œê0F¸…Ão¸òaT"	U^ÑÍ!<yÔ¼<*vIÂ“ğµ|’fëŠï†09f*ëlÉ9<¾+G¤0ÃÌÏ–U\şÇÁß’÷Ş2·Ñ1áÕUı ŸCZW½:,ëš¼wrãeïQp?ävö¹\ªq:„ÿ³Ü´À{¶—ub}Ò9”ùëƒ#\2UëÖ/¼ñÂ©½øXGî%Ğåô„šì1‘aNã7ëjŸ`xg¸ÒÃ‘Ç¸–	‘>%®‚?ó*˜’08MîëpGûäa©6„×ûÌ8Ä4zô¨ı¨<Â¥aÔºŒ™&u	Aª põƒË¤CXAuMa†LÉÖ~µñíøğ½©Õ”ù?ıdwÍf—ÆÓß/ĞpmüXšJ âm	ÄÛç€8.8ö Ì?<¯ãÅ
ùW›Gª ­0ò¨|&#•Şe$ÄğûA”yğeF¾ñ ¾ÉHïeoÊ3‘÷(2g9yi>¬r\F8,à¾LÓtó>Šx%›
	n;ïc\˜Êåª§£¦°6ÇR‚ë÷.ºà10ıÖà?µ]ä`jáØ¹?ñA%‚S„Ç—&ı;2'ã²éç-Y@pI§Hj‰¸+jœ¦‚Êõ™p6Ö<â/bn˜”ÀğiÑ¢š»nXL¢×²}ºÉ!S(Ÿ—f?dnÉç×EÂHhÑ²œÈ°
G{AQÅ×0QGÆ®R˜˜õŒ)Tûÿ‘g°Ä²—C1îÈ2oWRkS}9EÑ*1æ9ÉJšê1ÏÂqë€”äŞJ¥LÇ÷ZßÉIõlÄĞ#Ãë##×G¼³.z©˜N°n¨4Ô¶±÷¯®ÅáE+ƒúkeOÌ¢¾Ä«y¦²_¡¬İp±Ôk×â–Êp‡„‘ïX«³êüĞ‚?€¤_ÍÕúÚË&¸fJÑ•8…‚ü
,¸ôş¤G„÷Œr,æÔñ!æV»C¹È†“‘ûr{õ”¯)°jpêûÊ·ÔOşjí´ñû«°ŠË@„9iÖ¬‰;]ü³h.xV¹„Õñ.3÷›ÕYN[¼çÇ Bî…áfışò,ğötS–)ºSTZhí¾µ>ËAÜZ¨å6í3M%IÀpkY·±V å rÜÆB-1ı,er TG© L
u0õÎ×—ä4DL8VâÈBR€G¤cªGBÃÔ°PÇç¶”aÍŠNúåè|û(ÑÖjam$5°«Æ\¡Á	 L«%¥F>z¹8ëÃ“C¤l,ÍÂ¢’‘ÚT”µ¾ŒïÍ×€!øeMÑ£-‡Ñí¤uYÊù2#àJ S©Êrğ,…4Ê²kò]‰LÈy˜¶íeW®ÚŠªîMm~WSŸH$é4ÑªŸ¢ŠaËÜ}˜İºŞ°b3+·‰Ui{!b	*–ç¶VI	M°ƒMB®©Æâáò4Yş³N	»¥uqæ1´i\¿Ûp•¾›ËY¼
¸Cà›¿@8ê|s¸ iÅú†cÇØö‹WÍ¦ÿõ9¨»õ•æmHh{Å5+ßŸƒ”ÓüçY¼áI‹¿>NPï‰u»(‹}ñ­õé1 G<·½
æEZ°ê®§(›rœ“C²ä²y‘”½µ—¦ÍZè„5;x–A^€<ÎÆ#86üçn<:–û;Şl(g[áÉ'ğ£Z´lY“·õ[
Ëm!¾QñÖ³¨Á6¢LVÜ\Œ²ë~sœ®¾y˜(+Ğ´ŞJ“(%~IZ¥d{Ã{ıa¶ÆUÎFYÄı]àwñQšºï 1(ú[{¯÷5p€Äuù/_1‰&¯.ÂÀk¥ŞßÚ¦¥z¦ÁMZ>R]wĞß€Sè†&Ï¢/5ô2‚Ÿ«ãˆö g)Km'=ÁHñe6dG0ÎÆ’ oT£..¾a«H •¡ş*ëcã`‹„P/ƒ•œÈ÷Ù2ã1¥	(V’ß-)Ë†_ibŞcË)Ö.¿Kép›Tã¹urÕ½¯PÁ}'rHTp‰n‚`şáC/lZŞÂ¤™½Ñ â¥°*Ø?®áşxK(ó4kkØÃÙÎA–üİY½ôpWRM'F?@Ëş.Éç¨&ãµ"§ê¸åN€w&Ñ‘»uƒ¹>°‘»zÌä)w¡"s/rÆ¤4Ÿü ÷ŠhÑ¬šwrÃïv*ßP%=LÂú^‹®¶S$¯1m°íÇ!´ùNC˜¿fë¿1É®¶v |cuK¨¯
šVßáKP%>ÒAPâÒ"”O¡jË¬T´ä 	mş¯Úü±½H.W>vEºl“Vàò«Âşİ»÷Ÿ—’bşÄKIƒ{&Æu<Ö‹ò!Ö:sP”à" C£)A¾7…L¢CÂ4¯±¡AY{kë¦b—ÈÁ¯ñ–ç‘W|»)âùı¹»"ûgúQ¾ÀëZäî¯W(Ä3eÃ÷#±ÔCH“œ¿åŒ]4ãefŞÜûr _än•#½ÒÄ ¯mp;D3!ÒÌçÍ}¼°”x¨yP>aºå2w'ç1¦QOròE<BÒµyÌ7mKï¾ËÿP È±Ä(ØÌ±T!ZôÜ“Å|5™ğ¿×àé0KQ·ÊÌs`Ñ¹¸¼ûÛ€#ıïË,9Í*n@™ÎÙûå pCõt’Üóu™>Ú?FÚà30õú¦öd6ZÀãÃ F1°VÈÇşt"RIy®›¬îÿx+n›¹2£¸iåKÉkÚW˜<ÔÏıÛMïAÖi¯m˜€‡|Uœô3²X|jÉG+šZÁ¥Èôõjá<	1ÖI˜`júğ¹n¤\ÿkŞ3×ÍÍUé”ÓA ‚Ş,ƒÅÃyBm‰é^zÔÊƒ‰ ]´(á~JO-Èàš$âæ©øö…` ûJbÃæçeó¯¥6â­ÿ†ç¹NÍˆƒïiã¡sğ÷úÁ7lÍà[åô€xÁÎ’Gëa_ªóuåÑs9Âc½éô#8å’|È—ßpŠº‘H 6l•¾^|0qGï[Ñeû
EÈY6@8özÎ8²Tî…év†¾¨¢Á¯}C…dÈë,b‘ŞÏ,¯èdÜëW7ó_æ¬d.ôCòÓpo·j&˜ÊÙxåÎFGÙVåvY&¡2öÏÎÿM¸xFà®xœÛ=…q/‡xHFª‚¯gˆ‚Ofrj^qª‚£ÉÅ5‘I‘k¢³ïÄI~ùN6dôš\Ëè6ù(£%#×d&&/V…Äœ®ÉÁL@~;“÷ä+L“å™}&ç2»OŞÆì7™Å“O!ÄÃ•+Øß-$Ü1ÈU ´ Æ©x340075UHÎH,ŠÏINÑ+¨dXş@üùæäo'[¤r02ıa}øó»!ª²øÜäÒˆ×9vLß,§îÊ¿fúLæƒmÑ•ä$–¤‚ï«9{ÍC²íàÚİ,?ÿò½ùºú$ºâ¢ô$RC­y¾óª-;ÕÔøåö0U¯ù±‹Òø‚ò\òşüC7~İõáäy¯óOÿt9›ßo “Y…ê€)xœ»ÉØÉ4Á\!)19» ˆõ
*lT¦LlìO
V1›¾-ü¹BZ÷DõM CŠƒ·tx­UMo1=gÅD ‰.°áCŠÄ!%M©m"%R/‘Ùõ‚¯½²½úë;c/,4iÔC¹¬=™÷fæÙ´Îû•5ı¥PırçÖZE-ø²eE)9TV¨0H×Ì°Ôqßæ×j¥8î2p˜‚ïó‡äb0œÂíÃİ=ğ­ã*ã&DQjã `n½_;Qğh¿¹ÊXn*ásLO‰™¥üo)m@¶[rÂu!ÍkÅi¥Pö”˜[sÊG2ÍÆBı›ÁÀ[¸j,CoÉF%	–qc¹–IcË´±Œ½eÉÒ)Vk3˜ ËûÒ	­˜”;9­ÆCXPÚqg´”l‰MG–»KŒ%î÷~h…ı;T¦!«Bá20zVüâkÃÉ6ijò²Hi8ñ,Ñ×÷d	%¼’8]ÅœxåÈÓ–<ù'Ÿ¶£%iò$ƒš_“iD™î”p‚I¢qFÆ_Eº—“p2³J:l“Ü%s`Yf¸µq´*…F–Z|8ítß2Üé
RÔhĞ¨³$…LSO4Í1 `g–â´à=$ä3ê‘ƒªŠÙĞãÕCÔòp-hçeGıDÊ$¶?%İ	âëùAr¾B=×ßIıö :?:¯{©ËauĞCÏ—0£:<Ó#”Ã™¹I£À²'~q½î´¿r)õ³Úh#³ó¶üÉ„ƒ1ju˜Ùˆ.il%çeg¼Ç5/4ØµŞĞ{@…§•±ï8¥N%g‡DkòY„ÃÎ“©x°Àñ¸%èAZb)/û7HïğØgŠüíÑét‡öE£uÃ¤­«
Àµš”ÒE&¾uÑ`è-èK»ÓvíÏgĞ~ôAí“AÕÇİˆ.³@¡ƒajÅ½¢je|’\uö~İËèì¨ŸƒxÜÎüäõ+_x8£ÿ’Œj	—Ò—ì*£¨àƒ0Aç¹´:-ùDˆ7’ÙuôŒ9ÆqŒ9ªÇ+±OˆÕÄP@À÷²y(;(Ú£Ğ„DÜü—ÁşíÇò±[­³åÓåxXWtŠ‡/Åo¦lTç&…#xœuÏJÃ@Æ©ÁrèU
ƒâmL› $/‚_ äÏ4]šî†ÍZğ”WP>„7í3ˆOá»˜lÚº-tnóıvf¾oZ_­×»xò³4@Î_`H€qğĞôEğ?œšox•ëz{óaJ(„ŒIüÌ}A½Ñ“0ñ–5 ËhÃ#bB2˜‘x"€"F áÄ§qİY]—·Y!s’•+Ë;FfV{óRe±%oE¶"õj©§Hv-õéº–œ©ëJ)(ƒ&Òß ì*ìæ/äát;m¶óCwäK ú­@·³"ªmIÖ3ª{Iú+r¯¦È^9[ÄZ5SE£øl|—ÚAÓØÍÂÓtØ]Å»vºøÖš{‡U'ÈÍ,ALÏ:fï\¿û·;áâ¢yÜøcŞ¢0å‡hxœ;Î÷ˆo‚2kB»ÓDe»‰¹O‹RS ÀVÁŒ+'9%>½(55*bIÊ)M…©±Ø¼‘q£8HÈóqvÑsLIL+*Í,‰:9ŒÙ¼K/ ™˜œŸSš›W¬æå—ÃX©)Ø&ÈrF¦dæÛ‚M..åÍ'™™˜$@Â%™¹©zÅ9©©z¦š`C&ßeµÆ)¹Y‹M– ¨×L™°sxUÛn›@}6_1UÀ%`çÒVêƒcÓ$¹ÈqEnd­ñÚ¬‚YÊ.MÚ¯ïÌuÒâ86f÷Ì™33«ñŞ‡ıRûs‘íç¿t"3kÂg¶ÎS¥Ù
Ä	+X¬yÑpyÊ4÷,±Îe¡aÍtÒ¼k±æVclY”BÏ†èM~L‘»ea€óLhÁRñ›ƒN¸a­b‘•‹L•ÆøJ;Ş¿D×ßéO\p|%×âRi¹ŞhUDáUˆeà.L{.ô]À;^Á>>ñİèş‡Çå)mW.äóÉ¼p­¼¬=ôé¡WQ¶x rÚG¨!í€¢-·9D”@’	ú¹ö@“„µ$q„¸‹CM¾è‡&.¶á1ö_M&J¥şUÂ0–ş&‘OUáçL‰b™ÊBy¦ˆŠë™±ÀÃ`~}«+œrìEõ¾æJ±wìq8‚ïÏ~`w-:DJ9Ï¾çc,jã†Ñ5´o0Ãğ’8{ïälˆßà<‰nC¢ìï¦4
ß!ó>Œ¢«;"=ØMÚHÄReÌùn«æğ~`R?ÜMÙHÜEy18/'zôNÖ¦o½;;Ÿ˜Š·qÖ‡l^j-3PÚŒ­I_x˜ +Ïóé{ä
¥A.ëMøÉÒ’» ù³ve˜³ø1«DW§Ø³j@84ƒnÂ(N\°oxÊcm»€Ó¿İ®kÁ‹Gá7„Ø_jÀ€}×oß^Á·9B¡[˜GWw—†y$Ÿ²Š¡[˜Çç§g¤ÃSjv#5–&/D¦Á®ª6ÔEúqZÂœØm=%çÿ¤(ù«³‘”9NêB–«8‹“¦”T½8áñ#ˆ%BAN}àÏê,eÑàDÖtù:ˆ¥6
5«ÁNUğ)$ÚÇˆ'UÓ7|.MölUıaÔsãuó0b§óòxÔf3dêÎ¯zg3Uê½ŞJpk©S´‚WV]ÿ ÿDDæ„nxœÛÀw…o‚ÃD¯ÓÓX5&ÿcÒä*ÏÈÌIU)*MµâR ‚ÉÊlæ¾ FZ~‘BRiII~Bf”UQ™i
9É)z™ÅñE©ÅÅ©)%Ñ±šU`§²™« €ô%ç¤&ih¢*¼Ç&Îƒ"ğƒÍ K0y²_xœ•SÑnÚ0}ÏWÜ‰@Š(I)é&íhÔUbbª>!“\ÀZ°#;Ğ²¯Ÿ¯§+š(å!¾>¹>œs|Óút±ÓêbÉÅEy¨6R-H_Ø¶,vš‹50óÛ1d¦XV¡‚éä¹ÂróÌªâ •„9Óå•:ÀŒƒT0F¶.p,Â¸`Ùï^À·¥TT|‹ßŒr¶R;^-&†ˆ™&ş 02Ş0fR¬øz§XÅ¥øY¾P¾Bœ ´Àœk„jÃ5i)¹€8)@¹Q¬pÏµ9÷†²­-
b‰m¨¾rõÕW©¾tubêèÚ)0€Ùº®µBK%v»,vH/­À™Q”€Q7I#òvœÎ±¿4Û³ëÅu»Fìõ=dE[¨é²Ú-4l ¡‡”x(ö7DhâAï‹ÀÏôîìù¨MnpÅºÅL»­0£“ƒ’Ï ù„•ŠhøSCÏ&äºÈc4tyÊgV@L„£ÂŒ›0‰ìÑÌ˜.1ã«0ˆû/Çâ´¼òÄ}o¤aÓàgÉ¨6N¢nÚ™iÑÀ–rV–9CÜÍdšá¯‡³ãî$¬o"¬ã¯×«zÖkpò÷ô°ú{_³›Ä»dæç†"•[„%Ó<£°¥ÒV{Ocµ°ûNÔë‡Ğ¯]û2+©«·¨5[c§=OoÚİ€>Ê.ËÎ%µ‘Yè}²ÛyšŞŸIç9OĞ§¿Ò÷Ù¢3Å=¥ÓéÇ˜=­nò4:Ãkt¦×ï£Ûôşaô»§	¿İ=ü/½¿’*Ã]´µxVmoÛ6şlıŠ[ıÁvçÊ/qœ6@$®ÑH» iW`Ğmi“E…¤ì¦ÅöÛ÷)9r:$-‚út<>|îÈ{iÿ2(,Ó|PÜÙDåA›æ_Å¦È$•&Í×$rº~sAQ"´ˆ¬Ôt9{M»Ô&tõù=E*·Ze¤VdIKı¥ëÄ†Aº)”¶´6©e›ndPœÇb¥ËÔ.f@fLa:‚X®(1Û…U½^v!öNƒÖ³gÏf*ßJm	²%3Ä©I)ûd„-µ°©Êû´Y)Éª¦‘–qŸÖZÊœ–XƒÖ[Ø˜D•YLKÉ>Š|À•V†CŞtü*†D7{pÅ~coĞòG6÷ÂaŸv‰Ô8å~{,ãB•æVæ&µwuìà	PÃ/55—Æ€;"´Út­•Æ=lHÄ¢°2öìk‹ÓÁ`·Û…‘	aÊ¸ü›Gf©Lé] šã&v“­ñCØèŒƒ´Ò:;£!bŞÒÍ©»…şz°¦ÁM"Xb_o¸Ê”Òİ«+Fy‘­Âöyqxa ¿m|>_Aa›
g¶êAÃúãá¶O–eVŒšìn»CƒqÓ pö áèƒLšL 60²¹‚¸`å¶ s®…)–Rë;ºJ95Véºz—§AÅÈÒø„¨Mxõùï4IñiNã©œT#É´Ü¦ïù ²c
^1PÆN',{ù˜å‰—§,yùòè¥“‘	DøôV>%°xâ97xÑ¼£»Ù|Ä¾]H¹P¹¤‹işĞ¿6í=ì\½\¼ì`k[ÖŒ†µÊ‘vª½UÌÜjº·bœj²W±'N5®UµC«W‹Ñ~oí˜Óî·×ş9„£{õZ®RxÄõÙQn¸Ä¤ÕLúõ@iM¿Ù t1òV|£©¨Ú„Š1g¨‘9jÑVfwd
¥«;Ô¢ñğëÄ£ø°ÜãŒ‡U¤pj…4a¤wyjS‘1.­LÑWdşÂ{1Äçã\æ¶¯¦¨ÕUAíúûèW·àãIõ{\ıN«ß“>Òİÿã}=¿ÈÄ*‰)¯» {‘£Ú§ın™‹e&ÅnsöQ—ÒåÅMÂUn&8ÔJ£”)4’¾¹
ô¹øºÿzn1Ê¤Ğ]/oPıÄZv;×ó×^ÀÍ$4™”E÷(â˜C0‡S#>öæz>ÿğ“p5æ#p—ŸæO£9^?AîËüòò÷ÏOãÕÄúĞGØÍ¾œÿ„¯5±§ĞŞŸ¿™øxş4½{w§÷ùí»ÿ½6}2’ŞŞüá_ÒJDè¬Ê%÷ÍœûxüWi¸¢¢‰oÊS®µˆS™[î´õÓk š‹°ù±í7GŠƒUçÊığ ç‡“AûB{lô}Ô
(ü”àe¤÷¥RøkU®Yæ§¬FbÔo¿ĞPõ4Ş?Í¬Î^ÌØ¿[ÌNa'Ø%)æÎ44%´ßÚ]¬`ä&·
Í¼‚únÑÆ˜Õõ¦Ûèv<IqWnÓ´÷³!‘ÃŒ{ï6^9òUêú±‘99h×øâÔ™¸k¢•Ú p ŸÑÌ|"—±Dœiæß‡§Ãp¼ú‡èûh/½Ô	Q¾1 t`æ¨½Ë#-7ü,øÒº;-
TU¼¸ô aéh:¤Xr©3=d³_ııñ ÂŸ¿ù)‘çşô7ÿËpf’ê/‰xœ}’¹NÃ@†‘â†!šQ(rà8Î… ’i"
$.‚”„5¶XâxwmÊHtt ?%´©(x*ƒ€=‰0²4ã™oÇãÿuşfáöa¸İ=n+ÿ¾%}´Û)‰ lá AÇë2âa
ÌAĞ&î¹ÃºˆRCH&“‘>zŠmöEàè@uÁ‡†²äÚ@Á²ÀlÈWa±€t!r’?yYp dÁŠi˜êïpÙbacÏ#9G1¶è[teÜãqXÈ•³HeµşXª`«#l<'ÏsÿŒéĞSÂC²<Iúò$ÙG+“hO¢ìgÓê¯¤ÿ}/#²6IŠ)‡ä,G)1ƒFüz*zÙ]„-šKÔÒÚÿÌ`?q/ä²{„¯šŒàb˜~à2#›×®#8$Á×÷£—dJ‰é-¹šÁ íVç	qYa(E–
>Ñô”pçÌ ˆvBùöMLuÑ½v¬Ğ­R—²á]æ«êÆ–™u¨Ö×Œ±ÍŠ$_5§>¯²â¼…xœíıÛ¶õwÿŒƒƒäÖÖµº\¬½\€C‹$¸KR`Y Óm«'‹*Iãıß÷Ş#)Q²|Ë¶î§Íhsùøø¾?H=}rÙhu¹.ªKQ=°úhv²šL§Óï¥4Ú(^3-LS)KÍŠJ^–Ü 4y+Y£Ee£XÍ³{¾‘¶“I}œÃ\V6¹`fWèÉ¦(B›¬ç{ÁòB‰ÌHud¼ÊÏs‚cFˆ‘5“‹Ûc|ş|2ağÛ(¹gâ×”ÆY±¯¥2HWÚÑEpı¡xFô+ñK;3Ît-²bSdìA(ìá~øŸ*—‡ª”<Ÿì¥¤š3©H¼b¼4BUÜˆ¨c
–aå‘é¦†?ä‰×µ’µ*p…¬Q¢Äîj5$tµJ€V”I-£½´dkÁTÏ©ÏTQ\ïTD„Õ[ÅóPA	jvâd$µÒ»Æeûvl'ŒØ×¸©ÿµè½Ù5Wº}×ÍxÊ„nÔ`+©öÂOæ Fåß3YáPY¬'Rd^hƒÄh¯ÉRn'£Ï;eëDæ¦ßİ]ß¦w7o¯'âS&@74~Ú±KZ¶d¯d%&“×/¿{÷ãÛôıõíİÍëW0>ıSòMòõ´ywû#îŒ©õóËËúX‰uDªí¥3o}©Á 3q	­ˆ/§“I.6,µği¶Ïã/¸Úê™%€oa…ªØ[Õ /²òLî÷hıºÉ2!r‘'½ˆ¨ŠA?‰ø$²Æğu)æ3ö%MŒ²X;E$CLû³å’}5qÔ93™lW<ˆÕZ#Î½¥¸fÏÙ‡Âì˜vZ;Yì`ñ÷Ôã)ªm;ºL\UqtÓN²»VtÑ¬…‰TÒô„yÇæ,rÈáñ‹Ş€€ş~wr/  ÀvQvPóFáŠ>lI@Ç ‹-ĞºØÄVÀøZ>ˆá¢§L|*L&Áı¸#8ë³€ÓÔ3¯uS”y*¶ÛşŸ³S½™B<ù·ÕAø‘]°ÃˆN¾o! ,êµ$´kÏªgñş»FgF–hhoğ zêDáU¡„nJ3éÑ8,°³©“š›¸àÔ4İñªxùæ5Å€8º’M™Ó*Uàv‹
³¢ß
“B`K³’k·}7½Ã€-öh4+ê—€C-ó ˆ1p^°Å à±7$ö,ùs]{e4¼t8cX÷pCÆ‘ÂşB¥i¬E¹¹wy˜.tk@äÇŒè—Ú’â™XCàBĞ$+%„ô õ€8TÂknŒÒzöÛF3&JĞÃßÛN¸ùÿµK ‰{tR$Õ-|`ÙèdÈŠñ¶ãàiÒìk°1˜>‰%ûûŸãYß¸¢ëIké´ØJğËCˆÀêÀV²Cî0´Y‰  Ôî`M.m]u`c#”¾-Õ}U¸ÁÄqˆ±z6	üy+½Èw[h´ ,÷ŞU~xGÛKğœ€Ü_}œòb±ÌF‚Å+y`©îC¡¡…(sW¤p0&.+İn‘­Eµ7JˆV˜.Hæ7\q»:mŞ–[éšë6NÃ¹(ùÑYF³¡L|ÔåğÅ…^ÔÇ‹<ÿ0|õü.XGfe÷Éu#A #ƒ_œ}~ s& ·¼uáşÏÑ:ø‘RÚÇóQ?t#{D>¤O¡LüÕœQ¤vÎy+öY­ÄC!]¶h9«ï·)z*Ÿ4
€4YˆVÂ-÷Õ×º0ë&»ÆÖ^Çš‡åVİ”åËx¡Íå_.)øæÂp(!g‰uÔÛ/B‹EÚ÷2oJ¡Ã`[†ë>ZÎ|µÛï/‚*{í{'_f¥T·.)ñZSùN™ËAi:Pî2¨O;E[,Ñ£5¢Ôå×ß8£²ğµÆ¿q¨T%êÔñ	ôÜ$
¤!0@ÂTˆoviKChŞâ ñHüôC¸uÙ3u½¥•ÔN)é‘¸1v|»œBÍíö™ˆ	iîcz.®ŠuƒÂx%ÍKÙTùÏÊèÖï-"ÈÀ›²È&÷W)”±ü7­&û‰h¯·”Dmã–@[~û‚&ü½¥êÄ•·Ñ,şvù››ù}Æ ¥Å ÈÀ[©—9A‰í4¼‘ÁÚ9 ?ì°¡×ùÂ4ÃXD&ìM)¸«`ÂŸïŒ9ÛK…”fp<›Bi3¿ÿ‹ áÑ;3[¼XŠ’É	x|Õ(È¡á'|ì7+í{HOÔï³“E ÑY‚½27±_Ú?sOãòÄäğ‡©ÑtÆ1(ì‹²øY¯‚P9¨C¥WÈû^$ìÙĞüñÀè×ıfls}Z„Öb'²û é	3l£›ª×;CYŞ¿Ø	»é·×ÌsFøYSƒeÔ}Á»ÀîÁ—“Ôçõ›ğ^¤Ûl¤3¥fˆí¹b uEæûÆ¾b8 „eáTlI§Bíeúú‡A™£MÍó½ƒbö>V€­T±ÖLky -ìĞ×¨òŒ0_´’æé°‰àtGœ=¿i±±|1ÛÙ&º‹"çÆÕßªÑf–°[jÇ°ë$q ¯Î;ÀÁ1À+´ZFn÷ÉYë r€øĞŠ!êØº -®ìÁØ4®Äa!×?C’bwGBò
Œæ'±¾*ğáYâ¥BÚŠoF{á	P³)‚\A]oñZo8kÀV=ĞA…JqšÀJÈ™%š¨‰gì	¤áŸŠ
ª£“„ñ’—.Ö9!ôxy†(–í@‘P(9‡ÍÅCå
·Uì%ì†aÁa$ÈŞË£~ AÃä²1Ë¥Tş½3\ç+×ŞFF{Ü×“~Â!´Íkì+™öˆd~Æ’‡SÈ ¯‘1'‚újÌ}¼àqÄL Ñb¡±Ç3öìdP7øl~¶…ĞãÛ VXÿçµ‰éëGÆ4x ñ>¢Aœ4¥Œè)p‘Ë¬Ù[­ş‹š¤Ç·û¿&{úékGÆ4‰-'hY<’ÎŞAŞqçp½²À%7hVV²ÙîXa|â@T¦Èğf­ÊdUÙ>æ‘z€º< O³\KÚ^H©uùO;š Å³±µZex ¿Í8!ÂB¸5”­‚šïVğü’ÊD†•,ôÁ€ƒ­K™İƒHvÀÛ+,·3%}Œ+¥.I,@äRx+Ô/ÿ ÙCXqAúç†cg¨2÷'g4C<‘¾Ú™ÖÓ€«hÉlÜ¾€À=0{Ø,´7øúp¸‡›Œ[Wg‹%ß¯sşÜ[­;7^ƒŠÛBW(ïàİˆîÕ%ç’Ğü†±ssèçæ<ù¾±²Ã“Òy@^O’¹¢ñøs>Œ©ÿ½wp1hM7œÎ8—#‚?WÈ­'yV{ÏM$=İ÷P“é8,Œ½eÅ³Y+µ•clÅônÖèTé†Ø}Y5ûµPàœzÒ¶µ%\xÖK·/VÈ¦Êi‰`«°Vï!]ívUN¨ì‹.#(±WV€+Ü±w²PÂ_y´7Q­Üœ£®HÜírÇuî÷rºì¨9ŞsÛ^‰®»3<Éï.Ä‰?ƒçëÆuÄ«Õ©îV}1nšŠb*Äo:I®$^eR†EQåAº°Sí‚P€v
etrßöõâ)ÛÛ4xF9d†nÖZ–D:Ì°ŸH†gùh#xKÜ;7N`†úkŒÔ²ïìË…ëüA ñg¦=ècGÇÃì9òúİƒ,Ğ¤kŒáy»³n®=ÇŸ¾dx¡§TûÌN¢ŠP6ã1H›9a¾÷C(I &¼ osc÷YÄÀ¹¿o¯ñ:[ÙEö2²ı>ÄŸ÷DLºïL:ouø=´ÊPq¨è#uä–‚GÚóº×úğÑßóã–Ş¡op¦×éBÏ.ÈtŞ8!"ÃsŸU$¯	ŠĞ('k”ğ<O-8ho-á=µYF!Í0ÈÉq–‘Í‰ºsAŞ”fI\!'ÕKÉqÙï.œèXìNútpÕ‰@÷
á8új½Í,Ğ#Z²{~£{a Šªå|$<GùhB±ôû/rğ£e õà©m|>ÏßùÈ‰ä!¢BŞÑJïK_^œÉã-»#¹oÈ6–½T‹A©4‡PQ-Ü¹úx·ÌŞ—¾9™Û¦w”B1¹`bò™/é#jòeA°¹ó…¹ÿÀÅú•‹áµXÈ;Aš uÛ
D›÷¢ó0rÒ=‡hÚyçÍcßHQ9pÍõÑAy÷ôßh-û.oß£7u­0|ä£Š?=­â¨Vò`g.øF*£áŠn*¸?£|44C˜.ğ£ÌCiŠßEiŠrMSw(Õ3[iÏ&ÿ èHâë¸FxT]‹Û0|®ÅBœÀÅ¾k
”¦	´”’‡ÂqÅZ;âlIÕGZ÷×ßÊ‰¤„B«'IÍ¬V.Œªg× j­Œoñ¸á”ªlt½£"ZFèhíÎBòL³ü…•h£(¯˜µ¢h,Là)ã+¥k”69oa<†GÁgt,¾‹àzÄ+†9!KØ4ÖaàëÕfñ=L–Bú_7HK‘£´ …©ÖF‡õ·Å–híçÄ…t(9!§”y+qòLn0ÖF•†Õup¸d²ô”»õØ¸½’aö.ùğ_¼÷7X[¥ED7ªp?™A¸(è_ñ}ñ¾2Ã3~¢öÎ’Õx]õ	ÄSÎ
ã…Ëf{f–³y/~ :Jv„~H’ûÂ<e7g ĞÕÇ[%˜‹™ªÎ×|fX3Qát\äúÄN’\Õ½4G›¡İÙ1–bg˜iÀ)àFròÌr‡È9pauÅ`’M&½\uj”³W’£!À€Ëæíì]ìuÍêÍÉ|¯B"{ç´§i)ÜŞïB†´”öµ]·MÒ•8ímqÔ¡eŞd•/6ğéŸ$¿¬«Ô1³cU•ÖŒ^y‹e9éÀè>y¤k{î‚iá3ƒ?¼0x:öŠòqò§{ê}v²zõ‡Ñ+&@G'äƒxœM1
Â@E1•ì	ÄêƒÚ"6öiDÄ>,Éh’İ°;‹®Wğ¶â¥<†I$ê4æÏÿo^ı»Ø±+zFØÛ ï”>‚.‰#öØ@iÇ²(Ğ.Ø˜ÂA C–dºÊfmÑm|mÄ;J~™ÉTĞ9¥Š—•±¼¶ÖØµ±Õ: Æ‚Ô¤s¾$lçFcS®Òü‹Í¥û{êÃ®êˆå êÍŸ›h½+XLœ±Lx•TÁÓ0½û+† Ñö¾HÛ]*¨–•8.{šXulË§¾qšT*¢|Jœ73oŞ¼É½ÁC*–_ö#wÁ¿<t˜¾><ªÿ>Jqàl“0p	PkÊÙúîçl %j¦’,Ã!…0Ç†’„í-Hà–°u´`ëP×J=R¶­'9’¶«Ñ¹8À)¤#œ,wÀİ,´’ó	:æ˜ï6G˜ügRkúÍ…ØÊi“7a 4X:)õ¹6âD‡,MõŞ]ÑEof¾Í…ï{èñHK"Cšè‚sáT1ÉòÚR¾Sê—•‹	€‘W-1”héúÎúÌ•KS¬3+Ñ–<[nÓŒV††å1÷MÉËK´ñ\àÜÌµÜ7˜>ííúË~÷ı2Ğfz%]XØ_–ì°[¢®Êı=Í[â,&yÙnÿ¯îeêSä\{7kU]±˜Rz0áä]@SgpqÍr)@„à§Y%ÛvüŠÿmc¬ğš	“îì@Àã`[¬bÔæ­9Ïw.ô6ƒ±‰4±t5Èå¦±A&.qÇEÅ¹D‡}tá %cK™hÌ÷²@ÁJ²‹x‚(s¶½Ğ•Ú‰r(I6b
ƒ:çÎfâ@8Œ4%¥0WßÆ_dÒTôjFË›Š¹EĞ(¹;œ¶\ò›¢¥ö´Ö£7JıL–YŠ	ü9øíCp8ı#ì¼)™“¬ƒtóm÷,³Ğä³°ªgzeÀFÖzAS¥Ğ®ù#ˆ&(I[4bÑàÕ¼Q¯|lƒUxœ;ÈyˆsÃ¦Í«™Ä˜ !ÿl¦xœ340075UpLIL+*Í,‰wÎH,òqvÑ+¨dØÉP9ÕÇ¤4µİLì·ëÔ)I)çÌLLâã3ó€ŠãAÊ¼2¹†[ªW=±ê÷ó¿_¾ı Ø Ì´xœK*ÍÌIáÒÒKMO×ÍÌKË2*“¹ŠSKJJòósŠuµ¸ Şšú¦xœ340075UpLIL+*Í,‰wÎH,òqvÑ+¨d˜%xË¥$bI`"·õÌnO-öÈZ#C3…øøÌ< âx²ƒ¾©f¿Yµ±ıÌ›œÇÕC6*ü İù Dí*úxœeRÏoÓ0Ö+ROüí¤§N°F7“ÚUR´qá2z@4¹ÉKcÉ±ƒí,‹„è™³¹ğpGê‘w.üù?pC–!°,Û²¿÷½ï}Ï_?n|ÿ´ñ¥¿eßOZ+²Õé,ÁcRƒgaBU_#ÀeH“b 5•ğ&m¨G¯×{Ê8)d&Aˆ™ÒÆptr<o‚5Ì$æÚÈÖì4t\šÔT.ÿÌ_Â]*EStĞ‰ÌystÓˆ| "‚QµÖ’jT£+SòœEè @•¢åZÜæ¥A¡†2ÁÄ¢Òû‡a)“Ræº0¤ºäeC¡f±~UÿÔ@bL6‹¢ os&hFy®I(ÓaííÆ~-HbRŞ0ÎäZtQS.ÿåÌ5:=<ŒHŠZÓöw^_ø»;Şßî7çm×^B&5«ô	q)gç²À+k‹‚1ªïíîÍıÇ³ªkÁtz
ï ß@à±w•7–
0Š
'kìÙàî-{¯{í~İWìÍ ªå,•ÎT^»}ùÅìG·WóApÃzÁ‰ıö°e?GÕş+Ø]½|òyÓşlwìõg›«ît»õ®"ÖË¾xœK+ÊÏUpLIL+*Í,‰wÎH,òqvQÈÌ-È/*QĞ ¬
ºê Ìxœ]?KÃ@‡‘€C†®®¯dÈ Ó&
’ÁQŠ“[¸$o“£ç]¹œE§€Ÿ@Épw?ƒôk™\šzÍm÷<÷şùİ~ò9y¿½„RmS”òV„„IÁ0!f$Û|<.jÛvNßm)‡Lğ5-%QTğ…Í²<‘ÎüÀ{¡TI+x¢E©€#æ ¤YIxÑß|ÖíhÁr” qG«¶e;Ç­¦]ß:An4öõ¬<0Ğ¬G3=šè¦Gá?ò"Ò6'Óû-!èÂ~BmÆiçuWQ¹aîÛ	ïz0æÚÚkÌíµ™æÎL¡Up,
GÆŒ™©3¡Û|Ÿ}5WÖÅ9IÅ§Ml½üüZoÖwQíÎ/xœ;Î·o‚2kB»ÓFe=FÃ¢Ô°U0ãÊIN‰O/JMÍƒŠ˜ƒE’rJSaj,6od\ÊÈÔ>9Œ9Z¨]G®Â)ß¼‹¹— tË ä¹,xœ»"vNlƒ3»kEbnANêd_æ»0öfM–4¶ÉK¹Ö úÕsç+xœ;'ö‚{‚¥AQjŠBJfQjrIN¥BI¾BPbqARjQQ¥B@¦B~‘‚SjbzNªS~^ª‚SNbröÄFåÉ¡Ìw'[±,Ô³ˆ7WçRVÈIN‰O/JMÍS°UP°ˆ·„	&å”¦*@'s³bKLÊ/KÕ›|–µks!› P¨,>¾$xœ•‘AkÃ0…ÏÍ¯ìĞÚ¤ƒ-ŒBÇzèmŒ ÚJ"êØ™í²_?7n¶ö¸œœ§ÏzOVaMô;òm\7ÆzhEÁ£\rû;™&ÅùÒŸ2\ë•¬eŞ 8bI.Izu¢±&…o	ã‰…mÙç«
ívµÏ’À‰¬c£!2÷é"]Ä¶¾26Ê{£;XóÊ(¼.æT#«ğ’E¨>ãÅ$¦¨$',7>˜ôä–mŞ€´|"!
OB(ì… –ÒØF± í(æyÛì£ÚZu™®ò¾qYV²¯ÚÃÙ>²d¿“ïº[Ò’´èrÅúèB·µ{İmŞ3ö€Je5º0Ê•åràæg`¾HÂÓ~ö–¬pné«eKÑòZ^óÃZã–n6=™N“¯æ¾i©x31 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÆyIy›.G†°ş\©kÒõXÊyÙ9°9)‰iE¥™%ñÎ‰E>Î.':w5Lªn|ï›­»¿kÎqq¨>Î®~Á®¦‹cö†±ÍÌ¹P£;½~Ò‡íå J‚\]|]õrSV+Ê|ĞÉ“Ò6¿H=ÒË¹1ùÄÊÔŠÄÜ‚œÔb†7¯oè—–®QØÿŠ#È´èéß3u‘9PsR«â‹SKJô
*”_ÍÒ®Ûûöc“İ¥¶õÕŒbçç®ZUWãºûÁ¹ÃœO3m¶zßKæú" Ãct¢ëxœK ´ÿ©©_yĞ­ñ‰+<_ÁOá×èSídŞq‘sW›ÜclO½°ç;ğøÄ–uNŠ­‘Ş7\‚ô…kiïxf	„áºêOĞÍÂ&+§x340031QĞKÏ,ÉLÏË/Je(»Å`e¼Ì‚Õnµól¶*“9_L€@Á1%1­¨4³$Ş9#±ÈÇÙ…!ë–ã¡3Wzl"tÔÔµı.‹~1„èãéìêìÊ`º8ÖhoÛÌœ5ºÓë'pØ^¾ ª$ÈÕÑÅ×U/7…a§XJTØÚ”ï]¢ßôò«YjpA¬L­HÌ-ÈI-føsîÿò;üÚÌ!š}ß÷$ô6q@ÍI­Š/N-)-Ğ+¨dP~5K»nïÛMv—ÚÖW3ŠŸ»j-T\ÍçÓÙWfµz¾{tJxyÚlÍ=·~j„ _eBî€yxœkgjgšĞ*²ZáPæƒÆH”¶ùEê‘^vÌÉ&ÎÌ · J©x340075UHÎH,ŠÏINÑ+¨d`”ùYrÏš‹5¬RMå,â×¢*‹ÏM. )½+ÈûĞ9û@áÜù«>g–÷èºÉf@WZ“X’
RìÊ×İÓÍ¾ÀùrEiÒº+íg×¨¢+.JO)tŞÍ¾'üĞ¦ÿf?}sL2ømÃ¢4¾ <¤<QñÑV¥»—?;µ«eÉe¡¹³¿  œîSèë Ù:xœ]ÏNƒ0ÇcH<pØÕë/rà`$‚l“%†ƒG³ø¤ÀoĞÛ¥­‹H|oáÍøÆ×”1;zëçÓßŸoÿfíìãşˆÜf(Ä¬(p	’²Æ„3„¤&ùÆûÄëÆ¶Ó‡[Ê çlMËAåìÎ®ó"g	AàÀ#Wª¢iY)`ˆ(B^V·À‡u7›×
¸£²kÙÍq¥×÷mRdFã@Ï*BÍ47P8 …nı#?Ö(ë‚Öz¿%„}ØÓ_hòÍ4­Ó¼î*Nc÷ Ì}{áßŒÆ\[›c¹½6‹Ñ<˜)´
EÑÄ£13õ&rÛï³¯öÊº8'ß¡×&ÖëÏ¯õníÅÊ<ïÛUxœ;Î·˜o‚2kB»ÓDe»‰¹O‹RS ÀVÁŒ+'9%>½(55*bIÊ)M…©±Ø¼‘q)#3Ğ€ÉaÌÑ@í:
p]&Hùæ]Ì½Ì %!ÍjÒxœÛÀ·„o‚ÃFŸ'l  (¼]xS]oÚ0}^~Åx€J(”›´>"V‰uˆuªúT™äÖ‚Ù¡-ûõ»×N¨ZM ññ±}|îñ¥ñ¹³·¦³’ªSÊ­VA’W±+r„½•jBÁr6†t+ŒHK40ŸLáEÌ £oZæ(5,…-VhÌ´1ŠMc­Æ¹Hÿ„ÜÚ”PÊõd”‰µÙËòiBò,,,ëÙx§˜jµ–›½¥Ôêk§Ù“±ğâ@è´Ú ”[iÙK!Äh:ÏÈ±ÁgiéÜ;É¦u*¨X%v8ë1¾ñø†qÏã>ãk„£¡ÃœĞÔïÚtbÑÀ-®ò=ò¢3¸ G w“$âÚ>¦êkÀ±Âæbø4lÒfÜÌDİšr¦uÜ•±wGõ»¸GõWâ¨¸¦ê‚˜Ôd]“_j²®Îš\Ó×’^›_1Õù~§¨u20ú¬ü‹°¦¦ˆú¯1o]B~¿bÔ÷yêK³à(§vSôâÏH=fLåú âîkÏ«øPŞtân•İZ)õXéVÉRŠœm”[oÑ77Ï¨[,ˆ•~Fg‹ng‡ÇÎ¤æ¯š³åß¤]½„³^5ŞTc¿íàSõãs•I¿Èö*„™.e9Û+¶ıkËáéÂJX™r¬ÚXç2´X²¦6­(ì¶¡[}®8È0ÍQ˜–Ç;´Vl°Õ\&ÓæUÀ¿ĞæˆEë:ìÒ5¼ÿMÌéÔŠ'ÄfË$¹»P®Ö<!7ÿNÎ«9_˜{LæóŸçõjcm Ñî&£j­Sû1š%w÷£óöŞÊ=mïáûíıÿÒûrá¿åì4xœ[É´’iƒ(£HLÓ—ÖìÌ÷iœ¼-w½’ğ—ºp £uf¦xœ340075UpLIL+*Í,‰wÎH,òqvÑ+¨d˜%xË¥$bI`"·õÌnO-öÈZ#C3…øøÌ< âx2¯ÌE®á–ê‡gO¬ºÄıüï—oA?Å 2ë;xœ[É´’IÉÄ ôÒ3K2J“îÎ<çÏbüÒô¿~™«ÁöşÙ®½•Ø?öP­xœ340031QğuqõğqqÕËMaHvÙôuÉ®¿–Zå‘‡ãâV,ºrï J9Xh)xœ[ÉÔÎ´Q‰ ËëŠTxœK ´ÿ‡‡=È‰º€P’{ïMg[-¾Š¬,Ç‘QWìëØ/uu¬ ¿êR5råıÌ~Yl‘¼7MU»àÎÃ	åi= µqKŞc
ô[P#3ëZxœkgjgšğYäóéì+³Z=ß=:%¼<m¶æ[?5Â Årš§x340031QĞKÏ,ÉLÏË/Je(»Å`e¼Ì‚Õnµól¶*“9_L€@Á1%1­¨4³$Ş9#±ÈÇÙ…¡dmŞáıwZÄİ¦©Jı˜ı­Ï
Cˆ>Î®~Á®¦‹cö†±ÍÌ¹P£;½~Ò‡íå J‚\]|]õrSvŠ¥D…­MùŞ ú-@/¿š¥fÄÊÔŠÄÜ‚œÔb†ÿ¯‹Ş½>ŸXªzuêÜ#½û>&æì‚š“Z_œZRZ WPÉ üj–vİŞ·›ì.µ­¯f;?wÕZ¨2¸šÏ§³¯Ìjõ|÷è”ğò´Ùš{nıÔ İJj0æ€zxœ6 Éÿ‡‡=jì*A¼ÌÔŒ<X,&'+NÓñ‘QWK]…sC¤èĞæ;6Š§¶hÏÆ‘¼K</¦©x340075UHÎH,ŠÏINÑ+¨d8¸ÌŞÎZµ51Í£¹¾mšûQİUY|nrH©tù%-~N³N®=¹ÕsÛ¥oÏmĞ•ä$–¤‚/N[%újV|Ú«E…Yß¯ê…iIÏ‚®¸(=	¤ôä§%Ï6Ä'º”ÊO˜Ÿ”Äw‹Òø‚ò\ò'Mï¥\çìş°t¿Rwı‰Öœ°3  rZ>ã€(xœ3 ÌÿÙÙkZÅL åi8(É:ºWû‘Fa!âµ¥Q »§æÊº„¤Ó›ô+—æƒ)xœ6 Éÿ‡‡=;H¥1^M“]¥V+å`—ÖQ‘QWK]…sC¤èĞæ;6Š§¶hÏÆ‘¼K0oÍ¦xœ340075UpLIL+*Í,‰wÎH,òqvÑ+¨dhy {QFWâÎ4¶KÅÚÛl|‹ßoÜoh``fb¢Ÿ™TRvĞ7uÃì7«6¶Ÿ9bs‚ó¸zÈF… Pé"Öí)€›xœeQAkÔ@¦‡®“(•=¨<¶`\fS,ìvi…Ğ­õâ¥îAP)Óä%˜ÌÄ™‰i@Ü³çñâİ ìÑ‹ÀàÕÿálŒ©èc˜f¾÷½ï}ïëÇ­ïŸ¶¾ø;öı|°&;•oƒèÌ~{8°¢“öüí¯_<ş¼½	¦+¤/âœ*_#OÇÀeL“b%5•æt10ÎA
™‚ÉR¦´œœGÏúd539Ä•6²€;—&•«¿tÉà®”¢:è\V<KtËÔˆB "i»w’:T¯«Tò-KĞA€*E›¸\65ÄRÊY«÷7ÃJ8%FV»4¤ºáMO˜ f™Øüªÿš j 7¦œO&u]“7´¤¼Ò$–Å$O¦³°J2’›‚÷ŒK¹]w”«9+€NR Ö4CïÕU¸¿üí~ßu3à”R³ÖÀçrp.k¼¶¦·øÁ1„WÓîİŞŞ:|~ºl§-çğüzt‚ëº©TÀ€	PT8Y³ÀFwoÛ{Ã÷»q¼d¯Çm/…Lğx©*<Ï³?¼¡½ùt{=\ì~y9Ò8íˆxœkgjgš`'ìş¨ïxeÕŠŠw‹8¯óœ³}\=1p À²¦xœ340075UpLIL+*Í,‰wÎH,òqvÑ+¨d¨©èú½Ó÷İßàƒşUÓZMW–˜™˜(ÄÇgæÇƒ”ôMİ0ûÍªígØœà<®²Qá –T#òë€ VxœÛ=…ñìÆ¢“ë¬Ø6ë‰–jLÖttŸ|@›mr§£3˜~êh¸9Âî17 i0‘ë‡xœ äÿÙÙÅa!âµ¥Q »§æÊº„¤Ó›ô¶:àŸ9xœ;'öYdƒs=—²‚KjZf^ªBAf^±Br~^^jrIjŠBI¾BIFª‚³‹WNrJ|Q±‚­‚z€E¼…:˜Ÿšå@RL`P)¦03¨€LÀ*`1RçB8%)19;'3=£èœü"°Ó ® ºL¬ÇnlzQ*Ô1–`“7ÿd	e YGAgï(€xœm‘ÁNÂ@†#‰Ôp1œ<MÂaÛd³)œŒÑ‹€hR•€DCÈ²,´¡vIwo}•Äñ=ôèƒøî–0±=lgæûÿÎü”ßö_*e`>)S<¯Ş€YH½?Y~î•êº¤“m“³?Ş­ƒ®/0œ+%"JçÉò«p˜´c.e–—„äXV®è”CHbœ‹h8çVh4‚!eÓ0˜ø
˜EL¬ÌNÁ[_OºM¯Y¿Å€º<äL!vë×q°é“¬”öšçš@+Ò.v7ôÜkã4@½2§†5ºm½7nî®Sç†XD(ƒ«ÆÙı‡î\¶.L#¨c~å}hkp¬å÷I<!f üXÌ'>pÊü|Ff,Ìçl
Á„™0«8qÎQ>òc«XÔlÈF$ƒ¶WÅ·ï˜z±g™.õKƒÍş£	×}pxÔ2ª¿ÿ¬…©1f!§±íäaç—TûëŠäjî2¯Õúº›¨j¢Ò:¬ií/e½ê¦xœ340075UpLIL+*Í,‰wÎH,òqvÑ+¨dpš“á9WY<DeËÓÏŸWM)÷640031QˆÏÌ*);è›ºaö›UÛÏ±9Áy\=d£Â? Pî"áâ€¦@xœÛ=…ñìÆ‹m'k:ºO> Í6¹ÓÑL?u4Üa÷˜  øPî;xœkgjgš°Bd}œé»c/<õ°Pc(¹ç&Ñí;q7 Ë”>à¥xœ;'¶Olƒóä0æ;›­XDØ7.îGxœkgjgš°BäÆËMç³Ê\ÚÊ·$9S»ù/Ó&Ÿ‰{¼Ğá¿ïmxœ/ ĞÿÙÙ'100755 char_lcd.py SÏòdö˜Å7ÒøVó²íunb‘'²ºCê ö&xœ]½NÃ0F…"1dèÊzQ†H	iÓVª„20¢Š‰-rœÛÄjjWv¨`ŠÄ€ò ìlˆg@¼‰Ó7Ş|ïÏçßÑÇèíöˆÚ%(å¬	’¬ÀHp„¨ tóş¸¨lÛ9}·c¨àk–=IR2ÁvAÓX*8œ%ø!€÷¢D(s¦`Ë²¼˜B) A 9áYwó=X7£E‘¢‰{¦š–ÍWÛ¾UŒÜhìëYi` I‡&
:45ĞM‡ÂäÍ4Jšœ…Şo	Aöô*º¦u`˜×]Íã™{æ¾­ğ®{c®­Í±ÆÜ^›ioîÌZÇ¢p`üŞ˜™Zºõ×Ùg}e]œ“Dìq\GÖó÷õjız: î‚Lxœkgjgš°B„ëZú%áÙŒ¼½Ò!f™;õ«îLÜã ¤zƒî‚xœ áÿÙÙ>Å éø¾ŸF¿–¡š×«ÚÏG“Ê19‘R‡ônæƒ$xœ6 Éÿ‡‡=¬‹€: àşyY Ã˜;È‘=î‘QWfİÇ£/PwÅn­\UƒÛİ-‘¼Kh¬Å¦xœ340075UpLIL+*Í,‰wÎH,òqvÑ+¨dès5ğ=úÉfn®tË­gİçBnW˜™˜(ÄÇgæÇƒ”ôMİ0ûÍªígØœà<®²Qá \N#&ã€Qxœ3 ÌÿÙÙ–øÓB¤JÕKYHµ×êU¿~‚‘ªèRÀÎ
—3æ¯7#àR	ÜËı4r+í„_xœÛ'ö‰{‚¥AQjŠBJfQjrIN¥BI¾BPbqARjQQ¥B@¦B~‘‚SjbzNªS~^ª‚SNbröÄNe×ŠÄÜ‚œÔÉ¾ÌwÙalM–Ezñæê\Ê
9É)ñéE©©y
¶
êñ–0Á¤œÒT¨ ¡áæß,>Œ›Ù\˜ ŸÕ.Aînxœkgjgš°Bäø·{ç#œ>tM3È8İ0÷3+Ó³‰{¼ã'ıg€uxœ»É¸‰q¢ú& -øé‚+xœY ¦ÿ‡‡=?‹ı8?¸ò„ñ ú3¦µÜj‘Q47¸HGOæó“±2¿´ouıÿFl40000 examples L£ïriHRQ[æ¾'ÖTJf½|‘¼KÖi&çæhxœ6 Éÿ‡‡=¬‹€: àşyY Ã˜;È‘=î‘QWÇöŞÏXBò0Š–0hË€`óæ‘¼K|yåf»7xœ;ÈÙÏ8¡ §z¦xœ340075UpLIL+*Í,‰wÎH,òqvÑ+¨dh>²íªÄé=şZÙA3]W–¦Y1˜™˜(ÄÇgæÇƒ”ôMİ0ûÍªígØœà<®²Qá "Î!ä€°XxœÛ=…ñ@3ã†ù,›Ÿ°°l¾ËµÀˆ½¤´(O¡Za²¦£ûäÚl“;ÁôSGÃÍv‹Y'ÏUªxœ340031QHÎH,ŠÏIN‰ÏM.Ğ+¨d8ÊğòÇ¾ùnû§-œu}õ­óî“OZ¢)-JOŠ/(Ï)æˆxyl]ƒ"k“ëÖ;ùÓ¾ğ oj%N¨xœ340031Qğñtvõve0]k´7ŒmfÎ…İéõ“8l/_`Qäêèâëª—›Â°CØÃİÿÙçÉö³nÉ/ıûß% jêÉ™xœK
1÷9E_@éÉwDÔ¸ñ™éVãü$FôøÎÂoQ¼’E€Q_˜\°Y›èÉØ¶¹°ÈÜF
y¯­zÄ,c
,KÕèº¬›ƒ÷\çŒGªMkªy*¾ÊmÊ°‹#§2½Ÿ]‚ß»o®CLı²†5TÖ’&D`QÍvH¥ÈŸ¹:¤0<Ò÷i¼‚ä<?I#œ÷Ûİi¯¾ö“KE·XxœmT»rÛ0ìùçÊ±”>3™$e
Ï¤†È£xC`€ƒhı}ö@J‘Wà¾n×Á…‘Î±Pµ‰J8’£¹L%ş]8+i¤6Mr(ÊööÒ¹>ÑûLßE”Ö;¾k¾0`¸âÅ™éÀWyb—íõ$¼Ô•>NS\ŒïX¤ãIgr¡#•9ƒ¦xšI”LŞp Ó™$(“Sî>7Í¾rn!+jnAM±7°ƒGŞídÏ{Z§uÏú•º¸Ö…Ù%ÍÙ¯uÑÂÉ¸;é…»ıÓÑë ™A:U]ÉTBÇ)«á¸p¦$yÌr‘	ƒ@½@îÿ‘l¿Œ!.&ñ¢Øƒèpk RÃˆøÍy$IÒß¼Y	÷Jn‘Fä(—y	)!z§Œ¿X›ä\:_Fâ9+’ŞÄıÜFUB•§]É1Ë«u_8µ’yÕz	j5j’™¶ŒæœjoBÄ0Q²¹!³wQ[~`Ö‡ÊøéJgIo™(âäœbË9CïëµÁîè$¬=¾”Xw&b˜¦šŒW¶kn£t™rDx.lŸ	@VA·¸d ÁÁ·d¶ò'cI,›hkîX5 ÀTÄ{îL˜Mâ<G+y$>q:_ÈŞºeuC¿¢b®{ÅÏ–};p;BrcÚŞÏ‘j°Š*§j§“Ü–œm®[ÊÛöG„ö2åˆÊ˜4[bJ65y·Ït´SÌX ½Mîï¹Ûírô¬âk¸™“À¼š}}|;Ğw¥­ı~¦Ú/lEÉËqĞÊà¶Ãˆ&ëÖ2²úZÕ÷‰õ¹.×û&£…­õÉûD1îÁªŒĞ ãzÚ7QŞXAvS‹12Ï·‡‹–µıˆlÈ]o	¯·X­*¸o¯¯C<­ |åZ/d©üfz£ÿßMóLaõ›â
€‡6xœ;Î·ƒs‚gRbrvëMLÕ¼‰1d²³¢WNrŠ‚­‚³‹cJbZQifI¼sFbPÀ	ª^C“‹KY!¤´(OdDNfzF‰B~Şäƒlb›3³0I( AIfnª^qNjj†©&Hlò]VkÜ’Zl«'_eËg2Ğ hè0ÂìM€º8xœeSËnÓ@U-`±àİ, ]µ‚&ªë¤mÚ„ªAJã$D´µY€xX{’XØ3Æ3&„È‰’ù$öHY²áXÀ¾°ã?»“Ëã±æÜ{æÌ¹s¿}šûõyîëi¸•ra¿¢Bé¯1 Şl<âÙmì2E¶W®<lŠ¡Áø)Áú,V}4…mÌbj~
Ûœ`Üšó‰Äí)l+¦°íYl¿ÑªÆXat"íKş»…‘r}qq¬¸º‹Çš.H3lud°¨¸I‰â»$³#÷XZZª™–”` à=ÓeŠP©–âd}“÷@÷§6ìHç¡—§Dbÿ–H‡‹­\dc¬G=Ë€6/ïcL ˆP¿‘¤(*Öå¸ôi`ÈuÑ W„ö€c:%™Ä$İPï)Ã(PUº
¨ºHÃˆ¬ALh`fvI€ºÿ‡çÎN6Ûï÷•×Iƒ,):µ³=#Ÿ/sÑUzÜ¶bÆD÷#Êa’Óc°Ğcé†bcÆP§WçÖW2ÓîÇÿË¢Ö ÊÌĞÀœ¢‡\aeÑ>X[|·¹ãB´îßH]¹wTm…U+«ê!¼…tº»›™É¾ê‚	&!«˜ñË7¯ú·RçîDåxf¾Ã³h65p©åz8#Iã+æÿ\»6jËåË~¦\÷¿¯.øÊ•pş[^=¹ÿeŞÿ--ú—ÌRêòÂÙPß‰”:¿u£¯å*şKõÂZc£Y8j6Bî™†õXP` Œ]}TßÏ]J~PinlærEÿvmåŒ˜êµUÿG]ùen~FÑ4qM¸¦¥ı.C¢ÉåØšHÇt—'¢Õ­äÂv´ğtÒÄ³„:µ˜èC“`–ÈZZLPÛÂšÓ·K5d1,C×1i)8„¢Ùº“ùrªj“+xœu‘Ko£0 „ïü
ßQ&<ŒÔ®
4BBiš47c›7$qLIøõÛí^wç2Ò'4šœ1 ó4†3ÊLj"S¥95l•f™
3¦k&24;“Î˜³^€ÌĞ¬Ü²sfêˆBBD±EHÆ4lª˜˜„ d›Kxå‰ƒÑWà©ùñLqÎ‡J<’S÷@C×ĞÌÔTTCU¥oÚUB0üJCúgçöşRT¢²ÿÄŠsq­
ğğGîÜcø	Ø†~ì¼ïÒù—€Æ«K\Çq=ÇÙ¸›EfeôR7²ÊZ_Íx8:ÂĞq•íZ1e¥s³¸¾á»çŠÄù@°_åÍ'% AßGÖši2vºPËné¤Ú§Åu†ä¢î¢…»/‹´C[/¾¼<T„`±8ùÚ>?¤éÍ¹ú	_§@x^g>ºkÔ8­±ÑÓKÓ3÷¶_œÙ“ŞOª_’ıw‡÷Ã]í'ì›‡³*8úŞQËÊ÷©Ë|á°õ!Ç‹ìouäï–u$Ëë:'ú¥÷tXØhíÈ»Gãr2¢ú8\´x4úS®>ßÂUªŸıÖ_Œ³$(w›äíj³ä&äµ~›“UÍ¸V]höS67ÜñÛ÷nL\İYäÉ§¤€djLnÖ%oe«ÉÃ4E]¿ñó1ºãÕVÜñYÏúf¤¿ŸÍã×?&gŠ£€3L;öøÃ²Õš”+xœu‘Én£@ Dï|Eß­ÄìR2J³ãccBnÍÖ€ÙşúÉd®3u)éI%•ôhŸe@TCNI°”H|&‰¹˜)R,Ë
ç’*ªi¦@…iqŸİ(°¢Ä,TE²¬šg"L /À8WY(°¼”ç9›g™Èà‘M\Lé­/_?ı†Sœ÷cIŸ“¦ş8IäAæd	<±Ë2ß´.)Íz`—t3ÆàåÖôY[-o¤¤ÅÿgFZ2”<ı‰fÚÎx¶Î}@—À780Z¢!¤é´Ó6V“µ¥ûš‹OñxzgB(İ8Úíœd­7G#év$oâC<0  Óçì8Ó?kúX#İ?zÖQ»x-ÊÎX/Qt­aììN–—pJwêmjãRÙsÂ€´‰ïøİi£D’¬Íü˜î|9›XØjAİ¬4h¨~Pm\k²“úq§èŞ§µÛÃ‘œÀ™]5üå¾ÃiÕ—bl6m„ÄKÆÕ.–¥fëü9N‘½D%	;]Íq´ÉÉ4\1úş¶aY<àá»§ÀN±ÔıC:e¡Ş¥Âk«—­í;+ùĞöˆhğ}1…_˜Ëß7¡Ï€Ê]Ï¹UU¡s£Ö™t×Ê a66Åh¹ƒîwh‚­ÜF0cüf¸%ûCß¼2àu9ó×™y0şmŒ	ÚÓø&2öæsş&è×o‘3xœu’Ioâ@„ïş-Íe¼oR2Šl³0Ë%j»¦ñí&6üúa2Êmæ]JúTU—zœ $SW@2ŒD6u]—bš	È: –ìƒ%ƒ-\0ƒŠ£$5õÅÒLÃP4IS´£b“Ô3±4"¥8…ÄTàÛoá£b¤ªm[ÏòìV”£a[ª™¦¬b[@T–€oüT3bÎ+Š^ó/}ÇÙòŸi]şB²®)–ª¨–‚^$]’„'-)çÀĞˆòñ-A¯UÍàRÜß3ÊO·ä?±ì’54C/ÎõFş-F´òG3g½‰¼/. µ›ºãögé.ƒÄN½~ä†æé¬Í?Uæ·CÆ¾ï¸£å—j ™ªn˜lç½up´z88%pæ½óŒ¶»‡ĞGÑê¶é7s‰wÃØZ´l±˜ÂÛIrˆj™yEšboî7\@SíÊñIå‹i#“j¶óâGØmç6ƒ%•iE$±,f’_fpï›Ïİæp¸ùE·£hÜĞæ–Ô^ØMöäÆ°aU°Ì[kß³Œ¢;»îrbjø«.ìF#p?ï-XdŸÄ¬]šŠ³OAö˜6óz3kJ ººµEåÃX¢×ÅÖ8CºçõÈ^Mş½c±U·éZ^×õ*³•2îE}y}ñ•uàù+£8Æ˜;Aéı:ô†gÑ·,rï»•+zÓ4ObçM@oê´ß	7ófƒ/&Le€.·¢@®7h8ú!kèÈê‘s^óºmr*2À¤„æEA«ìãH;AÒúf{ş#­Pä9ƒ©÷³$¿^qı™©xœ31 ½ôÌ’ŒÒ$†š{¹,Â•&¦_™v¦¶òìzéòÅÅ†f&&`%™éyùE©ÆyIy›.G†°ş\©kÒõXÊyÙ9°9)‰iE¥™%ñÎ‰E>Î.•Ö~ìÔ¶‰?èÿğú‹yÁoSØïBôñtvõve0]k´7ŒmfÎ…İéõ“8l/_ Uäêèâëª—›Âp½©IQ·+ƒÎŒßæÌ¹y;¥5æ@¬L­HÌ-ÈI-f˜}'9Çï†úç,ÖB~™Vê×µjNjU|qjIi^A%ƒò«YÚu{ß~l²»Ô¶¾šQìüÜU0ep51M_Z³3ßW¤qò¶<ÜõJÂ_êÂY Ì‹vk´gxœ•TË7¼ÏW´OI–ö¾@¬YØ]	ZFNE¶4„(’àCòäëSœ—-Ã{ğœ$²««ºÙ]‹åf»œ?î–z^Í¶Û¦ôº¦çõëÓrKoŸ6›õ—Súôöø´ÄÕ¿~yY¾.p\ıùó¯ªvµdô>ˆĞP-"í™-)ö¥H¬>Ğg&˜‹‹¶GJ=\ üL.h)	«(pddM>ï"#YNTNteÄàFÕL«ªOmİ•œ5Åì½iˆÍ‘ÉÈå@sdÖiÓ¤ÚÙ^¯AQQÂ®:ÕÔİN©ªæ5Ë€©“{ÌZq«íÁ˜B"k„Lèy¾ˆ]’Bü3¶æê”||¸¿G+‚
%QSéÎ÷c¦‰‘*Şû9‘]î_UUww=èK—ûË8pßİUÕ-[«VHÉ±U:à~”|îL‚¶"ú=À6š œ±89Ë43BĞëG}´¬(z–úPO®.œ¾•şÑß_¿ĞwápÑ|­ª¿K!Æ7"¡¨s¤ßoä–ÉéôîG½ĞYœó€éh\Æ`^¸•wpÆ¸kéF”­b+1Uõ/¾*fåHø49rÂŒ*ğí™¶1-û¬š ·l“Æôöï¥ø2üŒç}Ã¯}GĞsÛîw”n7zú´Y­Çİ7Ä_Yæ2Ş7‚‘}6 nè~|Í÷(ÇášÍ~•÷Ú“¯ú»’ú»dÊ]­qB•GÇf8D =•kw]ëô‘²ıO{?,ugü‘,üä(Úe‡Š² ßıIiXP1ŠvBŞ)¡Û™È)û©o†rúŞ˜goZÉQ!-O^Ä(Xqòµ½pL‘’>óàkğ ¬"ùà.Z6è0‚Ôİ‘t
E!¥ˆ<Ù·m*iJô¤Æ²¨kñ>4n‰åi×ùU–©ßëıNtJ CøÎÙ†zîŒhMbäXY•c*¶ˆj^V;ôR²PÕ¾"…Œ=ö’ÎƒÏ£Pi²‚% 'I+]Àµ5üêİUF×æ…xœûÂó€g‚ˆ„cJbZQif‰B@eIF~‚sFb‘³×DG±arl Â	î‡Txœ áÿ©©§•µ³á§—0°È{.|¡úÙ»ãZp‘»nì_<\g-ö-xÿÙ(|±knÀ•sHÿtOc                                                                                          	   	   	   	   
   
   
   
                                                                                                                                                     #   $   $   $   $   %   %   %   %   &   &   &   &   '   )   )   *   *   *   +   ,   ,   -   .   /   /   /   0   0   0   0   0   0   2   2   3   3   3   4   4   5   6   6   7   7   7   7   8   9   ;   ;   ;   ;   ;   <   =   =   =   =   >   ?   ?   ?   ?   ?   ?   A   A   B   B   B   C   D   D   D   D   D   D   D   D   E   E   E   F   G   H   H   H   I   J   J   J   K   L   L   L   L   L   M   M   M   N   P   P   P   Q   R   S   S   S   V   V   V   V   W   Y   Z   [   \   \   \   \   \   \   \   ^   ^   ^   ^   _   _   _   b   c   d   d   e   e   g   h   h   h   i   i   i   j   k   k   k   m   m   m   m   n   n   n   n   n   o   o   p   p   r   r   r   s   s   s   t   u   v   w   xGÖÄ®òUÁ–Ğ¢,_/mRøP’ió’¬Ñ|(±58_a¯Åë¯Hø6Q’µg©ƒ²CŞBæ
ÖgÒ,›T6Ai¹/qzÜŒ©°âFRùÄc®ÔdIù[zù»é9ßU9Ü¡?OùÍ¶Oi±‡ò
Qdä"Â„zy¤\úƒ-ZÅL åi8(É:ºWûw¼¤„NBšÉ¯UÉµI¶Òöç=P1^¡íæÖ†ıY»¾BhR›#êš+~½íñ‚>Ò†¯{Ïª­)–q;›Múp,ÒìàŠ$ú—3’*SÎwy¾ñ˜rO)íc´Òf1*Mh{9‰&&¼{¬ø´5£]2½V™lĞ|-—’À@·w :ˆ°yAp	şGÇ#{ù0%ÿğşä;H¥1^M“]¥V+å`—ÖQ<$”‘€bS$5V—¶Wç f`?‹ı8?¸ò„ñ ú3¦µÜjA@ˆß•kLîí}Ÿ-Ååb«E‹‚\‡[ CÓxub®Ô‡Í¬%E½!bãè 	/İF2’*„¸ ã\bGëUleXI#T$´åóóª”wKIŠ·Ê\RåON…¶jszõ”èxJi¢EW9'xÃ›‘zÒçıôöRùK]…sC¤èĞæ;6Š§¶hÏÆL£ïriHRQ[æ¾'ÖTJf½|MU»àÎÃ	åi= µqKŞc
ô[Mÿ‡•f]<‹ı'™DÔ_mP[-P!t\9¾ù¾5
ñüE0'ÉQ3ĞíÈ•ä'ƒ"[mq{mLQC»¼WÂ²ÿ6ùMm`4á N¶SXéÆ®€!jEµÜoãfôqSµYeÊz2 A ÖX‰€I5ôSÏòdö˜Å7ÒøVó²íunbTÖÅ†ÃÏr¦úN5£ÛOñs/<X¸×¸—³%WE¬—™Á8†Ñ\‚ô…kiïxf	„áºêOĞÍ`Äs¯oó~_ìx Û{­ºOKa!âµ¥Q »§æÊº„¤Ó›ôaX?-SíjF9‡ÀG]öıÇ±³7cD²õ¤¼Šı9*wYÃ^^¨¢ÔŞâfİÇ£/PwÅn­\UƒÛİ-g(ä*Ù%pB9ûZ(A‰^åÔíi¸Äºí?şæ»%/ßg»ssÌjì*A¼ÌÔŒ<X,&'+NÓñk)¯jÿU\R÷âÊ{£û-®²|n2ê9÷`êYâ„Ç%6i¤tGâÇyz¨xî¢	×Î=ãyW[t­nÃ¿İ€„F–%Ã›ãíL¨vÚ ::[S¦8>«C›z4àlôyĞ­ñ‰+<_ÁOá×èSídŞq{d¸bÀ^nö˜"ş¾3ìZ|xŠû¹MîıSÁOz–…q40©w~!ª³›ˆÙ£µWMAKÓÖ‡‚ğ_™fb.Bo[÷eƒÄ¶Õ”¼O*kRI™E©uf:„‡ãß–é‚œÌ¥¬ßæ&?·=„à-Ñ-Ü–Òs+¶<Msï±¿‰3nbn²ÓYTù©-4ŠãC¦ÎŠòl9˜®Pb/iƒ{gâ˜í=èE0HÅò<m„Úæ‹PÎTÛxoÂ±±õºğÉÏJ¹ŸËùDÍo?•µ³á§—0°È{.|¡úÙ»ãZp•öŒ3g„/â£¨÷©(ˆ?Õ§”‰0—iMá²ˆàÛ°vm‡U6	ƒÃ1šQÚDtX¤Qa;™‹I*Y}2›ÜclO½°ç;ğøÄ–uNŠ­£fªêš_fê¢qj÷Õ.V*”¦¤ÚC)D÷wWä‰¯¿VŸì§àç³cşí“8eüìQù÷¨LÇ&±š^)ñïçÜQ-şs¥â« ÂiàYd†Ÿr'YJ>cĞ¬‹€: àşyY Ã˜;È‘=î¯^5è>ÆáĞåH8& tÕ^F‹M°„Æÿ–‹h+1ç,~r¿÷É6öµ'÷ŸæHÑQÚ|Ëâ¦
ÆÌˆ–Š¸HGOæó“±2¿´ouıÿFl¹ y•L4u_‡6û•”bdÎ¹dZV­d÷ŠPöP.o{| 
¼uÊÒ„vb@BO)Ü{„ĞÊÎ·.½§½šœùáJjØbL,u¶ğ÷ë¾|ÍÖH†Á­»ùıì÷U«îÁ&æ¶sL ?KÓjû/är4ÁMe°›ìª±‡ÌÄ<È	Ç'T± şÁ¦O¹}& |\ƒ±[0ö²ñ'Å éø¾ŸF¿–¡š×«ÚÏG“Ê19Æ>ä™ïFOÏ¬‹Tv–~ôÆ£è3,‡yUõÊWş=-~ƒÙ3ÇöŞÏXBò0Š–0hË€`óæÈ‰º€P’{ïMg[-¾Š¬,ÇÉòÈt€æ°_aDuŸbcRßĞ)½
8W"‘gÔ–Ì}yÍ¯w£sĞ/ÙWE#¦“L¿ÕpİÊ—0Yf$ÔˆN±«8ëD^$ µ¼*ë=×¥4r„E ,˜û7mn¹(œ×¸šõ<Fi p&$€Diï;Ô×¾9^[ûebŞ´×¦—M°¸Ÿ¡#¤Øé²‘ŸÒµ^¤ci+ƒı²LÙŒ2ã'¸Ş%ù„KVä¥bp£ÛZŠ:¾Ã„r\ÒÿSOp˜x@’)İáCkÀqŸªóiwŒ-EÄk İ™ÎO3é5ÿ/vE0·X4Š½Ş™åZ’%!1wMŠJ‡ŠÉáeàu.kUPmw¾î ›®éä‚ïBæd×	‹ğ¥¿"‹È…lVÌå•.´©Ì=]º›|Á>±ÔÏ3áè"0BFÑ´= ÛÏh3²–ûèRÀÎ
—3æ¯7#àR	ÜËı4ìëØ/uu¬ ¿êR5råıÌ~YlñĞr1i#e+ÛÁ•àì1ÌzúéJóËkÔš…IîâÊ§f›)¼Úù(Võy9Nü*ĞhÔN\ÒXÓG¿†õ¤?œ3€®îùÌ†9ZØL§Ş¶1øÓB¤JÕKYHµ×êU¿~‚û«SâÚ×{ ı™eLÊ
¹ßxü¢RáÎ“:ÌGâX ÿsõšm|ığwÉĞÇFÑ*²•)sùı‚ş\Îÿ§Ü+T)A÷¼cp‚ÿërîëÏau%Õ•Ä¾ñalºfv­ÚÎdt	Çú[Mj-êt–ÇâOybVša²D{‘+ÓWÖ+‡"Ãn
N.úòşs~€ë›‘Bµ–Sæã.k<˜MZ²‘ï‰7ê,Ù¯†İ6›éÒ$yñ™§SöíL‚Ç`!Ä´-YÍVEşŒ`Åu`&Ï5åÇV®çŸÊ½œ×^ë¨·˜d*!èÍj@¬_¦E!‰8¤¶‚—GŒ›§gŸíôD1®ÊR°}*T^ÆšÃÍòò»¹>ÿÜğ)ÅŒı¼‹rÃèÏUØÛ£—+I¨Çbp®s‘‰`å0À›„×1rUŞãœU´øŠä4¾‰„l‘Ûğ€7êöo„1‰ó¶4ÏF_ÍW#îE2bKË9ÄxÃÕkËUÔ[X‘5)@o »ØŠÕµg6ŸÀáı%L¿Sí–yBš%0)W%Dz;o”ĞÈÕ_ÌµÛbjÅÈ§“iï®¡MXë Æ^ï{}²ÎnL®¶»XñzCÈDoÌ„ÀŸ(¿v‘x sk€‰_®sÂÜ&ï·6›ı‹ƒaÛúV1Dß`Şû-İjcH–¸ E`uÂ™7ñOŠöàÿ çÛo¸»Å-Æbay0(€ÒwNê‡§@µ*T-	^ÙÊÙ‹ƒTT¦    `3  Ÿ  oç    e4  ¾  8  Z¨  7  Dz  l  o¼  ;~  1Ÿ  ~Â  h#  w/  r|  mğ  a¨  sr  mÃ  …‹  Ù  gœ  s  Qz  p  Ë  æ  a½  k9  e!  nŸ  3  7a  S}  ‹  =Ô  d³  ™  p¸  e  \  W+  »  ^g  jz  md  Vÿ  V   tp  jÙ  Å  9  rÛ  	Ú  h‚  §  sÂ    Bâ  ‚K    E  WŠ  2Ä  kÏ  gŞ  6  r'  V‰  pY  fô  q‚  |¦  rk  w»  T4     d,  :ü  z‹  Yd  YŒ  2ù  q¿  eµ  q­  dU  [+  ;  _`  	  …Y  jP  «  na  $  n7  aN  dé  e  ^  n  l  Ï  [   2  
é  [³  f¯  ¬  pú  ò  \ø  ¦  _‹  k\g-ö-xÿÙ(|±knÀ•sH‘vs½1k·UPO€ã89ºê£#!/bin/sh
#
# An example hook script to block unannotated tags from entering.
# Called by "git receive-pack" with arguments: refname sha1-old sha1-new
#
# To enable this hook, rename this file to "update".
#
# Config
# ------
# hooks.allowunannotated
#   This boolean sets whether unannotated tags will be allowed into the
#   repository.  By default they won't be.
# hooks.allowdeletetag
#   This boolean sets whether deleting tags will be allowed in the
#   repository.  By default they won't be.
# hooks.allowmodifytag
#   This boolean sets whether a tag may be modified after creation. By default
#   it won't be.
# hooks.allowdeletebranch
#   This boolean sets whether deleting branches will be allowed in the
#   repository.  By default they won't be.
# hooks.denycreatebranch
#   This boolean sets whether remotely creating branches will be denied
#   in the repository.  By default this is allowed.
#

# --- Command line
refname="$1"
oldrev="$2"
newrev="$3"

# --- Safety check
if [ -z "$GIT_DIR" ]; then
	echo "Don't run this script from the command line." >&2
	echo " (if you want, you could supply GIT_DIR then run" >&2
	echo "  $0 <ref> <oldrev> <newrev>)" >&2
	exit 1
fi

if [ -z "$refname" -o -z "$oldrev" -o -z "$newrev" ]; then
	echo "usage: $0 <ref> <oldrev> <newrev>" >&2
	exit 1
fi

# --- Config
allowunannotated=$(git config --bool hooks.allowunannotated)
allowdeletebranch=$(git config --bool hooks.allowdeletebranch)
denycreatebranch=$(git config --bool hooks.denycreatebranch)
allowdeletetag=$(git config --bool hooks.allowdeletetag)
allowmodifytag=$(git config --bool hooks.allowmodifytag)

# check for no description
projectdesc=$(sed -e '1q' "$GIT_DIR/description")
case "$projectdesc" in
"Unnamed repository"* | "")
	echo "*** Project description file hasn't been set" >&2
	exit 1
	;;
esac

# --- Check types
# if $newrev is 0000...0000, it's a commit to delete a ref.
zero="0000000000000000000000000000000000000000"
if [ "$newrev" = "$zero" ]; then
	newrev_type=delete
else
	newrev_type=$(git cat-file -t $newrev)
fi

case "$refname","$newrev_type" in
	refs/tags/*,commit)
		# un-annotated tag
		short_refname=${refname##refs/tags/}
		if [ "$allowunannotated" != "true" ]; then
			echo "*** The un-annotated tag, $short_refname, is not allowed in this repository" >&2
			echo "*** Use 'git tag [ -a | -s ]' for tags you want to propagate." >&2
			exit 1
		fi
		;;
	refs/tags/*,delete)
		# delete tag
		if [ "$allowdeletetag" != "true" ]; then
			echo "*** Deleting a tag is not allowed in this repository" >&2
			exit 1
		fi
		;;
	refs/tags/*,tag)
		# annotated tag
		if [ "$allowmodifytag" != "true" ] && git rev-parse $refname > /dev/null 2>&1
		then
			echo "*** Tag '$refname' already exists." >&2
			echo "*** Modifying a tag is not allowed in this repository." >&2
			exit 1
		fi
		;;
	refs/heads/*,commit)
		# branch
		if [ "$oldrev" = "$zero" -a "$denycreatebranch" = "true" ]; then
			echo "*** Creating a branch is not allowed in this repository" >&2
			exit 1
		fi
		;;
	refs/heads/*,delete)
		# delete branch
		if [ "$allowdeletebranch" != "true" ]; then
			echo "*** Deleting a branch is not allowed in this repository" >&2
			exit 1
		fi
		;;
	refs/remotes/*,commit)
		# tracking branch
		;;
	refs/remotes/*,delete)
		# delete tracking branch
		if [ "$allowdeletebranch" != "true" ]; then
			echo "*** Deleting a tracking branch is not allowed in this repository" >&2
			exit 1
		fi
		;;
	*)
		# Anything else (is there anything else?)
		echo "*** Update hook: unknown type of update to ref $refname of type $newrev_type" >&2
		exit 1
		;;
esac

# --- Finished
exit 0
#!/bin/sh
#
# An example hook script to check the commit log message.
# Called by "git commit" with one argument, the name of the file
# that has the commit message.  The hook should exit with non-zero
# status after issuing an appropriate message if it wants to stop the
# commit.  The hook is allowed to edit the commit message file.
#
# To enable this hook, rename this file to "commit-msg".

# Uncomment the below to add a Signed-off-by line to the message.
# Doing this in a hook is a bad idea in general, but the prepare-commit-msg
# hook is more suited to it.
#
# SOB=$(git var GIT_AUTHOR_IDENT | sed -n 's/^\(.*>\).*$/Signed-off-by: \1/p')
# grep -qs "^$SOB" "$1" || echo "$SOB" >> "$1"

# This example catches duplicate Signed-off-by lines.

test "" = "$(grep '^Signed-off-by: ' "$1" |
	 sort | uniq -c | sed -e '/^[ 	]*1[ 	]/d')" || {
	echo >&2 Duplicate Signed-off-by lines.
	exit 1
}
#!/bin/sh

# An example hook script to verify what is about to be pushed.  Called by "git
# push" after it has checked the remote status, but before anything has been
# pushed.  If this script exits with a non-zero status nothing will be pushed.
#
# This hook is called with the following parameters:
#
# $1 -- Name of the remote to which the push is being done
# $2 -- URL to which the push is being done
#
# If pushing without using a named remote those arguments will be equal.
#
# Information about the commits which are being pushed is supplied as lines to
# the standard input in the form:
#
#   <local ref> <local sha1> <remote ref> <remote sha1>
#
# This sample shows how to prevent push of commits where the log message starts
# with "WIP" (work in progress).

remote="$1"
url="$2"

z40=0000000000000000000000000000000000000000

while read local_ref local_sha remote_ref remote_sha
do
	if [ "$local_sha" = $z40 ]
	then
		# Handle delete
		:
	else
		if [ "$remote_sha" = $z40 ]
		then
			# New branch, examine all commits
			range="$local_sha"
		else
			# Update to existing branch, examine new commits
			range="$remote_sha..$local_sha"
		fi

		# Check for WIP commit
		commit=`git rev-list -n 1 --grep '^WIP' "$range"`
		if [ -n "$commit" ]
		then
			echo >&2 "Found WIP commit in $local_ref, not pushing"
			exit 1
		fi
	fi
done

exit 0
#!/bin/sh
#
# An example hook script to verify what is about to be committed.
# Called by "git commit" with no arguments.  The hook should
# exit with non-zero status after issuing an appropriate message if
# it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-commit".

if git rev-parse --verify HEAD >/dev/null 2>&1
then
	against=HEAD
else
	# Initial commit: diff against an empty tree object
	against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

# If you want to allow non-ASCII filenames set this variable to true.
allownonascii=$(git config --bool hooks.allownonascii)

# Redirect output to stderr.
exec 1>&2

# Cross platform projects tend to avoid non-ASCII filenames; prevent
# them from being added to the repository. We exploit the fact that the
# printable range starts at the space character and ends with tilde.
if [ "$allownonascii" != "true" ] &&
	# Note that the use of brackets around a tr range is ok here, (it's
	# even required, for portability to Solaris 10's /usr/bin/tr), since
	# the square bracket bytes happen to fall in the designated range.
	test $(git diff --cached --name-only --diff-filter=A -z $against |
	  LC_ALL=C tr -d '[ -~]\0' | wc -c) != 0
then
	cat <<\EOF
Error: Attempt to add a non-ASCII file name.

This can cause problems if you want to work with people on other platforms.

To be portable it is advisable to rename the file.

If you know what you are doing you can disable this check using:

  git config hooks.allownonascii true
EOF
	exit 1
fi

# If there are whitespace errors, print the offending file names and fail.
exec git diff-index --check --cached $against --
#!/bin/sh
#
# An example hook script to prepare the commit log message.
# Called by "git commit" with the name of the file that has the
# commit message, followed by the description of the commit
# message's source.  The hook's purpose is to edit the commit
# message file.  If the hook fails with a non-zero status,
# the commit is aborted.
#
# To enable this hook, rename this file to "prepare-commit-msg".

# This hook includes three examples.  The first comments out the
# "Conflicts:" part of a merge commit.
#
# The second includes the output of "git diff --name-status -r"
# into the message, just before the "git status" output.  It is
# commented because it doesn't cope with --amend or with squashed
# commits.
#
# The third example adds a Signed-off-by line to the message, that can
# still be edited.  This is rarely a good idea.

case "$2,$3" in
  merge,)
    /usr/bin/perl -i.bak -ne 's/^/# /, s/^# #/#/ if /^Conflicts/ .. /#/; print' "$1" ;;

# ,|template,)
#   /usr/bin/perl -i.bak -pe '
#      print "\n" . `git diff --cached --name-status -r`
#	 if /^#/ && $first++ == 0' "$1" ;;

  *) ;;
esac

# SOB=$(git var GIT_AUTHOR_IDENT | sed -n 's/^\(.*>\).*$/Signed-off-by: \1/p')
# grep -qs "^$SOB" "$1" || echo "$SOB" >> "$1"
#!/bin/sh
#
# An example hook script to make use of push options.
# The example simply echoes all push options that start with 'echoback='
# and rejects all pushes when the "reject" push option is used.
#
# To enable this hook, rename this file to "pre-receive".

if test -n "$GIT_PUSH_OPTION_COUNT"
then
	i=0
	while test "$i" -lt "$GIT_PUSH_OPTION_COUNT"
	do
		eval "value=\$GIT_PUSH_OPTION_$i"
		case "$value" in
		echoback=*)
			echo "echo from the pre-receive-hook: ${value#*=}" >&2
			;;
		reject)
			exit 1
		esac
		i=$((i + 1))
	done
fi
#!/bin/sh
#
# An example hook script to check the commit log message taken by
# applypatch from an e-mail message.
#
# The hook should exit with non-zero status after issuing an
# appropriate message if it wants to stop the commit.  The hook is
# allowed to edit the commit message file.
#
# To enable this hook, rename this file to "applypatch-msg".

. git-sh-setup
commitmsg="$(git rev-parse --git-path hooks/commit-msg)"
test -x "$commitmsg" && exec "$commitmsg" ${1+"$@"}
:
#!/bin/sh
#
# Copyright (c) 2006, 2008 Junio C Hamano
#
# The "pre-rebase" hook is run just before "git rebase" starts doing
# its job, and can prevent the command from running by exiting with
# non-zero status.
#
# The hook is called with the following parameters:
#
# $1 -- the upstream the series was forked from.
# $2 -- the branch being rebased (or empty when rebasing the current branch).
#
# This sample shows how to prevent topic branches that are already
# merged to 'next' branch from getting rebased, because allowing it
# would result in rebasing already published history.

publish=next
basebranch="$1"
if test "$#" = 2
then
	topic="refs/heads/$2"
else
	topic=`git symbolic-ref HEAD` ||
	exit 0 ;# we do not interrupt rebasing detached HEAD
fi

case "$topic" in
refs/heads/??/*)
	;;
*)
	exit 0 ;# we do not interrupt others.
	;;
esac

# Now we are dealing with a topic branch being rebased
# on top of master.  Is it OK to rebase it?

# Does the topic really exist?
git show-ref -q "$topic" || {
	echo >&2 "No such branch $topic"
	exit 1
}

# Is topic fully merged to master?
not_in_master=`git rev-list --pretty=oneline ^master "$topic"`
if test -z "$not_in_master"
then
	echo >&2 "$topic is fully merged to master; better remove it."
	exit 1 ;# we could allow it, but there is no point.
fi

# Is topic ever merged to next?  If so you should not be rebasing it.
only_next_1=`git rev-list ^master "^$topic" ${publish} | sort`
only_next_2=`git rev-list ^master           ${publish} | sort`
if test "$only_next_1" = "$only_next_2"
then
	not_in_topic=`git rev-list "^$topic" master`
	if test -z "$not_in_topic"
	then
		echo >&2 "$topic is already up-to-date with master"
		exit 1 ;# we could allow it, but there is no point.
	else
		exit 0
	fi
else
	not_in_next=`git rev-list --pretty=oneline ^${publish} "$topic"`
	/usr/bin/perl -e '
		my $topic = $ARGV[0];
		my $msg = "* $topic has commits already merged to public branch:\n";
		my (%not_in_next) = map {
			/^([0-9a-f]+) /;
			($1 => 1);
		} split(/\n/, $ARGV[1]);
		for my $elem (map {
				/^([0-9a-f]+) (.*)$/;
				[$1 => $2];
			} split(/\n/, $ARGV[2])) {
			if (!exists $not_in_next{$elem->[0]}) {
				if ($msg) {
					print STDERR $msg;
					undef $msg;
				}
				print STDERR " $elem->[1]\n";
			}
		}
	' "$topic" "$not_in_next" "$not_in_master"
	exit 1
fi

<<\DOC_END

This sample hook safeguards topic branches that have been
published from being rewound.

The workflow assumed here is:

 * Once a topic branch forks from "master", "master" is never
   merged into it again (either directly or indirectly).

 * Once a topic branch is fully cooked and merged into "master",
   it is deleted.  If you need to build on top of it to correct
   earlier mistakes, a new topic branch is created by forking at
   the tip of the "master".  This is not strictly necessary, but
   it makes it easier to keep your history simple.

 * Whenever you need to test or publish your changes to topic
   branches, merge them into "next" branch.

The script, being an example, hardcodes the publish branch name
to be "next", but it is trivial to make it configurable via
$GIT_DIR/config mechanism.

With this workflow, you would want to know:

(1) ... if a topic branch has ever been merged to "next".  Young
    topic branches can have stupid mistakes you would rather
    clean up before publishing, and things that have not been
    merged into other branches can be easily rebased without
    affecting other people.  But once it is published, you would
    not want to rewind it.

(2) ... if a topic branch has been fully merged to "master".
    Then you can delete it.  More importantly, you should not
    build on top of it -- other people may already want to
    change things related to the topic as patches against your
    "master", so if you need further changes, it is better to
    fork the topic (perhaps with the same name) afresh from the
    tip of "master".

Let's look at this example:

		   o---o---o---o---o---o---o---o---o---o "next"
		  /       /           /           /
		 /   a---a---b A     /           /
		/   /               /           /
	       /   /   c---c---c---c B         /
	      /   /   /             \         /
	     /   /   /   b---b C     \       /
	    /   /   /   /             \     /
    ---o---o---o---o---o---o---o---o---o---o---o "master"


A, B and C are topic branches.

 * A has one fix since it was merged up to "next".

 * B has finished.  It has been fully merged up to "master" and "next",
   and is ready to be deleted.

 * C has not merged to "next" at all.

We would want to allow C to be rebased, refuse A, and encourage
B to be deleted.

To compute (1):

	git rev-list ^master ^topic next
	git rev-list ^master        next

	if these match, topic has not merged in next at all.

To compute (2):

	git rev-list master..topic

	if this is empty, it is fully merged to "master".

DOC_END
#!/bin/sh
#
# An example hook script to verify what is about to be committed
# by applypatch from an e-mail message.
#
# The hook should exit with non-zero status after issuing an
# appropriate message if it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-applypatch".

. git-sh-setup
precommit="$(git rev-parse --git-path hooks/pre-commit)"
test -x "$precommit" && exec "$precommit" ${1+"$@"}
:
#!/bin/sh
#
# An example hook script to prepare a packed repository for use over
# dumb transports.
#
# To enable this hook, rename this file to "post-update".

exec git update-server-info
ref: refs/heads/master
# git ls-files --others --exclude-from=.git/info/exclude
# Lines that start with '#' are comments.
# For a project mostly in C, the following would be a good set of
# exclude patterns (uncomment them if you want to use them):
# *.[oa]
# *~
ó
íËú[c           @   só  d  Z  d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l	 Z	 d d l
 Z
 d d l m Z y d d l m Z Wn e k
 r» d Z n Xd Z d Z d „  Z d d „ Z d	 „  Z d
 „  Z e
 j d „  ƒ Z d „  Z e e e j d d „ Z d „  Z d „  Z d „  Z e e _ d „  Z  d „  Z! e! e  _ d „  Z" d „  Z# e# e" _ d „  Z$ d „  e$ _ d „  Z% e e e j d e% d „ Z& d „  Z' d „  Z( d „  Z) e* d k rïe j+ e) ƒ  ƒ n  d S(   s×  Bootstrap setuptools installation

To use setuptools in your package's setup.py, include this
file in the same directory and add this to the top of your setup.py::

    from ez_setup import use_setuptools
    use_setuptools()

To require a specific version of setuptools, set a download
mirror, or use an alternate download directory, simply supply
the appropriate options to ``use_setuptools()``.

This file can also be run as a script to install or upgrade setuptools.
iÿÿÿÿN(   t   log(   t	   USER_SITEs   3.5.1s5   https://pypi.python.org/packages/source/s/setuptools/c          G   s#   t  j f |  }  t j |  ƒ d k S(   s/   
    Return True if the command succeeded.
    i    (   t   syst
   executablet
   subprocesst   call(   t   args(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _python_cmd%   s    c         C   sT   t  |  ƒ B t j d ƒ t d d | Œ sJ t j d ƒ t j d ƒ d SWd  QXd  S(   Ns   Installing Setuptoolss   setup.pyt   installs-   Something went wrong during the installation.s   See the error message above.i   (   t   archive_contextR    t   warnR   (   t   archive_filenamet   install_args(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _install-   s    c      
   C   sk   t  | ƒ + t j d | ƒ t d d d d | ƒ Wd  QXt j |  ƒ t j j |  ƒ sg t d ƒ ‚ n  d  S(   Ns   Building a Setuptools egg in %ss   setup.pys   -qt	   bdist_eggs
   --dist-dirs   Could not build the egg.(   R	   R    R
   R   t   ost   patht   existst   IOError(   t   eggR   t   to_dir(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt
   _build_egg8   s    c          C   s6   d t  j f d „  ƒ  Y}  t t  j d ƒ r2 t  j S|  S(   sL   
    Supplement ZipFile class to support context manager for Python 2.6
    t   ContextualZipFilec           B   s   e  Z d  „  Z d „  Z RS(   c         S   s   |  S(   N(    (   t   self(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt	   __enter__H   s    c         S   s   |  j  d  S(   N(   t   close(   R   t   typet   valuet	   traceback(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   __exit__J   s    (   t   __name__t
   __module__R   R   (    (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyR   G   s   	R   (   t   zipfilet   ZipFilet   hasattr(   R   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   get_zip_classC   s    c         c   sÁ   t  j ƒ  } t j d | ƒ t j ƒ  } zw t j | ƒ t ƒ  |  ƒ  } | j ƒ  Wd  QXt j	 j
 | t j | ƒ d ƒ } t j | ƒ t j d | ƒ d  VWd  t j | ƒ t j | ƒ Xd  S(   Ns   Extracting in %si    s   Now working in %s(   t   tempfilet   mkdtempR    R
   R   t   getcwdt   chdirR#   t
   extractallR   t   joint   listdirt   shutilt   rmtree(   t   filenamet   tmpdirt   old_wdt   archivet   subdir(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyR	   P   s    "	c         C   s²   t  j j | d |  t j d t j d f ƒ } t  j j | ƒ sj t |  | | | ƒ } t | | | ƒ n  t j j d | ƒ d t j	 k r™ t j	 d =n  d d  l
 } | | _ d  S(   Ns   setuptools-%s-py%d.%d.eggi    i   t   pkg_resourcesiÿÿÿÿ(   R   R   R)   R   t   version_infoR   t   download_setuptoolsR   t   insertt   modulest
   setuptoolst   bootstrap_install_from(   t   versiont   download_baseR   t   download_delayR   R0   R7   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _do_downloadf   s    !	i   c   	      C   s!  t  j j | ƒ } d	 } t t j ƒ j | ƒ } y d d  l } Wn! t k
 rc t	 |  | | | ƒ SXy | j
 d |  ƒ d  SWn | j k
 r£ t	 |  | | | ƒ S| j k
 r} | rü t j d ƒ j d | d |  ƒ } t j j | ƒ t j d ƒ n  ~ t j d =t	 |  | | | ƒ SXd  S(
   NR2   R7   iÿÿÿÿs   setuptools>=sO  
                The required version of setuptools (>={version}) is not available,
                and can't be installed while this script is running. Please
                install a more recent version first, using
                'easy_install -U setuptools'.

                (Currently using {VC_err.args[0]!r})
                t   VC_errR9   i   (   R2   R7   (   R   R   t   abspatht   setR   R6   t   intersectionR2   t   ImportErrorR<   t   requiret   DistributionNotFoundt   VersionConflictt   textwrapt   dedentt   formatt   stderrt   writet   exit(	   R9   R:   R   R;   t   rep_modulest   importedR2   R=   t   msg(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   use_setuptoolsx   s(    c         C   sT   y t  j |  ƒ Wn< t  j k
 rO t j | t j ƒ rI t j | ƒ n  ‚  n Xd S(   sm   
    Run the command to download target. If the command fails, clean up before
    re-raising the error.
    N(   R   t
   check_callt   CalledProcessErrorR   t   accesst   F_OKt   unlink(   t   cmdt   target(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _clean_check—   s    c         C   s9   t  j j | ƒ } d d d t ƒ  g } t | | ƒ d S(   s‘   
    Download the file at url to target using Powershell (which will validate
    trust). Raise an exception if the command cannot complete.
    t
   powershells   -CommandsC   (new-object System.Net.WebClient).DownloadFile(%(url)r, %(target)r)N(   R   R   R>   t   varsRV   (   t   urlRU   RT   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   download_file_powershell£   s
    c          C   s‚   t  j ƒ  d k r t Sd d d g }  t t j j d ƒ } z6 y t j |  d | d | ƒWn t	 k
 rn t SXWd  | j
 ƒ  Xt S(   Nt   WindowsRW   s   -Commands	   echo testt   wbt   stdoutRH   (   t   platformt   systemt   Falset   openR   R   t   devnullR   RO   t	   ExceptionR   t   True(   RT   Rb   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   has_powershell°   s    	c         C   s&   d |  d d | g } t  | | ƒ d  S(   Nt   curls   --silents   --output(   RV   (   RY   RU   RT   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   download_file_curlÀ   s    c          C   si   d d g }  t  t j j d ƒ } z6 y t j |  d | d | ƒWn t k
 rU t SXWd  | j ƒ  Xt	 S(   NRf   s	   --versionR\   R]   RH   (
   Ra   R   R   Rb   R   RO   Rc   R`   R   Rd   (   RT   Rb   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   has_curlÄ   s    	c         C   s&   d |  d d | g } t  | | ƒ d  S(   Nt   wgets   --quiets   --output-document(   RV   (   RY   RU   RT   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   download_file_wgetÒ   s    c          C   si   d d g }  t  t j j d ƒ } z6 y t j |  d | d | ƒWn t k
 rU t SXWd  | j ƒ  Xt	 S(   NRi   s	   --versionR\   R]   RH   (
   Ra   R   R   Rb   R   RO   Rc   R`   R   Rd   (   RT   Rb   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   has_wgetÖ   s    	c         C   s¨   y d d l  m } Wn! t k
 r7 d d l m } n Xd } } z8 | |  ƒ } | j ƒ  } t | d ƒ } | j | ƒ Wd | r | j ƒ  n  | r£ | j ƒ  n  Xd S(   sa   
    Use Python to download the file, even though it cannot authenticate the
    connection.
    iÿÿÿÿ(   t   urlopenR\   N(	   t   urllib.requestRl   RA   t   urllib2t   Nonet   readRa   RI   R   (   RY   RU   Rl   t   srct   dstt   data(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   download_file_insecureä   s    
c           C   s   t  S(   N(   Rd   (    (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   <lambda>û   s    c          C   s7   t  t t t g }  x |  D] } | j ƒ  r | Sq Wd  S(   N(   RZ   Rg   Rj   Rt   t   viable(   t   downloaderst   dl(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   get_best_downloaderı   s    	c   	      C   s†   t  j j | ƒ } d |  } | | } t  j j | | ƒ } t  j j | ƒ sv t j d | ƒ | ƒ  } | | | ƒ n  t  j j | ƒ S(   s  
    Download setuptools from a specified location and return its filename

    `version` should be a valid setuptools version number that is available
    as an egg for download under the `download_base` URL (which should end
    with a '/'). `to_dir` is the directory where the egg will be downloaded.
    `delay` is the number of seconds to pause before an actual download
    attempt.

    ``downloader_factory`` should be a function taking no arguments and
    returning a function for downloading a URL to a target.
    s   setuptools-%s.zips   Downloading %s(   R   R   R>   R)   R   R    R
   t   realpath(	   R9   R:   R   t   delayt   downloader_factoryt   zip_nameRY   t   savetot
   downloader(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyR4   	  s    

	c         C   s   |  j  r d g Sg  S(   sT   
    Build the arguments to 'python setup.py install' on the setuptools package
    s   --user(   t   user_install(   t   options(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _build_install_args"  s    c          C   s³   t  j ƒ  }  |  j d d d d d d t d d ƒ|  j d	 d d
 d d d t d d ƒ|  j d d d d d d d „  d t d d ƒ|  j d d d d t ƒ|  j ƒ  \ } } | S(   s,   
    Parse the command line for options
    s   --usert   destR€   t   actiont
   store_truet   defaultt   helps;   install in user site package (requires Python 2.6 or later)s   --download-baseR:   t   metavart   URLs=   alternative URL from where to download the setuptools packages
   --insecureR|   t   store_constt   constc           S   s   t  S(   N(   Rt   (    (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyRu   6  s    s'   Use internal, non-validating downloaders	   --versions!   Specify which version to download(   t   optparset   OptionParsert
   add_optionR`   t   DEFAULT_URLRy   t   DEFAULT_VERSIONt
   parse_args(   t   parserR   R   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _parse_args(  s"    c          C   s@   t  ƒ  }  t d |  j d |  j d |  j ƒ } t | t |  ƒ ƒ S(   s-   Install or upgrade setuptools and EasyInstallR9   R:   R|   (   R“   R4   R9   R:   R|   R   R‚   (   R   R0   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   mainA  s    			t   __main__(    (,   t   __doc__R   R+   R   R$   R    RŒ   R   R^   RE   t
   contextlibt	   distutilsR    t   siteR   RA   Ro   R   R   R   R   R   R#   t   contextmanagerR	   R<   t   curdirRN   RV   RZ   Re   Rv   Rg   Rh   Rj   Rk   Rt   Ry   R4   R‚   R“   R”   R   RJ   (    (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   <module>   sZ   
																			
ó
íËú[c           @   s   d  d l  Td S(   i   (   t   *N(   t   Adafruit_CharLCD(    (    (    sH   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/__init__.pyt   <module>   s    
íËú[    ã               @   s   d  d l  Td S)é   )Ú*N)ÚAdafruit_CharLCD© r   r   úH/home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/__init__.pyÚ<module>   s    
íËú[QQ  ã               @   sÓ  d  d l  Z  d  d l Z d  d l j Z d  d l j Z d  d l j	 Z	 d Z
 d Z d Z d Z d Z d Z d Z d	 Z d  Z d Z d Z d  Z d Z d  Z d Z d  Z d Z d  Z d Z d  Z d Z d  Z d Z  d  Z! d Z" d  Z# d Z$ d  Z% d Z& d Z' d Z( d Z) d Z* d Z+ d Z, d Z- d Z. d Z/ d Z0 d  Z1 d Z2 d Z3 d Z4 d Z5 d Z6 d Z7 d Z8 d Z9 d Z: d Z; d Z< Gd d „  d e= ƒ Z> Gd d „  d e> ƒ Z? Gd d „  d e? ƒ Z@ Gd d „  d e> ƒ ZA d S) é    Né   é   é   é   é   é    é@   é€   é   éT   é   é   é   é   é   é
   é	   é   é   é   é   c               @   s  e  Z d  Z d Z d d d e j ƒ  e j ƒ  d d d „ Z d d	 „  Z	 d
 d „  Z
 d d „  Z d d „  Z d d „  Z d d „  Z d d „  Z d d „  Z d d „  Z d d „  Z d d „  Z d d „  Z d  d! „  Z d d" d# „ Z d$ d% „  Z d& d' „  Z d( d) „  Z d* d+ „  Z d S),ÚAdafruit_CharLCDzFClass to represent and interact with an HD44780 character LCD display.NTFg      ğ?c             C   s§  | |  _  | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ |	 |  _	 | |  _
 | |  _ |
 |  _ x3 | | | | | | f D] } | j | t j ƒ q W|	 d k	 r| rÚ | j |	 |  j | ƒ ƒ n6 | j |	 t j ƒ | j |	 | r|  j n |  j ƒ |  j d ƒ |  j d ƒ t t Bt B|  _ t t Bt Bt B|  _ t t B|  _ |  j t  |  j Bƒ |  j t! |  j Bƒ |  j t" |  j Bƒ |  j# ƒ  d S)aç  Initialize the LCD.  RS, EN, and D4...D7 parameters should be the pins
        connected to the LCD RS, clock enable, and data line 4 through 7 connections.
        The LCD will be used in its 4-bit mode so these 6 lines are the only ones
        required to use the LCD.  You must also pass in the number of columns and
        lines on the LCD.  

        If you would like to control the backlight, pass in the pin connected to
        the backlight with the backlight parameter.  The invert_polarity boolean
        controls if the backlight is one with a LOW signal or HIGH signal.  The 
        default invert_polarity value is True, i.e. the backlight is on with a
        LOW signal.  

        You can enable PWM of the backlight pin to have finer control on the 
        brightness.  To enable PWM make sure your hardware supports PWM on the 
        provided backlight pin and set enable_pwm to True (the default is False).
        The appropriate PWM library will be used depending on the platform, but
        you can provide an explicit one with the pwm parameter.

        The initial state of the backlight is ON, but you can set it to an 
        explicit initial state with the initial_backlight parameter (0 is off,
        1 is on/full bright).

        You can optionally pass in an explicit GPIO class,
        for example if you want to use an MCP230xx GPIO extender.  If you don't
        pass in an GPIO instance, the default GPIO for the running platform will
        be used.
        Né3   é2   )$Ú_colsÚ_linesÚ_gpioÚ_rsÚ_enÚ_d4Ú_d5Ú_d6Ú_d7Ú
_backlightÚ_pwm_enabledÚ_pwmÚ_blpolÚsetupÚGPIOÚOUTÚstartÚ_pwm_duty_cycleÚoutputÚwrite8ÚLCD_DISPLAYONÚLCD_CURSOROFFÚLCD_BLINKOFFÚdisplaycontrolÚLCD_4BITMODEÚ	LCD_1LINEÚ	LCD_2LINEÚLCD_5x8DOTSZdisplayfunctionÚLCD_ENTRYLEFTÚLCD_ENTRYSHIFTDECREMENTÚdisplaymodeÚLCD_DISPLAYCONTROLÚLCD_FUNCTIONSETÚLCD_ENTRYMODESETÚclear)ÚselfÚrsÚenÚd4Úd5Úd6Úd7ÚcolsÚlinesÚ	backlightÚinvert_polarityÚ
enable_pwmÚgpioÚpwmZinitial_backlightÚpin© rL   úP/home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyÚ__init__e   s:    "												
#zAdafruit_CharLCD.__init__c             C   s   |  j  t ƒ |  j d ƒ d S)z?Move the cursor back to its home (first line and first column).i¸  N)r-   ÚLCD_RETURNHOMEÚ_delay_microseconds)r=   rL   rL   rM   Úhome­   s    zAdafruit_CharLCD.homec             C   s   |  j  t ƒ |  j d ƒ d S)zClear the LCD.i¸  N)r-   ÚLCD_CLEARDISPLAYrP   )r=   rL   rL   rM   r<   ²   s    zAdafruit_CharLCD.clearc             C   s9   | |  j  k r |  j  d } |  j t | t | Bƒ d S)z7Move the cursor to an explicit column and row position.r   N)r   r-   ÚLCD_SETDDRAMADDRÚLCD_ROW_OFFSETS)r=   ÚcolÚrowrL   rL   rM   Ú
set_cursor·   s    zAdafruit_CharLCD.set_cursorc             C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  Bƒ d S)z=Enable or disable the display.  Set enable to True to enable.N)r1   r.   r-   r9   )r=   ÚenablerL   rL   rM   Úenable_display¿   s    zAdafruit_CharLCD.enable_displayc             C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  Bƒ d S)z:Show or hide the cursor.  Cursor is shown if show is True.N)r1   ÚLCD_CURSORONr-   r9   )r=   ÚshowrL   rL   rM   Úshow_cursorÇ   s    zAdafruit_CharLCD.show_cursorc             C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  Bƒ d S)zFTurn on or off cursor blinking.  Set blink to True to enable blinking.N)r1   ÚLCD_BLINKONr-   r9   )r=   ÚblinkrL   rL   rM   r^   Ï   s    zAdafruit_CharLCD.blinkc             C   s   |  j  t t Bt Bƒ d S)zMove display left one position.N)r-   ÚLCD_CURSORSHIFTÚLCD_DISPLAYMOVEÚLCD_MOVELEFT)r=   rL   rL   rM   Ú	move_left×   s    zAdafruit_CharLCD.move_leftc             C   s   |  j  t t Bt Bƒ d S)z Move display right one position.N)r-   r_   r`   ÚLCD_MOVERIGHT)r=   rL   rL   rM   Ú
move_rightÛ   s    zAdafruit_CharLCD.move_rightc             C   s'   |  j  t O_  |  j t |  j  Bƒ d S)z!Set text direction left to right.N)r8   r6   r-   r;   )r=   rL   rL   rM   Úset_left_to_rightß   s    z"Adafruit_CharLCD.set_left_to_rightc             C   s(   |  j  t M_  |  j t |  j  Bƒ d S)z!Set text direction right to left.N)r8   r6   r-   r;   )r=   rL   rL   rM   Úset_right_to_leftä   s    z"Adafruit_CharLCD.set_right_to_leftc             C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  Bƒ d S)z}Autoscroll will 'right justify' text from the cursor if set True,
        otherwise it will 'left justify' the text.
        N)r8   ÚLCD_ENTRYSHIFTINCREMENTr-   r;   )r=   Ú
autoscrollrL   rL   rM   rh   é   s    zAdafruit_CharLCD.autoscrollc             C   s€   d } xs | D]k } | d k rb | d 7} |  j  t @d k rB d n
 |  j d } |  j | | ƒ q |  j t | ƒ d ƒ q Wd S)z<Write text to display.  Note that text can include newlines.r   Ú
r   TN)r8   r6   r   rW   r-   Úord)r=   ÚtextÚlineÚcharrU   rL   rL   rM   Úmessageó   s    
&zAdafruit_CharLCD.messagec             C   sg   |  j  d k	 rc |  j r: |  j j |  j  |  j | ƒ ƒ n) |  j j |  j  | rX |  j n |  j ƒ d S)a%  Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.
        N)r#   r$   r%   Úset_duty_cycler+   r   r,   r&   )r=   rF   rL   rL   rM   Úset_backlight  s    	"zAdafruit_CharLCD.set_backlightc          
   C   s  |  j  d ƒ |  j j |  j | ƒ |  j j |  j | d ?d @d k |  j | d ?d @d k |  j | d ?d @d k |  j | d ?d @d k i ƒ |  j	 ƒ  |  j j |  j | d @d k |  j | d ?d @d k |  j | d ?d @d k |  j | d	 ?d @d k i ƒ |  j	 ƒ  d
 S)zÁWrite 8-bit value in character or data mode.  Value should be an int
        value from 0-255, and char_mode is True if character data or False if
        non-character data (default).
        iè  r   r   r   r   r   r   r   r   N)
rP   r   r,   r   Úoutput_pinsr   r    r!   r"   Ú_pulse_enable)r=   ÚvalueÚ	char_moderL   rL   rM   r-     s     
zAdafruit_CharLCD.write8c             C   sQ   | d M} |  j  t | d >Bƒ x+ t d ƒ D] } |  j  | | d d ƒq, Wd S)au  Fill one of the first 8 CGRAM locations with custom characters.
        The location parameter should be between 0 and 7 and pattern should
        provide an array of 8 bytes containing the pattern. E.g. you can easyly
        design your custom character at http://www.quinapalus.com/hd44780udg.html
        To show your custom character use eg. lcd.message('')
        r   r   r   rt   TN)r-   ÚLCD_SETCGRAMADDRÚrange)r=   ÚlocationÚpatternÚirL   rL   rM   Úcreate_char$  s    
zAdafruit_CharLCD.create_charc             C   s1   t  j  ƒ  | d } x t  j  ƒ  | k  r, q Wd  S)Ng    €„.A)Útime)r=   ZmicrosecondsÚendrL   rL   rM   rP   1  s    z$Adafruit_CharLCD._delay_microsecondsc             C   sm   |  j  j |  j d ƒ |  j d ƒ |  j  j |  j d ƒ |  j d ƒ |  j  j |  j d ƒ |  j d ƒ d  S)NFr   T)r   r,   r   rP   )r=   rL   rL   rM   rr   7  s    zAdafruit_CharLCD._pulse_enablec             C   s!   d | } |  j  s d | } | S)Ng      Y@)r&   )r=   Z	intensityrL   rL   rM   r+   @  s    
	
z Adafruit_CharLCD._pwm_duty_cycle)Ú__name__Ú
__module__Ú__qualname__Ú__doc__r(   Úget_platform_gpioÚPWMÚget_platform_pwmrN   rQ   r<   rW   rY   r\   r^   rb   rd   re   rf   rh   rn   rp   r-   rz   rP   rr   r+   rL   rL   rL   rM   r   b   s2   		C
	r   c                   ss   e  Z d  Z d Z e j ƒ  d d e j ƒ  d ‡  f d d † Z d d „  Z	 d	 d
 „  Z
 d d „  Z d d „  Z ‡  S)ÚAdafruit_RGBCharLCDz`Class to represent and interact with an HD44780 character LCD display with
    an RGB backlight.TFç      ğ?c                s  t  t |  ƒ j | | | | | | | | d | d d d | d | d | ƒ|	 |  _ |
 |  _ | |  _ | rµ |  j | ƒ \ } } } | j |	 | ƒ | j |
 | ƒ | j | | ƒ nR | j |	 t	 j
 ƒ | j |
 t	 j
 ƒ | j | t	 j
 ƒ |  j j |  j | ƒ ƒ d S)a  Initialize the LCD with RGB backlight.  RS, EN, and D4...D7 parameters 
        should be the pins connected to the LCD RS, clock enable, and data line 
        4 through 7 connections. The LCD will be used in its 4-bit mode so these 
        6 lines are the only ones required to use the LCD.  You must also pass in
        the number of columns and lines on the LCD.

        The red, green, and blue parameters define the pins which are connected
        to the appropriate backlight LEDs.  The invert_polarity parameter is a
        boolean that controls if the LEDs are on with a LOW or HIGH signal.  By
        default invert_polarity is True, i.e. the backlight LEDs are on with a
        low signal.  If you want to enable PWM on the backlight LEDs (for finer
        control of colors) and the hardware supports PWM on the provided pins,
        set enable_pwm to True.  Finally you can set an explicit initial backlight
        color with the initial_color parameter.  The default initial color is
        white (all LEDs lit).

        You can optionally pass in an explicit GPIO class,
        for example if you want to use an MCP230xx GPIO extender.  If you don't
        pass in an GPIO instance, the default GPIO for the running platform will
        be used.
        rH   rF   NrG   rI   rJ   )Úsuperr„   rN   Ú_redÚ_greenÚ_blueÚ_rgb_to_duty_cycler*   r'   r(   r)   r   rq   Ú_rgb_to_pins)r=   r>   r?   r@   rA   rB   rC   rD   rE   ÚredÚgreenÚbluerI   rG   rH   rJ   Zinitial_colorÚrdcÚgdcÚbdc)Ú	__class__rL   rM   rN   M  s(    !			zAdafruit_RGBCharLCD.__init__c             C   s   | \ } } } t  d t d | ƒ ƒ } t  d t d | ƒ ƒ } t  d t d | ƒ ƒ } |  j | ƒ |  j | ƒ |  j | ƒ f S)Ng        g      ğ?)ÚmaxÚminr+   )r=   ÚrgbrŒ   r   r   rL   rL   rM   rŠ   €  s    z&Adafruit_RGBCharLCD._rgb_to_duty_cyclec             C   sg   | \ } } } |  j  | r$ |  j n |  j |  j | r@ |  j n |  j |  j | r\ |  j n |  j i S)N)r‡   r&   rˆ   r‰   )r=   r•   rŒ   r   r   rL   rL   rM   r‹   ‹  s    z Adafruit_RGBCharLCD._rgb_to_pinsc             C   s×   |  j  ro |  j | | | f ƒ \ } } } |  j j |  j | ƒ |  j j |  j | ƒ |  j j |  j | ƒ nd |  j j |  j | r |  j	 n |  j	 |  j | r© |  j	 n |  j	 |  j | rÅ |  j	 n |  j	 i ƒ d S)zŞSet backlight color to provided red, green, and blue values.  If PWM
        is enabled then color components can be values from 0.0 to 1.0, otherwise
        components should be zero for off and non-zero for on.
        N)
r$   rŠ   r%   ro   r‡   rˆ   r‰   r   rq   r&   )r=   rŒ   r   r   r   r   r‘   rL   rL   rM   Ú	set_color’  s    	!%zAdafruit_RGBCharLCD.set_colorc             C   s   |  j  | | | ƒ d S)as  Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.  On an RGB display this
        function will set the backlight to all white.
        N)r–   )r=   rF   rL   rL   rM   rp   £  s    z!Adafruit_RGBCharLCD.set_backlight)r…   r…   r…   )r}   r~   r   r€   r(   r   r‚   rƒ   rN   rŠ   r‹   r–   rp   rL   rL   )r’   rM   r„   I  s   		.r„   c                   sF   e  Z d  Z d Z d e j ƒ  d d ‡  f d d † Z d d „  Z ‡  S)	ÚAdafruit_CharLCDPlatezVClass to represent and interact with an Adafruit Raspberry Pi character
    LCD plate.r   r   r   c                s×   t  j d | d | ƒ |  _ |  j j t t j ƒ |  j j t t j ƒ xF t	 t
 t t t f D]/ } |  j j | t j ƒ |  j j | d ƒ q] Wt t |  ƒ j t t t t t t | | t t t d d d |  j ƒd S)a  Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        ÚaddressÚbusnumTrH   FrI   N)ÚMCPZMCP23017Ú_mcpr'   ÚLCD_PLATE_RWr(   r)   r,   ÚLOWÚSELECTÚRIGHTÚDOWNÚUPÚLEFTÚINZpullupr†   r—   rN   ÚLCD_PLATE_RSÚLCD_PLATE_ENÚLCD_PLATE_D4ÚLCD_PLATE_D5ÚLCD_PLATE_D6ÚLCD_PLATE_D7ÚLCD_PLATE_REDÚLCD_PLATE_GREENÚLCD_PLATE_BLUE)r=   r˜   r™   rD   rE   Úbutton)r’   rL   rM   rN   ²  s    zAdafruit_CharLCDPlate.__init__c             C   sF   | t  t t t t t f ƒ k r- t d ƒ ‚ |  j j | ƒ t	 j
 k S)z?Return True if the provided button is pressed, False otherwise.z9Unknown button, must be SELECT, RIGHT, DOWN, UP, or LEFT.)Úsetr   rŸ   r    r¡   r¢   Ú
ValueErrorr›   Úinputr(   r   )r=   r­   rL   rL   rM   Ú
is_pressedÇ  s    !z Adafruit_CharLCDPlate.is_pressed)r}   r~   r   r€   ÚI2CÚget_default_busrN   r±   rL   rL   )r’   rM   r—   ®  s   $r—   c                   s:   e  Z d  Z d Z d e j ƒ  d d ‡  f d d † Z ‡  S)ÚAdafruit_CharLCDBackpackzVClass to represent and interact with an Adafruit I2C / SPI
    LCD backpack using I2C.r   r   r   c                s\   t  j d | d | ƒ |  _ t t |  ƒ j t t t t	 t
 t | | t d d d |  j ƒ	d S)a  Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        r˜   r™   rH   FrI   N)rš   ZMCP23008r›   r†   r´   rN   ÚLCD_BACKPACK_RSÚLCD_BACKPACK_ENÚLCD_BACKPACK_D4ÚLCD_BACKPACK_D5ÚLCD_BACKPACK_D6ÚLCD_BACKPACK_D7ÚLCD_BACKPACK_LITE)r=   r˜   r™   rD   rE   )r’   rL   rM   rN   Ò  s    z!Adafruit_CharLCDBackpack.__init__)r}   r~   r   r€   r²   r³   rN   rL   rL   )r’   rM   r´   Î  s   r´   )r   r   r
   r   )Br{   ZAdafruit_GPIOr(   ZAdafruit_GPIO.I2Cr²   ZAdafruit_GPIO.MCP230xxZMCP230xxrš   ZAdafruit_GPIO.PWMr‚   rR   rO   r;   r9   r_   r:   ru   rS   ZLCD_ENTRYRIGHTr6   rg   r7   r.   ZLCD_DISPLAYOFFrZ   r/   r]   r0   r`   ZLCD_CURSORMOVErc   ra   ZLCD_8BITMODEr2   r4   r3   ZLCD_5x10DOTSr5   rT   r¤   rœ   r¥   r¦   r§   r¨   r©   rª   r«   r¬   r   rŸ   r    r¡   r¢   rµ   r¶   r·   r¸   r¹   rº   r»   Úobjectr   r„   r—   r´   rL   rL   rL   rM   Ú<module>   sv   çe from .Adafruit_CharLCD import *
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time

import Adafruit_GPIO as GPIO
import Adafruit_GPIO.I2C as I2C
import Adafruit_GPIO.MCP230xx as MCP
import Adafruit_GPIO.PWM as PWM


# Commands
LCD_CLEARDISPLAY        = 0x01
LCD_RETURNHOME          = 0x02
LCD_ENTRYMODESET        = 0x04
LCD_DISPLAYCONTROL      = 0x08
LCD_CURSORSHIFT         = 0x10
LCD_FUNCTIONSET         = 0x20
LCD_SETCGRAMADDR        = 0x40
LCD_SETDDRAMADDR        = 0x80

# Entry flags
LCD_ENTRYRIGHT          = 0x00
LCD_ENTRYLEFT           = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# Control flags
LCD_DISPLAYON           = 0x04
LCD_DISPLAYOFF          = 0x00
LCD_CURSORON            = 0x02
LCD_CURSOROFF           = 0x00
LCD_BLINKON             = 0x01
LCD_BLINKOFF            = 0x00

# Move flags
LCD_DISPLAYMOVE         = 0x08
LCD_CURSORMOVE          = 0x00
LCD_MOVERIGHT           = 0x04
LCD_MOVELEFT            = 0x00

# Function set flags
LCD_8BITMODE            = 0x10
LCD_4BITMODE            = 0x00
LCD_2LINE               = 0x08
LCD_1LINE               = 0x00
LCD_5x10DOTS            = 0x04
LCD_5x8DOTS             = 0x00

# Offset for up to 4 rows.
LCD_ROW_OFFSETS         = (0x00, 0x40, 0x14, 0x54)

# Char LCD plate GPIO numbers.
LCD_PLATE_RS            = 15
LCD_PLATE_RW            = 14
LCD_PLATE_EN            = 13
LCD_PLATE_D4            = 12
LCD_PLATE_D5            = 11
LCD_PLATE_D6            = 10
LCD_PLATE_D7            = 9
LCD_PLATE_RED           = 6
LCD_PLATE_GREEN         = 7
LCD_PLATE_BLUE          = 8

# Char LCD plate button names.
SELECT                  = 0
RIGHT                   = 1
DOWN                    = 2
UP                      = 3
LEFT                    = 4

# Char LCD backpack GPIO numbers.
LCD_BACKPACK_RS         = 1
LCD_BACKPACK_EN         = 2
LCD_BACKPACK_D4         = 3
LCD_BACKPACK_D5         = 4
LCD_BACKPACK_D6         = 5
LCD_BACKPACK_D7         = 6
LCD_BACKPACK_LITE       = 7

class Adafruit_CharLCD(object):
    """Class to represent and interact with an HD44780 character LCD display."""

    def __init__(self, rs, en, d4, d5, d6, d7, cols, lines, backlight=None,
                    invert_polarity=True,
                    enable_pwm=False,
                    gpio=GPIO.get_platform_gpio(),
                    pwm=PWM.get_platform_pwm(),
                    initial_backlight=1.0):
        """Initialize the LCD.  RS, EN, and D4...D7 parameters should be the pins
        connected to the LCD RS, clock enable, and data line 4 through 7 connections.
        The LCD will be used in its 4-bit mode so these 6 lines are the only ones
        required to use the LCD.  You must also pass in the number of columns and
        lines on the LCD.  

        If you would like to control the backlight, pass in the pin connected to
        the backlight with the backlight parameter.  The invert_polarity boolean
        controls if the backlight is one with a LOW signal or HIGH signal.  The 
        default invert_polarity value is True, i.e. the backlight is on with a
        LOW signal.  

        You can enable PWM of the backlight pin to have finer control on the 
        brightness.  To enable PWM make sure your hardware supports PWM on the 
        provided backlight pin and set enable_pwm to True (the default is False).
        The appropriate PWM library will be used depending on the platform, but
        you can provide an explicit one with the pwm parameter.

        The initial state of the backlight is ON, but you can set it to an 
        explicit initial state with the initial_backlight parameter (0 is off,
        1 is on/full bright).

        You can optionally pass in an explicit GPIO class,
        for example if you want to use an MCP230xx GPIO extender.  If you don't
        pass in an GPIO instance, the default GPIO for the running platform will
        be used.
        """
        # Save column and line state.
        self._cols = cols
        self._lines = lines
        # Save GPIO state and pin numbers.
        self._gpio = gpio
        self._rs = rs
        self._en = en
        self._d4 = d4
        self._d5 = d5
        self._d6 = d6
        self._d7 = d7
        # Save backlight state.
        self._backlight = backlight
        self._pwm_enabled = enable_pwm
        self._pwm = pwm
        self._blpol = not invert_polarity
        # Setup all pins as outputs.
        for pin in (rs, en, d4, d5, d6, d7):
            gpio.setup(pin, GPIO.OUT)
        # Setup backlight.
        if backlight is not None:
            if enable_pwm:
                pwm.start(backlight, self._pwm_duty_cycle(initial_backlight))
            else:
                gpio.setup(backlight, GPIO.OUT)
                gpio.output(backlight, self._blpol if initial_backlight else not self._blpol)
        # Initialize the display.
        self.write8(0x33)
        self.write8(0x32)
        # Initialize display control, function, and mode registers.
        self.displaycontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.displayfunction = LCD_4BITMODE | LCD_1LINE | LCD_2LINE | LCD_5x8DOTS
        self.displaymode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT
        # Write registers.
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write8(LCD_FUNCTIONSET | self.displayfunction)
        self.write8(LCD_ENTRYMODESET | self.displaymode)  # set the entry mode
        self.clear()

    def home(self):
        """Move the cursor back to its home (first line and first column)."""
        self.write8(LCD_RETURNHOME)  # set cursor position to zero
        self._delay_microseconds(3000)  # this command takes a long time!

    def clear(self):
        """Clear the LCD."""
        self.write8(LCD_CLEARDISPLAY)  # command to clear display
        self._delay_microseconds(3000)  # 3000 microsecond sleep, clearing the display takes a long time

    def set_cursor(self, col, row):
        """Move the cursor to an explicit column and row position."""
        # Clamp row to the last row of the display.
        if row > self._lines:
            row = self._lines - 1
        # Set location.
        self.write8(LCD_SETDDRAMADDR | (col + LCD_ROW_OFFSETS[row]))

    def enable_display(self, enable):
        """Enable or disable the display.  Set enable to True to enable."""
        if enable:
            self.displaycontrol |= LCD_DISPLAYON
        else:
            self.displaycontrol &= ~LCD_DISPLAYON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)

    def show_cursor(self, show):
        """Show or hide the cursor.  Cursor is shown if show is True."""
        if show:
            self.displaycontrol |= LCD_CURSORON
        else:
            self.displaycontrol &= ~LCD_CURSORON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)

    def blink(self, blink):
        """Turn on or off cursor blinking.  Set blink to True to enable blinking."""
        if blink:
            self.displaycontrol |= LCD_BLINKON
        else:
            self.displaycontrol &= ~LCD_BLINKON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)

    def move_left(self):
        """Move display left one position."""
        self.write8(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVELEFT)

    def move_right(self):
        """Move display right one position."""
        self.write8(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVERIGHT)

    def set_left_to_right(self):
        """Set text direction left to right."""
        self.displaymode |= LCD_ENTRYLEFT
        self.write8(LCD_ENTRYMODESET | self.displaymode)

    def set_right_to_left(self):
        """Set text direction right to left."""
        self.displaymode &= ~LCD_ENTRYLEFT
        self.write8(LCD_ENTRYMODESET | self.displaymode)

    def autoscroll(self, autoscroll):
        """Autoscroll will 'right justify' text from the cursor if set True,
        otherwise it will 'left justify' the text.
        """
        if autoscroll:
            self.displaymode |= LCD_ENTRYSHIFTINCREMENT
        else:
            self.displaymode &= ~LCD_ENTRYSHIFTINCREMENT
        self.write8(LCD_ENTRYMODESET | self.displaymode)

    def message(self, text):
        """Write text to display.  Note that text can include newlines."""
        line = 0
        # Iterate through each character.
        for char in text:
            # Advance to next line if character is a new line.
            if char == '\n':
                line += 1
                # Move to left or right side depending on text direction.
                col = 0 if self.displaymode & LCD_ENTRYLEFT > 0 else self._cols-1
                self.set_cursor(col, line)
            # Write the character to the display.
            else:
                self.write8(ord(char), True)

    def set_backlight(self, backlight):
        """Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.
        """
        if self._backlight is not None:
            if self._pwm_enabled:
                self._pwm.set_duty_cycle(self._backlight, self._pwm_duty_cycle(backlight))
            else:
                self._gpio.output(self._backlight, self._blpol if backlight else not self._blpol)

    def write8(self, value, char_mode=False):
        """Write 8-bit value in character or data mode.  Value should be an int
        value from 0-255, and char_mode is True if character data or False if
        non-character data (default).
        """
        # One millisecond delay to prevent writing too quickly.
        self._delay_microseconds(1000)
        # Set character / data bit.
        self._gpio.output(self._rs, char_mode)
        # Write upper 4 bits.
        self._gpio.output_pins({ self._d4: ((value >> 4) & 1) > 0,
                                 self._d5: ((value >> 5) & 1) > 0,
                                 self._d6: ((value >> 6) & 1) > 0,
                                 self._d7: ((value >> 7) & 1) > 0 })
        self._pulse_enable()
        # Write lower 4 bits.
        self._gpio.output_pins({ self._d4: (value        & 1) > 0,
                                 self._d5: ((value >> 1) & 1) > 0,
                                 self._d6: ((value >> 2) & 1) > 0,
                                 self._d7: ((value >> 3) & 1) > 0 })
        self._pulse_enable()

    def create_char(self, location, pattern):
        """Fill one of the first 8 CGRAM locations with custom characters.
        The location parameter should be between 0 and 7 and pattern should
        provide an array of 8 bytes containing the pattern. E.g. you can easyly
        design your custom character at http://www.quinapalus.com/hd44780udg.html
        To show your custom character use eg. lcd.message('\x01')
        """
        # only position 0..7 are allowed
        location &= 0x7
        self.write8(LCD_SETCGRAMADDR | (location << 3))
        for i in range(8):
            self.write8(pattern[i], char_mode=True)

    def _delay_microseconds(self, microseconds):
        # Busy wait in loop because delays are generally very short (few microseconds).
        end = time.time() + (microseconds/1000000.0)
        while time.time() < end:
            pass

    def _pulse_enable(self):
        # Pulse the clock enable line off, on, off to send command.
        self._gpio.output(self._en, False)
        self._delay_microseconds(1)       # 1 microsecond pause - enable pulse must be > 450ns
        self._gpio.output(self._en, True)
        self._delay_microseconds(1)       # 1 microsecond pause - enable pulse must be > 450ns
        self._gpio.output(self._en, False)
        self._delay_microseconds(1)       # commands need > 37us to settle

    def _pwm_duty_cycle(self, intensity):
        # Convert intensity value of 0.0 to 1.0 to a duty cycle of 0.0 to 100.0
        intensity = 100.0*intensity
        # Invert polarity if required.
        if not self._blpol:
            intensity = 100.0-intensity
        return intensity


class Adafruit_RGBCharLCD(Adafruit_CharLCD):
    """Class to represent and interact with an HD44780 character LCD display with
    an RGB backlight."""

    def __init__(self, rs, en, d4, d5, d6, d7, cols, lines, red, green, blue,
                 gpio=GPIO.get_platform_gpio(), 
                 invert_polarity=True,
                 enable_pwm=False,
                 pwm=PWM.get_platform_pwm(),
                 initial_color=(1.0, 1.0, 1.0)):
        """Initialize the LCD with RGB backlight.  RS, EN, and D4...D7 parameters 
        should be the pins connected to the LCD RS, clock enable, and data line 
        4 through 7 connections. The LCD will be used in its 4-bit mode so these 
        6 lines are the only ones required to use the LCD.  You must also pass in
        the number of columns and lines on the LCD.

        The red, green, and blue parameters define the pins which are connected
        to the appropriate backlight LEDs.  The invert_polarity parameter is a
        boolean that controls if the LEDs are on with a LOW or HIGH signal.  By
        default invert_polarity is True, i.e. the backlight LEDs are on with a
        low signal.  If you want to enable PWM on the backlight LEDs (for finer
        control of colors) and the hardware supports PWM on the provided pins,
        set enable_pwm to True.  Finally you can set an explicit initial backlight
        color with the initial_color parameter.  The default initial color is
        white (all LEDs lit).

        You can optionally pass in an explicit GPIO class,
        for example if you want to use an MCP230xx GPIO extender.  If you don't
        pass in an GPIO instance, the default GPIO for the running platform will
        be used.
        """
        super(Adafruit_RGBCharLCD, self).__init__(rs, en, d4, d5, d6, d7,
                                                  cols,
                                                  lines, 
                                                  enable_pwm=enable_pwm,
                                                  backlight=None,
                                                  invert_polarity=invert_polarity,
                                                  gpio=gpio, 
                                                  pwm=pwm)
        self._red = red
        self._green = green
        self._blue = blue
        # Setup backlight pins.
        if enable_pwm:
            # Determine initial backlight duty cycles.
            rdc, gdc, bdc = self._rgb_to_duty_cycle(initial_color)
            pwm.start(red, rdc)
            pwm.start(green, gdc)
            pwm.start(blue, bdc)
        else:
            gpio.setup(red, GPIO.OUT)
            gpio.setup(green, GPIO.OUT)
            gpio.setup(blue, GPIO.OUT)
            self._gpio.output_pins(self._rgb_to_pins(initial_color))

    def _rgb_to_duty_cycle(self, rgb):
        # Convert tuple of RGB 0-1 values to tuple of duty cycles (0-100).
        red, green, blue = rgb
        # Clamp colors between 0.0 and 1.0
        red = max(0.0, min(1.0, red))
        green = max(0.0, min(1.0, green))
        blue = max(0.0, min(1.0, blue))
        return (self._pwm_duty_cycle(red), 
                self._pwm_duty_cycle(green),
                self._pwm_duty_cycle(blue))

    def _rgb_to_pins(self, rgb):
        # Convert tuple of RGB 0-1 values to dict of pin values.
        red, green, blue = rgb
        return { self._red:   self._blpol if red else not self._blpol,
                 self._green: self._blpol if green else not self._blpol,
                 self._blue:  self._blpol if blue else not self._blpol }

    def set_color(self, red, green, blue):
        """Set backlight color to provided red, green, and blue values.  If PWM
        is enabled then color components can be values from 0.0 to 1.0, otherwise
        components should be zero for off and non-zero for on.
        """
        if self._pwm_enabled:
            # Set duty cycle of PWM pins.
            rdc, gdc, bdc = self._rgb_to_duty_cycle((red, green, blue))
            self._pwm.set_duty_cycle(self._red, rdc)
            self._pwm.set_duty_cycle(self._green, gdc)
            self._pwm.set_duty_cycle(self._blue, bdc)
        else:
            # Set appropriate backlight pins based on polarity and enabled colors.
            self._gpio.output_pins({self._red:   self._blpol if red else not self._blpol,
                                    self._green: self._blpol if green else not self._blpol,
                                    self._blue:  self._blpol if blue else not self._blpol })

    def set_backlight(self, backlight):
        """Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.  On an RGB display this
        function will set the backlight to all white.
        """
        self.set_color(backlight, backlight, backlight)



class Adafruit_CharLCDPlate(Adafruit_RGBCharLCD):
    """Class to represent and interact with an Adafruit Raspberry Pi character
    LCD plate."""

    def __init__(self, address=0x20, busnum=I2C.get_default_bus(), cols=16, lines=2):
        """Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        """
        # Configure MCP23017 device.
        self._mcp = MCP.MCP23017(address=address, busnum=busnum)
        # Set LCD R/W pin to low for writing only.
        self._mcp.setup(LCD_PLATE_RW, GPIO.OUT)
        self._mcp.output(LCD_PLATE_RW, GPIO.LOW)
        # Set buttons as inputs with pull-ups enabled.
        for button in (SELECT, RIGHT, DOWN, UP, LEFT):
            self._mcp.setup(button, GPIO.IN)
            self._mcp.pullup(button, True)
        # Initialize LCD (with no PWM support).
        super(Adafruit_CharLCDPlate, self).__init__(LCD_PLATE_RS, LCD_PLATE_EN,
            LCD_PLATE_D4, LCD_PLATE_D5, LCD_PLATE_D6, LCD_PLATE_D7, cols, lines,
            LCD_PLATE_RED, LCD_PLATE_GREEN, LCD_PLATE_BLUE, enable_pwm=False, 
            gpio=self._mcp)

    def is_pressed(self, button):
        """Return True if the provided button is pressed, False otherwise."""
        if button not in set((SELECT, RIGHT, DOWN, UP, LEFT)):
            raise ValueError('Unknown button, must be SELECT, RIGHT, DOWN, UP, or LEFT.')
        return self._mcp.input(button) == GPIO.LOW
    

class Adafruit_CharLCDBackpack(Adafruit_CharLCD):
    """Class to represent and interact with an Adafruit I2C / SPI
    LCD backpack using I2C."""
    
    def __init__(self, address=0x20, busnum=I2C.get_default_bus(), cols=16, lines=2):
        """Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        """
        # Configure the MCP23008 device.
        self._mcp = MCP.MCP23008(address=address, busnum=busnum)
        # Initialize LCD (with no PWM support).
        super(Adafruit_CharLCDBackpack, self).__init__(LCD_BACKPACK_RS, LCD_BACKPACK_EN,
            LCD_BACKPACK_D4, LCD_BACKPACK_D5, LCD_BACKPACK_D6, LCD_BACKPACK_D7,
            cols, lines, LCD_BACKPACK_LITE, enable_pwm=False, gpio=self._mcp)ó
íËú[c           @   sÓ  d  d l  Z  d  d l Z d  d l j Z d  d l j Z d  d l j	 Z	 d Z
 d Z d Z d Z d Z d Z d Z d	 Z d
 Z d Z d Z d
 Z d Z d
 Z d Z d
 Z d Z d
 Z d Z d
 Z d Z d
 Z d Z  d
 Z! d Z" d
 Z# d Z$ d
 Z% d  Z& d Z' d Z( d Z) d Z* d Z+ d Z, d Z- d Z. d Z/ d Z0 d
 Z1 d Z2 d Z3 d Z4 d Z5 d Z6 d Z7 d Z8 d Z9 d Z: d Z; d Z< d e= f d „  ƒ  YZ> d e> f d „  ƒ  YZ? d e? f d „  ƒ  YZ@ d e> f d „  ƒ  YZA d S(!   iÿÿÿÿNi   i   i   i   i   i    i@   i€   i    i   iT   i   i   i   i   i   i
   i	   i   i   i   i   t   Adafruit_CharLCDc           B   sÚ   e  Z d  Z d e e e j ƒ  e j	 ƒ  d d „ Z
 d „  Z d „  Z d „  Z d „  Z d „  Z d „  Z d	 „  Z d
 „  Z d „  Z d „  Z d „  Z d „  Z d „  Z e d „ Z d „  Z d „  Z d „  Z d „  Z RS(   sF   Class to represent and interact with an HD44780 character LCD display.g      ğ?c         C   sª  | |  _  | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ |	 |  _	 | |  _
 | |  _ |
 |  _ x3 | | | | | | f D] } | j | t j ƒ q W|	 d k	 r| rÚ | j |	 |  j | ƒ ƒ q| j |	 t j ƒ | j |	 | r|  j n |  j ƒ n  |  j d ƒ |  j d ƒ t t Bt B|  _ t t Bt Bt B|  _ t t B|  _  |  j t! |  j Bƒ |  j t" |  j Bƒ |  j t# |  j  Bƒ |  j$ ƒ  d S(   sç  Initialize the LCD.  RS, EN, and D4...D7 parameters should be the pins
        connected to the LCD RS, clock enable, and data line 4 through 7 connections.
        The LCD will be used in its 4-bit mode so these 6 lines are the only ones
        required to use the LCD.  You must also pass in the number of columns and
        lines on the LCD.  

        If you would like to control the backlight, pass in the pin connected to
        the backlight with the backlight parameter.  The invert_polarity boolean
        controls if the backlight is one with a LOW signal or HIGH signal.  The 
        default invert_polarity value is True, i.e. the backlight is on with a
        LOW signal.  

        You can enable PWM of the backlight pin to have finer control on the 
        brightness.  To enable PWM make sure your hardware supports PWM on the 
        provided backlight pin and set enable_pwm to True (the default is False).
        The appropriate PWM library will be used depending on the platform, but
        you can provide an explicit one with the pwm parameter.

        The initial state of the backlight is ON, but you can set it to an 
        explicit initial state with the initial_backlight parameter (0 is off,
        1 is on/full bright).

        You can optionally pass in an explicit GPIO class,
        for example if you want to use an MCP230xx GPIO extender.  If you don't
        pass in an GPIO instance, the default GPIO for the running platform will
        be used.
        i3   i2   N(%   t   _colst   _linest   _gpiot   _rst   _ent   _d4t   _d5t   _d6t   _d7t
   _backlightt   _pwm_enabledt   _pwmt   _blpolt   setupt   GPIOt   OUTt   Nonet   startt   _pwm_duty_cyclet   outputt   write8t   LCD_DISPLAYONt   LCD_CURSOROFFt   LCD_BLINKOFFt   displaycontrolt   LCD_4BITMODEt	   LCD_1LINEt	   LCD_2LINEt   LCD_5x8DOTSt   displayfunctiont   LCD_ENTRYLEFTt   LCD_ENTRYSHIFTDECREMENTt   displaymodet   LCD_DISPLAYCONTROLt   LCD_FUNCTIONSETt   LCD_ENTRYMODESETt   clear(   t   selft   rst   ent   d4t   d5t   d6t   d7t   colst   linest	   backlightt   invert_polarityt
   enable_pwmt   gpiot   pwmt   initial_backlightt   pin(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   __init__e   s:    "												
&c         C   s   |  j  t ƒ |  j d ƒ d S(   s?   Move the cursor back to its home (first line and first column).i¸  N(   R   t   LCD_RETURNHOMEt   _delay_microseconds(   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   home­   s    c         C   s   |  j  t ƒ |  j d ƒ d S(   s   Clear the LCD.i¸  N(   R   t   LCD_CLEARDISPLAYR8   (   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR%   ²   s    c         C   s<   | |  j  k r |  j  d } n  |  j t | t | Bƒ d S(   s7   Move the cursor to an explicit column and row position.i   N(   R   R   t   LCD_SETDDRAMADDRt   LCD_ROW_OFFSETS(   R&   t   colt   row(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt
   set_cursor·   s    c         C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  Bƒ d S(   s=   Enable or disable the display.  Set enable to True to enable.N(   R   R   R   R"   (   R&   t   enable(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   enable_display¿   s    c         C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  Bƒ d S(   s:   Show or hide the cursor.  Cursor is shown if show is True.N(   R   t   LCD_CURSORONR   R"   (   R&   t   show(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   show_cursorÇ   s    c         C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  Bƒ d S(   sF   Turn on or off cursor blinking.  Set blink to True to enable blinking.N(   R   t   LCD_BLINKONR   R"   (   R&   t   blink(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRF   Ï   s    c         C   s   |  j  t t Bt Bƒ d S(   s   Move display left one position.N(   R   t   LCD_CURSORSHIFTt   LCD_DISPLAYMOVEt   LCD_MOVELEFT(   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt	   move_left×   s    c         C   s   |  j  t t Bt Bƒ d S(   s    Move display right one position.N(   R   RG   RH   t   LCD_MOVERIGHT(   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt
   move_rightÛ   s    c         C   s'   |  j  t O_  |  j t |  j  Bƒ d S(   s!   Set text direction left to right.N(   R!   R   R   R$   (   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   set_left_to_rightß   s    c         C   s(   |  j  t M_  |  j t |  j  Bƒ d S(   s!   Set text direction right to left.N(   R!   R   R   R$   (   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   set_right_to_leftä   s    c         C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  Bƒ d S(   s}   Autoscroll will 'right justify' text from the cursor if set True,
        otherwise it will 'left justify' the text.
        N(   R!   t   LCD_ENTRYSHIFTINCREMENTR   R$   (   R&   t
   autoscroll(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRP   é   s    c         C   s€   d } xs | D]k } | d k rb | d 7} |  j  t @d k rB d n
 |  j d } |  j | | ƒ q |  j t | ƒ t ƒ q Wd S(   s<   Write text to display.  Note that text can include newlines.i    s   
i   N(   R!   R   R   R?   R   t   ordt   True(   R&   t   textt   linet   charR=   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   messageó   s    
&c         C   sj   |  j  d k	 rf |  j r: |  j j |  j  |  j | ƒ ƒ qf |  j j |  j  | rX |  j n |  j ƒ n  d S(   s%  Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.
        N(	   R
   R   R   R   t   set_duty_cycleR   R   R   R   (   R&   R/   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   set_backlight  s    	"c         C   s  |  j  d ƒ |  j j |  j | ƒ |  j j i | d ?d @d k |  j 6| d ?d @d k |  j 6| d ?d @d k |  j 6| d ?d @d k |  j 6ƒ |  j	 ƒ  |  j j i | d @d k |  j 6| d ?d @d k |  j 6| d ?d @d k |  j 6| d	 ?d @d k |  j 6ƒ |  j	 ƒ  d
 S(   sÁ   Write 8-bit value in character or data mode.  Value should be an int
        value from 0-255, and char_mode is True if character data or False if
        non-character data (default).
        iè  i   i   i    i   i   i   i   i   N(
   R8   R   R   R   t   output_pinsR   R   R   R	   t   _pulse_enable(   R&   t   valuet	   char_mode(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR     s    $
 c         C   sQ   | d M} |  j  t | d >Bƒ x+ t d ƒ D] } |  j  | | d t ƒq, Wd S(   su  Fill one of the first 8 CGRAM locations with custom characters.
        The location parameter should be between 0 and 7 and pattern should
        provide an array of 8 bytes containing the pattern. E.g. you can easyly
        design your custom character at http://www.quinapalus.com/hd44780udg.html
        To show your custom character use eg. lcd.message('')
        i   i   i   R\   N(   R   t   LCD_SETCGRAMADDRt   rangeRR   (   R&   t   locationt   patternt   i(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   create_char$  s    
c         C   s1   t  j  ƒ  | d } x t  j  ƒ  | k  r, q Wd  S(   Ng    €„.A(   t   time(   R&   t   microsecondst   end(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR8   1  s    c         C   sm   |  j  j |  j t ƒ |  j d ƒ |  j  j |  j t ƒ |  j d ƒ |  j  j |  j t ƒ |  j d ƒ d  S(   Ni   (   R   R   R   t   FalseR8   RR   (   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRZ   7  s    c         C   s$   d | } |  j  s  d | } n  | S(   Ng      Y@(   R   (   R&   t	   intensity(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR   @  s    
	N(   t   __name__t
   __module__t   __doc__R   RR   Rf   R   t   get_platform_gpiot   PWMt   get_platform_pwmR6   R9   R%   R?   RA   RD   RF   RJ   RL   RM   RN   RP   RV   RX   R   Rb   R8   RZ   R   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR    b   s2   		C											
						t   Adafruit_RGBCharLCDc           B   sV   e  Z d  Z e j ƒ  e e e j ƒ  d d „ Z	 d „  Z
 d „  Z d „  Z d „  Z RS(   s`   Class to represent and interact with an HD44780 character LCD display with
    an RGB backlight.g      ğ?c         C   s  t  t |  ƒ j | | | | | | | | d | d d d | d | d | ƒ|	 |  _ |
 |  _ | |  _ | rµ |  j | ƒ \ } } } | j |	 | ƒ | j |
 | ƒ | j | | ƒ nR | j	 |	 t
 j ƒ | j	 |
 t
 j ƒ | j	 | t
 j ƒ |  j j |  j | ƒ ƒ d S(   s  Initialize the LCD with RGB backlight.  RS, EN, and D4...D7 parameters 
        should be the pins connected to the LCD RS, clock enable, and data line 
        4 through 7 connections. The LCD will be used in its 4-bit mode so these 
        6 lines are the only ones required to use the LCD.  You must also pass in
        the number of columns and lines on the LCD.

        The red, green, and blue parameters define the pins which are connected
        to the appropriate backlight LEDs.  The invert_polarity parameter is a
        boolean that controls if the LEDs are on with a LOW or HIGH signal.  By
        default invert_polarity is True, i.e. the backlight LEDs are on with a
        low signal.  If you want to enable PWM on the backlight LEDs (for finer
        control of colors) and the hardware supports PWM on the provided pins,
        set enable_pwm to True.  Finally you can set an explicit initial backlight
        color with the initial_color parameter.  The default initial color is
        white (all LEDs lit).

        You can optionally pass in an explicit GPIO class,
        for example if you want to use an MCP230xx GPIO extender.  If you don't
        pass in an GPIO instance, the default GPIO for the running platform will
        be used.
        R1   R/   R0   R2   R3   N(   t   superRn   R6   R   t   _redt   _greent   _bluet   _rgb_to_duty_cycleR   R   R   R   R   RY   t   _rgb_to_pins(   R&   R'   R(   R)   R*   R+   R,   R-   R.   t   redt   greent   blueR2   R0   R1   R3   t   initial_colort   rdct   gdct   bdc(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR6   M  s(    !			c         C   s   | \ } } } t  d t d | ƒ ƒ } t  d t d | ƒ ƒ } t  d t d | ƒ ƒ } |  j | ƒ |  j | ƒ |  j | ƒ f S(   Ng        g      ğ?(   t   maxt   minR   (   R&   t   rgbRu   Rv   Rw   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRs   €  s    c         C   sj   | \ } } } i | r! |  j  n |  j  |  j 6| r> |  j  n |  j  |  j 6| r[ |  j  n |  j  |  j 6S(   N(   R   Rp   Rq   Rr   (   R&   R~   Ru   Rv   Rw   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRt   ‹  s     c         C   sÚ   |  j  ro |  j | | | f ƒ \ } } } |  j j |  j | ƒ |  j j |  j | ƒ |  j j |  j | ƒ ng |  j j i | rŠ |  j	 n |  j	 |  j 6| r§ |  j	 n |  j	 |  j 6| rÄ |  j	 n |  j	 |  j 6ƒ d S(   sŞ   Set backlight color to provided red, green, and blue values.  If PWM
        is enabled then color components can be values from 0.0 to 1.0, otherwise
        components should be zero for off and non-zero for on.
        N(
   R   Rs   R   RW   Rp   Rq   Rr   R   RY   R   (   R&   Ru   Rv   Rw   Ry   Rz   R{   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt	   set_color’  s    	!)c         C   s   |  j  | | | ƒ d S(   ss  Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.  On an RGB display this
        function will set the backlight to all white.
        N(   R   (   R&   R/   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRX   £  s    (   g      ğ?g      ğ?g      ğ?(   Rh   Ri   Rj   R   Rk   RR   Rf   Rl   Rm   R6   Rs   Rt   R   RX   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRn   I  s   		.			t   Adafruit_CharLCDPlatec           B   s2   e  Z d  Z d e j ƒ  d d d „ Z d „  Z RS(   sV   Class to represent and interact with an Adafruit Raspberry Pi character
    LCD plate.i    i   i   c         C   s×   t  j d | d | ƒ |  _ |  j j t t j ƒ |  j j t t j ƒ xF t	 t
 t t t f D]/ } |  j j | t j ƒ |  j j | t ƒ q] Wt t |  ƒ j t t t t t t | | t t t d t d |  j ƒd S(   s  Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        t   addresst   busnumR1   R2   N(   t   MCPt   MCP23017t   _mcpR   t   LCD_PLATE_RWR   R   R   t   LOWt   SELECTt   RIGHTt   DOWNt   UPt   LEFTt   INt   pullupRR   Ro   R€   R6   t   LCD_PLATE_RSt   LCD_PLATE_ENt   LCD_PLATE_D4t   LCD_PLATE_D5t   LCD_PLATE_D6t   LCD_PLATE_D7t   LCD_PLATE_REDt   LCD_PLATE_GREENt   LCD_PLATE_BLUERf   (   R&   R   R‚   R-   R.   t   button(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR6   ²  s    c         C   sI   | t  t t t t t f ƒ k r0 t d ƒ ‚ n  |  j j | ƒ t	 j
 k S(   s?   Return True if the provided button is pressed, False otherwise.s9   Unknown button, must be SELECT, RIGHT, DOWN, UP, or LEFT.(   t   setRˆ   R‰   RŠ   R‹   RŒ   t
   ValueErrorR…   t   inputR   R‡   (   R&   R˜   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt
   is_pressedÇ  s    !(   Rh   Ri   Rj   t   I2Ct   get_default_busR6   Rœ   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR€   ®  s   t   Adafruit_CharLCDBackpackc           B   s)   e  Z d  Z d e j ƒ  d d d „ Z RS(   sV   Class to represent and interact with an Adafruit I2C / SPI
    LCD backpack using I2C.i    i   i   c         C   s\   t  j d | d | ƒ |  _ t t |  ƒ j t t t t	 t
 t | | t d t d |  j ƒ	d S(   s  Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        R   R‚   R1   R2   N(   Rƒ   t   MCP23008R…   Ro   RŸ   R6   t   LCD_BACKPACK_RSt   LCD_BACKPACK_ENt   LCD_BACKPACK_D4t   LCD_BACKPACK_D5t   LCD_BACKPACK_D6t   LCD_BACKPACK_D7t   LCD_BACKPACK_LITERf   (   R&   R   R‚   R-   R.   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR6   Ò  s    (   Rh   Ri   Rj   R   R   R6   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRŸ   Î  s   (   i    i@   i   iT   (B   Rc   t   Adafruit_GPIOR   t   Adafruit_GPIO.I2CR   t   Adafruit_GPIO.MCP230xxt   MCP230xxRƒ   t   Adafruit_GPIO.PWMRl   R:   R7   R$   R"   RG   R#   R]   R;   t   LCD_ENTRYRIGHTR   RO   R    R   t   LCD_DISPLAYOFFRB   R   RE   R   RH   t   LCD_CURSORMOVERK   RI   t   LCD_8BITMODER   R   R   t   LCD_5x10DOTSR   R<   R   R†   R   R‘   R’   R“   R”   R•   R–   R—   Rˆ   R‰   RŠ   R‹   RŒ   R¡   R¢   R£   R¤   R¥   R¦   R§   t   objectR    Rn   R€   RŸ   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   <module>   sv   çe dist/
build
*.egg-info
*.pyc
setuptools-*
DEPRECATED LIBRARY. Adafruit Python CharLCD
=======================

This library has been deprecated! We are leaving this up for historical and research purposes but archiving the repository.

We are now only supporting the use of our CircuitPython libraries for use with Python. 

Check out this guide for info on using character LCDs with the CircuitPython library: https://learn.adafruit.com/character-lcds/python-circuitpython


**Adafruit_Python_CharLCD**

Python library for accessing Adafruit character LCDs from a Raspberry Pi or BeagleBone Black.

Designed specifically to work with the Adafruit character LCDs ----> https://learn.adafruit.com/character-lcds/overview

For all platforms (Raspberry Pi and Beaglebone Black) make sure you have the following dependencies:

````
sudo apt-get update
sudo apt-get install build-essential python-dev python-smbus python-pip
````

For a Raspberry Pi make sure you have the RPi.GPIO library by executing:

````
sudo pip install RPi.GPIO
````

For a BeagleBone Black make sure you have the Adafruit_BBIO library by executing:

````
sudo pip install Adafruit_BBIO
````

Install the library by downloading with the download link on the right, unzipping the archive, navigating inside the library's directory and executing:

````
sudo python setup.py install
````

See example of usage in the examples folder.

Adafruit invests time and resources providing this open source code, please support Adafruit and open-source hardware by purchasing products from Adafruit!

Written by Tony DiCola for Adafruit Industries.

MIT license, all text above must be included in any redistribution
try:
    # Try using ez_setup to install setuptools if not already installed.
    from ez_setup import use_setuptools
    use_setuptools()
except ImportError:
    # Ignore import error and assume Python 3 which already has setuptools.
    pass

from setuptools import setup, find_packages

classifiers = ['Development Status :: 4 - Beta',
               'Operating System :: POSIX :: Linux',
               'License :: OSI Approved :: MIT License',
               'Intended Audience :: Developers',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 3',
               'Topic :: Software Development',
               'Topic :: System :: Hardware']

setup(name              = 'Adafruit_CharLCD',
      version           = '1.1.1',
      author            = 'Tony DiCola',
      author_email      = 'tdicola@adafruit.com',
      description       = 'Library to drive character LCD display and plate.',
      license           = 'MIT',
	  classifiers       = classifiers,
      url               = 'https://github.com/adafruit/Adafruit_Python_CharLCD/',
      dependency_links  = ['https://github.com/adafruit/Adafruit_Python_GPIO/tarball/master#egg=Adafruit-GPIO-0.4.0'],
      install_requires  = ['Adafruit-GPIO>=0.4.0'],
      packages          = find_packages())
#!/usr/bin/python
# Example using an RGB character LCD with PWM control of the backlight.
import math
import time

import Adafruit_CharLCD as LCD


def hsv_to_rgb(hsv):
    """Converts a tuple of hue, saturation, value to a tuple of red, green blue.
    Hue should be an angle from 0.0 to 359.0.  Saturation and value should be a
    value from 0.0 to 1.0, where saturation controls the intensity of the hue and
    value controls the brightness.
    """
    # Algorithm adapted from http://www.cs.rit.edu/~ncs/color/t_convert.html
    h, s, v = hsv
    if s == 0:
        return (v, v, v)
    h /= 60.0
    i = math.floor(h)
    f = h-i
    p = v*(1.0-s)
    q = v*(1.0-s*f)
    t = v*(1.0-s*(1.0-f))
    if i == 0:
        return (v, t, p)
    elif i == 1:
        return (q, v, p)
    elif i == 2:
        return (p, v, t)
    elif i == 3:
        return (p, q, v)
    elif i == 4:
        return (t, p, v)
    else:
        return (v, p, q)

# Raspberry Pi configuration:
lcd_rs = 27  # Change this to pin 21 on older revision Raspberry Pi's
lcd_en = 22
lcd_d4 = 25
lcd_d5 = 24
lcd_d6 = 23
lcd_d7 = 18
lcd_red   = 4
lcd_green = 17
lcd_blue  = 7  # Pin 7 is CE1

# BeagleBone Black configuration:
# lcd_rs = 'P8_8'
# lcd_en = 'P8_10'
# lcd_d4 = 'P8_18'
# lcd_d5 = 'P8_16'
# lcd_d6 = 'P8_14'
# lcd_d7 = 'P8_12'
# lcd_red   = 'P9_16'
# lcd_green = 'P9_14'
# lcd_blue  = 'P8_13'

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Alternatively specify a 20x4 LCD.
# lcd_columns = 20
# lcd_rows    = 4

# Initialize the LCD using the pins
lcd = LCD.Adafruit_RGBCharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                              lcd_columns, lcd_rows, lcd_red, lcd_green, lcd_blue,
                              enable_pwm=True)

# Show some basic colors.
lcd.set_color(1.0, 0.0, 0.0)
lcd.clear()
lcd.message('RED')
time.sleep(3.0)

lcd.set_color(0.0, 1.0, 0.0)
lcd.clear()
lcd.message('GREEN')
time.sleep(3.0)

lcd.set_color(0.0, 0.0, 1.0)
lcd.clear()
lcd.message('BLUE')
time.sleep(3.0)

lcd.set_color(1.0, 1.0, 0.0)
lcd.clear()
lcd.message('YELLOW')
time.sleep(3.0)

lcd.set_color(0.0, 1.0, 1.0)
lcd.clear()
lcd.message('CYAN')
time.sleep(3.0)

lcd.set_color(1.0, 0.0, 1.0)
lcd.clear()
lcd.message('MAGENTA')
time.sleep(3.0)

lcd.set_color(1.0, 1.0, 1.0)
lcd.clear()
lcd.message('WHITE')
time.sleep(3.0)

# Use HSV color space so the hue can be adjusted to see a nice gradient of colors.
# Hue ranges from 0.0 to 359.0, saturation from 0.0 to 1.0, and value from 0.0 to 1.0.
hue = 0.0
saturation = 1.0
value = 1.0

# Loop through all RGB colors.
lcd.clear()
print('Press Ctrl-C to quit.')
while True:
    # Convert HSV to RGB colors.
    red, green, blue = hsv_to_rgb((hue, saturation, value))
    # Set backlight color.
    lcd.set_color(red, green, blue)
    # Print message with RGB values to display.
    lcd.set_cursor(0, 0)
    lcd.message('RED  GREEN  BLUE\n{0:0.2f}  {1:0.2f}  {2:0.2f}'.format(red, green, blue))
    # Increment hue (wrapping around at 360 degrees).
    hue += 1.0
    if hue > 359.0:
        hue = 0.0
#!/usr/bin/python
# Example using a character LCD connected to a Raspberry Pi or BeagleBone Black.
import time

import Adafruit_CharLCD as LCD
# Raspberry Pi pin setup for LCD
lcd_rs = 27
lcd_en = 24
lcd_d4 = 23
lcd_d5 = 17
lcd_d6 = 18
lcd_d7 = 22
lcd_backlight = 2

# Raspberry Pi pin configuration:
#lcd_rs        = 27  # Note this might need to be changed to 21 for older revision Pi's.
#lcd_en        = 22
#lcd_d4        = 25
#lcd_d5        = 24
#lcd_d6        = 23
#lcd_d7        = 18
#lcd_backlight = 4

# BeagleBone Black configuration:
# lcd_rs        = 'P8_8'
# lcd_en        = 'P8_10'
# lcd_d4        = 'P8_18'
# lcd_d5        = 'P8_16'
# lcd_d6        = 'P8_14'
# lcd_d7        = 'P8_12'
# lcd_backlight = 'P8_7'

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Alternatively specify a 20x4 LCD.
# lcd_columns = 20
# lcd_rows    = 4

# Initialize the LCD using the pins above.
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                           lcd_columns, lcd_rows, lcd_backlight)

# Print a two line message
lcd.message('Hello\nworld!')

# Wait 5 seconds
time.sleep(5.0)

# Demo showing the cursor.
lcd.clear()
lcd.show_cursor(True)
lcd.message('Show cursor')

time.sleep(5.0)

# Demo showing the blinking cursor.
lcd.clear()
lcd.blink(True)
lcd.message('Blink cursor')

time.sleep(5.0)

# Stop blinking and showing cursor.
lcd.show_cursor(False)
lcd.blink(False)

# Demo scrolling message right/left.
lcd.clear()
message = 'Scroll'
lcd.message(message)
for i in range(lcd_columns-len(message)):
    time.sleep(0.5)
    lcd.move_right()
for i in range(lcd_columns-len(message)):
    time.sleep(0.5)
    lcd.move_left()

# Demo turning backlight off and on.
lcd.clear()
lcd.message('Flash backlight\nin 5 seconds...')
time.sleep(5.0)
# Turn backlight off.
lcd.set_backlight(0)
time.sleep(2.0)
# Change message.
lcd.clear()
lcd.message('Goodbye!')
# Turn backlight on.
lcd.set_backlight(1)
#!/usr/bin/python
# Example using a character LCD backpack.
import time

import Adafruit_CharLCD as LCD

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Initialize the LCD using the pins
lcd = LCD.Adafruit_CharLCDBackpack()

# Turn backlight on
lcd.set_backlight(0)

# Print a two line message
lcd.message('Hello\nworld!')

# Wait 5 seconds
time.sleep(5.0)

# Demo showing the cursor.
lcd.clear()
lcd.show_cursor(True)
lcd.message('Show cursor')

time.sleep(5.0)

# Demo showing the blinking cursor.
lcd.clear()
lcd.blink(True)
lcd.message('Blink cursor')

time.sleep(5.0)

# Stop blinking and showing cursor.
lcd.show_cursor(False)
lcd.blink(False)

# Demo scrolling message right/left.
lcd.clear()
message = 'Scroll'
lcd.message(message)
for i in range(lcd_columns-len(message)):
    time.sleep(0.5)
    lcd.move_right()
for i in range(lcd_columns-len(message)):
    time.sleep(0.5)
    lcd.move_left()

# Demo turning backlight off and on.
lcd.clear()
lcd.message('Flash backlight\nin 5 seconds...')
time.sleep(5.0)
# Turn backlight off.
lcd.set_backlight(1)
time.sleep(2.0)
# Change message.
lcd.clear()
lcd.message('Goodbye!')
# Turn backlight on.
lcd.set_backlight(0)#!/usr/bin/python
# Example using a character LCD plate.
import time

import Adafruit_CharLCD as LCD


# Initialize the LCD using the pins
lcd = LCD.Adafruit_CharLCDPlate()

# create some custom characters
lcd.create_char(1, [2, 3, 2, 2, 14, 30, 12, 0])
lcd.create_char(2, [0, 1, 3, 22, 28, 8, 0, 0])
lcd.create_char(3, [0, 14, 21, 23, 17, 14, 0, 0])
lcd.create_char(4, [31, 17, 10, 4, 10, 17, 31, 0])
lcd.create_char(5, [8, 12, 10, 9, 10, 12, 8, 0])
lcd.create_char(6, [2, 6, 10, 18, 10, 6, 2, 0])
lcd.create_char(7, [31, 17, 21, 21, 21, 21, 17, 31])

# Show some basic colors.
lcd.set_color(1.0, 0.0, 0.0)
lcd.clear()
lcd.message('RED \x01')
time.sleep(3.0)

lcd.set_color(0.0, 1.0, 0.0)
lcd.clear()
lcd.message('GREEN \x02')
time.sleep(3.0)

lcd.set_color(0.0, 0.0, 1.0)
lcd.clear()
lcd.message('BLUE \x03')
time.sleep(3.0)

lcd.set_color(1.0, 1.0, 0.0)
lcd.clear()
lcd.message('YELLOW \x04')
time.sleep(3.0)

lcd.set_color(0.0, 1.0, 1.0)
lcd.clear()
lcd.message('CYAN \x05')
time.sleep(3.0)

lcd.set_color(1.0, 0.0, 1.0)
lcd.clear()
lcd.message('MAGENTA \x06')
time.sleep(3.0)

lcd.set_color(1.0, 1.0, 1.0)
lcd.clear()
lcd.message('WHITE \x07')
time.sleep(3.0)

# Show button state.
lcd.clear()
lcd.message('Press buttons...')

# Make list of button value, text, and backlight color.
buttons = ( (LCD.SELECT, 'Select', (1,1,1)),
            (LCD.LEFT,   'Left'  , (1,0,0)),
            (LCD.UP,     'Up'    , (0,0,1)),
            (LCD.DOWN,   'Down'  , (0,1,0)),
            (LCD.RIGHT,  'Right' , (1,0,1)) )

print('Press Ctrl-C to quit.')
while True:
    # Loop through each button and check if it is pressed.
    for button in buttons:
        if lcd.is_pressed(button[0]):
            # Button is pressed, change the message and backlight.
            lcd.clear()
            lcd.message(button[1])
            lcd.set_color(button[2][0], button[2][1], button[2][2])
#!/usr/bin/python
# Example using an RGB character LCD wired directly to Raspberry Pi or BeagleBone Black.
import time

import Adafruit_CharLCD as LCD


# Raspberry Pi configuration:
lcd_rs = 27  # Change this to pin 21 on older revision Raspberry Pi's
lcd_en = 22
lcd_d4 = 25
lcd_d5 = 24
lcd_d6 = 23
lcd_d7 = 18
lcd_red   = 4
lcd_green = 17
lcd_blue  = 7  # Pin 7 is CE1

# BeagleBone Black configuration:
# lcd_rs = 'P8_8'
# lcd_en = 'P8_10'
# lcd_d4 = 'P8_18'
# lcd_d5 = 'P8_16'
# lcd_d6 = 'P8_14'
# lcd_d7 = 'P8_12'
# lcd_red   = 'P8_7'
# lcd_green = 'P8_9'
# lcd_blue  = 'P8_11'

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Alternatively specify a 20x4 LCD.
# lcd_columns = 20
# lcd_rows    = 4

# Initialize the LCD using the pins above.
lcd = LCD.Adafruit_RGBCharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                              lcd_columns, lcd_rows, lcd_red, lcd_green, lcd_blue)

# Show some basic colors.
lcd.set_color(1.0, 0.0, 0.0)
lcd.clear()
lcd.message('RED')
time.sleep(3.0)

lcd.set_color(0.0, 1.0, 0.0)
lcd.clear()
lcd.message('GREEN')
time.sleep(3.0)

lcd.set_color(0.0, 0.0, 1.0)
lcd.clear()
lcd.message('BLUE')
time.sleep(3.0)

lcd.set_color(1.0, 1.0, 0.0)
lcd.clear()
lcd.message('YELLOW')
time.sleep(3.0)

lcd.set_color(0.0, 1.0, 1.0)
lcd.clear()
lcd.message('CYAN')
time.sleep(3.0)

lcd.set_color(1.0, 0.0, 1.0)
lcd.clear()
lcd.message('MAGENTA')
time.sleep(3.0)

lcd.set_color(1.0, 1.0, 1.0)
lcd.clear()
lcd.message('WHITE')
time.sleep(3.0)
#!/usr/bin/python
# Example using an RGB character LCD connected to an MCP23017 GPIO extender.
import time

import Adafruit_CharLCD as LCD
import Adafruit_GPIO.MCP230xx as MCP


# Define MCP pins connected to the LCD.
lcd_rs        = 0
lcd_en        = 1
lcd_d4        = 2
lcd_d5        = 3
lcd_d6        = 4
lcd_d7        = 5
lcd_red       = 6
lcd_green     = 7
lcd_blue      = 8

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Alternatively specify a 20x4 LCD.
# lcd_columns = 20
# lcd_rows    = 4

# Initialize MCP23017 device using its default 0x20 I2C address.
gpio = MCP.MCP23017()

# Alternatively you can initialize the MCP device on another I2C address or bus.
# gpio = MCP.MCP23017(0x24, busnum=1)

# Initialize the LCD using the pins
lcd = LCD.Adafruit_RGBCharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                              lcd_columns, lcd_rows, lcd_red, lcd_green, lcd_blue,
                              gpio=gpio)

# Print a two line message
lcd.message('Hello\nworld!')

# Wait 5 seconds
time.sleep(5.0)

# Demo showing the cursor.
lcd.clear()
lcd.show_cursor(True)
lcd.message('Show cursor')

time.sleep(5.0)

# Demo showing the blinking cursor.
lcd.clear()
lcd.blink(True)
lcd.message('Blink cursor')

time.sleep(5.0)

# Stop blinking and showing cursor.
lcd.show_cursor(False)
lcd.blink(False)

# Demo scrolling message right/left.
lcd.clear()
message = 'Scroll'
lcd.message(message)
for i in range(lcd_columns-len(message)):
    time.sleep(0.5)
    lcd.move_right()
for i in range(lcd_columns-len(message)):
    time.sleep(0.5)
    lcd.move_left()

# Demo turning backlight off and on.
lcd.clear()
lcd.message('Flash backlight\nin 5 seconds...')
time.sleep(5.0)
# Turn backlight off.
lcd.set_backlight(0)
time.sleep(2.0)
# Change message.
lcd.clear()
lcd.message('Goodbye!')
# Turn backlight on.
lcd.set_backlight(1)
