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
PK    s�yMEX��n   �      Adafruit_PureIO/__init__.pycc��˥��Wt20�� ��`���H�(� I��9)�I)��%z9�y���E�ef9������)�iE��%��E������y@^�^Ae	P�Mn~JiN�Ȋb�� PK    `�yM��*�  59     Adafruit_PureIO/smbus.py�[ao�8���_�4���q���]��qZ�&v`;�[�!K�ͫ,�D��qx���̐�(GΦ��u�A�[�pf��Ù�r$��z���2�)�O�~���'�JE?
2�&J�#���e�\�Imŕ�ơwp���d�RZ�8J��L�l+��2h�y"����_z�B�D��2ј�ROE*ZO�P�06]B�����K$���:���"��l%��KiŹ
��t)ų������!OE����F��,�$�|��� ?��#���k�t�y�3;HۖXŁ���%��f��˖	�e)����/#�[�ǉ�2$� �5��(ZgM�M��4}�Yƫ�5�t�gI�e%�
b��W���S��&��0�7d�G�"��o�O�Y�E�I	Q�Bc��ź�b�H/�03i=��Ua�enUB:�8P^(�q�Z�6J����z�3��X܍���W�+�3��g-�?y;���u�bx-:����%z�{7��b8�����M��o�����U�F����p"n���	�N�����I�mo�}��������C����ɽ�DG�uF�~���3w����� x�\��N�7���.��w� �o;77�E�=l���;��0�y;o�7W=|���:�ozf1�ֽ��o[�s�y��YC�!i��Q�ۣ/i��u'�ဌ��>�`�hRL~��Z�3��-ף�-�I�Ŝ!���A��!�W�C����W�W���a�;[�>x��Y��p�2�{ N��R�Bp��qp�E�Eb|�:Ӣs�oc���<��t��Ԋ�#�i)���/g�俽8�o�N~1��w��`OՉI$hdJ�-��l>�	�4��4K��2��4�g��O��A��B���Qs��U�}�e�|��&f��x�^9x�P^μ�d�T��kx� ���Io ܟKq�����T�#���TFbn�j-�  �i+`t%j��� ��R�x���C܃"V�L���dx�+�W� 	jN�O���)�t2�o����B��?�'�����5��\�޻�U4�\]��Y�߰j��`8�M���UϾIk�n������ק����7�����f~(�E���b8s�M�/�0�l���2���=ܽW�/Hʽ��h�ms��'NA�^u�/�'���������#]H���y�J�A�CV�}ݟ�Ӭ
/I�)N�D�b���X���~p�����:�����)s�xk��^���tK��BFW�G51���	�ƫ�������"E��� �G8��qn�,���r~%9�������Иّ���u��3 ��;� �:j ��4��%
2������*�a�6q1Yě��gw;��H���I9I�	����/�upy+�J��d.7'���'+	��>`�B��ӕ^4
bm^0���7L�v�]�Y��O�J����[\6�	2�%�7[γy�-�����}�����QѰ�K��#>8v$�&��)0%�tm����̽O4�ю~�_͊	�����G;pzʾ A���rZ��֮@�B�r�S���E�9V9cL$|��:�Y��%i�x����s�x8;����^K_�1�<ס-8]�?����":�H�F�D���4[S��X��l�C��1��QA���]�i2
L�l�zl-�`���p�S#^
J�L�EN�nϤ�1���B��Þ�<�-�<��j�s�:�o[���$ޖ}��Ӹs��0P�#�� `x��"ga�hR�te$U&5�cb�*T��2B]�`�]ȸ�>�OmrI5�>�~�j|u];ظ�}��v�w���3�A/>Yo���aQE���C4�m
F�[��>y�d+<���W
��'̖���F�UӃtP�O̐�TG��O}[���� 36��Ql�+NT�\�����J�8}�/ϙ�.8}�h7./M�*R�tڀs
}9��� �s�Hn�^a��l!����4&��$%}�����{���t�LLr�O��_=�]��3�ƒBVn��T��Y�@�P�1]�x�_
Z-���F�4U>��)�v�PZO��ֱ���U<SE�Q��b.-�������.��>��l����/�l%y�S��8Ŏ<��cM��F�J���ʯ��!����V���g�ns�1���D�qf���1�p'�L�-�%��#�L�gM�ir������0)���xb [*6~u�-��L��7����X��i��v��ZE>ml���}���Ұ�*���l��c:I"`�0��R�gU�a�<,s���2����n����^��	-�v�]��� �59s��u�������,vU<���ZEG�9�r�1����b��k}���,[���G��d�\i�I��^6��3{�������qZ���c�%���Ύ[�N��+�W���R�E�a�3��Kpz��J����!��O�Lj7$� �I�h!���
Y	��e�@X?�XjB��Ӧ$�'u����W$��C�Q$�r��2�[�B�Eu�<�Et0�-\��(�6P�Q�U��L�%����&J���u��2mK�
�l<^��H�E&h��gY%��PnT�&�Gq *zF��9M8��^eG�sBF��{��T'������q��w �ΓE����A�������V^ o-<:|���;QUu;۰K�qT�D�� ��v�Ѳ�C�SV�Q�Sz�7��51���|N0R�ڕU���=u������3C��6��$�I7�H�H|�1�v|� �¯ANq�,L���+���'N]���"���:j��8m���ހRM��s$ޣX����$�M��dJ�i$�N��-�����ɵ�ܘI��6��ږ~~�ͨ9��=� �V��o� O�1��s��oDr!o���崕���Q�a�r��t�G�e(�΁����8)��"�m��H�U��-��4s!�Cפ?sT��򳅕��j��VM'�YF[��X�����	�v�*9/�4��o}g��=�*�"�rl�8E���.����578�`�'�yX}�-�9qE���vKz��4�dn�՗�y�~��4��ʅ[�ȫ��:�T� !R�P~���t$����Zz! Q*=b����u�p��(N�?GtÀ�*t�PT�I����W���w?
d8�f.2��N�y
9?x�_v��Zi���qӲ����� �T��zcn�L�S����5��GQ�o�jq��딱�D<������a6�'c㢃O�l�{����#�� �ջ�x�f~]L�WG:����=
#Y��Z 3� H;,CrC������{+C��j�o_Wz��6-yaM�2�t���5͔�(0]0C��z��[#�6�:uh!j=ӻg�f�-]ʵ�y���<�b�7�i��z}M�L��h���;�H��~JV�i��Ɣy-$����?�3��a���o�1�m��?;���z��.�3 �����֫䉳�3���$��-t}�#���j��ZV{%8
�\�tJ�����w�
}��.���\�=i�^�1����������t�K���U�asJ8���'u��iBښA�j>���q{^�[��n���P����+b��]'~j�co����������`Ͽ�	�����BXт�9Z�6y��h_�Y�Tl_�~{�r0�r w}��q�{����z�p��o�OM�Mo���=;�7�P�[R�����yA�nP���q�o)�|�*���t�[��߯�+Xh�,�QS��ck+�����DUa��G��,���k�]<�g�Ky���ŧ*b(vjk���R�����|ǘ�'&IL��ۛ�]��M.�ľ��N���L�1 X��ۜ�D7����H�{�ܼpPI��٣"�����%Uc� �MU�-;�G�_�@{ZM�\z©[��L�i���c�e#��6��r�ľ[�VA^p�gA��u����6ٴ���a�u����ɛK6&j�G��ٶ���Ӯg�յ��VT^�V�UG�w��/��4s�g�Ǆ��Y���\�����8�W�;G(�U��-�����C�4L�d����V3��JU6��e��PK    `�yM              Adafruit_PureIO/__init__.py PK    s�yMs�0=y  �/     Adafruit_PureIO/smbus.pyc�ZK��V�R?fz</��q��Ig�8!����q2���T�P*MK=#[-u$��S�*Ne�
�bˎ5�Y6��TA���
�;�!���8q;��\_]]��9���9W��kf������~j�w���9K�@�6��l[�g��-z5Ѯ�^]�����5E�)z�=!,��q�Iў��h�dk]�S��G���놈�E{Z�����Y�Cs"���E0%�{E@���/��> �Y�>(�9�^��h�^�~D�D������"8 �GDpP�-ѥ���B���c"8�[1����0.�O��Q>ɷ���V���s��Փg�()¬�wB������NN�й�Sl���~�� w�/�.E���b�,&��xz��b��_x�r��ɢ�?/�{?婸~���ڕw��X�+�"��"��Moc��R��X/�A�dᢅ�*��S�k�<�h���P�F᠘G1���h¨�����b�$
gB�&:��z��A�y�z���Dj1�l�(���4�JMW�"�q���f�r���� �dp�QS99�m���Aƻ���f^ �q���$�E��e�y��=���^b\N�e�v<υP\��
�X7
� ��R�wx�(NlQ^,�X�s~ֻ�r|"��<���l�e���yoc�/�w\(O�XH�j�-��~%�,��<V���?d�,��#�J�t,E[IO�U):yH�$֜Ř��bsgQ̡�7���]���;$���>z�ɛJ*sV�Rh�����o��g���=p�jL��-nl��V7���x��j�V]ܬCD�I.�oR��8�ո�j�A���74ʆ����n�����M����$�u���-��"��b���N'�#-����B2Є���+�������AL�vTl9���������J������%ǹBT�/�����Fx�|+ā�V�)��:noE�-ZY?s�#&�(	��Q0��9h7r�����"j��$�y�X�T��I�§�/9a�h��U�K�9��x��ؒU�#)�!��,��;�b�O*
u7B������O���`�e@<0�&�^��h]X���
`҅Y�`Z�����bF�����m�R��L0�	�4���X^Ͽz<��6v19O�r�:h�߃L3s�8{&C,�&���&�C0��-xz�����&��	X	*�p䨴��Q��;Ge<:*�p�����2׎��;�vL7�ƽp�샏Ge?�<*��Q9g���=*��������l�S�E�6�p�Q�/��,O#�B?������]Qv
�D^?�l^�hJ��!H�vl%y[��1����ǬF�k-�=���6�%��;�s �ۄ���N�$�v�ɼ�NH����&�a�>L�,�0���F�hDJ��PdҼ9c7͜���8/8�l�tCmЌ�7�����.�D�HҢ�V4M�s�}��4�dF���?�=�,��_cǶ��&���rE܈�d���<��*:��b�2�����ڃ�f˚�L����R�O�+�R�'�!IO�>ik�8O��%q��%:�~��خ���ܣc��:4
cϻ�pc��sSu��u�>�D���/?!�#�0Ik/�Սw�-^,O�y�Yn�SW�]tPXz�G-�FT�u�}�4m^юODЁ�HI��k�}Jk��V�z����FG��	uA��h�c�$�y׵��=e�ihi,i��pS��ې�L����߶-P���G<KT\�&��H�m����c�9��a�����2�g7X�ңS^��|���r��Rv��5��B��v�1&d�î�Y35c����b����.�$�S|]%�͞,�"2
��P�O���	W�ԐR�Ҙ�h2�b�@�$F`ŤI�+i��d�]b�-�Il�� ��,%%t|�o�Hd�P�0��XTǋ�X����:��Iԁ7�Y�B��%פ1NjH�D]�9��_X~g���qQ��#�C�U���
�jմ�^/!U��#Hp6ÏNWk:, צ�ր����u�l�6��9���Q7K{�LR.j)�=G�Pj�!=4,6$#�+��	z��z~@Z��ᕜ�8��3B�2��r��\ɲ4s��qr�Y���"��aȽ�����\�G�˚���WJ�۟'v%�:�A8���Z�=�+&����`�P@��]mH�wӍE�SU��!Z\Nh�~R��>B�0�#��TG�]G�vS�򩔋㘃i7���7���L)�L2�����T���)�N����2:=d�$��!�yPk������I�vq���Bر��.z�9�bK�f�ܻ.�<K,�}�F�����t�s�,�`@I�ب� ����`�y	{�j�5�L��.a��0��I����I���0L& 7��)��;ܶ�Q3�Q��Q3]E͌s�R�f���Y<)m��N�����G�e;�c8�3rz|4 >��0	"
*.����+�����U��H�f����QQ�z�cG��oL 擖��ٻ!����]LQ�b�.H�Śva�}��Q�B�ڸ|�,Tʀ��l��s��3΁
N'>�*�ݟ��L�/E����8�\s0Ǘ�	��^:H���q��f$��()S�n�A��3>���i��3Xe�9���\H� ~���~��;�\�3N�jW˳v黼+k,ڙ3t!�z�(t�Ԋ[]yC#��_o#�LM��.&�1	u+��w4�4GqH�9���cWge�����C �_h�]�3QuFcTD=dȱ�]��-/�<&y�L��)����񹶹�B��L
�2��廊aбk�G��,�k8�䵄�c�����c��$?�➱�J�lC��oݲE5ҿ�;��.�t��\��,�S�j\CI�È�kxb���S��)bl:A�M{�ε�c4L-�GH�Ԙ�뢒_�#�f�ίs�d����� ��2$�X�q�W�v����
N�*y��9Hdq��Se�Hѣ{d\��2����!ԛO�#L[�#R�S�K�`�S�SF��<�n���#>)/y�%fo������o��b8'�+2V��n�f�@{I��~�\5��w�D'f������bl:��C/�=���C3��Bj�̰�w:�Mc���!%�s�F�q�����Z�vE�Ʊ�woR#u^e*"1�ݒ~��K�M�C�k��pW�E�i�h�QyKA*�c�dtd3��W����kgޔ��쳻8EM�}>��S\�5aˤ:x�(�%�:�Wqe>��$̧��Q�T�l�l�5�O�//����h�.������]eN��F�H4�DQ��î�T��\_^���:a<G�Ў�Az��M�M�8�6�EE��;�u�0�p��i8��V>>�̗d��50�\��s��M�ϥ�j\�ͯ�%vl����U�/F�Nϲ[���c��ϱ���~v|Ī�����2�������"ҥ|� ?��]���J
	��^� ���*&yFj=Ĩ>�}�{F'@�� �����4� ���|��|�	�1	�1�Ǝ�/���M�����h�W�&�`WƥnY��	,�d.�o�*�.�ƅ@㌠e��I����Dy`A�E1tFǔ����(Rf��F���s�*mz�&N��Y�>�{
gu���Øxח���o�x�3(�E�x���K(^F�wq�P�;����]E���}�������І�v�'�*�l֚��T�ޚh5Z{�����;����3��5ۚ��i��i�,�[��C~CW9��G(�A�_��ǵ��������wee�1�y�lZ�r�2'/�.�_Yv���j����;޹U�[>w�eO#�W�X��xk�oq�����s��ٷ��V?��M�o�M_~o띿�]1��՝Y�b�{����,iB5]^9[���x��u�u�>m,�t�j�)XcS'��9%�C~�8��M{�Z���z���՟��Xh-L��PK    s�yM�N}�  �     EGG-INFO/PKG-INFO���n�@E{~ŔqAҖ`E*LD	P��c�Z���>��3�PJX�H��s����<S@����4����!ۣ�
��.ʐ��Q�d7�X�Y�Bw� ��^��h� *@�䙀����� ����``'u|����1
��W@-�k�`��"8�#��H8^�E?q�JAgPFđ|�=E�Łu�B��*�A�S|+z�J���WO���u���|s���Vn̈P��Z�胓�g2'�r��Gk����O?�v�g�,�>d[�6L�}��7/��1���e3���(�El�L����.``�U!�/<��Xr4��]| ������0���ge����u�L"�Y뵼h�5P0��9���Y!�Âm�*���P��1)��|Z����q���}z��1�D޻���y�	�H=�/PK    s�yM��2         EGG-INFO/zip-safe� PK    s�yMq;O         EGG-INFO/top_level.txtsLIL+*�,�(-J��� PK    s�yMTi�1i   �      EGG-INFO/SOURCES.txt+N-)-�+��rLIL+*�,�(-J��׏�������&�c��KMO���K���v���s�ǭ"�?4��5X������ԂԼ�Լ����̼�b��K��sR�Rs@� PK    s�yM��2         EGG-INFO/dependency_links.txt� PK    s�yMEX��n   �              ��    Adafruit_PureIO/__init__.pycPK    `�yM��*�  59             ���   Adafruit_PureIO/smbus.pyPK    `�yM                      ���  Adafruit_PureIO/__init__.pyPK    s�yMs�0=y  �/             ��  Adafruit_PureIO/smbus.pycPK    s�yM�N}�  �             ���   EGG-INFO/PKG-INFOPK    s�yM��2                 ���"  EGG-INFO/zip-safePK    s�yMq;O                 ���"  EGG-INFO/top_level.txtPK    s�yMTi�1i   �              ��#  EGG-INFO/SOURCES.txtPK    s�yM��2                 ���#  EGG-INFO/dependency_links.txtPK    	 	 o  �#    # Copyright (c) 2016 Adafruit Industries
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
DIRC      [��$1}?[��$1}?  � S  ��          
lcD������9*wY�^^����� .github/ISSUE_TEMPLATE.md [��$1}?[��$1}?  � T  ��          �{d�b�^n��"���3�Z  .github/PULL_REQUEST_TEMPLATE.md  [��$1}?[��$1}?  � U  ��          	��s��$��~F�G�y� 
.gitignore        [��$1}?[��$1}?  � V  ��          ?؉[�E�2�_v���^�� 	.pylintrc [��$b��[��$b��  � W  ��          ���_�0:�)�ɢ3��欔� .travis.yml       [��$b��[��$b��  � Y  ��            �⛲��CK�)�wZ���S� Adafruit_PureIO/__init__.py       [��$�?�[��$�?�  � Z  ��          95y��]9�N�>vR_;@��� Adafruit_PureIO/smbus.py  [��$�?�[��$�?�  � [  ��          >�%S�e�`%�<p� $T LICENSE   [��$�?�[��$�?�  � \  ��          q��:���1p� D����ŋ 	README.md [��$�?�[��$�?�  � ]  ��          (\#�+~���>҆�{ϝ�� ez_setup.py       [��$�?�[��$�?�  � ^  ��            �⛲��CK�)�wZ���S� requirements.txt  [��$�?�[��$�?�  � _  ��          ㎳����Q�����g�V��� setup.py  [��$���[��$���  � a  ��          ʯ�!�F$E�%�u���� tests/test_I2C.py TREE   � 13 3
X��=� 1��WYI�p�"tests 1 0
��F8�9p����md����C�G.github 2 0
�)�
8W"�gԖ�}yͯw�sAdafruit_PureIO 2 0
�U�q��~Y�����R�W����H|�^�J�#x[���i݈�[core]
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
x+)JMU0�4f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-sSӊJ3K�J�R=����,Y�k���7&�4v��B���tv�ve��,��1u[��Y���
�*!P%A��.��z�)k�����W�P����e�MG���R��SKJ�
*�_�Ү���c�ݥ��Ռb��ZUWsW�r�cW����69=�g��<#�����b�/��,�X����;7e��ֽ��ɥw�x+)JMU06g040031Qrut�u��Ma`����!�ew�+7�֞�� H4�x�Z�o�����+61PKw�";��j�INԳ%C��A@P���"U~�1���}ov��%��Z�� Hlrwvg�͛��<J���鳓?��P���]ެr���s�Lu�2-�\�E��i���C�-�U���Yߩ~�K"��ϯt��,Lbfj�S=�S7��z�R�Tk�,U����Ry�|���4Äd��a�7�W6q�� (K����j_(?˒ �!Q-��X�8�s��#��F������xܔeڏ /�!O+�R݆P��U��Y@)-
�b�}��Q���.���"��mK��E���Z���(�V-�)|^���a�c΂.O�Te:�� �5W;�Q\6���2>�]%�mmB�iY�1��q0f��t���:����_&Q��R� �!��N��fx�ϓ�ZT2H��;��Y�N��W�ʏ"5��rX:��>tZA�b���A�Gj���讶m��W5���t'5�������?���)~�Ro��W��Iw4{���;z�~��-5���d0����^^]x:�.����K�3G㙺^g;����<W��I�dw_/���-�:�F�{>�����Nf���Ew���'W�� [�C�h8:�`���`4kc]<S���EM_u/.��u��Ä�T������嫙z5����� �뾸�ŠZ�;�l�~����;��1�PC4{To^��kv�7�GT�7�&��]'�r��t�R��pJ��OƗT���� 1�994��<�ᮡ�ۏ�����A_���e
���8����<\q�ga�с �)�� ��'=�Sݫ!Q+P����(��O�Nc�s���y��ޥ7�T�ϙ�|�t�;J�}I-��\�j�
V�F��� �&��t����1�XK-��'�A�,��:𲵟�:����U]%�����%��ίG=8��{��;zI#����t��"8��=��8���k�?�x�~©�u�g֗V��'o���,��ǿ`�h�M�^�g��Am��>ZO���Euz\��9?��M�=�Y�iFt��3����Xaz�}=(���y�yJ)��J��[��e�G����γ/Ol)�0
�[+�� �"��!	1�)H������!�n�n�O�s-7���#��� 7�,B������?R�K��@�_���#��Ga~G!��AP%�
yN!�d=c�}����%D5�A��O���8�ՠW�����)G�ס18��WM/_����>MN2�\��tay�d6"��b�$S��]��8�A��B�'���nS!�"��S9Po�h�y8�w�	7�h���R�W�q~��٪�\F�M��{_Ĝ���X�˫�p4LFͦHP�l��M=�L�TtߍCGnM����-b;�,���\� �B>h��d������������y(pr�"=�~nR�T�HX�]��wt���C�7ɦ�$�p�
�U�"�� ��,$H�=��b>�~U?�ך�L�eH�"��Q�ɋ3��U��'�$��#!���@�B�B��H�HL%��k���J܃j�C�b��~P:�L]�Sp�G?*��� �>P }ʰ�d"���) �aW3�-;���x���ݲ����`�Ξ��6iaC����Ly\���;i8H���~�I�d"3��t��=�1V"���T��w��6]���~�y�~�~.�3����{`���'��nv�S3�P��[�3BȐ4IFcyfl�[���
e��5�lPވoaW���G	�����>��|��j��$ ްë;T2�!L&I�΄ɜ�唄��e�9CR2�Y��(�l��n� )��&BG��E����'��	���(�D�)*���S<%`�y�E�V��F�%v�<z �D��Vek�6L	�CȐ ��r�2��s}�[	�Ƅ4
E�s�OR����O�ձ��`�2�����8��K���D��N�T��?��XrQ)������2�'��{Y#�ci��g{�Ɔ.9��X�l��*_�{��%�<��v�"{
;��4�X MF��L�Gɰ��K�h�qy"�����(�4����P���a�O��#��(����u��/�P`SR$�3�G���c��{�*��7�����-ā��k)H㸉�MY��� qa�����b7@�n���l�)�Dֈ����|�c�]�!�����/���$��Ql��#g�l/��?v��~HC�~�ņ�/��8�W�����?�7<&�	W疎�@N��������e���Q�+s���VTrз����*��4\k���$П�S�K"Kp�,�S��蠔g�^�I#Z&~��~6��S���Mv��ɼ�����v��<A���(˞�`%�eK�3!��QI/���NZ���lK��ϑɕ{:�T���?>U=?GJ3��d��W)B��ș=hy�r�.��[�����@���ܦ	�G����t�ޥcN��2���!:#��'�k��̙P�mU@0(B�#�����o����嘀
%X��_���xd�G,b�w�R�Ű�:
�,�ڻ��s�B˥yP��6�1��6Ĵ�Ф%��e�=�I'�u��iI���6�m9�eY�E�6!'�H1���G�]&ߪq4�U���7;a7i��ġ�+��Nf�[C٥���}͙��8�5= ��1�h8���\R*<R���� ���0tTb�H�6��a�0I�F�� �la*.�6fCr�^l����i���p,]o�`<���A1�u4����~�Z�����S'lbH��f��֖(�f欈����[��M�߰p^*��^yVE9����m�NK�\����P�:2��՛4P����I�\���#��4�w�䤏�, ~�e%�}]�K2�Q�$$6��3�jU��w٤iaM�P�Җ̶�U'��[���0�h�8%��>��[r�%F	L.1F�4��I9��#7�VA���:�o�:H+T��S��<i�ő��ԫ��(�CJ��`##�Y�hu��q�~�:~f�PZ�-��v�p'���΀��o��U���Yoۆ�o���Q|������3΀[#���v,�����0�:)��B\����C�]��vmP�6�t	��|!��X}~W:.�� �T�M�1���Î���T�F��\BzCü����K+ ��e ��c \V�K�QK��.��`i�nYoX"�d\S�ݼ��H?�FM^�H(��8�E��+�Hh�f]��\�}��S��KT��d�@�p�RR�*��~�R<8�z*����b�g��*jɗ��Y�.��٪4��+�<�^���)�xx�(h�����"�4�0�+�Ҍ��������x��x� k��B���M[J6T�u&��f	��f�S�!�ԿE�0�}�Ez�dT ؤD��/H����$60��J�n�-z���C��]�d�ۅ�	���h�Kt+�G.ʦ�4���ll����2���LYlzo�<����4�<�C�3K&�2���.�܋�V~FC�6���˚D�����z���Y���i��m�\#2��DJTVm �<��^�-��
���\s񷈅�+�|P��w&M(G�`�
)ڭ+��8��5�&�k�n����9�o����U�
j��|��3j-M����Ɉ��+�jp|�1PYpo��[��e����'ѫgYbi������si1r9&T�R�Mg��d���_Dk�J+�v<�֙�Lu<�{T�㑗�_8�C5eB˝����0���6z��/��_�v9S�%�]�=p(5(Ӹ}E��yg��v�q��.�����F����(����*���ًW�W�3�x<?����Q��Jz��2�K��7��rUf�u�	7���H�S;e&\�୼���՘���y�͕�L���P}� 9K�
Y���z�7o-e�p-兵6\�&�!�j,Ms)�E�u�G��HF�8ŋr~O�C���aΨ��
�!�n��|�7���3ީ���]���AxJT�Otj�0�Q��&�_ߪ8��#�ʯR�|$��E��M�+1I��le�?��|����E���+1���]7�'8�?5O|?����f7V��Щ(�)'��ۉ�&�����"`���|�H\�L(m7h�0��%��ܫ����=H9����>{>��V,e������1���$V=����b� �f;9�/�H�ӥ��|G�d�����Ko�o����\����C�u2IM,���\� 
5t���a����Hw}��Y��\3��t�E-\6�k���&�´ip�WR����ӝ^����J���[����uU7T����[���;�!�ix	ow�N�Z�s{_�����D\��������c�����a�lX���r�=gx��@���V�ao��	�7x+)JMU014f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U�9�y%E�7:�7��N1Z�\�j��8�����MM�J��2��*ss�=�?b`��]H���E�������	q�cJbZQifI|@iQ��?���)����1Fn����٠����~���������pA5Xv?c�6�ճ26G�UB�J�\]|]�rS��Y�}�����lA'�˄��vC�V�����T2(���]����&�Km����]���(��4�(575��X�������G�7]���ݭ��<�ơ'=��j���m~��ū�́k׶�y��>l��S����3|y�fqǲ�ǔ�߹)k׶�u~� ḫ�x��Y
1��)�J�Y:��Yf�L+����Y��We��Q ў��6�XL��r)�F�3�H9�˅��ɽ-%fR��_�o&x�H��y����.*~�c�0qݹ2\�q^���������lpp�NkU�q����&���{��H�]} 9�E�x��A
1@Q�=E/��i2逈Wɴ	
�#5.�� ^��_<�m[׫Gȸ�1��@C��Flu��t��V����!C���fb`�jJЖ���.h)MdS"���mě��t���u�������)f��2s��O�Rh�9�?Yx���>�>k�C]x�Zko���g��q�Ү*�N6YpE�cumɐ�A5���H��(F���s�R���ݺ���&g�ܹs�4������^��@u��}��.RU���u�R�g�<��T��Y���������E��Iޫ�߉w� ϯu���ďB�'j�c=�W���z�P�Xk͕�p�[�Pi�\�_�8��h��~臷�U�8�M�D�t���g�M���]HT��˖:Lݔ+��@'��.�z6�3��e��v��C��*��>���*�ܙG)�lF=�ׁ����.���`Զ���̟�-�[e��O5�)|����C��^��X%:�j�Ӛ��(�Ak��O֋h���:ͳ8Ĳ0��"�NV�Y{)�P�yњ��p�s�ɩ�o�i�I˖�(��by9���}�,� PSm-�����a�+l3�&)pແZE�,��ۦQ⢧���ɻ����cu=��w{]��=����]r1��(����jx�ڃ�����P��_�z���D���������sy��ިט9N�e��?���PM����a湺�:��~ݿ�O�7 �?P��p���=��;7�푺�]�=�Ѕ�Ap>�:���`�ĺx�zo�_�//���o���T����Q���D]/�=<|݃v�ח=��ֹl���۾j���#5������E��f;��p��t����6��Ѥ���?�5T{��,���I�bV���]U���p7�z����ڗ���@_�Û{�����p�/	��y8��4ȟ���{v \'��=��tTG���D�@	�."?�>�;�: �3�I}�+g���3���j�����Z��U����-��rg3�Ab����J�c
������Kj�ޒ����˖n���JO��U��c�%*�s��9�t�|2�/�����h���	�V���;��q�޽�N�?r���S9�dǬ�V�G=g���,��ǿ`�`茺N�c��a۴�cv=�u�:���q�����o�����܏r���O ��}���
����^a��
�W��r��$�ȱU�]&:p�N>]��z��Ćҟ #����_` �. z��C�4`8���x_tp_��C�������ꕀ��'������Eq5���
��B�h�2��]���@7��{b�N����A�+��t���a���;�"�'s��E!�����q��^�!?Y9?R��ס18��W��^g���ͮ�� d\�������lD+��I�fz.Z��8�{^��B�'��Lnkc!�,��S9Pg��`�88��	�i�ÆR���az��ި���m��;_Ĝ���4����a0�jF��H��WQ6��cG8�!=Vq쑪�|����B;�,���X~�B��y��,�q��:�F{���M��rp�=@?5)E�S$,�.��[{���C�m��UH�'�p�9D�Ҟ��I��uh*�|&�U���]j�2�� �@P���f+f���-�'+�$��#>�O�,C�BB��H�HL%��k���J����!v1�U/�4S��48�d��G�c(��>eXh2�B���װ���`z�j�mUVn� �����*��Aؐid��SW�-F��&���H��I5�d�#3��t��=�1�"���T����M�Yo���Q����\v�=�؊�?� u1�Nv����f��Dk��BȐ4I	Fcyfl�[�i�#6���֔���߂V_��G	������.��t�j���ޠ��=*��&���΄kє�锄��e�)CR2�Y��({Y�;��=��R�	�f>�r��f�����$Մ�)J���S%`�85�E�VN��%Vu=��D�z��%a7L	=�CȐ ��r�2�G��b�$9o�(|N�?IqG���.����ZX�A�줐���/�P�?I�J�
=�L��CA��hIX>-#y�P������q���i��qrh<��h¦c-~H��G�)���h�W�s�v��{�9߁���֡͐?��sFY�3f<gJ& 5a�8������ J4���Rǻ����p7D��	�6mV����u�$�H�g<ձb��DU0�k�J��w��*�I�~MY���AF��;u�'e�l��s���'̉t?!$��閵�w�0%L��I��=�xD8�l�a�In{Q�X]�� X�n�Qx(g+Fń�i�.��8.�Kḛ
�x�8�ל��Z�����u�e����a�Ds��9�v�� ���Q�ƀk���W���K=��"�Wќ>�P��Jq�hb�4����j���I0�>U�4]%�GG��6i��ěQ|{�&Z�Q��z�?����g�_�M���M�g�0�~����U��.����)r����ГYA���\8DʴBˋ<y��3Ӊ���9X��G8�u��T� bɓ�j��]:t��4,c���JF"W� ɜ	qD%��M�/ y���(�'s9f��C�*�B_�,�ȃY��EA
��ݯ��ʲns\4�6--.��-vd��(�Lh��t�^E�H���;Z.����gK�l7k�܆�I����h�$�è��)&8R�Ʉ�$b�f��~P��$ȟ�p$5�Mw2�o(�zL�I�a��3�qvKz  ��c��p�I��~��%�BʽE��~�X`�H�4��a�0�g�F�� v�bm̆�}9�<��Y�@ŷ��X��y����:@jŌ8/�Y�H��t���5]�-<aCz%7c/�ym�R�Q*fN� ��-_�+���N�B�S�/KҲZ���x��j��F^:ՠ�^�.��w��V�_.�aV��
��-��J��qJN�� ��'^��>V�yE�2�$	�-�̼JyF���]voXS,T��!�)�g�	lg�?��j'�ɤ�˿���Br�A�K��$M|R� �HM��F$����A��ۼ'�
%,ˊ�T�4O��r�dco�,81�ҥ)����9Z��rl?�W���)��/��v�p'��5�瀳�o5��U���Yoۄ���צA��=�ٮQ�#�cv�pkDV�z،���	�]F\�+��q�3vɖy��M�]B7Zb�.V����16�+�e�b� $���1����Ө�Z��ބ�a��H\�%���K��,g �b�}�IKO��7��]�4�dׯ�,]2�d��S��֨�+6�K�zFkT����vlօz1N��W�VK��De�A�4���
P�+M�>J�`�l�Hn^-���ٌ+�PI�$�@�*�$ghږ�)^B��)���\���H���G����O�*�Ns=#밲(��<�q/l�j�����)�j�ʐ��`c���dC�_gb�u`�_�:�Ҍ�5B���/�D$��&%�W��$���JA"aF`��eʴf�耢���+n���(7!��3�D��.ҍ��(��ҁv�[�������`Z1e���tW+�.�����,�DeJ&�Lr/v`�}Y�z@ˊD�����z���Y���_����m�gp5"%*�6�yE�p_�F����6��o
������[&M(G�ˍ$/<�h�,w���#����7_�v��S����ܾ]�KtV&*��D��θki����QF��\1V��+��҂;���ؒV/�/��1�^5�zK� �Y��!-�By��-H)����Se����/�k�JK�q<�:��Ly<�{T�㑗��݁3��&��5�=������ǂ����+ �,g����e���bE��ȶ4�An���RaJ��Qa�j<��ƣzs���vx����r����%�<9�V)`_��%��;�}�Uf�u�	�<)�2���L���[q�)�W�1ѥŧ���L}Dv(?c����Y���}ro�X�|�Z��+m�*M�Cfܱ4ͥ���Y�]pD��`�S8+ᇆ�Ͽ�`1��n��pȶkr:��E��݌wj)/��:-?|��-ȷ;`��(��o�w��oU�_�����W�z>O��"��M�+1I��li����|������ٯ�8��r���X�=��a)Z"��X��C��(����o+��[Z��|8ހ���W�!#q-x2���ݢ��L�t(\s�j�� �|�G��w����[����|N<��WV�:�%<!��谟���6��q�x1E��.-�;�I&J��*�����Z���e��}9�['�Ԅ��ȅ�PC�*)�hV���ހ��OS1�;_��5]q�.�v5_vGm���a�48�+��z���V�[hxW�rY��[����_�J�=v��]��m5<����E�C-���p��\"�.���V`�B��±��Ῑ�gc�4��g�\f��j&Я�9�cD�[�Đ=�x�SѪ1��~�@V�v�ޖ�p��Z�EA
�HLf54��$�ۯ�$��
҇�I�sΞ�9�Wf������Yt��ֵ�x��vCc!�����`�� +�& S�h/E���Y[��b'���j4��P&�W猻8+�8���'`Z ��m8��r����:2�3g��e��uA��t� ��bg��H`��#+�����xBel�:�&��x�����/X����=�|eѱ��i}�:�׫M�#�XJݼ�!-%G�1B
sk�9�����[���;�RԂ��FH�<I�=S	wkg��ut�d��P��c�V����_��;����G������^5����yߘ���ʲ4��f����\��52�֍�r�k����2�/�Ť���� ����-,�QÔ;�k&U'`��3;(��{i��;i����!خ�#Y`A�BsB�Wh4���8G��Z��@����&M�+��i+6� X8c�Z�8��VT����ظ=�J�'��h��w����'��p�����.pY�k������_��W�x��]J1�}�)�Q���g6 ���@�Ӄ�d�d"���{��������Vkp<��E������Z�Xr1���W�NS�+�:�.� �.Z"����w�0������Wt�U�߭�Wۮ�?Z��2�x���y���
�z�1K�g�Q�N�!w��{)���� ��?0�%�z�{�D�$X��ު@��cϲ?���[Hx�NKj�0�ڧ�}��?��Q
-=A��q&��$6Τ����^�Z$!�\����?H#��l�DVS&�0{�h�2$�|�s�fJΩ��z�YOd'����3�%���E��C4*�r+��~�W~)k��t��G3�n\rٞ ��#��=<���~Q�_e���P�}{�+�~HZW��8	�Xn@?�Y�њ�?	x���E��WZx+)JMU022d01 ǔĴ��̒��ҢTO�i.>յ̞��������S�|�LL|<�]��].���gL�Ɩ�zVƦ��JTI������^n
��>�����_7�-�dp���a��n��Ԫ��Ԓ���J�W�������dw�m}5������B���<�k2�Ӹ��EX꣚�{gpn�8�$������37�;�?�t��MY��u��Cw Cl[�x+)JMU02�d040031Q�K�,�L��/Jex$ƻ�x>��*ӛ�8�f�/�l11 ǔĴ��̒��ҢTO���om�Y����ŷ�������x:���2\P��Ϙ��-A���M�Qf��� WG_W����}V_�n([���2aGæ��PE�U�ũ%�z�ʯfi��}����R��jF��sW��*������Lv�Qŋ�kv}�k�R�F������b�/��,�X����;7e��ֽ��X�j`x]S˒�J�k��]/�nDEԈY������ds��yXUP�˯��gV���<�'�"Ͻ�wn)���&�+.%��8�lű��l� �H�#{`4���'�1��?�8���2D(���d��K�Ϛ�a�d5|B����?2�b#�a?��Sb��M�����}��E�QI��Ո�H��,���8�}}�7��j�f�m�v���!��0�^��|�OM�$�z,O�n?� �_��(e�}8�y�x����P��N�;-5�4�u��%l�1��aڽ{���Vu�ʶ���cO^bQ�x���U�����~. ���9����-��3���yĽ�TAz��~�����r���L�q\��õ���fPi��P�1َ��+7\���࢘�������:Z��lc��;	���e�J#[���F^Q�NNt�G�/��}�?�4� �?�~��Ha‣qD�^���5ս�*އ{�����y� jߥ���k�HTɨ["#(�EÛ���J`���>�K�y��*�6f���������_����-FM�(3s��ˋ��EQ���ڙp��X0���1&;>]�m��ּ��ۋ��9��\v����l�s���VۇF�:/��<^n�\�X�o��i
C�U�UA���>JN��~�C�1	o�;^�!�BA��+dNsXN-uz��W5t�
x��~����Ϟ�1���)����V�g��~H���]\��ԗ����'��AB�x+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b���ݭ����ڱ�I	�[;l� -= xx��[j�0E��U�0ة-�PJ��+���L�$vId���j�P}�]�r߶�0��;��))�t��]�KȈ�e��Zo�I�ho���;5���E��8k�l�v�E���LA���������wow��}������,����Ƣ�G��ZF	E����i\�Vy�]� �=_�u��co�] ���c�|�m�mIw��Q���h�@�� �x`�x+)JMU067c01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U%E�e��z��9�U$&<x.ɲ%hK��-��x�u�)�iE��%��E���Uk�y�,������r�]�s��x:���2\P��Ϙ��-A���M�Qf��� WG_W����}V_�n([���2aGæ��PE�U�ũ%�z�ʯfi��}����R��jF��sW��*+J-,�,J�M�+)�+�(ax6���M�9{wk�+��q�IO�D�Z�y����N'}���s�e��P�3^-�x�$������37�;�?�t��MY��u��Cw ��x�S]�1����}Pa;���P�:`QЇB)�;�IB>\��M���͓&�9��s7�l���y�.�� :�a���[�?k�!Z���)�"�<��	��C&�E��jg���l�q�t���
w{�x�hT���9�:g�V�p���L`��aq;�ao;�wg_;�\��,Q�"[�.�5�o��Z�-��	�qd-�yx���)�Q۠�,D�1<�����rq���ӛ[t,��.�>`�������~̤��;���=&Aab�3{���jE��|�X�Zr�Dͳ��3�p��pf�X�$�3�����۶�����FwX+c%O�KS�7Fc�j�?���}cN$f�WQ��5�ܜ�M�]�a����Y{Om����!�rX�ٱH�r�w���VFa*_�b�:q���>8��ֶ�56L�V��>ڴ	���U�Ms�$�s'm��"F��B_�X�ց�$��@SNU�0�����9LP�i%����@��k^��*��Xz�V1�9�5U��8���R�#�B_��S/M!���3�zM�����v{u�s�p�����_�x5�AK�0�=�W<�^*z[Vq.xN��6�&!����"���7CH�����s�T���/uJ}+��Z'��߭פ���L��Rd�"��XK̨	�>��>�М�#��=Lt��;�ג��(���4S�8�����"g��9���R�����g�3�I�{��%�e�L�a���Pk�.�inC�V(ۜ��j��;����c�Zp���#m�&ȎI�K?簱��_Fn�Bu����x�*�0a 	�2��rӺ���H�_T�@x+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b��{���.��:/(���_�8^�5 EN#�xm�Ks�@�gͯ轕�y	T%Si@"u\v7o�ie�׏f���s�=u��G�ө�@��_��9�T��nPJ��ʢA2]�DM5��T%I0�;�\�b��Xˡ)3]���b��j�@s_x�3�Оs�Tx��/8x��'�]�O��g�o �����&��
��$�pj�^x�z���yu!��g�P�u	^�c./g�	Q��ߺ 0�&52-�"3Z�̊M_���*3oB(s=�|j*5���U=ח:�*`Ø���>$.��X���^�s�ia���r�6>J� ��Y�(G��v�L8� \�H���9�<�%���s��4�j;mw�e����Y�߮|�x5��;����#!$M����#f7kuf�`���u��P��wv�8�}Qxkn�rՅ���i�ǃ ��sH̷��ZX�$�;�e�h��:f�C_u�~ԥN�\�Z���y�z���G��/ڒD��9E�T7ـ�?��j�4�YKb���xH��ڷ�}(����'��G�!�y�4�����sc�]���9nm���V9=��S(� yn�ux�1`^?�� ���Yx�S]�1�k�W\�
۱���n�B�(�C����$!��_ߛ�:c�>4O3�9'��ܳQf�����;L��V� �K������`@j�R�7�1ʃ�A� L9d�pB�(�P�L�)��H[ɬ�q�[�Q�/m�*3�8g��Y���!�0����AX��h���仳��=׭9K�����&���R��e��"��"��%:��c0�=*c�����a:���>c`��\\��q���˃�$�b�����'���ғ�=&A��Zg�(���jE�||�X�Z�!
��g��g*�
c��ֱ�I���F�;{l�J7Nʏ�Ż��Z+y�_�:<3z�^C��?7�+s"1?�"��P3��u��jeX/��j~��S$�K�������k��Tw���|����x+�.nJn�1;ꏻ�r����EOח$�����G��� ��'�{���Ɔɣ/��hS�>�<$C�z�]��HM �>�P�XR�A�\���f&�ď�q�ާ��фjN犆�ƣ�<��-U	0s��!8��q̉��R�l()��J�{h��
}yv����5��\��е�{��BvJi_�"��Ѩ�e�w0x�Zko���g��I�Ү����fa�INԵ%C��A@P���"U>�E�{Ϲ3CR��x5v�M�ܙ{��s�y��������/���l���f��F�T'��Tw�/�"��0^Y��:;8T�"_%驚%�ꇽ$���J��0��$Va�V:��;u��q�-�L�V�R+?��-�'����N3LH��a|�|`#���
��d��������,	B�"	���s?��0ҙj�+�O��MYf�����r/�m5�\�����  *܇{��Ю��b!Z�/2��ݶ�:Y�K��E�M1��l�R����E��:�,��$IU�#n2`Z�q�C�u`#���*��U���&䞖EcYc	L'�����O��eE�-�xR��T�o���<��E%��8ɱc�������}���(Rsm-���;�C��,�Y�~�6I*��j�6�x9P����uw2Pé���_���zܝ���-�z8{9��)��tG�7j|���7���R�^MөO������p���Q��?�P�1s4�����p����aI+l8��su9��^Bv���b8{ӂ���lD���ꪫ�d6�]_t'��zr5���>����	�\F�6��35x�_��e�₋AZ�:L�K�_��_������ �����Y��.��˖�w/�/�ÉC5�@�G����f{��xDez��l�_[�u2+'�N-՝�4��d|I5iX��
�����C���ʳ��������{i8�d��>X�@l��m��pM�o��e�{&A�p�"� kx�S=ս�%����¸����4�8�_�O��]z��H������N縣ܗԂ���u��p�`n��X�2+`үOW��S@�����}Rt�"�/[�Y�S+a:_�eP��l!\R/��z���ٸ7��.��4��?Og [)���3ߎs����É���'��Y'{f}n���x2�Fݟ����ޤ�u{v��Ԧ���d�{�]T���;P��#��+г��e�f��@�@>�\���W��n�
�g���r��$�ȱՏ]&zp���.�?�����-�? F��`k�=��  ]D��1$!�`Ӏ�"��#�;��|X:��-|�-t@�z&��Ƴ�z�����Eq5�ځ�=���	d���\:b	�~�w��{2�Ur��g�K��0��'O^��>[BT#���$��3^z������rd�p�#{���ya?]���D !���H�g`Of#X� �O2��K�5�n��}D�,Txx��1�)R�<�������cx[�p��?j)xE��?4[���ȿ��v�K�����Kyy5�f�I�H�����j�M��'�鑊�q�ȭ)��ջ��@lG�埞���~@�{�q�lA_�8��Y�=~��:N\�� ��MJ��	�1��.��p��&���}_!�ʙCd�8��	���R�gܯj��Z��	��_��6J9y�ay�
��d�0��R|$D��!\�^�Rh�i��d�pm�_\�{0B�z�]�r�wJG��kv����G�6���
`�O��L��@2��5�j�eG0��5ֶ[V~�� ������&M� lȃ42p��)�+�#�`'g	7�܏2�a^��Bd�4�����8�J��0����6|צk���o;��_A���E��q�Vw�n� ls8�d� ��xj�Qrs�@�&��h�#όMv`k�;B�Lֶ����-��ScZ��(�2{�����G:���\�Q��vxu�J&6��$�љ0c#�3������,"g�BJf0��E��ӭ ��D�H0��s�d�?<|����0E�Tcp���=���h�������n�G`;��Xߪl�AІ)a��p`QQnXf��p�/v+A�xØ�F�(�sn�I�;bW���:V��RF�R���o���p)�`3�H5z�I�
4����K.*�ђ�2|ZF�5c/k�r,-���aπ���%�!�똍�U�k|/s�DÚ"���A^dOa����ɨ�A�I��(��y	M4.O�1Q�^%����V�t�z L�X�c���3]�.�P�
lJB��v�(��{l|/[�����\���8�2�a-i7�v�)+�R$.��s0���@�h�-?ր�?B��������w���=d����8��e�s`�$��8�͖y䬝�e�����܏ ih�O�# ��0�eܜ'����P������6�����I���x�>�q!�,���0?�re.\� ފJ���>�]�Q���k���>���}*uId	��%}����ѫ6iD��O���� 2}�Vy��N�<�7Y{#\�Nқ'�eٳ�L��l)u&�8*��ߝ���Ik?�m����92�rOg�J��ǧ���Hi��A�b���*E���9�-/\� �e�� }+��X�;8��4A������!� ���t��I]XƲ<DgD���|�Y�9��
EH�bDp9��MRГ�P�KU�K�_�,�ȃE��� A
��}TG�/��^{\{�Qh�t!JC#;�;&<ۆ����$\�̺3�d�.�0`:-I�U�Ʋ-��,K�h�&�㤁)&xR���ȼ��[5�f�건��f'� M�[��8�tE����}kc(�4zA[��93�g��`<<�'�ߐKJ�G�[����d�揎J,��f��#,&�b�H�`�-L�E��lH�׋�#��U0T|� ��������!2(&���fU"Y��O]�7��t!v�M�U�]����A��̜Q^{[�r+�����B�3�O+Ϫ(��5x�-�i�㖫���[Gf���z�� j��Ղ5I�Kt�vR�f������>��O������yI�2j��Ćf^�
����.�4-�)�Vڒٖ����w����'�d����uK� ���(��%�H�&}<)G�t��*H#APY��{�m^i�J��Cb
y�'-b�8����z�EwH��ld�4�����?��U�?�"��qK����܉�yö3��[��AU���n�۶�����y����l�Ee���3�ֈ�rðK��k38��N
��W�i!�`l��]��M']B7:_�>V�ߕ��16�+�gSb� $���c�}i1U�Q�5��^��0/b$.�Ҋ�`hHj� ���|��z+��Fi"XE2�[���>הb7�2:��O�Q�W*J��>NnQ���2ڱY��4z���,���%#Y�&�8ܭ�T����$��T �������X��=�J�Z�%�jV��1[ե�v���"�<��u� )� lx�(e����K"�4�/�k�Ҁ�A������x��x�k�h�H�� a���а�3K����[�x�%x_s�m�1y�v�BN�6!Z�ҽ�JɑA�+�a?���[4{'L����)fM��P��ـ,�\��;T?�Б-S*��)ɘ���/�Z3�3��Id2��	+��@	���ݶ����-��d�
�ɣ�;^�����'���E,�YQރ���ꠈ`�����Rj[V>(��8ت5�&Cװ������9��W璹�U�*��|�K�3j-����Ȉ��+�jp|���,�77��-%Sri�'~x����=��yc����1������}�oz8�K&�����������ػb����"�,ՎG^��Քi(w"X��,����/>[�EHݖ�w<���Ԡ̿��Ɩ��ٕ����V�����7�Q`?���1����/�'�0(gj�x~^�Ƀ��K�=�r_SЗ���c�jÚ�~n.)�2�v�C���[y))�W��[�w�+����	١��@r����|'��8o�Z�|�Z�kͳ:M�k>f�XZ�R&�P�,N�(�l� q��"�
P���
���Qi��C�ܐ��vo(*_�g�SKy���i�U�� �Ԁa� />(���V'~G������<H��P+f��b�&����g�������WbMY�$�Op� �&����n���Щ(�)'��ۉ�&��F��"o��`���|eH\�L(m7h�0�����܆���=H9����M<;5��V,e�����	.���$V=v���b� �f;9�:&�H�ӥ�|G�d�����o�/����\���W:�+2IM,��\� 
5����;a���&Hw=��Y��\/���E-\�k���&�´�(q�L���ӝֈ���t���[����PU�J���G��9���ix	�d�N�Z�#y_�ږ����\��ˈ�������c�����\�lX��J��bx��@���V�a�����x�Z�o�����+61PK=�";��`�IN�ڒ!�I�  (je�B�*?�E���7�KR���zW��A�������7�y�����??{��C�K6wix��U#h����3�]�˴s5�E����U��WIz�fI|��a/���C<���:̲0�U���N��Nݤ~��EK-S�U�T��OotK��1���y�q�(_��al���,Y�~�1|��,K�ЇD�H�b���Ϲ�2�t��J��S;�qS�Yh?��0�<��KuB�"W��f��0(����^G�:�kp�X�V���zp�-�N��kQnṢ0[��"��y�cdƇ��9�<IR��[���h\�PFq�{�����v����	��e��X���E�ɪ?� ���DQrK�$^��:;���?O>jQ� !Nr�X,/g!;1Gl_e+?��\[�a�0�N��i5�y���M�ʢ�ڶ�&^�t|>{ӝ�p��&������w���qK��^��g
#&���������p�o��߯&��T�'�����b8���wq��^��9����r8���XͰ�6`湺Lz� ��bx1��mA��p6����Du�Uw2��/�uu=�O�B�G����.�Y����/j��{q�� �{&ܥꍯ�N�/_�ԫ�E��/�]����,�z��eK���ݗ��D�!�r�٣z�j��\�����p<�2��h6��-�:��������N�S��|2���4,�`�����ȡ��P��`w��~Tн�4����o,S 6��6�y�&ԟ��e�{&A�p�"� kx�S=ս�%����¸��>�4�8�_�O��]z��H����ΧN縣ܗԂ���u��p�`n��X�2+`үOW��S@�����}Rt�"�/[�Y�S+a:_�eP��l!\R/��z���ٸ7��.���4��?Og [)���3ߎs����É���'��Y'{f}i����x2�Fݿ��9��g���I����tc7�M��G�ɠ�ڻ�N��w�6�G:��W�gC;�0���?�|�w�>+L/���ݜ:�;O)�:�YIt�c��L���=7]��y��-�?F��`k�=��  ]D��1$!�`Ӏ�"��#�;��bX:��-��-t@�z.��Ƴ�z�����Eq5�ځ�g
y����"t��(���"d�#��X!�)����a�O��Q9"}���F#��I�g��*��#����:4G2�����8"~�ާɉ Bƕ��.,����F$��A�dj���k��G� ��Y��$���Mc*�S��y*�-C-2��<����R*��0Ώ�5[���ȿ��v�K�����Kyy5�f�I�H�����j�M��'�鑊�q�ȭ)��ջ��@lG�埞���~@��q�lA_�8��Y�=~��:N\�� ��MJ��	�1��.��p��&���}_!�ʙCd�8��	���R�gܯj��Z��	��_��6J9y�ay�
��d�0��R|$D��1\�^�Rh�i��d�pm�_\�{0B�z�]�r�JG��kv����G�6���
`�O��L��@2��5�j�eG0��5ֶ[V~�� ������&M� lȃ42p��)�+�#�N�n$�eRü&Y�Ȍi"#eOq���a<7�]��M�"��uޫ?�����F�㌭8�����.�p�������8T����2$MR��G�����*-v�B��mM)�7�[���ƴ>�QBe� �#<饏t<_��Z�.	�7����Ll�I��3a�F2g�_9%!|Y0Dΐ���` ��.x�[=@�/��Б`l".���B|��w?J5`�
��,��C	�{^eѲ����b��:��vQ��U���S�@��2$���ܰ�`��\_�V���1!�BQ�����wĮ��Swu�n�5��&�,������p)�`3�H5z�I�
4����K.*�ђ�2|ZF�5c/k�r,-���aπ���%�!�똍�U�k|/s�DÚ"���A^dOa����ɨ�A�I��(��y	M4.O�1Q�^%����V�t�z L�	X�c���3]�.�P�
lJB��v�(��{l|/[�����\���8�2�a-i7�v�)+�R$.��s0���@�h�-?Հ�?B��������w���=d����8��e�s`�$��8�͖y䬝�e�����܏ ih�O�# ��0�eܜ'����P������6�����I���x�>�q!�,���0?�re.\� ފJ��۾ �]�Q���k���>���}*uId	��%}����ѫ6iD��O���� 2}�Vy��N�<�7Y{#\�Nқ'�e��L��l)u&�8*�埝��Ik?�m����92�rOg�J��ǧ���Hi��A�b���*E���9�-/\� �e�� }+��X�;8��4A������!� ���t��I]XƲ<DgD���|�Y�9��
EH�bDp9��mRГ�P�KU�K�_�,�ȃE��� A
��}TG����^{\{�Qh�t!JC#;�;&<ۆ����$\�̺3�d�.�0`:-I�U�Ʋ-��,K�h�&�㤁)&xR���ȼ��[5�f�건��f'� M�[��8�tE����}kc(�4zA[��93�g��`<<�'�ߐKJ�G�[����d�揎J,��f��#,&�b�H�`�-L�E��lH�׋�#��U0T|� ��������!2(&���fU"Y��O]�7��t!v�M�U�]����A��̜Q^{[�r+�����B�3��+Ϫ(��5x�-�i�㖫���[Gf���z�� j��Ղ5I�Kt�vR�f������>��O������yI�2j��Ćf^�
��o�.�4-�)�Vڒٖ����w����'�d����uK� ���(��%�H�&}<)G�t��*H#APY��{�m^i�J��Cb
y�'-b�8����z�EwH��ld�4�����?��U��lJ븥�nu�D׼a�pV�V٠*[`t7�m�p����<J��p6ܢ2�cv�pkDV�a؎����_'�X�+Ҵq�6�֮JѦ�.��/Y���J�����)1�c�Az�1⾴��Ө��KH�ch�1xiEd0�$5s��JtI>ji��{��4,�"�-�KD��kJ��W���֨�+	%]�'��tqe	�ج�b��ox{
�Bu�ʒ�,\h�VJ*@�Ce��Q*��UOEr�zY,�̞[�B-��\5���И��RX���}�S�ºi��z 6<T�2����x�%�p��Y�5Ei�� ���ua�\{��o<S�5p4U$�]�0v��а�3K��/��}l�0)O-u�e��c�5_�v�nW2�����K.�̭��$���)��Щ�P���`j��M]k�g������<�4���5�l�R-WXI��N)��!�A_�eM"�b�R�X�lJ\xԴ�m�(p�!5&�.�qM�P/\w�n��Q�q�G�\�-b�Ҋ���ͬ��x�r���Z���A}@��][n�@�-^#�: �s�v�.I�Y�i�8/�w�/:����8�n��h�b��F���4�+��2����Ӥ�4/��'�6���̸$*H
(�����d��mS��Z��
����6f)R-�&S�x�����PM��r'��5�=������������W@�]��m�}W�cJ�Tl_�li�An�]u[+�Kae���(�1� ��� ��AI�8:{�
-�
�r�����<8꾖�C/�a}	|�F�W�L���7���)3`j�N�������~�"mV|2 O��R�Ƀ����$g	\%�w�U��步�'�����G�Ӥ��c�A���-�������#��xQ.�u辳`5���_a8��9�������~�;�����V(O�
�M��	����}��[%�Wpd�4�E@��σ�1��b�ɋ!&i�S�,�6��^s��I��}%�є��������i�@�������:E1���v;1�d�ғ�^���������k��	���=f�eCq���Qs�\�)��?�4��g��8܊���Cp�1Ծ��ݟ����jc�ǆ�V^,�l'�U��iv�t��L�Ps՚�M�V�|������v�F&���YU�D��SV}� ��0����R3�;�kk������ۢ}=��Qۤ`U��w&�����~��%�ת��6���c+?�?�˪��g����p~?'W<;� ��l��P+~/�+������a��^|$�������p�=s�o���k�����io5�W�1"�ؿ !BxmR�r�0�3_��\� B,U�T ��,�o �f�	���q2���������uY�(��ZB��T��BC�D0�a����^Ĳ U�kT�ԒI���(�PI"	ű�$�XE�(c�;��-p����m�0�F��V�ٟ�M�>=@� A���
�s��$#-�r��"�V�-in��4gY�y��6)�S��cf��Z.lk������ zj`C�S�=�[F��L�X)Y!mﰵ{]����Ǉu\�����T5��u'���K��@+��i�W��%����c�R��u�lv5抌x�0�^84^@EG��#��ģ{7L�@��	�V�����R/�*N��|����yʕ�,}�Z�3N�]�*�n<q�VύV��I44����.?�O�Z������1��]�kw��^��mMFGޱ:�r��7��B�|��"3�=�ӭ/�c�.��1�:����:S?�hq~]�v�R^�n���&8<|�m@:�.Z���BѰNo�,�C����gM��(8��/��E�.N�;��a#p�;�m�?7����������9�:*f �2���-a�q6�MAU3P��)������ ���x+)JMU0�4f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-sSӊJ3K�J�R=����,Y�k���7&�4v��B���tv�ve��,��1u[��Y���
�*!P%A��.��z�)k�����W�P����e�MG���R��SKJ�
*�_�Ү���c�ݥ��Ռb��ZUW�|O;�tҧ��8�X�
uY0��R��KR�K��<s��cY�cJ��ܔ�k[�:?t �px~x+)JMU0�4f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-sSӊJ3K�J�R=����9s�	ˉ����*y��/�f�y>�ή~��T�e�3�ncKP=+cSpT�Y%�$�����U/7�am���W���t2�L�Ѱ�h7TQjU|qjIi�^A%��Y�u{�~l��Զ��Q���Uk���j�Y5r��Qcm�_��ɯY���H̃8�$������37�;�?�t��MY��u��Cw �Wy�x-�M�0�]�)^�+�(A#��
��ؤ�u:��^���~��c�8t�]ti��=ʤϜ�V�	h`��lVj���T�Ÿ�%l��{�/NZ�����$�ƓrU�e���y�|]n�a�!���vp��1���4�x��ˊ�0���S���1鴴��@�ɢ���E���Hǩ�n��N��=�;��E����?��Wv�foo5��]��H����Z���ɴ�D��β��i��1��0W,�H���{���uM�Md1xz��p�1���S�z�9��"ꌯW��[�,�I�7DK����0w��E��ZoI���!�MD#��'!��.��3�pC�������ᒙC��;���Ӛ|{�>������:�sЍm�o�.
�O~(��EV�?�����0��U�r.X㓌�u�X���-�ARb�!xVͪ����G ���֚#,�Uc�{p��I��F!9A���@ŭB�KG�������
+0M�����l8L�q�!@���@�i��NS��`F�f]W oixt�q�Ƶ������f.8)�mER���:�ޘ>9���ˍ8'}�vހ�
]ƹڭ�tZ��i�x+)JMU02�d040031Q�K�,�L��/Jex$ƻ�x>��*ӛ�8�f�/�l11 ǔĴ��̒��ҢTO�̕Yg�=�f���	�]ax0�j�����_�+��`������T���U`V	�*	rut�u��MaX�g��վ�놲�.v4l:�U�Z_�ZRZ�WPɠ�j�v�޷��.���f;?w�Z�2���arM�z�޾K}Ts�|��Ǘ��3|y�fqǲ�ǔ�߹)k׶�u~� �f�x+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b��	�^�&�;���ĵ�I�+�� -�!�x�[koI����XZ�C��&�%��vl� �EQ�i
ӓ���Glk��}ϹU���ĳ3��lM��[uo�{�zfA4S�g��/�r����>�o���yuu�j�P����3?U�p�%i��d�@u�t��j����w���;��K��$�P��Z�X���M솩�7�"�ZE�-��F7T)��:N0!�����r���@ƦKJ�Ez�����M���]HT���V:Lݔ+.�@'��.�z2�3��e��v��C��*�n}���*��̣�yA6�>�ׁ����.���,��mC�����Z�[g��O�5�)|����C΂.O�X%:�� �5�;�Q\6���>�]F�Mm|�i��!��q0f�t��/�K���_DA�RA/
�>�N����x�΢OZT2H�;��Y�N��W��5��rX��>̵���,I���:�e�mm�fo�j2:�^w�}5��������'�	~�P׃���Taĸ3��S�3��S?������rܟL�h�M..�}<��W���:���h���)�NGj�%��A3��E�}ٝ���`��Qg��r�Fc�Q���tн:�����r4�c=�gc�ӿ��M��g����ɛ��9���ts��;�|7�~3UoF�>������y�,պ��EC�:����X� �r�٣�~��C�����t0R��h8��tO��׃I��:���f9�.�&�9Xb0s�7rht1Tq6B�]A�|?���CjY|�o�-b �K�����"����� �G^��p��K� kp�U]չ�%����0�Su� ����'�=�w.�i��NT��j�����Z��U����-��r�s�Ab�{��J�6�XK���%�A�$p�:𲕛�:�&��eU%�j�d��z9gWî�OG�ѹs������h2�
��|�|;.�w�����N�7�T�:�1�K�^G�3��l�����?9������nP�v{���~��s^��oAm�tx�.Aφv~���=����S�'V��w����Vh�l=���g%�E��z�2с�w����֋/Ol(�	0�{+�� ���!	1��1��e� ��<t��[x�-�@�z)��Ɠ���{y
p�"���l��
����	d���\:B	�n����G2�]�J9V�K
�F������*E�OU�B1?
�{㌗�n)B~�r^Q�l�Ccp$c��\�f����.M�2�X}�tay�d6"��b�$Qs��]��8�{^��B�G��Jnj!�,��c9Pg��`�88���	�i�ÆR���a�~QoT^.�&�۝/bN��r�-���h0���5#�U�.�?�U6�ocG8�!=t�Б[S�
V����e�vT,��!��y�Y|�totb���ɓ��8��"=z�~jR�X�HX�]��t���C���:$�p�
�U�"Yk����%H�{h*�|&�U���]i�2�� �@�F!'��� o������\���H�>���aTM##M#1���-^��+qF�]��Y�z�t���&�y�Q�� �?��@�)�z@���H� <��]���������v�ʍcd����4���#(� ���`�� ����I-���D>��eRͼ&Y�Ȍi""e�q���a<�|�{�C��E�[�o}P��<���[q\����.�p�������8P����2$MR��G��l��*-v�B��mM)�7�[���ƴ>�QBe� �#<酋t<]��Z�.�7����Lh�IRNg�h���tJB��`��!)��,@B]���|u)��&BG��������s��)���$Մ�)J���S%`�85�E�VNN��%v�<z ;7�
��JVm�z��!�e����nHr�0&�Q(
������w.uWmu+�� e4)d�������D��N�T��?�XpQ!������2�'��{Y#ci��c{䆆.9��X�l��J_�{��%jV���v�{
[�4��!MF����Gɰ��K�h�qq"9�yA�h8Ie5��w���w��"��(��r�5����ѡ��$�Hjg��"X1������U�kx�I���K�TR�Z���MY��� qa��������m7t�� [�yB�������ζ���=d���0��%�s`����8���y�s������37 ��M/
��l���psZ��+�K�Bi⟛؄k�9a���q������2ʂ����2W�¥୨�C�z�@��8��p�8�G�@�O�.�,�U��O1"��R�9zU�&�h���Z�>�D���2M���ӧ��&i����Q|���L�,{��JˆR'B �Â^����a��rS�ن:��!�+�t�*eA�Qot��n��f0��1����.c�8�2{��"�$��u�o�~_���6��=��M�C�(�t�.�3R����	Q��+@2gB}7AT��IS�(.���2z2�c*<a��~)�k�Ey0�ߡ Hò�U�:PY�5������r�44��m�c³i�IQ�IK"�Y�`&�VY�{L�%)���X��`�e�<Z4	�0��G�	�T��82�2�V��Y�:,����1�!H��p$5]�Mw2{���.�^��+�����V�@ ���X���rI��H}+4�{���t������iv1x1�Ra�7�D� v�"��a��� v��yR=���dH�bJP�08B�����7a�i�M7 8�\���C� )%+����2M�ܕ���V�Sغz5Q�V�����j4JwI����|e#7����iU�<`i�y)^v)�F5b��Z�n�%c�B�����{��c�[��`E	�-�-�T�^�%�o�#{BB����U=/H�FM����:��W)K)��dƮUk��ʕ6d6��.�۹<��jG�dR�ExUKn!���0��%�J�*�M�ϐ�����ȫR�j��$��~L+��,�"�٠y�,��4���P�#H�=r�4=!�2i��G!�ۏ�U��*�u�k�:w��f�;pV�Fѱ+z�t7�m�p��}mD��8����2]��5R�r�L.�kS8���24�W��#�q��\�}a�6W�ˠ�������q9�f4J��%��1�Q@z�1!鹕�Q��<C�
�a�����%���C�\5g �ޢm�IK/��n\��bi�!��oX3�d�ۊݜ��Ȧ?�FE^��/���0�E�;�@hǦ�(��T�}��d��m�ڌd�@�p�Rc�K�Į��	<8(�LR�T���lB�*l$`8~�r9t�fuY���%�
��\��u��z
m -*<4L\Fp<����͵���R�0�C���Ž�A�~��8�B��*C򟂍ͦ-%*�:K�� ���dCH3vo2�(��) 6)��$'i�f_
	3��/S�[f�(��Xq�M�3�f�Ovw�X�:Hcx#�G.�.�t���ll/(�u;�^�O�O`���<����4�8��kH�2��y�*�;�����m}a��L����c%��*ae�n�5߶�We������,cA�yC�p}Ļ&6���})���,&.��Q9��L�P��/�$/<��a-Xj���#��.�7_�v��r���ܾ����LT��(�w�;���:+o�6:b��W�wfy_�%�^$h���C�j��(����;�%CZ̅�*H)����ug����/��T�%�?;{�J�<Z�M��������@M��r'��5������������u�W@�Y�Tm�}��c
�4nW�mi>7�����q��.��������x�؍G��Q����� JʙZ<���t���Z� ��U�K��k�}�Uf�u�	�<)�2���L���[q�+�W�1Ѷ�'�+���)١�|Cr//d�N�rʽyc)��o!ϯ��4ioP�uPc�E��[�Zgɵ�����p^,�,����b�3Jm��pȶkr:?�E��݌wl)/y�:.?��䛥
0Lk�ŷڻ�׷*ί��|��T=��&�U���#|����vT���$&���p+Z�<Y����oo  ���k�Ԓ��7A��ݠ���H�]s%l�� �>�#������X�����#�j�߁��3���h�����F+Xl7�زEb�);]ZO�LDI�4��*]��L�Zh��ep�}���!�~�ҕ�ȅ���B/))?�����*��Y� 7��B���v�Iv�W�,�մ"�ˣ�y���VWZsW'�r���v[����J�wI����=������l�&���EOB-�
�
w��r��~�;n|�B��|Za��±��%�k��N������	��j��b�{����saxmTKO�@�ٿb8I��^z�Bm�= q�ؓx��}���*NQ��|����t���맇х��J�����T�:M��O墤��4˾*ۿ��r�,�S�W��|���;c�y1q �uH����$<��C��8ޱ���.��@*� �yJ$J{&os1@���|�Ny��u[�l�� j�+=�)�$A���[����A�9?�!.�� ���#���E43`}� <�6��Q
�w�Z���sQ#��e)�bCV��������S�s�I�(��� t|+�A�@D��<�$YH6yoR¥�K	!"G��3\�49E0~�6�>����-��P��B��UM��P�
�l������bmf�F�64ʏn�yj�	a�d'���|�<-�\C�>4�ϋ�Ҝ^<Q؏�)ǞK�vG'��㵬�uA�-0�d8c��й7�Nt�P�0�3�����VA7;�G5ނ[ʟ9�"��O@��;6E �Ac�M撢�<?1(-[��nY�Я)0��;��yߏܟЩθ�_�+�H�OU�s�� ���X�K��k�v7���5�c�a�Ժ���O�� �ܫ_�v[�gozG�R�W���o�����7��mGQ�k�r�!x����D[��7��o�����m�M���H-z_�(��z`:, �ҶtIͻN�ȴb���ۥáym�٬;���[�U��^_��r؅j�K��ƴ;C�Y鐣otߩ��gK�%x�[ks��g���UA#$;������J�d��rMC#f5̐y�R��9�v��l9�Q��r��������>z<��:z���Ӿ�D��ؿ^�����q��j��y���ꇳ,Ic_'{�����(>Q�(�U]���>~����O?
�������V]�n��YC�c�U4W��uC��r1���i���^+Wy��al���$��k7�>Sn�D��B��E^��a�\q�:Q�t��ӱ��.�̴@�B�V�C���F��XS3�R�ٌ���ҷkp�X�V���zp���f��kQn�M?Y4�̧�i�bd�=rt9�b��[���h\�PFq�{��J��z-7��y�X���Y�ɪ�j/�/��<
�hM�(���:9���;�>kQ� !�R�X,/g!;1Gl%7�T[�ai?�N�c��̦I
�n�VQ,�nk�4�x�S����}{�S��������z���ӆzߟ�^MF�ڃ�5<S���K�m���/G��XG�D����ï�A�����Q�1s0����E����`I+����3u�u�Bv�u��?�Ѐ���d@�gÑj���h��\��G��jt9���.�����]��&��o��_��m����AZ�
:��K�^~�߼�����n?��aw���=�T뜷��m_��p�#5�jȁf�����m��L������6��hRL~���=�i�����jҰ�� 3=#�FCg�!4�T������9���������ӧO���#����҅��%�����[�c����D�/�M��ۛ� ��ޮ����Q��A���<�p�2�����$m c�NC]��	,�KL�A#�3�v��|���q�Y�͔��A��yi�gw�y�=�V�;�G	��C�`���u��P�Cw��c��O���;��ԝ=[/�T'+Xf�g��������:j)�!/⏫R�)��[�+��f ��
u�ӕ2ZG �A�n꒗a�$p����%�c+a<^VeP�ϭ�l��Sq��j�qओagx�\�o� ;0O�)���c�������GN��q*g�uߪ�7���ڿ��9��;��Ψ�;v��Ԧ�����y眗���[P��^��Ùs?N�<�sNoS�'V����
��Vh�j=�������(�V=v�耥:�tY�U���J����Ɗ;��  ]@�� �i�pC�����}�/b�^p-D�X��r�IC=�s���Eq5�؁�W
y���f�
pE�%~�����7"d�}/*�X!�(�-�~��߫iJP�(D&�0�����^�!����)G�ס18����1�B�ڥɱ ��]�z�t���7�ao�Z�5��!%j����0+S5��`Z�sWX��X�b-)�1Ψ	ی凟a�ٳ�]�FE��z�L���R��gɞ�T���,��ZA�����\����֧�����Y� <\������^��g���N�{ϻ���l����R���O{=��:v$
8�ΪN�&���p�U���U�?k����d6��8�|�+��������E�%B�{��� �R_.w?Oªd��F �Q@�e<�<#-�{��@�zqW!}N�"&+����L�l���RLW�j��@"#�%���)���f+����B�D� ,�#���2$�t�Bhiu� ?�TWȆ{0B�z�,b����$9�C���dڀU`jP&�q�6���`��Юf`3G��3ֶ[Vn��c�7��a�UAAؐid 0b�+��,��?��0(�GbP�Q&��cҹ��G�AC�uY��,����">���tfJ5S?�>�?#V�:�����>���WD�cV=7��� Z��>�Cj��J���o�X[x��CǤb-٧<7œ�F���Q�x{�t��'̖�$�Ԣ)���W��˂R�z$���STY�i�t�C�'�Т@o�#�I��L>��>K�y8���*��A�:N�𼁕���:a�X�D�z��%A&۞��d`f�>�%�̜$�P����4
E�S�~đ���K�ՑZ�0�M
Y��ώ���\$a(�+�$��C��)�*�ђ�2� #�@l����KK5k�S�64,�qHQ�:f#|T:��\.Qð���$�;��Sز}�a���5��(�q��w�����4�8�n\���z^%.RY�����G��n�x�����tE�@���o�KaSi$'6�G�C�,��d�`&��!p�
A7nJ��Wr��Q�&��4�>�Ě쬤(�J�P��T���xH��	�|H�[���2
�1%L�~I���xD8�l�a�����?��37 ��M7
��lŘ�psZ��+�K�Bi⟛؄k�8-��Q���E'��� �2ʂ��Ӄ���¥੨�C�z�= �A�+�48\+Ʀa�
�� Pc�J]Y��hN�b� ����ѡ6iDۺx��6���H�Urrx8ͮ��J��(�>D�4Өg_�0��P�T�vP��?[�:h���n*>�P�OS��ŞN[�,h9�OT�M���=I���΅C�t(-�-��L'����6[�O�Y�z�5�	��,	���er��aY��JAW� ɜ	��Q	�"�R!��'�!���\�y��P��JR(�k�E�Qe!�>I)�bX�I��*��6�v��r�B��Fv�v̀61.J[���]R� �-�Y�{�0CWVY�6L��,�G�&!F5t�1��v��L�L�U�h��{�nv�6�$��CM;i����76�j���W���[�0c���7$�R����h�)��7�铃F������K�Q<�45G �e��b��M6OP���u+I���LS�aR�]1�0g ��Y�v��8�4�k0<[n��񱳏���@�la�&y�ҍ�+�t�I*�
K�k�@��r}[��h�
�,H+O�G��Fn����ӪP������씐�j{C��h�װ)�rz������g[a�r��$2���[�J��q�J�d� �2
<,�}��yA.7j��ņ�#ͼJ�J��d3��XS,T��!�)�x�����ps�������%��\@`��u%m���hH�RS|f$V��hA���x-�Jz�S��x�<q���Fj(�%��In�����z��V��0r���񪣗�(�u�h��X5{g�*�Es��f�m�?��M�Ȼy���m��W9n�\C.�6������.�?�i�8�3v�yǜ�ͥ�$3h"�p����p\��)�R]6� �p��v�LHzq�iT}-OѯBh�f!R9xiId04Q$Y� ��h}�ң,���vi�XEz���k�.��b7�4:��֨�+�%��	yi ���Ў�CQAǩ���o��Po��f� W�[K�	�ޔ&�]�x�_v��Z�6
��ٜ,U���p����Z�}�X��K=<Ź���:��� <<Z�x蘸����"7z�k���������5s@eH�C��ٴy��R�יXz�X���NA@v���]#d��c~��) 6)��$'i�n_
	3�R�Lkf�(ʻ���뙌r3�';�;�>ˎ��(��ƻ^���ծ}Q�L3�i�n�!Ow��2M/a_��"R�L��JUr/���:Y��g��L����c%��*a�I��k�ms#�8��")�Yǂ�+�(�z�Z�wP�4�5��1�������%y>*g��I�6FX�䅇\�Y�>���q�n�M�W���u���G9�ow>$:-t;
D�/�N������+��΀����@i��^	���LX���zM6:�~��o5��AL��2Ty�7	����W@�9E�z�Jɀ�^|�9�$g؜Ib�|CI���I}lj��ɶ�E��r�$�;���:��+qK���Y��<<���j�L�;���m|*��n�x�6���:�jK�;�PhP䷻�6��F�W�A��P+Z���oƣ�n<�7���M����[\Δ�3�x<;+y��Q��
z�o�З��)�����&���@��ڪ��bo�M��_��FC�ȯ�\!�����]$���
���Ÿܛ7�2����J�J��n��5���D�P�,�Q�e#���b�����V��pF��WeHMN秝1�x���N,�%['��0�S����U��������[��Wp$7���[w�T=�G	�	c�5Gx�]9����rI&̚���V�4�te6�x� x6����]"PN��Zv�.�ܼ��q�e�y� 2���o�����q��1���0�t����s	�H�6Z9l�o���u�v39-{G�δӥ'��D�dJ���rP7��U+PZ�λ�pqfҏP�u��]Ԛh�%�k*�?5�&c��X1���M~�u�����]�����$Ke@��F����������v��Q�-�y9������+/پ�6�G���rɵճ�"^����?>qn��N��#���ř�ʷJ��]��g.!�	{ۦ_2���l��[��U5�[1F���7�ɀ�xm�Ko�0 ��̯�z]�1��vUC ������B�!�_�}\;�9|��Fr-˜�x��L5J5�Qru�C�I"C��l2�5(&�2jܰ�
5B�.R�D:�DeEO��4�PSU�	�h���� ?/?���t�?�Y�3
^/_���C_*��Q� T5Q��3�!��T�`�ܹ%ൺ6���iγ[������i����K�e����`���ٮ�o. �[�&B�͓�+v��𴬐�Nj�;B�q]��8�$-%x���Bw� Rn�f��y3K�a���hm�[�J���(�$��	����xy���7���&^�� "���7=����Ea�s��m��.��e�.V�}��j{�:�}����(�j$��4cg:7�Q?H��R$g�RI�0�Ĺ>�G���i?�nG)�%�]���+*Y
`%����ޣ���/˪EG�')��GQp����
��:��0b�v�4�E�A��ud�h�q������������깡O�9K�[����'4`��H���V�U���ZLL��sZ�o�K=�p�dx+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b���׃E�$����;b�F��z�- 5:!�x��ˊ�0���S���1鴴��@�ɢ���E���Hǩ�n��N��=�;��E����?��Wv�foo5��]��H����Z���ɴ�D��β��i��1��0W,�H���{���uM�Md1xz��p�1���S�z�9��"ꌯW��[�,�I�7DK����0w��E��ZoI���!�MD#��'!��.��3�pC�������ᒙC��;���Ӛ|{�>������:�sЍm�o�.
�O~(��EV�?�����0��U�r.X㓌�u�X���-�ARb�!xV��f���G ���֚#,�Uc�{p��I��F!9A���@ŭB�KG�������
+0M�����l8L�q�!@���@�i��NS��`F�f]W oixt�q�Ƶ������f.8)�mER���:�ޘ>9���ˍ8'}�vހ�
]ƹڭ�tZ��k�x+)JMU067c01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U%E�e��z��9�ʤ�T�����-�u3;_�:�GM�u�)�iE��%��E���Uk�y�,������r�]�s��x:���2\P��Ϙ��-A���M�Qf��� WG_W����}V_�n([���2aGæ��PE�U�ũ%�z�ʯfi��}����R��jF��sW��*+J-,�,J�M�+)�+�(ax6���M�9{wk�+��q�IO�D�Z�y����N'}���s�e��P�3^-�x�$������37�;�?�t��MY��u��Cw  M�cx�[ko��g���Td�Д�ځ }�I�f#�I�5c�\ō���>,	E�{Ϲ3��i[iR%i`���̝�w�=�1�y�����˿�^�����U�^Sw�^���]ƙ��a�Ȓ4�u�w��Y���5��{��{Q�������~��Q��D�t����:v�T/Zjk����Vn|�[*����'��S���Z���F c�%�2�uc���&I��.$�E�ek�n��~��HWZ=��O���B���!�i��T�>��Rkj�QJ�� [p���_�vN�
��@���_�o-�m�y�'��Z�>�R�L���!gA��Q�pk�����(�a�T	�ܮ�u]�{Zfq�ea�YD0�����R>���QD�TЋO��9�޺����(Ŏ��r�s��U�r�@͵���C�s��f6OR��w��bYt[۶�ě����fﺓ�N��d�v��Փ��?i�w�ٛ��LaĤ;��W�3��W?G����r2�N�x�M/.χ<�z�W���z����L�/�3����KZa�f��������������D�g#�=OTW]v'�a��;Q�W���t�-�!x4�M���b0���.���[���o���\ҺW�a�]�����d���L���x�j��u_��bP�w�^�T�{�}�N�r�!�=�wo|�5��ӛ�#*��f�ڂ��Y1��p:h��d8�Y�&��I�bV���]U���pWP=ߏ��理�A_���{�����p�	��y���4ȟ���{v \'��=��TOu/�D�@	�."?��ԍ�C�s������΅3�T��Sչ�t�:J�}I-��T�j��V�F��� �&��t�����XK-��%�A�$p�:𲵛�:����eU%�����%�rήF=8��{�s�;zM#����t�"8����v\���[�?�8�~©�u�c֗V��'g���,��G�`�h�L�N�g��Am��!ZO���yyz\��9?��u�=�Y�qB���	�3�O��Xaz�};(�[���R���D9���D��˧��/;/�<���'��_��V�� �D�=Cb6.b(����W���!�n�9����ꥀ�OZj��)�,��jZہ�7
y���w�"t���O��2��r���ҋ�s?��'Oߩ�>YBT#
��(�3^z������rd�p�#{���Uf?]���X !���H�g`Of#X� �O��K�5�n�����,��9��1��b�<�u����c�P�p��?l)�9��G/����e�^'x��%@̉�_γ���G���a$��l��{��Ƌ���tHE�8t��T��ջYS ����ώ���`? �F;�'[��� N�Z'�hO�<�J}�S.ң�&��u��م~K{Z8Q{m�@�>���_��!���|��B�D���R�g�_�ƍݵ&/|	� d�mr�l��v�{+��a ɥ���D铿Ȑ�F��42�4S�.������`�������J��kr���2m�#ȱ�@�2�4�j!�d
��k��lˎ`z�j�m���8vA6�onO�k�8���!�������[�|��4rH�#1(�Q&5�k���̘&�!R��X�0�S�'�?��Zd����G�W���3�h{���}�9 ��8�= v���j�>B��IJ0��3c�-�Z�ŎP(���)e��F|��ܘ�'8J�� }�'�t���+7Uk�%��^ޣ�	a2I��L��͙��NI?\�2d!%3�H聢�ޙ��!��D�H0���S�t�?=|������<0E�Tcp��L���h�������n�G`�Q��U���SBO��2$���ܰ�`����ح I�Ƅ4
E�s�OR���Υ��H�
k0HM
Y��?aåH��P"U�	'e*�h�
J,���FK���i��֌�����T۱�=rCC��LK�c6�W�����k�LR�y�=�-�@̐&�rAFY��d�f�%X4Ѹ8������ J4����Pǻ�a�;`�XpBv���U����P`SR$�3�G���c��{�*��5�ܤ��-ā��t��q�Dہ�,�w@}����N���Ł�ж5�*��w�$�F��7?��-kokn0%L�~I��$�xD8�lS3��un{�<�g�z��4��G�!�m�nN�{�q	^(M����1�M��n��I��x��^���Q�@����2.} oE���۾ �m�Q�ƀk���>���}*uAd	��%}����ѫ6iD�������� 2}�Vi�IN�>�g�I{#\ݎ���ee���&P�XjJ�
4z�W�߇mp��M�g[�0�~�L���i��-����)R��x��'����\8D��Aˋ<G��Љ���}9X�;8��8B������!� ���t��I]XƲ<D'D��C�֬ ɜ	�����A��Q\n}e�d.�Tx(�Re�R���#�<�`"�C-@�.�e��(�e���ko�k�1
-.�@ihd��`Ǆ�n�iQ�IK"�Y�`&��Y�{L�%)���XVs0	ʲT-ڄ|5�#�G�^t�w�|��ѬV��_����Ip8���Hݝ��kC٥�����@�+�ݚ���k4�@~C.)�o��r��ac���X0��f�#,F�n$j� ��I�-�8�OP���u/I���L[�aR�]15(g �\Y/v��8�4�k0<[����s����@�S`�&y�ڍ��wz�I*�]
��0PF+�d�m��$����U����b�*T����/�����R��:j�5c�B��ӻ�}���>\�j�r��$2�z|[�J��qJ�d� �2
�,�}��yA.7j��ņ�#ͼJ]J��d3��ZXS,T�T�ٖ���ln��ps�j�n���%��\@`��u%m�ΦhH�RS~f$V���5���xA�jw�S�im�<q�U��F��%��In�����f��V��0r�����,�u���nu��=B�6x��[��eW4�n���p����<���8�2_��5r�s�g��]G:{�+��qH9l���0E��If�D��b��}�cS��lA��$) =���4��Ө�Z��_��0�B�r�Ғ�`h�H��3 �o�7���Y�W��V�4�����,�]2.n�nNit�ӟ[�"�Pė�&�nQ��7ڱy(*�8z��>,�z�6#Y�"�8ܭ���Mi���Q<��e�I��j�@��]�R�Z��G/�C��V��:^B��)����7������Ѣ�C��e���D��K�:��
3>�_�����cJԆ9�2$�)��l�R���3�4y����NA@6��c�!�܀�鞒Q`��;Ar�F��� �0#����2e�e�耢���+�]�d�������[��v��p-�G.�6�����llo(�};�f��Q`���<����4�8��3�H�2��y�*�[�����m}a��L����c%��*ae�i�5߶�Xe�����cA�yC�p��&v���)�ş,&.��Q9�L�P��1�$/<��a-Xj���#��6�7_�v��r���ܾ����LT��(�w��;���:+��j�1V��+��҂�^�	��Xi�|��ڶ�)�<宫I�İ;�c�&Pblg��qN��~f���n2~/����2��l1�¡���� �@v7M�d�@�E����d�� l�T`�W�a_�`yy�t�)S~�D�&����o��P�gn����W@P/�������E���aan��!oTz������A�j<��ƣz{���qx��niJʙZ<�������Z-��oy�K��w������~ny�W eLm�p1���J\ܯR�����T�)7W3%�S�C���du^^��|�{sm)�Ut!ϯ4*�4i/���Qc�h����Βk��w5����X�ߠj?�����(��
ái��|�3X�w3މ���C��&FxJT�Ϻ*�0�c����b�o��_�����W�z>��ƪ�� ��u0�;r��Q�?�L�>�K̭hi*	i���pT <��7�5*('o�^#�F;�U	�`Q����|yP ����o~����q��2|��0�����.�s	�H�6Z9��r|�:`[OQ�&�)8�ti�!3%�Ҡ~��4͗|�R�V.���.ܠ��#��]E.�E'�mI����O�|�X�AV��;�ɯ�7�pq����;��d���YS\���/�m��0w��*oy�˱���]y���������Rn���7^Ļ��k�V�����>?��'~�� ��V��%���i�
��3����&�i�,�;�t��sx��@��F{+ƈ�7�����dx��Q�1D��S�V�IwL@�e=�H&=p��={{��yT=(���sU�.nt�P��d?�qq��3��Ew���ϴ�C!�X"wF�d1��،a�ɡOl1�!�zk\��N���쵗���]l�6 ɓ�������U������e�P_�U@e~ޓ��L(x���ΣH���S��ꦊiz4��b��7(
�Y�b?}�{4�9M�R_(�)�m[� !��c	|!"��Dr�b>�!be,C	�(#�r��r!SC:�n)�I��xsa��I�� B��!B0&<� �.�A��y�5}�/f����=�]G���~,��g!�N`�7(BH��_����C9U%��kT�ܻ�7}�MW��@��)@�����j����g��s�ѬX��V�(��N���P�ihI����/�@<߃瑖4��٦�)~����ȳ�Gv�kV�/5½<��]D4�~;�u
�`��zg9:���!�aN�N��~ݵZ��iA�Nn��o錩��Q�ݟ4Fr5��aXnVUiw���B<\��l��#*ϼy`m��*U�$>[�r��zқ��P�"Ve&��ج"1��u��N���O�-cc�V�Mݥ��-D��=>�ҧ�3�Гp��7ޮ�-��0ky�umr-�LrA��h�V&"�ƕ�Oye����=F,WМdυ!{�ķ��CV�QLÃ�no֬L&QJ��`�zpmjbq$�:S�V�x�����s_�!M������̾�e���_�zǻI_^#kճ#L�/V��P��?��ֻ܋a���;��r�GՈϖ�l�BpC3��uz���a��jjh��{�T
l.����3e��|9[�9mH���۸�4����v��˗)�ݺ�kZ�	⫵���E�n[����Q�c,C��c�ɐ��.�Ax�|Ix�3�����m�-Υq�J��P���Fwq��Œ��w/�3�3N�֤������6���o�iN�
�`�dK�����Wc(�K���a��`����;0���i��Y�e�hM��ߩ���ex+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b�����N���3y���ӿ%�:NU�  M�$�x�[koI����XZ�&��$#K�@ '��`N6��V���M7ۏk��}ϹU� ��ٙ���(� ]u��s�}TgDSu������:��6����yuu�:z��3wg~���,K����޾jg�"�O�$
oU��D�����/u���ďB�'j�c=�Uױ�z�P�Xk͕�p�k�Pi�\�_�8��h��~���U6q�. (���ڍ5�ϔ�$�绐�f��-u��)W���NT-]h�tlg<��23��燐�U�P�}���*��̣�yA6�>�ǁ����.���,��mC-��?��Z�[e��O5�)|����GO��]�E�Jt��ALk4.w(��l�=XS%�e��������<�C,�`�,��d�_����A���^�|j����M�ԝF���d�F)v,������#����j��尴b'�1�
jf�$|7P�(�E��m�M����l�=��X]�����^W=m���iC��O��&
#F����������?�6T����x��#l�qy������s~��ިט9N�y��?���PM����a智�:o!���ޟ|h@�Y2�ܳ�H��e{4�w���#uy5��{�B������.z�I��7�{�/j��}~�� �}Fܥ�/?��o�N���y��_������Y�u������/�o�ÑB5�@�G��m�?r�6�t&���t���_�u4)&��{���4��hxA5iX��
�����C�������
���Q�^��pP���|xs��ӧ�����x�S��M���р��-�1T��Y�ڗ�&f���c �KoWpI�(�� �'x�|8z�z~�On�6�1Y��.�����%&֠��^;�l>�qC��8��,�f��� _؏�4س��<܃�T��ӣ��!Y0��싺�q��;��1cu�'�	����t���?��
�ك@����ߩj}i��ZJ�{ȋ��T�j
n��J���,�F��t����@w����eX8	\�=(b	���JO��U��S�%[��T�9�t8�d��;��"���xJ!��_�o����s�����vG��Y�;fݷj��`8�9���fa�?�����3�:펝n��i��h=�u�9���q����@�����p�܏ O������T����w��n�Z�Z�)�*��04ʱU�]&:`�N>]��zy�Ćҟ#����/0 @=�pe@l0��P ~"{p_��C����B(V���x�PO�\~��eB\�7v`��H!o4����]��{��o7��[b�F����A�+��t���a�ѳ�*E���T-
�	�(n�"��)E�'+�'ʑ��uh�d�`hL&�Юvir,�0t��^���eC؛��d� CH���h�s1̃��TM#!X��{����$V�XK�q�3*DB�6c��g�zv�K�H��p�ׇ��x�K"�%{"S�Ǟ�L�k��Of`�s�G;��_X�&v�f��|,pY; dr�?zYoT���:��!<�G�~<���f�K�.�?�U�g�ؑ(��;�:�����½T֣V�������v�����|�Ů,�rn{@|�F;\Jtm�-�N��J}q���@<	��1��4�G����<�U��I��}\��9e�����3����J1]Ϳ����\� �@� �BN��X  �z0�
������<��?ː�ґ
�id�i�R<���S]!����!���Q/�4+��$�
�iV���A������d:�yC����I�78�X�nY�q삎��ܞ��VqaC�����'������[��(�A�G�T3�I�>A�C�e1�d|�g����jҙ)�L������X��L��l�V�>��s�_y�{�Y���W�h;�����*Qj�&�cm��ZC���d��@�O���
G����u�0[���R�����'P��@WH͐C?D��7D�I�w���L��h�b����繽��P�W�P���G���g3�� ���Y
N��K���]��qj�a����� ��r��~n=�J�323�4����4V�DY���!P���{L�Bn�(�{�D�D|������Rwu���<L�&��\��#l�?I���b��iRD+���Ղ�
i�$��=�H�[3��F(��RM�� �9s�Y�������2�K�0��'2��)l�>аl�b��l��8J&G�oűL�S��<���d=/���2����@��*I7Dp�Qpda�"���}�w4��)	K�@@�D����3d��1�p'p�
�7KnJ��W��Q�)��4�>�Ělä�.�J�P��T���xB����	��|H�[���2
�1%L�~I��G�xD8�l�a�����?��37 ��M7
��l� �psZ��+�K�Bi⟛؄k�8-i�����pO<W�R$.d�3��eEK�SQ)����{@��.W9s�V��"oΩ��>�� �Wќ>�n�
ř��	l҈���\�]l"�'j�����ٳiv�4W�	iF��3�S3����l���N� j�����&8i��u�0E�X��Uʂ����Du�iQ̟ؓ	D��]8DJ��� �R&�t⡵��pi�5�:8�u��X��[I������]&�����!:!���|�
�̙P�M�@0(B�"���q������
EX�$�b�&Y��U20N\�>����@e���׎cZ.\ȁ���η���Ҧ!�E,����j�����2}f��*kcن�IP���h�$�è�6:&8�[@S�Y�I�*͞��ƽ��焌
nG�P�{�t{�����4E�o�g�_���@ �$�X������ɤ�%zpʽF���~������iv1x1�Ra�6�D� v�"��a��� v݊A�?�E��k�i�EL��H(y��&�&N0���ϖ��<�z|��#�dՐwfX�I��t��~$]k���B��ׄ�2ZA���(�%Y�V�����X��U��k���|�V!���j5�Q�?�aS�3��.��(�DT�_.X�DƸ@'uK U��9n_	�� }BF����OU=/��FMҲ��z��W�m)��l��`k��ʕ6d6�l/3��Y�c�V�c���]�]���"�\�����?��iXj*Ռ�*1�
P"�P�B��z*2��'�B�m��H] D� �E����g#�^f��(�(��c�q��襭�i�|�?�[�ۮ��삳�o��¢�Iw�޶	�?��M�Ȼy������W9n�\Cn�6������.��A����8�3��y{����$3�'"�p����p\��)�R]v� �p��v�LHw�iT}-OѯBh�f!R9xiId04Q$Y� 7��1}���,��[yi�XEz���k�.w�b7�4:��֨�+�%��	y� ���Ў�CQAǩ������Po��f� W�[K�	�ޔ&�]�x�_v��Z�6
����,U���p�����M�X��K=<Ź��[=��� <<Z�x蘸����"7��k������ۗ�5s@eH�S��ٴy�R�יX�X~�\�  ��f�2�=3�H���
 ���ޣ��4B�/����?)S�5�E��T\q��LF�����e�eGa�\�/�H������ؾ�@��rh�i��]�@�LӋC�W����-Sj�R�܋�g�{F�6���eE"�jfbh�X��JXyR���o�\_3��^I�vֱ �<��^���;�x�%oLa.�d�0qI����e҄r��� y�!��ւ����?rl�p�l7x��� �Q��۝ɁN�Dݎ�|ƛ�Sj-m����n�3 ƪq|�1PZp�W�n�.V:%��^��N��)�[M�� &�a��͛�����+ �"s�c��d��n/����ߨ3l�$1O��������>65M�d�?�"ZK�^�����"X╸�E�ά�V��}5f�ϝ���6>��m�ځ
��{_�f�W�%�]F�p(4(��]��r#��yנ�z(�-�?G��W�Q`7Лx��vp��-.gJʙZ<���<���Z	��׀�K��������~nyy\ eLm��p1���&\ܯR|���\�Wn�[�K��ʗc$���
���-�ܛ7�2����J�J��n��5���D�P�,�Q��#���b����V��pF��WeHMN燝1�x���N,�%['�3�S���V��������[��Wp$7���[w�T=�G	�	c�bGx�]9����rI&̚��V�4�te6�x� x6���U_"PN��Zv�.�ܼ��q�e�y� 2���o�����q��1�ˊ0�t����s	�H�6Z9l�o���u�v39-{G�δӥ'��D�dJ���rP7/V+PZ�λ�pqfҏP�u��]Ԛh�%�k*�?5��c��X1���&���L��}ٮ����j��2��[������n{Cy�^sW��rߖ׼[���^ו�l�u�G���rɵճ�"^����Tqn��N��#���ř�ʷJ��]��g.!�	{ۦ_2���l��[��U5�[1F���4u�dx��M
1@a�=E.��wڂ�WI�T�)u1���|��	���"�S�h�]��2�kN\BYl5�#�x���&-ٲW�u�lD;G\(G66������=����@F��������&�&؜bL)�Y{�}���Tǣ�q�ڶٶ�� G3x�Zko���g��q�Ү*�N6Y�E�cumɐ�A5���H�?P����;Ç%�v���Ab�3w��9���pDSu��W/���:��1�o��yuu�:|��3wg~���,K����Ξjg�"���$
U��D�����:^�I�G���б�>���S=k�y�����[��n�4R.�t�`B4M]?���*�8�M�D��ލ5�ϔ�$�绐�f��-u��)W���NT-]h�blg���23��燐�U�R��P#KU���G)�l�}���58],D+`�Y=�ۆZF3���(�ʦ��,j�S�4K12�CO��]�X%:�� �5�;�Q\6���>�_D�um|�i��!��q0f�t����K����GA�SA/
g>�N���&x�N�;-*$�Q����,d'��d���jk9,��	�ZA�l�����jŲ覶M����O'��QO���r4|�����E{��_4�ur6��(���jx�ڃ����P�\�z�������y����A�����So1s0����E����`I+����Su�u� ���ޟ|h@�i2����H��e{4�w���#uy5��{�B������.z�I����/j|�>?�b�־�#�Ru��F�wgu6<����m�k�=�ŠZ�ݿh�n����;�!�PC4{T�g=>�m��L�����~m@�Ѥ�|���=�i�����jҰ�� 3=#�FCg�!4�T������9���������<b��q��K�@}gν0�g~��� �ɼt��G�Q��>Q+P������u��P�w>��`�s�LzU�s�Z��aK)�/�]��PM�^��_)w6$V��[����:��k�����6�.\^�t�T�V�x2��ʠ�[-ق?�^��ՠ� �agx�\��hD;0O �B��2ߎ���{�t�#���8������Ҫ�w����?��9����Q�iw�tc7�M�=E�Q���9/O�뷠6�:�I�gC;s?N����@>��T�������n�ZoZ/)�*�YIt�c��Lt��|�,�����J�F�|gm�-��  ]@�<2$!�`Ӏ�,����}�/b�^q-�x��h��v�^����!��k;�B~��w!��?sW�+BG(!�����!�� ��c����N���!�>:�V)"}2��Z"��Q<g��uJ��#����:4G2������8"~�ڦɑ B���.,����F$��A�$j��k��Gs��Y(��s��Mm,ēź~,��}���8��>���P�s2?L_������I�v�K�����fsyy9�&�Q�H��^�v*��g��#�鐊��q�ȭ�|�w}M�Ў2˿<*�߁���[�p�lA_�8��X��x��*�N9�H�����"�)db�]�i�D�U�����B~�2�HV��q>3	��J1��U+7v���L�%H���Q�I�3����-�'+�$��#>�;�!{!�
�id�i$��]µ�\q%����!v1�U��4S��88��2m�#ȱ�@�2�4�j!�d
��k��lʎ`z�j�m���8vA6�onO�k�8���!�������[�|���rH�#1(�Q&��k���̘&�!R��X�0�S�'�?5�Zd����'�W���S�hs���~�: ��8�> v�^�{j�Ü>B��IJ0��3c��Z�ŎP(���)e��F|��ܘ�'8J�� }�'=w���7UK�%��^>��	a2I��L��M���NI?]�2d!%3�H聢�
ޙ��!��D�H06��Su0�w�x�N�	�S�H5f�8J��qj(�����K��y� vn�{�,1�0%�4!C,*�����
��aLH�P�95�$���\�ս���Ѥ��k��Cl�?I�J�
=�L��CA��hIX>-#y�ؚ��5B1��j:ְ'@nh��i�u�F���5���\��a��Ijw /���a�@��dT� �(�q��̼�&'�3Q��D���TV�x�z L� ��!�B�.7]�*|O�
lJB��v�(��{l|/[�����T���8p[�n�����h;Д������)z�8��vMǇ
���'��?����t�ڛ�CF�L	�_R96I<�#[��G�:��l�ؽ�� m�Q��f+�����D�^q\�J�\���&\s��	�$��PM<��^���Q�@��2.} oE���۾ �M�Q�ƀk���>���}*uAd	��9}����ѫ6iD��/����� 2}�i�J���M�\	W7��� ��L�,{��J˚R'B ���^����~��tS�نڏ��"�+�t�*eA�awx�:n���?��1����.b�8�2{��"�$��t�o�~_���>��=��M�C�(�t�.�SR����	Q����+@2gB}�AT��IS�(.�~�2z2�c*<a��~)�k�Ey0�ߡ Hò�U�2PY�57�����r�44��m�c³n�qQ�IK"�Y�`&-�Y�{L�%)���X��`�e�<Z4	�0��G�	�T��82�2�V��Y�:,�����!H��p$5]�uw2{_��.�^��+�����-� ��F�	�7�R���h�(�6���~�#}��b�b���(����# l����(ژ��r�~�O�
���o���t����-����o^A�*��n��y�7��t!v�M��]����F�T̜dAZy[��W6rc�O,�V��f�W�eQN��h��P���B�aS(os2����u��U��V$�?.���HU�u��Sr҇�H?������˨IZ��y�*�ҿ�l�4��X�\iMfS
�2���=��ts����I}�W-����&�#I���Aґ�b+#�HAe�y�*UV�)�i�8������Upb<"�KS��R/s�*�?���~�:|m�PZ'_��VG�Nt�k��g�j��Fw�޶�?��M�Ȼ}�����3΀[#���z,}��M�0�2���B\����C�����۠m:����B�u����p\��\�.�"c8!��#�K��<����	�U�,D�/-i�����f9�]�;-��b/�`�&��Q$C�e�a��!pM)vsJ�#y��y�"����at�JW��ЎͺP/Ʃ�����`)T��,!�����ToK�Į�R<�/{*��W�b�g��J*ɗ��Y�.��ٲ4��K=<Ź����)�xx�(h�p���"�4�0�+�O������vx��8� ��*C򟂍ͦ-%*�:KK� ���dCH3v�2�}�^! 6)�����4Bo+�����)�=�E��V\q��LF�^����y�Mv郮%��E�ԕF�ހ��}��]� �:��)�M�͐��Z�v�����~f�$[�T`2��$�b���ѐ�͠/�"�i531��dv%���-���6׈�3���Uȼ"�b�nKx�¾*����������%y>+g��I��X�䅇�ւ����?rl�p�l7x�� �Y���u��@'e��ھ@$���ZK䴼t2��犱j_i�ܚ�}Ŗ�z��}�OI��YֳX�w�h���CZ̅�*H)����Se����/��T�%�?;{��J�<Z�=������/�ݞ3��Ndkb{���=O��ꯀ`���ڒ�.��8iܶ"��|n��΋�J�]+*�?G����(����*�����3t�KʙZ<���t���Z� ���2�K��k�}�Uf�u�	�<)�2�6�L���[q�)�W�1ѥ��+�����P~� 9���|'��޼���µ��W�pU����:��4ͥ���Yr-8��FB0��)���{B��i��Rۯ0�횜��[CQ�z;�[�K>������D�D��x�i������+82��* U��ƪ����D�B�w3����\�	�C|U�-M�,͇�E>� ���+�����7A��ݠ��iH�]sjn� �>�#���;�3�5,:�i����gO���%<#�h���
���4�l��r�N��2Q�)��J׻n�ʪZ�r��_��~Ȥ�t�*r�-(��KJ�o�j�;�J��b���M~�����k�mm����$Ke@5�������~�ѕ���	�\+�ǖ~@��R�]�/jz�{��PN�r6Z^�{آ'��0�U���E=�{�W��b#��S���4�c�K��e״���\�;o5�W�ho����?c�Cx��ˊ�0���S�������4�,jHI Y��8�]�I��Gvb'��V��������Ӈٛ�[�g0&R;�#���C�V���s2-:Q�耋�{y�F�w��bGE�A6}�'�^.�Ee�FaYL�=��/Y�P��)�=��a{
u�7�m��/+i���Jr43B(,��E����;�u��k�"IH4�q�L)�Ql�=z�uv�b�(���)��&�����ҽ���Y'y��M��<�UA����ʼ���GQt=����OP.k|�q�I����2HJl<Ϫy5�(u?@�/w֜`)���܃{�L�'0
�	���*n�Z`�^�8: Ev���DVX��`hhZ|��f�a
�s����5H�u�zWϟ��M],��}0��)Ʊ׆r
�@�����Ia���<zc�䐆n �7����e.+t�f�&�i����x��[j�0E��U�ZF�x$C	-$���9���������.���yT��]E�$s�r�4 ���(q���<�	��D�[�*��4!��R���u�z4	���K�����O{����զG����2�]|�6����l�=b��=Q�sw)��޶�6M��s�_�y���?jeN�x��M�C!@�7vn�%j�J�V�5R��<�B��B�:<��rl[��;�7��E� M�xt�[��7% D�ɻ�������}�
�32`����Q"N!�B�16��c�U�K���ڷcܾy�u^�#�9q�'@ �|���L�O��]��;@qx+)JMU014f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U�9�y%E�7:�7��N1Z�\�j��8��`�J��2��*ss���[�μ��hyj��i�<��!nrLIL+*�,�(-J��gX�|"�|��9���d�Wh�4G.j�����_�+��`������T���U`V	�*	rut�u��MaX�g��վ�놲�.v4l:�U�Z_�ZRZ�WPɠ�j�v�޷��.���f;?w�Z������̢��Լ�b����gs��t�w������O����׷�����2�]۶�u���i_OA<Z�Z\R��噛�˂S:禬]ۺ���; ����x+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b���������bs��In���~1� U�$Kx]S˒�H��_��D7�j�,PDEDD^��(�PVT���o۷W�:�y2O�E��7n!/��M��\
J
GIFْcuC�0*�7�����߱}r�/��=�_��(C���|/HF�_�}�\�&��"F�X��� C�!6�q��c�!85i�d�?����$�筡_d%��xX�8�Ը�X��#�7��7 ��OV�6�o!���u�6q����%���R��c$���v��5O�Z�������_��P��zp��=�ω�R+�ǹ��y�F�~5#�A�O"���t�a�jnZ9[cp��Ï",J|���H���#�C'ȥb�q�?��֡W�tg0�t�xW���(�<H�қ�SNQ��i�N�Ϯ��]��qu����0
%!�q
������!��>��>�����i[���0�gk�5�J�!��SV��<�&���zt�;>B~���,v�JG*���4�I��.8�t��\���p+cp���*��C}@xtWC��ae���Jd��>ox�U��Ulx�k��d�v,o�Bmc�5E�U����fx�"]���ͨE\uf��Sy"�(�g37Z'.�b��,Ba2��ӓZ�A�Qn�}�]__O�����L��]u����Ԙ��>t��y�\�d��s�fa����d_���j�
�畲Pz�׷��It����Q	\_ s��bjk��������F�뵭�ۇ��={*&l��z���N��X��u�6��Y��wp1�_�����'Ϳ������Gx+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b��|!��ӭ��~㫼u��!� '� �x+)JMU067c01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U%E�e��z��9��v7./�2��)}�X�5���u�)�iE��%��E���Uk�y�,������r�]�s��x:���2\P��Ϙ��-A���M�Qf��� WG_W����}V_�n([���2aGæ��PE�U�ũ%�z�ʯfi��}����R��jF��sW��*+J-,�,J�M�+)�+�(ax6���M�9{wk�+��q�IO�D�Z�y����N'}���s�e��P�3^-�x�$������37�;�?�t��MY��u��Cw �ܛ5x+)JMU02�d040031Q�K�,�L��/Jex$ƻ�x>��*ӛ�8�f�/�l11 ǔĴ��̒��ҢTO����_�\�r⥽��J�y�˷j�����_�+��`������T���U`V	�*	rut�u��MaX�g��վ�놲�.v4l:�U�Z_�ZRZ�WPɠ�j�v�޷��.���f;?w�Z�2��tV��+w�X[�W,�k��;?� �/I-.)f�����e��)��sS֮m���� <�lax+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b�������8���a���h��� Rm"�x��QJ1D��S��",I&�dAA�^�����ɒ�A��f�`}T�

��܃4fP��q̘�#YO���t*�0�I[��p�ƫ j��tNl��>F�ڎ�i�ٛ`L6���w���u=ོ��E:��-�ŉ�rm������z�/
�k<|�_(۶3��B�+}CcL�2��~��β��	������O�� \�x-�1�0E�}
o�D+�#� %�%7MGjnϐN���y�x��87�	S���N�ء���4�h (fṷ&Jx�%l�$,!j��+@~%=Ε)*�>�+���,�s^|�6�?T'-�x+)JMU01e040031Q�u�q��qq��MaHv��uɞ���Z呇��V,�r� ���x�[ks��g���UA#${퍪���J�d��rMC#f5̐y�R��9�v��l9�Qv��Z�}���s�}�xDSu��ǿ�i_u��m�_/RU���u�R�g�<��T��Y������}���E��Iު�߉wo�_�x�'���O�B�zz��c7L�����*�+o��׺��H����q�	�4u�����<l�06]@P�ӵk�)7I"�w!Q�"/[�0uS�8���Z������xZ�ef� �!O���Z�P#KU���G)�l�}���58],D+`�Y=�ۆZF3ο�(�ʦ��,j�S�4K12Ꮮ9�F�Jt��ALk4.w(��l�=XS%�e��������<�C,�`�,��d�_����A���^�|j����M�ԝF���d�F)v,������#����j��尴b'�1�
jf�$|7P�(�E��m�M����l�=��X]�����^W=m���iC��O��&
#F����������?�6T��x��#l�qy������s~��ިט9N�y��?���PM����a智�:o!���ޟ|h@�Y2�ܳ�H��e{4�w���#uy5��{�B������.z�I��7�{�/j��}~�� �}Fܥ�/?��o�N���y��_������Y�u������/�o�ÑB5�@�G��m�?r�6�t&���t���_�u4)&��{���4��hxA5iX��
�����C�������
���Q�^��pP���|xs��ӧ�����x�S��M���р��-�1T��Y�ڗ�&f���c �KoWpI�(�� �'x�|8z�z~�On�6�1Y��.�����%&֠��^;�l>�qC��8��,�f��� _؏�4س��<܃�T��ӣ��!Y0��싺�q��;��1cu�'�	����t�Ξ�~��,��΅3�T��S���j������U����-��rg3�Yb����J�#
�� P7u�˰p��{P��ӱ�0�/�2(�VK��ϩ�sv5�8p�ɰ3<w.ڃ7D��?�'�B��1ߎ���{�t�#���8���w̺o����p�s����Cg�u�;��j�n�z��s�����-������b��̹'@��?�9����+����z��r+�^��S�UB�ah�c��Lt�R�|�,�������?F�|oc�_` �. zn����4`8��@�D��1v/��"P�^	h�񤡞��
p�"��o��
��B�h�3����\�B��n৷���u��J9V�+
�D˩����*E���T-
�	�(n�"��)E�'+�'ʑ��uh�d�`hL&�Юvir,�0t��^���eC؛��d� CH���h�s1̃��TM#!X��{����$V�XK�q�3*DB�6c��g�z�,t���Fѳ�^?���{�� �Y�'2��9��Vk�D`v?z�����ibg��`�8 ����B� '����F��<p������{��#*j6���"��^E�x�����������h,��@�a=j���ګ��zh��??�7_����!���n�åDg�v���^�<�����ݏē�*c�HC|l�*�H��^E�,��^��UH�S���J{>�0�8�����Z�1���Ea	�� t
�(�ي¬� �(Q;��ȃ?���)��FF�F�!��O<����P��?��B�@�2IN��.�6`����;l\ �M�c1��1���̑$�Ì�햕�.����i�hGP6�A ����p2���Oj�����I5�t��t�P:D]�0KA��y6�����&��R�ԏ�O�ψ���D����l��O;�a��ǻ���A�͠}5�ְ��i���j�1���5���1�XK�)�M�䮑��p9ޞ+]��	�e*	)����S�x$���RTX�Y�4�C�'��С@n�#�I��L>��>K��y8�����A��:NE𼁕���?bDn�J�m�d{��R�	�+�,/s&�XV@$�Sk�(�N�M�F*(�/.uWGj-$¨n4)d�>;��s��]� ��d��

�,���FK��؃�$�5c/k�b,-�t�aO��а'�!5똍�Q�t|.s�D��{"�L�@^`Oa����e3��Ӏ/�,�Q2�a�*>bҗ�DX�q-�'�yA�h�Fe5�w���_P�!���#���﫿��MI��\8�J�#��!l�/[#����T����pS�n���Վ�h2є����$�dG%E���P�n��n���l���D��O�C:ݲ����Q(�)a�K*�����#�qd��l�^6��ٽ�� m�Qx �f+����D�^q\�J�����&\s��iIe�*^~."7�\�����Q�@����.} OE�����y�\q��1�Zq06�8���T��\Es�hg��$�I#ږ�s5w}�!�L��E������iv�4W��hF��!:��F�ꅉ��݆R�B ���^����A��tS�ن:��",�t�*eA�awx�:n��?�I�\ ]�l."�Ciy��k��g:�ХDw�����:��+��M�dGH0�t�.�S�h�Z��U�ҷzH�L��&�J !�
E��8�QFO�r�G��",U�B�_�,�p�*��8"HòO�(�>PY�5������r�44��m�c�i�qQ�J'�Z� x�h��B������X��`�e�<Z4	�0��#�	��	�_ffr�
G��w؋�w�#����-�Hj�H�no���1V�h�m���@�k�ݒ���k4�@�!����ԷD;M��H�1�O�X0�7�./FX*��٦��9�.[$c4l�y�bĮ[1H�H�`�b�"���9� 	��r��$��	�!8]�1��r듧\���}�, �&�6�s�n�_u�kMRa7X_�h]����F�T��dAZyZ>�W6rc�,�V��,+��e��tT#���PGE+��M�e�ӻ�����h:��
��V$�1.��HU�u��W�#CH��Q�a)�SU�r�Q��,6�i�U�TJ�&������b�r��M���̆�v�`��Ø�U�ظw}�W-����&��+i����@C���3#�JLE��G �H��P�Pʳ��L��扳P.Nm6RCA�(�Hr��l��ˬ���sl?�W���8��/��v+{qU��VpV��W4%�n��6�����iy7p6�E����*g���k�%�fv�_��a�e��ч�"���c�n�2�S����d�A�.V����16�Q�����A��Î�	I�<����)�U�,D*/-i��&�$�9���Zz��^p�.mK�Hq�y͢�%C��^��FG:}�y�"�$�7!/`8?ڱy(*�8z_����m�ڌd�@�pk)2՛�$��x��.�T+�F��3���
�U�\����]�0x	����8�ssAg��B��G���`U$��"O�a�U��!x���^�`�>�f��66�6�X*�:Ko� ��2�)���k�se�/�=%��&%�W"��$���KA"aF`�Oʔi�l�Ey7W�t=�Qn��d'pg�g�Q"�� �pw�k���ҵ/(P�i�<3�Ӎ4��V�]���!�_XDʖ)�R�J���3_##k�A��"�i5314c�d�Z%�<�[~ͷmn�gpE$E;�X�yE�P/\'�f���7�0�P��$�G��2iB9��k���>k�R�G�9�����
����m �(���·�@�e��nG�H>�%�)����Yy��c�8��(-��+A�r�	+��{\��F������S���U��MBkg���qN��ޱ�C2�G�߫AG�/�6g��'�PARkq|R��&m��~��\/I�n�+,�J��"lgVp+����3��Ndkb�
���[�� ������`�Ϋڒ�.��8����U��kPi=�����(���M��yS;8}��3%�L-��J�}t�}���^�=�%��{i
��w�u�	��<.�2���o���[q.�W)���ǻ*�+7W���%�d��=I漼��3y!.�捥̫�<�ҟ�Ҥ�[f:F��~E:"�:K�Go�F�:¬X���j?��*��Qj��CR���ag�.�f�Ky���I��� /wU�az� /���.��V)���w�� U��Q��C�X�_��ޢFWG�w;���\�	�f���-M!]��E>m  ���+yk���7A��]��b7��o\sYn^8(�Lr�����/j�me\c�j��"� ݯ�0���\�#R��V[���`��LN�ޑ�3�t��!3%�Ҡl�\���|�
�V.����-\���#�v]E.h�&�lI����Oͼ�Xi=V��?p�_]&j�lW�hw|5�RP�Q~��_��?����]/���ET�o�k^�-���`���K���=^�MJ�����x��f�Z���
��|�o�n����V�[%�҉�
��3�����m�/��_����f���#�^���}�x+)JMU014f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U�9�y%E�7:�7��N1Z�\�j��8�����MM�J��2��*ss�=�?b`��]H���E�������	q�cJbZQifI|@iQ��?�����7��u�'�B��9r)P[}<�]��].���gL�Ɩ�zVƦ��JTI������^n
��>�����_7�-�dp���a��n��Ԫ��Ԓ���J�W�������dw�m}5������B���f����T�0<��h���ל��5וG�8��'x"T-ܼ��x��9p�ڶ=��߇M�z
�ђ��b�/��,�X����;7e��ֽ����rx��
�0=�)>𢗀��U�RZ�J�lu!��)���9��t��t�lq�vJ��п�Ke�k��k~@�+�ؐ�(�^���*y�匢���m�gy�=^a��ѷ�%�߈D1XG3I��	yk�9����(���9�xMRMo�0�Y�B@w
j�2,��]/�!���0�L�jdQ�4ޯ߳�n������Fn�~�� �sV�(���هE��<�����a
�7��������y�Ώt<6fW�����}�K�1���E)I�$(^�� ZB;+P��Ο��`�â#'C�ܘv�kLGg��+A�VX~K�]�
��Omc`>jLvE��k�ٕ�$ʪ�znL���X���pM����-Q��Q�XI躸u��[	��l�Xg��ڊ/!��O ����:������l�m'�\\�uن�J^m�ֆ�.@z�5�5�N.��D׃f�+�m�AL��S�E7��HxS�T](��eˢ�%]Q���37�-�4�N �|�}/���;��Lb	s��LѼWn��~M=.y�J���Q\�馏��
6���4����`������v�牒n����xS��ê*F]�1wO�g��J-�	�Kj�`�O�q_1 �	@xM�=�0��}
o����(�P,��q������������q�?��KCqC葫��д���Ms;{0 ���[�ĸ �%|
IC�l�����5RR��b]>f��{I!�ߊ��u�G_����s5xx+)JMU0�4f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-sSӊJ3K�J�R=����9s�	ˉ����*y��/�f�y>�ή~��T�e�3�ncKP=+cSpT�Y%�$�����U/7�am���W���t2�L�Ѱ�h7TQjU|qjIi�^A%��Y�u{�~l��Զ��Q���Uk���j���S�u쪱���&�g���g�A_�Z\R��噛�˂S:禬]ۺ���; ��y�x+)JMU014f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U�9�y%E�7:�7��N1Z�\�j��8��`�J��2��*ss���[�μ��hyj��i�<��!nrLIL+*�,�(-J��g��}�|���_�n����`�IF��P}<�]��].���gL�Ɩ�zVƦ��JTI������^n
��>�����_7�-�dp���a��n��Ԫ��Ԓ���J�W�������dw�m}5������B���f����T�0<��h���ל��5וG�8��'x"T-ܼ�{�q��>��ƹĲ�S�˂��B<Z�Z\R��噛�˂S:禬]ۺ���; )��xm�]o�@���_1�^��#$�VP���fP>��_����\�yNrN�'*�<m�.��`U&
ǐrh`���LÄQCGфNB�CE��`E�a1d���,3��D�$D�P���##���H�=Ұl(
Ĕ�C�`�S
���
�Q�5U"]��죲m�>!}$Jނ��#xnIQ��}(E�ܯDX�����eY�>�j� ����<�`U6<�i�t���f-��&������g��-�;���z�矹$�7Vd��55͝�[�������
'�wE��M�ڎc���Qд���j�}]��C�I�vE�����KҮo�Q�pt��mj�U����o���v1챣���׷��t!�h���]u�Po����7�if��V;��.o��o�(���+d{C��+�h5�1��%��6ٻ���T�TWGTߒҪ��C�ҋ��p�<�S_�����Ĺ\��y%��LF��|�a�P�q�wٌ�~�)3-�{�B�	%
^�K������:�ّ�e�06�vAQ�d��^��n,*v�o��r�콽E�Y���]o�{y~-�'	<�q&}u6�̾oLr����,��kZ�S\�9�g�8'�]I�l �.K9|�Aa�f��/����x�Uߋ�@���y8� z?h��kB�C�#	�P����˩kw�Kң�{g��u�B*>�:�|�|3�Q&#����u���A�Q��pm<�Y*4�]*n��E�,�9�����
��B@��*�c�:N˜��LY���ǆ'Q�bƑC&D�f�_\Yʇ�C&|����PFR2�Ȥ�X�I�@�E-�¤�RT���D^Je �X�9$8W�0�c����k�D�����?���p8��n{l2�<��F����u`F�,9�M^ę��c�:��:�7�r_iǵg��s�=cF��☄��pg��e��Z���[�+�������ۧ�>]ys�r4�F](�۰�b�y�R��y[+n����=���-A�`���=p1p��D���m�Ym�?[�Sh��w��&�����5��F��/�J.b���oO�Q=�F���Nh����	��6-m�Y^/�L��N=໩>����:?9v��أ�{���ȓ%���]S����}R��ɽ�cءUoa�[�&ŏ���c>ߢc�����>om���1ך>�Y��.�Ѳ���y����g�63}�����	Jx�NK
1s�S��0��3mADЍ{/�ھb���P�ފ70���ڲ�J�]ߘ��aB[
g
y*;�,꬙d2Cg)H��hC��9�*`���l�̳AM��(u�3	z�{����7\�=}�ӗrM#�R[���Z�L@{9 F:.v��,�k��[���H�x+)JMU014f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U�9�y%E�7:�7��N1Z�\�j��8�����MM�J��2��*ss�=�?b`��]H���E�������	q�cJbZQifI|@iQ��?�t��I^=K58ߋ>����������x:���2\P��Ϙ��-A���M�Qf��� WG_W����}V_�n([���2aGæ��PE�U�ũ%�z�ʯfi��}����R��jF��sW��*+J-,�,J�M�+)�+�(ax6���M�9{wk�+��q�IO�D�Z�y}��/y��)s�ڵm{^�����ģ%��%�_��Yܱ,�1��wn�ڵ�{�� �=��x��A
�0E]�se�N&)t��$�M%.��o������ZJn08<�=F -Q���N˘��!0Z�Ғ���T�՞u�G��p�׺z�[/�o,Y:8I-g�g����_�����[nٯ�[� �|;x��]
1�}�)�]��t�� "�	����.�V�*z{��C $$�y��1��� i�p,�SN���5{cm�
F��y�������8�� �e&�Ɠ�)���؂^�g�������t������g<�6��;ЃC�� k�R���M�*����%���h�n�ԒI�x�[ms�F����SJ�"� -�I��w��"S��d�%���93@10x�Do����t� �D%rj�-��&��LwO�>=�f��|u����x����r|�n0����X.mX%+[�:�M�V�)ffe��v���4�"n���v�TfVKs�H����N�*-��,��M�6N�w�,�v��M�ׅ���Q�^%���^9o'�L�y�+���r�֥-� 5N����<�^�uB�G�M�Y��JP�e�E���-9��G��"Y�jQ4YL���r&/jp�����y^���軋�\`i�hA��Y�̓N f ���c&o�D;�i�ߢd���O*�:�Q,\$�I��N�T�Ͳ��A
պ�4OWMfk얩�halE6�����L~i �ݽ���4O�pQ�e�7�˲��tX�E�T�
�Z%P�f�̰{x��\L���@�yBy�zeʚ9�3��R�3��]٬�A�TT�*շ=rF�	0�g� <�Me��<��D�$z���5��tQU��O�v�A)@wlk+�D0� �V���`�98y^��IE>.VI����b`>K�l�r����2�U�,+�[eS�����y��UQ�0oX�w-�ܵ���+;KB���ak0��o_�/._�/�ѫ���W�����s�6׶̡ȕ�N�5Tg��$�p'�J�jhNN��z�m��$;ˆ�;��p&2����ŷ�99;��ώƽ���Ó�7��������l�|Э$"}�Vv��#-�@�R����a���t��G��%ޭ���E�"���a��������,����sJ�iv�=.�jjБ�r���@kuJ��[P�PR+��>@2�
v�=�i��8����-��*�%�	�do��U�!1;a�tF��6��;�/aQ�J���k�_Y9���"R�0�:�Tt��c���%�=0�������6��X�!sU�L3�LM�D�p��.u�+u�Q�ݝ�9�ݿL�Y�8�
Sl�z�����]�U5ͫGE�2�Nbz�dSLnn�����;��j�aR�E�J�fX�и%t%`�\2`�M�h	A�0�ayQ���"��ҦUV뼶7��k8� +�yX5�Yz#��$,�|,��\Qm�0C�+m8b@@��ž��^�N<��B�b,��f��b��A��K���-��`��.�f�`�ǡ79��������	F��mK;_� J�E�M�����r�w��.D�GD�U��H�(i/τ(?v�Bd�@�4�q�/�I�����ؖ��d;��S�������������kVe)�t��޸�n]�Eh�U�!$��u��qz�2c
�4�Cn��Pn\�ɵ���u��!7����hm��f�"�y��Pƪp����;*��L$xqA������̋�CR��;�X�%ڢ��Vf����%E��wi�����_�NXʇ��'�p�-� %�����I�-獈&�%d+�[- ��������"J�	�ȕ)�N�9��4�XCjN �
���V��i���x�@�̚���p:��y�dD�z�=�_N�/��ӁC�����N�g��^/���8���&�ץ5���&�L}����r&���w����.)�\i���{99�����\$@3��S]���K��.�Fu�R`�b��ׯ�//�s�|r#y��R_ iJ�!�"X�U�ȳ��.���L�"�/�p�`ӢG�eԒ�ܙ�s��v ���F��it`��V��LHQ%�A�ҬN!���r�2
5��䱟h��N�Zs`a����}�]��l��@����A�	\U%���Bu�(в[�?̶{�z�������p߄fww������|��G�>�*��kl�#�2�1y�<��������(q��,�Е-��֣9�^�������̃1���I�}��ą�Po����U\D�R �31r�4C鹬�!j!I*䋄U)���f��s���K��w h q5�� �RY%|��Ȁ�A��� ( ��B5�\XhoⴸU�J�l��Ca���<.�?.�Z�_�ϥfO�#��Pi�,�u�AH�1gOրkHA���x[�ze�J�`�TZ�E�釩" zÁ�� -����������Ɨ�&]6˞��+�$��@A����4�'�i��up��G_��O_�x�g?-���X����BQH�*�W�����2� �n�h�Q�00Yĕ��ȿZ.^�OO=1��2�s(�$�DZ	����}�Z�|K���0��	]�uQ��9�0����܏�jh����[eh����f�`A���k��'�j�ҍ{si��b���Ry�4�VD��wU�1U/Z���e �%�o�kz��Bs��d�K�mCQ+����}^\�{+�D�u����κx��a+�;K�B�&6��u�xs��#Uh !48�8�����~x6~�F#���D����j�ҜN��^qN���? �L��O	3����������._=5��������};>�_�.�2
�B�����Y�sq�b� �J8��vϲt:t?�(�+���BВ-N\�?��"8�kJawg�!�H��A.�I�K	ݘgq�0HRO����x�V�g�ja�[	��@��VL��>��H2�i���t�����]&�	�.� � �KL�e�F8t��I΍�G�ݢ�KP(.����f�}P���ة���-X�?��P�0|:��P��$9^P��cv#�e��l21A�w�.#P�+����a�ٹ�cY�����u|��;E��YT�
j�bq3b�9�T<�)�_D��� �Y�&e�8���c<���m!Q�����
V���:,�#�U>R�#[���d` BP!�%:V�@#R-�|dC��{��\5�ύB���Z� ����s������d:��\�PU�p��O7��6�$��(����-D2
D�, �,r ��'�	'(�m�#	�o;"�*G��-O �ko3>�]e 41X�\���W��h��\H�E�r��@�$����D� b� V�</q�fk��j���ZA�(ᴇ_���冗��~,���1+����cx6*��0���o�!���n�jKx�ML�Y{���~�����X�9����-�I=�	�У������D*Qpm ����Ӷw
"���I�1'��*����몀�b�H[��%�N�= p60���S+��FhE�+Mj�L#'��E��Ff���#��#:�r�W`��U23ȍ�@���4�m:P�
��2�q�kZ�:%*	�^��_,3n%�X���,�"UR���Z?�
L<���0`g��I�/���A���4�ۤݡ��q�( h�O������oNǛI�����9r��@�$H�C��i����F���ƕ��^hF�]}Ѡ6k_T��5g8���(s�%6�Tq�4����`�L��p�\�E&���l��"5N��{�P� ��E\�R�0L�VRW ��r1VB�q�>�P�p�T�b1L{��@�h�j�y���(�N�I4��¯K.��$Z?)a��Y.�=�a7�&��3���ut݉ ,�7�ɣOݝ�������ÿM�}�]�{���{��k��貌ɯ?�,'B����u�[�+���.��u�Qm��� �1���T�S7Ne��@6��ű��5�_�&���j�`���5nI��vZ��"j�]���L��a���}�\�)�=��T�5.C�35)Q� ��%�����5����қᲸBl�5@�����|����ᥤ�c����Ԃ�Hj�J0D��'vqJ��p/0���ң��c^s�	E?Sg���Zm{xzLm8�q���B��E[l�
;�tÄ� 2�8����7��j���统������E]����=~��ţ���S.w�!\m�:;tR�y����DÑzEvYO�yz�7�/�vƎҊ$}�.HR	�E��kF�M�6�7������l�S	Er�a��0_m�̫u5�����g\�.���vƪQ�"D�s�\%���К���`���YD��q�~8џ2"�=��u\;�<�Y�s���7�N2��;�
!�F��O��C��٢���a��?$��!�:>3�<0�9~ȟ<y��<�u�'��R�2G?5�O:}��2M�k�� �x*yU�RI!��i��E�����v�%�K$6Du� \j����v�[)�CQh�S4D��D�\0ugU*�G\���J����4��P) ��[w�	�� !wt�e���ڃqw�@0C䑀~�PZ�O<o����U��z˥�n-�['/ON�X\����D����$!�X�I�Jw���wn����  �¤&�[�t�oͣN�a���N�/]b����4D�ǚ�Wv�Π�>o�9�89}�K�+��F�x�Q�添�����D�>	���k��j�{{��u	<���%�f��6���nA� ��>|��ϋ�?��m�}$� ��I�KZԩ�6��k�"��g̛�#r��4dV8�P�χ I�����'ܖ����vrS#n��E�y�`����i�9�d�z��E�_x;�"H@y�j6�7m���ѧ��3� ��UW7W'C����_�o��u�����u˴�4M��wi�"N�Uz�N��Yh^23����c��	I�\�d:�	}_�|,!&�,
a�������>9��s�G(5�mA����妬��.ίp{A'��.��(�!<�{�����1��i�s�>Hn��&&�ޓ2���:�yp��Y�w��'y�5���aa���;����U RG�T�S���:i�8�C6+��'=�x�5$�4�6go��:��l����7�;�O׸�p�3H~��^��� �'�m��T�;���Ɂ���L?P�����k6<�GD]�m�[��������S#�)��d�+����Z���Y �3�CHB(}{�sQ��&�xW5bRt�5�?Js�ǔVmٮ��.�b��`(�y�P&�DK�O��W�Z�s~�ӏ����kV)׾ׅ������nH4�yU�Q힯������DS�VK�[_V���0߶�6����gJ~���RЩ[�����b@��'��� �*Uu�J9��$E�v��Q��x�++�a�L� 13<TP�~�d�Zb7]{E��>au��~�:	�	��C����LpBU�6!�v��K��%��7�vu����i���� Phd�v0,V�}�8�^���θ+��|�ƌ��Y��\ņ�ш��	��ún?چNP������H�]T��Ү�?p
����
	� �B��E�w�J?D���� N.}�����q-���=~�怾P���eU~�a`I�7���m�ߦH<�=�]�IK���G���|!�U�m���,�9�0�`A�;�3� f�<�νv��gK8G�o�UÁ���#Q2��Z�G����<P2�:(�uyDP�^��!��G����!�����3��y�`�F�!��f[-�˛�V�c��Y&tC&� A�͊��G�m�0�aJ���g��-�=(E���z6 S�S�8����3�؊�Z0A;5��`��יI0��{Lx��O�����3M�]��M��|)x^_��-���PD�G��~��G��p�zs���=�.#,:x�||q��L`����E�9g&H)�T<Y���_rr���V8�z����'7��F��S��h�W���R7-
�l�Cۣ���,�:�2G⣔Uy�z�a��r�NG�e(�ޥH����;���F�Mv�(ߑ�$Fy�A�V���)>r���;S�L%c[�|rN<6k��JGW�����n��X�x�=��}��9Ա���S�\Ƕ�J�w������ɫ3����c9|u)�t��̉�~D�i�=����s���%&�;�,;4�J=�D�Y'N>jG�s B*x+)JMU014f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U�9�y%E�7:�7��N1Z�\�j��8��`�J��2��*ss���[�μ��hyj��i�<��!nrLIL+*�,�(-J��gX�|"�|��9���d�Wh�4G.j�����_�+��`������T���U`V	�*	rut�u��MaX�g��վ�놲�.v4l:�U�Z_�ZRZ�WPɠ�j�v�޷��.���f;?w�Z������̢��Լ�b����gs��t�w������O�����|O;�tҧ��8�X�
uY0��R�GKR�K��<s��cY�cJ��ܔ�k[�:?t L��x+)JMU0�4f01 ��̒��$��3����4��_�j��?�D�k������	XIfz^~Q*�#1���y��V��T��6�}ie�ǔĴ��̒��ҢTO����_�\�r⥽��J�y�˷j�����_�+��`������T���U`V	�*	rut�u��MaX�g��վ�놲�.v4l:�U�Z_�ZRZ�WPɠ�j�v�޷��.���f;?w�Z�2��tV��+w�X[�W,�k��;?� �/I-.)f�����e��)��sS֮m���� |ay[x�Z[o�F�g���CTW������q c�$���l@S�H��3�����9Ëliѷ]��$�̙s�rU��z�䫯��������UQ���NՇfk��t:�Θ�56���M[7ƔN�kҲL��&�j����i����6���q}X�lV��VͶp�uQj<��OwZ��Yc�A�U��<�}�1��1�2k�����'���5;�N��*v����0޼o�(�3�V���f�*W�X���ց<���|A߱+7��4i>���P�2�J�e�m�6�E6�D�8+ʵ5>&DvZ��Զ��&�:"���ћ���k����]Ψ�V�Ž���lQ7t^DĈ����=1Iv"<2.|s۶)��ס[h���K�����'ЮS�e׮@S�]������ ����T�wf*zT�Ʉ��!d�k^���L&�=<��
�L��__�M���]N��L�W|쒤�t;�R�2��L^\������.�^_�~��ӯ���n������ij����>�4�L#6vs.����=�������t2��Z%~������n�ܣC �}��R�lZ֬���H�]�eZ�:�yg8A@�U�.֟t�6�ԋ����%�k=�^q{��~�\�'�N�+ٶ��	I��!����'tf��}�lq��,R�wX�y'NQm3zY���V���_�Euݱn6�v�#�iFL�1�!��B�I|�r�� ��}�f��xp�^W��[��yk�	� a��8���}i�I��z'�ҕ��ǇN��T4���틲$c}�QGPERς@VmQ��l"���X�˥1	���'r�>pC�K/���1�	�wԩ����P�G�9����"c&������?�Љ�"��jז���^7D/����� ����i��t��}@4�0m��61� 7����n8�$+S�"���ޑ����_R��}�jəS�sP0^�Upx�{�,�S�����i)0#q���Pþ$���&I�t�,�V:��!h����5��.-[| �gz� }���Yi�����#w�M]�4�o�9IH�d6W����!u�j���;�X�
ى;�`�6��ݑ�|e���lp�!�Żۜ�#�q�r�.{ ���a���.�9 A�+�>]T"pX̶�0�����=瑎E!��[��`џ�g
ɋCa��׍!�%�½>{�6 xꃩ��7d-..a9t?<�أ����=�^���{+H�{8�}(t�K�VT�@�8�]��_�s����u�L�Z9|�$W��i�.�JV�#�f?9x��2=�Ɛ7cA���<��ށq�xv����i�?r_W���T�XPT���Z0Y��ç���qd�@8=�i���E��1\�P�K����x�� ���6ѓ�Q��8;DFU[}W�֕�3���\շ����'�zk������y�s�B��*�U�����^�:�[u[�g��kל����o��)���O�>�7#�!�w&oK�zÃ�>���YR�>�c��?�U���	>���vɁ׫�Q�/��<JMZL�햑�.:QyQ.ɢZ�b�_>�Z���@�r$��/x�Z]'��<� |O���N�K*48;��󸠰���P�D��������$>�דBK�����1�d�B,b4���f9E�-"���qCz�k��S�2�K�Vy�z)®��?��x]
Y�~�H�����J�$��D�Α��[��v���v��wH��]y`ϸ�V�7�_�q��JZ���;X+�2�N�T���5�@�1�}췔�Q'!T���b�B8�՛R�X���㨖w%?"&9���u��<@�;:�C0fu�~PR�P�l�gt�Z�(����s;��
���k�6�8:��VN��o_�dm^|K��%G�Pa�{��8���,z6� J�G�� /����mG
y�`&�}�1*�5��s)VI���m�"��Ӎ���o���,��H�C<�����k�����������Jj�:o\��<Ű�&<.���翘�`�� ���=�Oz[��(�Q�xZ9Q{������}mUխ���͵��0�\�'��C��idk�G��"4��xJQU�V�-����>�頩��m}������b-jl�y��r9FU'7h��R�2����Qj5���,��b�W�,ǎ���zrg}���]����4���̬�� ��B�
�ƏzuQ��y�B�_tJ�#ƞ���T������]ԓ+�*��PD��Lh��0l`���?�f�����LQe�0�uwG���lA"Q�ys}W!}"�ֺ��V���c���
U2i�H�G?hu��l���i4�i�e�{��W\��ˠ#=�t�=Z����\��W������s��cs��

=��X"��G�oF�hn�_�w8�K��z�A��woF��!|����5�*��^�ĥ���C�#�<� kiy A��w'���d-5�~�$��#I�u��$�o�đ�$��C���R�H3���~�>�(-���b�NS�`��V@>�-�S�Mf��;WSU��9
Oa2An��<hu��$s
<%˰��]O*�@<{謳\U����:4r�~���ъ/�}T���9���W�Tc"�V��n���H�(�ά&�SDek1��t` HBx��s�G{����D:�U ���s�+L���L��i@�d��?����`��]�ML�t��x]�Ň�]�.��n���y`�����L��S��=lA����$<?B}�2�An�52����!a�Q[:g��K�^��P���I$͏}j_�vTע��ڠ�:ԳC�?����^L��0^k��!������yQDB�y��g��h���Fa���� {�&	(DS��u��P���ݭ0h�Ȝa]i��Q-O_|�* �> ��&H�{�7�搒`�����ǩ��)�����Ѝ�Xw�`��.=��g�D�[���p��;.4� M����u����JDd��EWly��7R�t�����q�V�BZĝ���(�#,�ʓ�EC5Y�����@�D���OC���8�p�op��b:`�l��(��#��$�H$!�uC��X�z���F�}��,Z����;�iM����P�\
ٺ��<��s����h'�m����f?"&{����`)��S7��u����PϞ�^����$���:� Il+ �8Pr�1����o8K���ϑ�qd�<����t�����7J��C�h�ǻ�*������A9��#�� �']���Z��s~z��{��Z�Cw5;
k�a�;B�_� F��*���Z�Ah��~S�d#��$Ԁ8|&��r6��*��L��9�P��:�x
RL[�\E��}�z��%,���v¯�(�s��R,�:����\����6��EF��O�N��{xQ�����=���1��=��������3��6��}��,
B���|o#XsxO�^������/�q����z ���<��t��a䶀��Τ/C6�C�Yq>G�B��P|���_�:P�Y%�����BZ0�\l��y�\Di�C�w���@�Ĉ;�0�^l*(�0\t�F�K1����Oe~G�ӁK�{eW!�&�3���oO�:V-T��d�ﶍ�����ڽ��?6������xJ�~�:z�o��:�?L8�%	�K�Q?��~�DR#��̞����	�x+)JMU0�d040031Q(I-.��4r�+�dX�N�����uե��M{���* c3�x+)JMU067c01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U%E�e��z��9��v7./�2��)}�X�5���u�)�iE��%��E�����F)�4w�KRpKٛ9!����>�ή~��T�e�3�ncKP=+cSpT�Y%�$�����U/7�am���W���t2�L�Ѱ�h7TQjU|qjIi�^A%��Y�u{�~l��Զ��Q���Uk�ʊRK3�RsS�J��J*J��}4{��k��ݚ�ʣnz�<�n^�=��I��n�\bY�)�e��WK!-I-.)f�����e��)��sS֮m���� =���x��M
�0@a�9E.�L2����W��,4��T���x�o��+[k����atml"��!�T�8	����![��+�;wY�N(����T����)X�P���F���qۺ^xz�����m��_�VmȦH>��Gp �|���T��]?�?�mUo?�CxmRێ�0�3_a�����HmU�%�nH�\�4o�q���%	��f[��3�ht朇�3�����	?�� #N�N8��B�i�8 ��0��a1D�Lh�ZC[�z@Mf��F��r"���i3]����c������0LH���0e�0������u�Eu���4iJ?�Y[�|��O�}T��tlBH,��Zj���^��/�``���[���gV�����Ȳ&�|�����1X����lW�\�t>q���u�&o/,:���ɫ��hy6���i��[KZ.߯<�%�^�K/�з�qlv�D-C����C2���E�x��.�1�+����06d�W�Wj����Y��_*o��m^l��`ue��)������v���2�G_�r��H�:gx��H�==��e�lY��~���	��jS�[y�.ao
nW[k����xϤL8ՀUM�y�nI���U�����O�i�f��p��x����o�p��ӱ����g٪v��h ?M������K�F{C7�>Gb<g�E���R�W/E��*\n���k}���M\���y���'�E��h)A+N��z��C[W��J�K�T���0��)����A_�fl
P��L
�	@U
�}UCs��B���	x]RK��0�ٿb�Ӯ���=TUo��U��q6͑�	���i���c���JH���5�[��󷯟T�a�d�ѣ����GBb{~�̱���<痯@۪�fく���d�#����8g��A�']��q�F���Ik�4}5u�B5��YOl�+3��4�G����l�/դ����9ۘ
��|ң�|��̠<x4�*o�ǅ���@̈h�Wp1����I�M�����0�A��z0'sc�K���١��3��mM�z�u����>���z���Bq�4
>>�	���\H�ouKO��A�[D.T.�=�ӋI�n�F��P������K7>Ttg��^��Ǝ�	~�wB^U���/��֣�%�e���VoW���j}y1^,}�Aws�<.�T����o�	�7J��=�x	�o<a	�h��U{�6b� ;$��D
4?��'���de	B�-2ΰ��8�%<�5���3�w��J@ �Aq�s)l��7�L�<�����<`�B��J��]F%;Y��!}��9�S�,l�r���X��(74��;T/�>�Eq��u�`#��aq�P]g�J����m	��נN�@IB�U�7,��/V\��F,r%��K�>F��dP��H*�6"!N�@t���]QB�K@���Mߵ@�h�X��|�xo~" ��\�x+)JMU�4g040031Q�u�q��qq��MaHv��uɞ���Z呇��V,�r�Tq@��O|�k`�kp����I���P�������T ��&�xeV]oI�g~E�ŇH�):��q6�%� �.�N'y�`�ٙ�|��ﯺg��{���LTUW����}���ߖ[�h�3�} �ig܆�#c�����Q�M��>m�ȚUPaOAw>���~L���v�?kJ[M�Ӻ!�ơ�mN�:�U�x�l�NN���~�)7�4��#26�ڷ-n������>�ti�q	��dMu�J�qV��j0�p�ѓ�22~6�K^��Q:}���u�����pHt�R5e@}�!�8�h�Rw5��
<��1J��I�'��u��K�Ӝ���0�V�-wf�{�h�ÓI��P�n �V�=�@/J(���E�z��w)�1�;c-����l�'˄�ڀ����
Ф���I��^����%������F�0�����Rג���$��� ��[yr��;P� 0i�?�Y�:�&�4.#ۋ��-e	R=A#3r3�i��84V3|����Zf�����P�n9c��(��/������+��K����6�UD+��}$�2^�j��'�X���\�E��'�n�^?�b���\�n�&pf��R=rC��/Ou!��R��0����CL��@�]�"Rt��۶�!U!�pE�j���T��ǌ#�A����&�G"��&���i0\@�`'���CߓB�n^]�����T�<F�$#�Sq)�#d�W�H��!7wp�.���*:D5������KZ��#ʯ�"A���G�a��x��'rd�cf��F��*i��N#��8+�B#>ts��Zĵ$���f�5��I�a(K*��33��c�H�͛�T��3EH|��e;Ц��L�?�K�܃��U����C��؍��OF[��9���#W���;(�)m��	b=y,�֊]]<��cH��9�$�)2�]��?EC��_���`a���^��GX8�Rpg>9��H"���G��E�],���n�m�o�$}k ��"ۀ� <?N^�'�xf��:�:�(�E�E+,�A�H�l𽑾���h[�
�<c�bb
a���q�k����x���*���2��9�d�7AP�8=3Ϻ!��o���N��(;xfU�|W���#��҅c[���L�<1P������q��Ez�v�2���������i��F��:��߯���aQ͗4��^~���'�Y5�^�>|F���Ų��/ռy��9���-l��]���O��������<����2�]��Ӈ�b�ب0�MYNg�{	Rk�G���"�`'R)(��Ik�R���9�W���դ�vS͖�t9���}n��΀�E�L|�z]h��~�_YX`�ʋ��W���m�s �\Dv����nK�W�����lA���W`��I�jx+)JMU02�d040031Q�K�,�L��/Jex$ƻ�x>��*ӛ�8�f�/�l11 ǔĴ��̒��ҢTO�K�K'?�X��KS���Kb�hB���tv�ve��,��1u[��Y���
�*!P%A��.��z�)k�����W�P����e�MG���R��SKJ�
*�_�Ү���c�ݥ��Ռb��ZUW#�;u���������8מ��D��%��%�_��Yܱ,�1��wn�ڵ�{�� �Jk`x��=�0@a��(��cKq'uU��5�GB\�������� �٪
)ab�S!n%#EրCl\��BY5$$��U����\3�\Ek�>3)i�c^G�&v�yY�.�[F���ڗ����C�C
L1 |�޵����^���
�m�A��t�K(E�x�S]�1�k�W\�
۱���n�B�(�C����$!��_ߛ�:c�>4O3�9'��ܳQf�����;L��V� �K������`@j�R�7�1ʃ�A� L9d�pB�(�P�L�)��H[ɬ�q�[�Q�/m�*3�8g��Y���!�0����AX��h���仳��=׭9K�����&���R��e��"��"��%:��c0�=*c�����a:���>c`��\\��q���˃�$�b�����'���ғ�=&A��Zg�(���jE�||�X�Z�!
��g��g*�
c��ֱ�I���F�;{l�J7Nʏ�Ż��Z+y�_�:<3z�^C��?7�+s"1?�"��P3��u��jeX/��j~��S$�K��������NuG���w!X?��2��������(w���X��t}I�[}��|4��N
Pi}p��j�kl�<�"��6����C2t.P��N��I����e�%e4��_hfRO���}J~M��p�h�h<��c�rQ� 3g,�C�ǜ��*�͆B����ƈ�Зg��8�]S�!���]����)d���u.�;��?dw/x��K
B1@Q�]E7���IZq+��Xx?J������[�uj=��N�R{c�|�B�S%�B�;���#O��rj�BLH�����1��R�I���o}��.���e{_ƺ��/o���:�)2'D{� `�wN�Of�s��}A@x+)JMU066b01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-0U%E�e��z��9�ʤ�T�����-�u3;_�:�GM�u�)�iE��%��E���Uk�y�,������r�]�s��x:���2\P��Ϙ��-A���M�Qf��� WG_W����}V_�n([���2aGæ��PE�U�ũ%�z�ʯfi��}����R��jF��sW��*��i��w:���m�K,�?��,��j)��%��%�_��Yܱ,�1��wn�ڵ�{�� T:�Rx��IϣF�s�W�ݚ�f�L�,�g��o,�b���Y�x&�-�ԩ��[��JO�5M�MS���plS4�r\,�#�4�Y�Ϩ�b�B��	+0��@���-
�T�eq�%Y"�w�p�C6�|3i&ft�����z���+�9��?�_��8n[8��]_�h��(��=�F	E��)1���TU��*Y�O&�ux'ݔ�����	@��9m�$Ɋ$eZ����LW�+��F=�{~��w�T�ۙ%�x9���ad�I�Luh�9��k���A�,/�Ll)��Ԍ,r"&���1pPv��H����C'�ʖy��0�.��̏ʇ:�y�u���h�}b�����G
,��	��@����ge�l��@��p�~=��|��Hl� ����oރ�fU�������Vv+g���W�$��A/�PU�G���x�J)Z^�Z;�̜�ώ���š�FR�c��v0o޻И�l��i��rk#.�A��6�Dz�'��_v�����
�#C7�S��p3�h֊�[�E�Pv�2o������O��O6�үk��5���eK}�[�5�����d�H���U`J��WʾQ���aq3#hz��>�+�ۂ�h�'��<�zF���ۜ��"�޹{U�,�>�i&�C"�GN4�;�\���U?��kΝ��RR�J�����ihlkvGq��e`Â'I��"�Q��E��/���*VО"���(s[9����d���*q��z��ܺw��&m\\���N��TS#<N�О��'ܛ�D]ߒTE���e��6G��� ?j%~�8����2�pa7$c���ݯ����߉��fGx���ΣFF��)zo͸0m�L�������s5�����3QvY���T�O:���iJ
��:d�60bs���x�6���g��T�r	��1��,�GC�R �s���0a��g�(愜O��B��1f�'�u�R�ߢ9���?�_�o�m6���P�>_!�BV@��2��4���E_�e�����#p����Q
B���`@��oY�dE�R�$$���)�b�$��ˑgT��N���mJ����/g�g��5��2r�����n�z��,�g#��hKe?��ǚ�5i�{��e3!�,<.��|#5j�'xI��W��r�[���-*��j�懩[�0���%��W�z�h��ed -�F�`u�	v!V'Z�1�j��K]A�$W����J~���	�h;\b�V?��:]��1gEe=��L[K�����>r�1&�LHk\砢ܝ�/�<);Ԛ��Fx/�/�_�!��F������뛏��,Uk�4�"�^�3+g.|��[_I�ǅ�mRݦ��K�%gE)I�6��N��6Y�D:�k�9U��mx=���k�Q�K�V�q��^EC�G�ކ��BŽ�e��/��-���ػ$0<�X�7��m���_����Ea���.�˃[�Gz��p��]�t�ʥϥ�/�eۻ�յ�
t�Y�<$�b[�U�D{�k��]�,By��� ���%+��1�Y�|-No����<h����>��=k��U)b7�mC�E����s�7ٛ��C���k5��q�z1�U���ivL��{������d6w"��gM��l�����	����r��Wc���f}�- �p�?�:����^�x��Aj�0@�Y��@��ȎC�Ud[fI<x��ܾPz�.�����86�x��
)6a��w�ܱ�T;��RGŬ�rJ�)SO��9��K��Ӫ�$��J�)2�Le�U'�=Ƅ]�[��}ߎ1����T�
>�C&�@Ft�w����Ik Я��6N�S��q�=w��6}���L\x+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b���4���W'\�?�ҩ�&���
 <g!zx+)JMU0�4f01 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���xw��}2[ezS��,���-sSӊJ3K�J�R=����,Y�k���7&�4v��B���tv�ve��,��1u[��Y���
�*!P%A��.��z�)k�����W�P����e�MG���R��SKJ�
*�_�Ү���c�ݥ��Ռb��ZUWӘš�ƮPy�[X�f��ځ�&A_�Z\R��噛�˂S:禬]ۺ���; V3ulx+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b���v���_������ᖏ�� @�#x+)JMU07e040031Q�����,���+�dx6���M�9{wk�+��q�IO�D���ܤ�b��7s�v�n��y��!��;�fk  F�#3x�[ks��g���UA#$;�FU���d%P��r�����f�<�U����s��B���hw��Z�}���s�}�xDSu��e�o�W�hu�׋Tռ�:n�T�;�3?U�p�%i��do_��t�'j����w������:^�I�G���б�ު��S=k�y�����[��n�4R.�t�`B4M]?��k�*�8�M�D�t���g�M���]HT��˖:Lݔ+��@'��.�z:�3��e��v��C��*��>��Rkj�QJ�� �q���_�vN�
��@��̟�o-ʭ�i�'����>�R�L���C΂.�Q�pk�����(�a�T	Y/��6>�4����83�`:Y�g�����GA����3�Z''r|<u��g-*$�Q����,d'��d���jk9,��	̵���4I���*�e�mm�fo{j<<��o�z�?V���~��UO�c|�P����ë�Q{0���g�=��~������7����_\��{��?�_u��7�5f�u޿�O v2T,i��{�y�.z��[�n���'u֟(�l8Rmu�M�����H]^�.���Ѕ�Ap6�:���`�ĺ�M����m��s1Hk_A�w�:�������vx�����=����g�j��v�������p���C9��Q���\��?�I8�2��`2��tM�����^C�G�1�r6^PMs��`�g���b��l0������~T��>�4� ��8��{��i��p�:���T�pS��sy@4�wyw���u���e��{{�@�����_;�s2H��'�^柞㓛�`L�i��a0��v��5hġ{���4��u�P�4μ4���2��4��#/��.0��'��p��(�9xH�0��nt� |���uu�X��IzBrp��>���g녟�d��A�s�LzU��T���ZG-��=�E�qU�C57x���d�X�nu�RF@��;�M]�2,�.����tl%�'�˪J��Ւ-�s*�]:�t2�ϝ���`���	<���/v̷��}��9���iw�#N����[��f0��A�'�0�}����u�v�N7v�ڴ�C��:�����~js~���t��b8s��	����`��m���
����^a��
�W��r��}�ت�.�T'�.˿j��bC�π�?��Xq� ���[�2 6�b(?������C���n���WZn<i�'x.����!��;�B�J!o4����]��{��o7��[b�F����A�+��t���a���{�"MI� ����~�u�s��"䓕�#����:4G2q04&�AhW�49@��W�p�wQ�Ʋ!��TK�R�!�D��\�¹�A`e����C�=b�
�z+P�%�8�"!`����3l={�K�H���\��I��=[j�,���?��er]+��~"0��=�v���4�3�u0K��c���!s����z��l���}�y�=��5^�u��i��G<[ǎD��Y�I}�Dw4�}�ʰ���g�U�P=�����/ve���s���C7��R��h�Dhq�uR�U����� �IX��1��!>
��g�g��q��UHZ/��*��)S�d�=X�I����T��j�U��Hd䢰y} :Ar�l�a�[�qW���E|����Y�䔎TM##M����'��
�pF�]�E�z�t�Y�$'yHVp�L�
L���6. �&ӱ����l�H���a��v�ʍct����4l��#(� � F@�pE8���_�'��E�H�?ʤ�yL:�Y�:h(�.�q�� ��<�\�G�S��L�f���'�g��Wg���`c�r�ѧ�ð����݃`�ʠ�fоDk��tH��U�Rc5��k��b`�T�%���xr���W8�oϕ�����2���Z4e�W�*��pY0C�X�d�@ءc�*+8m��{(��"Z��|$4�:��χ@�g�!=�\�XT�8(�Sǩ��7�rr:@��['+r��P�U�� h�d���C��L�GX��d��3�Ĵ*9����F�( v��o�8Rb@Zq��:Rk!Fw�I!+����П�$��q���$�w�V�P0eAQ�4ZV�d$��{Y#ci��c{
܆�E9)�X�l��J��s��%jV��d|�{
[�4,���@��e1���SV���'�ҍk�?Y��D�E*��u�{=�����opY���(|_�})lJ"����h}(�E�8l��:nR!���Mi��J�V;���DS����X����BI�꺡�
��Ox�6>! ��t����CF�<��	�/��[c�Ǒ�6̳a{�<�g�z��4��F���nN�{�q	^(M�ss�C�p���%>�y�����s�9�BFY0�~zP\��<�r�[o��9�rőǀk���4,R� j�S�"Kp��Sl�UP�9:��&�h[������ 2}�i�JN��u�\Is��ׇ�f��&~rwJ�
�
z�W��Mp��M�g� �a�����i��-����)2���'�<s�t#��p����A�%���C�]��fk�ip �8Bϰ�7���%!� ���Ln9�9,k�CtBT�/H�� �3��� *�`P�\*D��$>D=��1/��TI
�~M<���9�,Dڇ"� \�>����@e���׎cZ.\ȁ���η��Ц!�Ei+���Kj�����2}f��*kcن�IP���h�$�è��8&8�.@����ɽ*�2�aO��͎�FB���#q�i'm������Xm������3�qvKz  ��c��p���RJ_R�m5�^#��`?}rP`�H�4��a�0�g�F�� �l�T�Ѱ���	�Q�n� ��"Ճi�5L���"��$T1���|'���tƀg��O�r=>v��S�ț-,�$�]�q~呮5I�]aI|M(�tA�ok��R^�i�i�(_�ȍ�?�pZ*?���[����Q�`o�VC-�6��AN����z���c+�_.X�DƸ@stK U��9n_	�� }BF����OU=/��FMҲ��z��W)W)��l�~_k��ʕ6d6�/3��Y�c�V�c���]�]���"�\������iXj�ό�*1-P"�E�BI�z*2�'�B�@��H�=�D�"�MS�R/��j|Fα�8^u���N���ڭ�V��_�Yŷ��_ќ��Yoۄ���צA��<���6s^櫜�F�!�U���C|m�q�Q���4qDR���˼cN��RF���v�X}z[8.�ؔF�.�Dc8I
H;F&$���4�����W!4L�����2�(����K{��>k�Q{�E��U,�"=�u�5�f���z��S��]kT�����߄�4���@h�桨��T�}ŷ�R��Qk3B��+�í��ToJ�Į��	<�/�LR�T��lN�*ld`8~T�r�v��wY���%�
��\��E��z
m -J<tL\Fp��U���=Y��VaƇ����{a��{��9�2$�!��lڼS`���L,=�,�e�S��w3v���_�{JF�MJd�F�I�ۗ�D�柔)Ӛ٢��n*���z&��L��N�βϲ�0D.��B����`c{�k_T� �Lyf�i��]�@�LӋC�W?���-Sj�R�܋�g�NF�6���eE"�jfbh�X��JXyR���o��H3��H�vֱ �<��^�V�;�x�%oLa.�d�0qI����f҄r��� y�!W~ւ����?rl�p�l7x]�� �Q��۝ɁN�Dݎ�|�˸Sj-m���Jn�3 ƪq|�1PZp�Wb����Xi���}M��[�r�դ�wb����o(1�3�
�8�Ha���!�𣛌/ڠ5Ƿ��3[̳p� 9�0 9��M�?�>���R���p����z%�i�5+ ��G��{_���s'��5�T��|ۿv���ɽ����`��ڒ�.��8��6����݇�}P�A^����(���M��yS;8}��4%�L-��J�}t�}���^�+>�%��{��ux�u�	��N.�2��
q���[q%.�W������+�+7W���%�d����꼼��3yC.�捥̻��<�Ҩ�Ҥ�df^F��EZ"�:K�G��F�^¬X�/�j?�%+��Qj��C=R���ag�.�f�Ky���I�V�� o{U�a�� /��.��VM��U�w�� U��Q"�C�X����^�F{G�w;����\�	�g�º-M%!��E>m  ���+y����7A��]�ŪW�(t\skn�<(�Lr�����ol�e\c���"� ﯾA���\�#R��V{�9�`��LQ�&�)8�ti�!3%�Ҡ~����~�R�V.���.ܠ��#��]E.hE'�mI����Oͼ�X�AV����/�7�pq����;��d����(�|��_<�M��o/���WT�xˋ_�-���`���۶��=�
��J���j�x��Z�_��
��|���^�4[!�����'��*k�\B�6�M�d��W�?���	��j��b�{C� ҄NxK��OR0`  	��#!/bin/sh
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
�
$��[c           @   s�  d  Z  d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l	 Z	 d d l
 Z
 d d l m Z y d d l m Z Wn e k
 r� d Z n Xd Z d Z d �  Z d d � Z d	 �  Z d
 �  Z e
 j d �  � Z d �  Z e e e j d d � Z d �  Z d �  Z d �  Z e e _ d �  Z  d �  Z! e! e  _ d �  Z" d �  Z# e# e" _ d �  Z$ d �  e$ _ d �  Z% e e e j d e% d � Z& d �  Z' d �  Z( d �  Z) e* d k r�e j+ e) �  � n  d S(   s�  Bootstrap setuptools installation

To use setuptools in your package's setup.py, include this
file in the same directory and add this to the top of your setup.py::

    from ez_setup import use_setuptools
    use_setuptools()

To require a specific version of setuptools, set a download
mirror, or use an alternate download directory, simply supply
the appropriate options to ``use_setuptools()``.

This file can also be run as a script to install or upgrade setuptools.
i����N(   t   log(   t	   USER_SITEs   3.5.1s5   https://pypi.python.org/packages/source/s/setuptools/c          G   s#   t  j f |  }  t j |  � d k S(   s/   
    Return True if the command succeeded.
    i    (   t   syst
   executablet
   subprocesst   call(   t   args(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _python_cmd%   s    c         C   sT   t  |  � �B t j d � t d d | � sJ t j d � t j d � d SWd  QXd  S(   Ns   Installing Setuptoolss   setup.pyt   installs-   Something went wrong during the installation.s   See the error message above.i   (   t   archive_contextR    t   warnR   (   t   archive_filenamet   install_args(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _install-   s    c      
   C   sk   t  | � �+ t j d | � t d d d d | � Wd  QXt j |  � t j j |  � sg t d � � n  d  S(   Ns   Building a Setuptools egg in %ss   setup.pys   -qt	   bdist_eggs
   --dist-dirs   Could not build the egg.(   R	   R    R
   R   t   ost   patht   existst   IOError(   t   eggR   t   to_dir(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt
   _build_egg8   s    c          C   s6   d t  j f d �  �  Y}  t t  j d � r2 t  j S|  S(   sL   
    Supplement ZipFile class to support context manager for Python 2.6
    t   ContextualZipFilec           B   s   e  Z d  �  Z d �  Z RS(   c         S   s   |  S(   N(    (   t   self(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt	   __enter__H   s    c         S   s   |  j  d  S(   N(   t   close(   R   t   typet   valuet	   traceback(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   __exit__J   s    (   t   __name__t
   __module__R   R   (    (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyR   G   s   	R   (   t   zipfilet   ZipFilet   hasattr(   R   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   get_zip_classC   s    c         c   s�   t  j �  } t j d | � t j �  } zw t j | � t �  |  � � } | j �  Wd  QXt j	 j
 | t j | � d � } t j | � t j d | � d  VWd  t j | � t j | � Xd  S(   Ns   Extracting in %si    s   Now working in %s(   t   tempfilet   mkdtempR    R
   R   t   getcwdt   chdirR#   t
   extractallR   t   joint   listdirt   shutilt   rmtree(   t   filenamet   tmpdirt   old_wdt   archivet   subdir(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyR	   P   s    "	c         C   s�   t  j j | d |  t j d t j d f � } t  j j | � sj t |  | | | � } t | | | � n  t j j d | � d t j	 k r� t j	 d =n  d d  l
 } | | _ d  S(   Ns   setuptools-%s-py%d.%d.eggi    i   t   pkg_resourcesi����(   R   R   R)   R   t   version_infoR   t   download_setuptoolsR   t   insertt   modulest
   setuptoolst   bootstrap_install_from(   t   versiont   download_baseR   t   download_delayR   R0   R7   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _do_downloadf   s    !	i   c   	      C   s!  t  j j | � } d	 } t t j � j | � } y d d  l } Wn! t k
 rc t	 |  | | | � SXy | j
 d |  � d  SWn� | j k
 r� t	 |  | | | � S| j k
 r} | r� t j d � j d | d |  � } t j j | � t j d � n  ~ t j d =t	 |  | | | � SXd  S(
   NR2   R7   i����s   setuptools>=sO  
                The required version of setuptools (>={version}) is not available,
                and can't be installed while this script is running. Please
                install a more recent version first, using
                'easy_install -U setuptools'.

                (Currently using {VC_err.args[0]!r})
                t   VC_errR9   i   (   R2   R7   (   R   R   t   abspatht   setR   R6   t   intersectionR2   t   ImportErrorR<   t   requiret   DistributionNotFoundt   VersionConflictt   textwrapt   dedentt   formatt   stderrt   writet   exit(	   R9   R:   R   R;   t   rep_modulest   importedR2   R=   t   msg(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   use_setuptoolsx   s(    c         C   sT   y t  j |  � Wn< t  j k
 rO t j | t j � rI t j | � n  �  n Xd S(   sm   
    Run the command to download target. If the command fails, clean up before
    re-raising the error.
    N(   R   t
   check_callt   CalledProcessErrorR   t   accesst   F_OKt   unlink(   t   cmdt   target(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _clean_check�   s    c         C   s9   t  j j | � } d d d t �  g } t | | � d S(   s�   
    Download the file at url to target using Powershell (which will validate
    trust). Raise an exception if the command cannot complete.
    t
   powershells   -CommandsC   (new-object System.Net.WebClient).DownloadFile(%(url)r, %(target)r)N(   R   R   R>   t   varsRV   (   t   urlRU   RT   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   download_file_powershell�   s
    c          C   s�   t  j �  d k r t Sd d d g }  t t j j d � } z6 y t j |  d | d | �Wn t	 k
 rn t SXWd  | j
 �  Xt S(   Nt   WindowsRW   s   -Commands	   echo testt   wbt   stdoutRH   (   t   platformt   systemt   Falset   openR   R   t   devnullR   RO   t	   ExceptionR   t   True(   RT   Rb   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   has_powershell�   s    	c         C   s&   d |  d d | g } t  | | � d  S(   Nt   curls   --silents   --output(   RV   (   RY   RU   RT   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   download_file_curl�   s    c          C   si   d d g }  t  t j j d � } z6 y t j |  d | d | �Wn t k
 rU t SXWd  | j �  Xt	 S(   NRf   s	   --versionR\   R]   RH   (
   Ra   R   R   Rb   R   RO   Rc   R`   R   Rd   (   RT   Rb   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   has_curl�   s    	c         C   s&   d |  d d | g } t  | | � d  S(   Nt   wgets   --quiets   --output-document(   RV   (   RY   RU   RT   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   download_file_wget�   s    c          C   si   d d g }  t  t j j d � } z6 y t j |  d | d | �Wn t k
 rU t SXWd  | j �  Xt	 S(   NRi   s	   --versionR\   R]   RH   (
   Ra   R   R   Rb   R   RO   Rc   R`   R   Rd   (   RT   Rb   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   has_wget�   s    	c         C   s�   y d d l  m } Wn! t k
 r7 d d l m } n Xd } } z8 | |  � } | j �  } t | d � } | j | � Wd | r� | j �  n  | r� | j �  n  Xd S(   sa   
    Use Python to download the file, even though it cannot authenticate the
    connection.
    i����(   t   urlopenR\   N(	   t   urllib.requestRl   RA   t   urllib2t   Nonet   readRa   RI   R   (   RY   RU   Rl   t   srct   dstt   data(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   download_file_insecure�   s    
c           C   s   t  S(   N(   Rd   (    (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   <lambda>�   s    c          C   s7   t  t t t g }  x |  D] } | j �  r | Sq Wd  S(   N(   RZ   Rg   Rj   Rt   t   viable(   t   downloaderst   dl(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   get_best_downloader�   s    	c   	      C   s�   t  j j | � } d |  } | | } t  j j | | � } t  j j | � sv t j d | � | �  } | | | � n  t  j j | � S(   s  
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
    s   --user(   t   user_install(   t   options(    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _build_install_args"  s    c          C   s�   t  j �  }  |  j d d d d d d t d d �|  j d	 d d
 d d d t d d �|  j d d d d d d d �  d t d d �|  j d d d d t �|  j �  \ } } | S(   s,   
    Parse the command line for options
    s   --usert   destR�   t   actiont
   store_truet   defaultt   helps;   install in user site package (requires Python 2.6 or later)s   --download-baseR:   t   metavart   URLs=   alternative URL from where to download the setuptools packages
   --insecureR|   t   store_constt   constc           S   s   t  S(   N(   Rt   (    (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyRu   6  s    s'   Use internal, non-validating downloaders	   --versions!   Specify which version to download(   t   optparset   OptionParsert
   add_optionR`   t   DEFAULT_URLRy   t   DEFAULT_VERSIONt
   parse_args(   t   parserR�   R   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   _parse_args(  s"    c          C   s@   t  �  }  t d |  j d |  j d |  j � } t | t |  � � S(   s-   Install or upgrade setuptools and EasyInstallR9   R:   R|   (   R�   R4   R9   R:   R|   R   R�   (   R�   R0   (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   mainA  s    			t   __main__(    (,   t   __doc__R   R+   R   R$   R    R�   R   R^   RE   t
   contextlibt	   distutilsR    t   siteR   RA   Ro   R�   R�   R   R   R   R#   t   contextmanagerR	   R<   t   curdirRN   RV   RZ   Re   Rv   Rg   Rh   Rj   Rk   Rt   Ry   R4   R�   R�   R�   R   RJ   (    (    (    s6   /home/pi/src/python/Adafruit_Python_PureIO/ez_setup.pyt   <module>   sZ   
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
PK    2�yM�i_  �     EGG-INFO/PKG-INFO��ˎ�0E��
��cL;� ^5Mԓp��8������R�ӎ]tG��WW/$hP��F1�w5<��=Z�am�G�rs��l��{F�v��TC�oQ&�SvBT�Spt�Z��R��-����Y.�۪��yquw�z�����l�*֣�c'�&���8�J��Cb����]���\ҥ/�S���Er{��������8�����og3`J|f�u[����%'�
ʘ���J��9.�C��®�vJB6��C�������k����P!X���L>���x!�9!g�Y���u7��P?j���#Z��4��Q��9�嚫���T|\�'���֟�'Fz�?�?�<c4YS�PK    3�yM��2         EGG-INFO/zip-safe� PK    2�yM���         EGG-INFO/top_level.txtsLIL+*�,�w�H,�qv� PK    2�yM[5��q        EGG-INFO/SOURCES.txt+N-)-�+��rLIL+*�,�w�H,�qv�G��(>>3ȍ�&����������������GI�h��k�^IE	U)��y)�yɕ�9�y�����f�RV�_��Z��R PK    2�yM<u�L   X      EGG-INFO/dependency_links.txt�())(���O�,�(M�K���OLIL+*�,�w�2�*K2����<��K��sr�s�KR��S��ma�tA
t�L�� PK    2�yM��6         EGG-INFO/requires.txtsLIL+*�,�u����5�3�3� PK    3�yM&Tq݊   �      Adafruit_CharLCD/__init__.pycc��������d(`b .�)@�Ȑ��������d �Dh�A�@�1%1��4�$�9#����Ed�(�I��9)�I)��%z9�y���E�ef9���������g���z�%@�6��)�9�v +�Af PK    ��yM` ��"          Adafruit_CharLCD/__init__.pyK+��U�sLIL+*�,�w�H,�qvQ��-�/*Q�� PK    ��yMt�|?  QQ  $   Adafruit_CharLCD/Adafruit_CharLCD.py�<ks;���+t���C&��uS�S�����||S�[� �̞afv!�㽿�v�4I3��|��J��V����n5�u��>��6)�-���:b����3/e�`�%i����-�d�&�?�Yܳ��}��-�_�x�%��K؆�|q��b7H����1�,\��ƍ�x��!sa|������/�c.[!���@���t������$��s#[��l˃�MqƵ����go�rě:M�����!4����Rs\��4����VHG���'����!� �XR�`�p����l�{ɦ�V"_d)4&ظ����|c�pI�Z��B��D��T�*���&ܚ��u0-�Q�XG���/Sl�����.p+ו|"�� �.¯��$4!S�XЁ��
KP�q}�-��L���U�HC��x�Ϣ0�I��:���>��/f��I���z2�m���؛���i����r|3c�c�;��댾�_�^����zҟN�x�W��AZ���7}f�0r4����j0��1M)��SDw՟t/�k�|0̾4 ��`6B��	���d6��;v}3�O�@B���	�ӿ�f�m��|a���p�����5L�J�_�>_���x��C�y���b2XZw�\5X�s��ܧQc��+Ď�Fv{��F������x���G�	|m�Z'35�v0�7Xg2�"[.&�+\&2ƌ	��d�)��o�}�����!`A�,Q:��Ro��/�y���ak3|�:��.v��j�U���c��7���;]�^!���n�݂f'�no��;��`z=�|a��f�o��'���dt9��3f�	�|������ X�%Q���L�}3��:\.f�V��7#���������Ѝ^o��� e�Yy�����}�.)"��\g� ��e6�:`�Mh�L,���n
q -��#��g�fpu|qQI��1X�U�����s��_���R��-�
�hiW���fg]�T��Dt. ؒ�F�E��'M�Qtv>���ڃ���K�a��\OkX�>�Yz�ٴ>��3��g�^�J�P�"<ӎX�Gl���d?Ն�pl�6�m���:�8#��������NZ��6��'��cxk�4`�R��G�;���:���t��l��S�?:�p���y���m�Sv>�1��{����[ܛ�Vv�T�<��Y[�Ao|;� ����
�0`��
ؑA��]���
a�w��^�]�H�3Xth�4�I�� Ʉ�h�cv��NL��};=8X������B� ���7o��6O�#�~��&�G=v�UD�Z�e�����I.;�s�@piA�� : �+�f�9x��|^�v�`q�`��l��1�?����,� ��J�G7�=
�8���|�q:� ƈ���=��==y�.|>�v����'{z�E^�&g��Z�[0%�96���C#�� h����X^�iJ�KD�_�\`���d
��H8��#�q@�0~ˁ�A4����!�$
#x�X��!�[�!(���@�rS���3��av�a�9t��u&�<��C��:¼4aG��@� M�pv"��0A"����?��3��̼X�	ش�	3�����z�pMlP
C?�B� �PŌ24�p�f��wG|��9λ�^PjSo�*���K�&%.G���^�C���.8$f^[�<\�;�Ƿ,������)��yB؊n槥���~�1"���<�;U���b^��(�%��X�O����
df�6.zB �Xq^JKa[P�	rLp5��u�В
�xE�n�E��'bj_�_=DMbP��u(�҇�Yź�����;�� oc�f��E��l��x@�ITn/x8*|���R4��[�{K�SJ�4�,t�� H��u����e�G4��W�"�R�K�l"T4��YA�V�7�ua	[B�>�3����U'��ڸ>��|��\���N�3�|����@9<��� ͍	WA ��R�Ei	Va𮐂6/�����SS�:���OP�*+I�Pd��n���l�Rj�)#Yabv1OOg��$��fA��k�g�&R��?*�roL4x�|� 1b��iy �<�ZWGк:�[����n=����[O��Vɞ�.�Z}`���N_���/wp�}��H�l�N,O!�TǘZ�4�R�ߨ9(�W�v�4� _('A�5� �:�Y�4�Zz1l� ��[�S@��!&_�� �㴦��WWYz?_�/}^+��z�������k+�&(���/[�H
VT6S8;q@�s�r�r��Ԅ���A��c}�pV�1?�l-�qኑ��;/I�[T����63�!�La��yR�U>�ĥB|1T�����YF�i[�z(����G�Ⱥ�K���ț=T�Z,v�졒��	��Ҳ�<OQs8�а�D[čk�"Hڄ[N�P�-�8{�*��:�8���^����@�_�QRw�S�^F��T�I�0�ĥF���c�XqX�|�-�0�xS��>6�M�B7K�<e)�h`��¹����*�+P^pە���zV��Vӆ{��^@>~`�%>�QC���]����f�3eл�=��ǥ+�/��hUbqL�"�mDd��QJߥ�W�^`���8���mïx�Z�)�^����-j��X��~bV6�0����N�珤Z�O4���` $A�G}����C�ͧya�Pz&���emW�t�U�K��_��י�B�6���8l1�5ݠN@��qE�u���P?�2	� ���fͪ<��JN��'��οK�g�G�,0@1��VV;���JE_�:Ut��E��f��]x%����ɮ-X����龳)7�؇�J+U��ڭփ���C��657>E������Pr�n�y\�<�҅�B�	��"�&��9Vr�K��>ԃ�D��+1�����=�� Z���!��+㏤���0������-L�;�]$`�	���%���'���e�������)�:�;B/��Hr*@���zO'z�.�ټ$}�(�}��K`˓Ľ���n���u'�b��:�G!6o\�Q��!,�;r/u"_�����������4w��������ҵ0�ɯ�����i�/@Zh*o��bx��Yr��k�ٻ����+a���yJ��������nJ�(63�ƦsJ���5�����_�E�E��}�6j+������<)_�4�]��,�����u��Uq���,�����V��g��E�R|���I�<�S�i<���ja�C-W"���S���T�=�@I�0�Lޮ�)�mY�3�J�"�RM��_4��fCd`�tG���*^�	]%��?�g%����f{d:���M�Y����,GT�)��ϞYT�穼��:��B�H��9n/quXe����Kޣ��@��K5���z�ud��.�����"��Ͻq�^~������V7�����c�_[P^OF�*S�a̿�U02���0d��<`���
�[^[�cA�A��*m�Ӥ�!:J!�,� ���kKdsL���P��O�V���vT;ڪ��íP�ձ���5(N'�Aqj�8-P�[٬y����]+3�w�d��^������g���3��Y�b��Uړ<_��)(~`��<`0`�Y��;cT��'��/�3�6�u5��֮�
����� ���T�	�d/�K��t�L�v��)O(s-˲�:R`pX߁09�V�nr�	��cqak/���I��Ӈ������ q����fE�&���٤��t��"SQ���8��/WN�۷f�]}�����l:�)�,�X͵ڂ����SS'�XQ��jj��?�ZD�������xV�p�%Z��z��&�}���B�&m���<K��Υ�^X_��,]� ��w< Gof���Y���w��[h#8��br��?�:������p�������^�6�gDd��h��Њg߲k�
�U+{;^Q3ܖ����.A�e.��	/�c��s��jY���>'��"j^`�t��k�jJ���
�H��'��;�{�%Bi�s]Ԧ�(�Zy��ܻ!]�j����`Ǆ[MN4��bd�Q��b������V-z�*�T�5�m��MF
�rC-�۞�}y����BJE~���y��]���+��a��0��|w-`�Q�]̱�¯��{�t��<�v���/*�o�a}aܮQ,���?U($a2����b�j_W��+|qq�¸�J�ՁE�J�\hVP�:��Q�t��.#3+��Zn�p�Ԃ�\�J��H��^��"�p�0)���BA�Q����
��P�Tx�;e�u��U���\�]1����ҋ�,
���#D%�
�*$��qR�?9����R?�OC;������O���q�el^W�*"��Eq��.�,�-Љ^^q��&��԰r�X�{ɑ�2��kG�H��u��9T���J/:�^1N\��8��א���_�i}J:��ϫx�L���WS_�\阢��JF|�`d��d�ͼ�^;G��p���ƽe=��[�M���Y&f�<^-��?��R�[�w�����#[a�H��<:� �>�<���� �
I):�3�Z��X]�����>�O�^�mO��������2W�z����$	���|����
�	�ՠO��E��׊:z��g��q�IG�eZZ�!|�~�5�U-�#�k)�\������Ԕ;"@�'�Ze�'��ŕ}e�Q} �(INI�U2[yK���z[��lII6�Q��O�鑛��V��VR�N�l4B�/B�*�C����mU����|�Q.	���o���gU�̒���WaL���D���Vxr�.LJP�񒺚׼05�u�Rn-�y�(u�G��d{/����2@��<1H{�i�k%�W���Wl����A������sNU�<1-\1G�(�\)�Yt�s
���e��mս�_�{��#��w䌍�<k�J{7ZD���i}yewA����=��*� k��TW}����5���*zy:O=�g�&т��=�����S��~4��V0Q�ƧN�ʒ ۶�]J�I�C3f�0�j�Ndn�}�h���4
B��o��\�`;-�z0� UH�� ��7-JUgF�����<�a�R2Z�C89e�*(x~�I����_�N�g���E��:ҿ���v�)���c-��|W"o��<� ?��?��t2#��ǜ\Ŝ҉ן|P����Aŀ��֦I<=�~E��#*��l��Y��Y&9����h0*�l0|�@��\7՗VܵiKh$m�Q�I�����yc��\#�����^i��r��/e;�'Q4��t	��-����N�oV*~�	>G�zV�ހ�h�s�f�@��O��92��3�xlZ��p���#�+B�$y=U8���m��
��Z��*d�P�b�(����,����� +�s������F�λR<V���ru,K���w��ˇ\��+��p`i?���@�QY�f�����#�	��GD��gI��gɏ�x��V=�,��h�a)[*�9,V�� jO\���q;Yz�J������PK    3�yMp#�"�  I  %   Adafruit_CharLCD/Adafruit_CharLCD.pyc�\Kl�y��9|J�DQ+i��]�(�;z�D�k{W�C���P���{1N��M�g�{D�!���y��8�CH��@��` HnA� >H����K '� |�%�����{Z�br�5����꿪����r������/Ԅ�����F�`�П!B�u�e3���v^���e��.�rr9 ���\�)ʃ�ɉ�p���p�DyD8�yT8��<&�Q>&�\8��|����'��?;���|w��g��s\?ː�q�<���x,����\������	�嗅3"ʗ�3*�S����9&��qQ��pN��p�E���pN���y��\��\��*�	Q������n������9-ʯ1�O1�OgR��uC8g��B<�����yN��s�Y���p�	�n=�[������z��6u�6��o�����(��� �c(,��=��$�uc(FQ��F1�bEEE?��>*b@��T�aˋ+s[�pin^��΂�K�Kg��@j���n�pb�+q���0�N�/(�uJ
C���3T��PajC�	�9T�솸B�7̕� TN�&P� Y�r�"�x�`Z<΍g@"�<*A�,��s�^����Q1רF�V�6C7r�ت�����Vk����[�b�5�ƭ�W�!����"�Y�5��Ҧ���Qæ ����c�݃~q D�*\1��0WLq`p%'L���A�+}� ϕ�8��
)p���B�W��W�rP�6,�^e�&C�3�����;g����M��xTl��'�0���xH�iE8n�� �}\�}B��'��N=$�b�ƹ���<4,|� U���|u�C�ua�E|J�b6>-f��I��s�p���d�y?/���R��\��)��n;���"�Yi�K c���6�}�ʢ��^��}ɵ�-�]�,{m�ZX�f��Q*��oYM"��("�����p��H��AK�����8�5���A���Ս�+;ոj5<ߵnP�0hmnY� ^�G%u]��ۊ\Ю�őu�/�vǵ"2r��Y�PN1��T��<C�ݖ�i����Z�N+��� xM	������N�l�v���刁�5�o.֭}���xkx�\�KK�à�lTk���V<�6$��`�3���7��*I�y�c7�+͠Q�x����[�������HV�*a-�>�"oӯ6� ��Z|�-u��� �^m5⮁W-@��Q�WrK�T�ip�m��nՈoI²�?\��t�����cת�.��j�4���>FXM���S�M�ZDP��!�]�W�j6��萇���ǞC;�>P��
|�������ר��{D�����Pm�f�Uc9���V�����M�w<3�1��;��F+�����L!ܽfëљһΏ�$S�l��'y�ŘR�i�+<���h�t�a���9��J*���2�����5IIW�-����r��t�&�M�A,"9zY,�yq���I!�Cu�I�ᩣ]�ㄙ���s���zuoO>��Ŵ|'p�R��q�?qԸ���xdɁoah4�-���&�ʻ�����n�W�]�be�cP��#U��E1Dx���l�lzA=�F��un�ߛ�wF�ފ����CI]W$�;q^5��6�x4"�V��bun��:7���>q5���ӊ�+��Z�e`A+n�b���qo�P�W���/�}{uE��=��V��{�x�h�]Z\�,�`*5Gq���������B\T����:_���{��W��x�
^��@��XXY��^Z��N�?Ӳ������9{a���� ��h_��*=�����ރ����Օ��u�}5XL�@%!�N�6�8r�9�4~h��C��?7�ό��ŏ0� �� !�vV���=SF����04�g:����SP7���b���p�lV����{��<�i\q77�t*�]��~��R�x�����E�h�7���A�q�6
�9s�x�1F���)*O��`��k&z��B*}��T�3�t��)�-z�����<j�0�s�僇@��
vH�=��$Ah�K�}\.y1��p�)l��v{a�������B<���%��x�0�\�n'���>Kc�1�?H\��G��(/D�Z��ZvB�sKwmu:��X֑���v�
1|��~+4�"�ExA�i����Pց!b6�b��Μ�m_��t"Ŧ�P��@�`�j�vSb�{�U}������y���]*5�WV��=9<#�#¿4�3'�A)*ry�+�s�3��5S�M.A� ��$��j���˴�-�IRU�S��ȅ_��P� u<B+���,s��kYkZQ�JZ�h�%��3(&�/ ?�F_As�g��є���%�0Q��1�(�湶E4G�ۂ��)anNR���M	�D��"O�Z%�Wz"�E�����(�;��8�wf����X�u-h1�H�SDȗ�4�v��3QG�~���T��3�X��u!1��g�2���,�;����j�ui�h6����-�c��X��mJ2,�~nA�.���<���C+�`���&#�#���D[5OŇ�&�����̊m�ڏrɃɒyv��Ak�$ל=A|\�O�i�ɦ",��W$��M��� }�/��T	X���T*q �/B�c=N�T��?�x��%0����y*@ �������Rq�)�d�/���v+����%��z�d�)H%�'{���P�p�#[ދ,�� ����༇Y���̺�V����'����}����32" �l�{�uSRM�"���;��anuRG�"܀���ĭC3eTw�h��x�T�D�&ٱ�-��t���~;�CpiI;R7:y�L6��:?�1/���:��V4oU����k�i���Vi�CHH}P)����O�Zl��Pz)@<�T��@\tir���)�Dw�(�n����!	j��:h�l���)��-DjZ �QW���v`;�:����&�ٕ�]���s} 	g�pFz�>f<Mu�F��v�CI�$j�cM)���錃��W��A�q(]�|�b�!�{a�T-~*�������z�T�4�3�@E���4s����Y�����i錤u���}����{���3|��#n�E�P�l( ���c�-��͖��H���ō�Y蹛F�*
cF�x�Զ����F���� ɩ/��j�#�{���7�1ܡ��(�Hq�}���^�l�����b&��j�F�5j�)�<e��������_iv��S*��g�86���G��9֘��.�,Y�r��MC�
Ǿ�Qq���i�"Э����Mʌ���rI��c� 	�g���1�e��N��>�馭 Xh�i�92����`*�4[4O�3��0$���i��g.'!FA��L�#���1I�s�z-U�%A;z~\*1t��T0J�����O@�wX�Ϳs�Ū��>C4�a�;M����H�Z4�{���U`E:o[so�w��FP�r�Tr�)(D"zo;��I�L�$��7�u]ߺʤu��f5�N�����VÐ���mkc?v#�U=Np�HB(Y%�d� �[����`!b{2�ֹ�D�V7_�reww��n��M���Tv�l9���r6K[�N����l�Q��Ө9%%m�.�.���f�0�~QhWZ�����h����o����k��,�Rb>VG�Ψ�n5v+X�K����q��%<�I�f��$��S��Nd�I	��M�wO�
��pN�{��i!�%o'{|!��gV�\�y���皑x͓��n�kG+K�FjS$�*�h�.}?�K()�����pǾ��1����I���e�r8fM#��j�R��a�8��Nj�Y�i��|��,��9�vͅ�V�����5��Tn�EZ������U*>q�JE�)!<Z\���*���v�Fl�n�j�Y��(�����6ww�<�IH���Q�1f��%�(VP�D�?���	��7D"O�i��s�} ��"ćF���  6<W�π������Xqxx�8R,�d�p�7g��m�f��\�L�d�	wn?t*���s�]�s�T��$�n(I�NR�F��m�~B<�L7��zҊ2�}���1O̐�\4��B�`�쑙�$�>D�X$��Vx0��p���x2�g�ܷ<2�T��P�(7*�?S���10�/���qqxB���m�:w\2$yMPNd�	�8_�6��9�mPl���"��j�6q�۶��G�d���/`ߣ|�$3����ygZ:w'�}��3�ih?t晆���6��-�g
Zw�Y{zN[w3$�N��D�����[^m�'���NB"7���Z�K��S��R}����WYhҟә�p<��Y`]ig�Y=�w����u������YlO��f�u�%�Ru8߬3�N�_F�yC��&��<2�O��CFS���|�l�U6b��W�gfH��θ�͝9�)�%8��K�,���@�h.%��o��=8�U��6��V��5���mwX�����St�e��c���s�YA�ps��	��h���Ǵ���Py�Hj�d�����P.��(>��(�Q���$����L�0OLI���x-Y#��m�$85��T�N�+7@䲡b-��ERl
�ӯ�}
�q�>��1�XH}"c���`e�ք�~���'1��/^�Gw��sI{��=����p�i᪞����s*!$ѳ	i�"�팿����|�.�~lF���B�c�G�JF�=C����Iv��G�T�b��8��w^T憟x���Co�0���I7�"�Bϛ91�6�I�9�M��pe��#F��Zj���qި啶��x?E�#T��V)�D�ˋ�>qXP��SAIdF[k�Ю�4SV7�^I*"���W�tp*�%F�nڨo���'7�{�,H�iJ�g!C�w<��Z���a�'i�~��>~0j_��;MR�|���/������_G�2bQ?��w���LJ�0���� �7ʞ�v����0��Ҁ��4�N��>�/���#�N6�9#���D�͋�}��.�\�"Q�5���I.��я�F6��U?�9[4�ʨTI2�\���!7�oh^Yd�������M#I��g�EUwe���-�/ؐ	Rgy$�2p�IՈ�Q�,�G=���E�:R�,��92\*���c8k:��OJ�� -� �j������@�ˑ���Q�s�cp�|X�F2ˮFM��}뾗�:�.`�BwuK�L~�V�t1��X#m)f��$q�+�<�/�%�$���v!+`���nݻg`<��顤����;W �R���O�f�q�1�~G<��R~��e\�'�|�.>-b~�N:]��D|V��ۘ�ҕ��Fg6���~!�(˚k7W��[����M"�Q�����sV�qh�"���V��w�&LƬ�2%j��^�e�D�廮���`pv�����hpS������]�D��3�f�vM��K�^�E�n�*��b'�4����*;�&�:���������0c��L@�Yϣ�-,-��78G�Aͯ>\�7��k~q׋+�P�xi�)9E�⽄It���Ѱ���0���fg�Lg�-�Z�FY��)���M{�Fmk�]z��|M���WD��%q��3�1�턱���&	v�	���)�}�x�O���`�'�qr���N��_�W1g����丳:)�N��o"�H)� wY�&��6��\<H/����l���"����|$���ҏF�Y�Դ��4m������q&AI%��3�0���_E�5�(T����0��d��f+�4�s�M���H#��U.���.c�T�e)��x�$���W�DKI�[G&:q�4�"�N��x����%�I�nyy���K[�}$1	f}�Z���%㆚�Պ��Q��b���x|�Ť<-Jb���%֩塒X�,�F2���#Y�tY����j���R6]���VJ���R"�ֳw�>{��]m����H\t����6ӣ�G�ږוPH}=�H��׾���aC
����Q�N����ؘ�5T�0��ld�����A��#lp��ܴi ���D�Ϋ�'�n%����I�CF�4I�����8��߱�i�/�xŧD��<�	fi$SQWQ���D�[���{6�����T��'}�����Y܄��j�m����n�Cq6{��޵�xc�F��F��u?��P�2�o������P�:��@�4�i���G�M��Q��o	���n-�@�t���#�1��O�4��a�E���$D�/m�\����rO��h�kN|o��PK    2�yM�i_  �             ��    EGG-INFO/PKG-INFOPK    3�yM��2                 ���  EGG-INFO/zip-safePK    2�yM���                 ���  EGG-INFO/top_level.txtPK    2�yM[5��q                ��  EGG-INFO/SOURCES.txtPK    2�yM<u�L   X              ���  EGG-INFO/dependency_links.txtPK    2�yM��6                 ��1  EGG-INFO/requires.txtPK    3�yM&Tq݊   �              ��{  Adafruit_CharLCD/__init__.pycPK    ��yM` ��"                  ��@  Adafruit_CharLCD/__init__.pyPK    ��yMt�|?  QQ  $           ���  Adafruit_CharLCD/Adafruit_CharLCD.pyPK    3�yMp#�"�  I  %           ���  Adafruit_CharLCD/Adafruit_CharLCD.pycPK    
 
 �  �3    from .Adafruit_CharLCD import *
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
DIRC      [���&VM,[���&VM,  � \  ��  �  �  
lcD������9*wY�^^����� .github/ISSUE_TEMPLATE.md [���&VM,[���&VM,  � ]  ��  �  �  �{d�b�^n��"���3�Z  .github/PULL_REQUEST_TEMPLATE.md  [���&VM,[���&VM,  � ^  ��  �  �   *�3nbn��YT��-4��C�� 
.gitignore        [���&VM,[���&VM,  � `  ��  �  �  QQ� y�L4u_�6���bd� $Adafruit_CharLCD/Adafruit_CharLCD.py      [���&VM,[���&VM,  � a  ��  �  �    Ji�EW9'xÛ�z�����R� Adafruit_CharLCD/__init__.py      [���&VM,[���&VM,  � b  ��  �  �  =5�]2�V�l�|-���@�w� LICENSE   [���&VM,[���&VM,  � c  ��  �  �  `׏�4r�E ,��7mn�(� 	README.md [���&VM,[���&VM,  � e  ��  �  �  2���c��8e��Q�� examples/char_lcd.py      [���&VM,[���&VM,  � f  ��  �  �  �<$����bS$5V��W� f` examples/char_lcd_backpack.py     [���&VM,[���&VM,  � g  ��  �  �  bX�����%WE����8�� examples/char_lcd_mcp.py  [���&VM,[���&VM,  � h  ��  �  �  T�|��H��������U�� examples/char_lcd_plate.py        [���&VM,[���&VM,  � i  ��  �  �  �1*�Mh�{9�&&�{��� examples/char_lcd_rgb.py  [���&��[���&��  � j  ��  �  �  	�o±������J����D�o�? examples/char_lcd_rgb_pwm.py      [���&��[���&��  � k  ��  �  �  (\#�+~���>҆�{ϝ�� ez_setup.py       [���&��[���&��  � l  ��  �  �  (\��ki�xf	���O�� setup.py  TREE   � 15 3
1^���ֆ�Y��BhR�.github 2 0
�)�
8W"�gԖ�}yͯw�sexamples 6 0
��clO���;��ĖuN��Adafruit_CharLCD 2 0
yЭ�+<_�O���S�d�qA��맺=�9'28�l�w�[core]
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
PACK      x�x�m��n�0Ew��ME�a�Lm��
R�#~U���}U�:� ///��:+���(�;k�r��XЊ��ģ��FI��%��>h���H�w���	�Ea����{#���+6�JkZ���-���u��Pɗ5�i�kߝ(�)���(ӯ|����"���*T�8xVF�&��<�,	���Q˚d����/�����Y�)�,��i�$�En�tCZgT�r[���_L��j��r�ʶ��~�2?v?:�k�x���K� E笂h���VpMMmK(��e��N���0�A�/ ���L�x�`�I��Ұv�d��g��H �������k_��5J�>mMg�h�o��-���}�c����+�]��$��>�'Ry[�W���RP�~Ժ��<2�乎�aM��x���MJ1��9E�G�c@��	�K~zx3���Q��7^�Z�G�r�9�\c�e��l�>zm�.R��"��Y�4pg@��lg���jN1�R�A�YU[�A%�ɷ6��wx���&x����R��R�ve���y��AN�I7b���}C���t�@��i]���D�"��|�g��kb�D�������X˖x���Aj�@ �~�>� kW�6�Ґ@�~@�j���G>��q������fPU��Z�>Q��F�!֚Ce�^R��,���C�%i�Ĭm�

��Dʕj*L�cld�y������p�G�O���e�=t����)�SH�����4��[ss,~�lWX�q���=ܦe��L3�x���[
�0 �{����M6�������d�k�n?���
����,}r��FC��)fCїj�q���ؽx����5�)��@B�f�m��3�\99[:^�>�p��8���`��*�J�k��i�R �����:6U�k���u��ߋ���z����HD�x���A
1�y�܅%��lf@DP�~`�D�Fb<��_�]�P��4^�d�Y��N-&��Ɖ�[/#I�z�Қ�1�$"Ǒ�#�#��#+
^�r`����K�sYV8�Cy(l[�_�<w0���"#{���1�>sk鯳9������v�b~w�\�*HG�x���Qj�0D�u��/�Z�Y(!4=B/�Ү� ��+|��W�|<��L�U��L1*yr��i�D"��Ɯ)I�Eg6�um��Kb�VG���4xV�V"e��̆���;�����r�O�����RRC���y���t�������:�^�����,۹X��p���[Mn�x���Kj1D�:E�c�>�π	� Y���6�#3����#��E�{P��"��/��x��c���t��|AW��"�Q��h�E!�w��j�j)<�J�Ƙ���ʁS���륯p��>۱t�ǫ��C��~}�ɦ����fG̰צ*�����] ���ȶ�ǥ�l7����᏶���fN��x����J�@��y�f=�������'O�C̤{4����	��7��BQU՛0��%dm��Ǝ�0ydS�):��&�ѻhYT�!*��;���1�ѨC}#INņ��cu&�������)��?k�˴~�$����I��;~���U�(K*4��	q�L�˿N�wi�6���k�[�EPZ]`��6=������Ñ��~ �b��x���M
�0@�}N�T&�J)t�C$�����޾���z��U"���U���x�RP[@L�[	��+��J�ƽ5^!��;G  ck:��4��LR�����T��Q�ϰh���(e��m��v�Ri���۸�.��ƅ��-��p �sn?�o�y��X��M}�x����J�0��}��V�L~ADЭ�����B��4��>����|�ޘ�2*&�YXX&Xy-���)������/�D.	N��Z���2�MN�QF�m��o����[9F��)��|֌�0�:g�Pe���R������:���<�D��nb-� �V>���B1�L����ۙa����u��r�f*��o����`^��w�`_������֡P��~���μ},Cm&�x���Mj�0�:Ż@��eA	=@���Sc�,�����t93��a4��5x!=��ГU!��3�Ge�[�X9e�E��):X"&����T����/6�t�G��y�/�a�;�/']����7�y���WR�j�4�ޤ�R���1�������뱣��[�8��ޘ�x[��_�R|�x���MK�0E��\��n"Jg���}I�{�	��1M��Vĕ;7�����A$N�"	����")�I�~J�u�X�� I�����UM(�e����}L�����7^��5��8x1ڈBR���r:M��.n�T*����P�wm/�Awp�e�i�PV%�Zx!��.�5�׹{�zd�l���6^\YH�,P�|,���6��ƣ���΀�c�O����S�r�=��yߡ�?�@uݐx����J�0��}��ۤMۭ���^e�L��6)�Dp�ɧ��,�
�GO����1��6]/U�K���
�h�F)��Ѧj��V�`�m�`$�`�]U˶�궩3h�7$H�R
�;�H��3�!�c0ѝ���On�p�n�'��\��Yb��*!k������a�3��Z�^t$dz�#F�1̰3hcv��_����8�8�E�K��8#����x��f�-�R)������k�t)eJ�����f<�1���@S�@O��ǀ���x���MJ1��9E�k5�d�"�n�y�N���yyf2oo\x7U|U���@�\%S���\S$����D�e�I��u��*:���.����h�db�Xӂ)XIR#���I�j��OZ��u�E|�6c�Ut�K��Ѯ�𶾶��iL��+u-3x(m�C��'��Ak5�}��UV��?n�A篓�w��.��V��q�c�+���Xa4(�i0��,�T&r� aqi�x����j�0D{���I�-	��#E�4���j��uH�ϏCڔ�fx3#�pFQ�M��%M�979����iI����ƻ@�I9G!*rv��j��d�SHћYk��[�����y�.����K�K�2��!�^#?��z��W���2JTK�"�]��1
C��^��񓁎.� �ؐέy?�׷���	��O��ظ�`G����5n�x����N�0�{?�J�w�gK��J�F��%��q�{{L�Ќ4�ofja������]�D^D���P���Y���6j��
�r/C�^QÙ�akM�Gq�����'L�uAH�s�'���9�r����Q���[��m��u�ls����ӯ�)������E�64��;��.S����z��ɰ�����pg@ʶ�:�1�{�i<i���*�sR��~\�P^.��~��cd��x����
�0���셐�M"J]�u-irc�A�,���W�a8� �h�|�2( �c�	�2J��$����V_p�Ċ�l��F�8 :������܁�|��RȜ�9���6,����g��\�6аL�3ZI	���q�;�k��s��"�E�J��Տ�<�;]�/EMʓx����j�0D������ke%(���[��B�k튈ؖqU��}�_����f�NB������'�tP��HDn���y�ɓ*�<!f����t�$(HS��'?�\w���^�K�[/�В�8��<�qDEFx���RZ���[����;�M�m6h�u����3�0��@��6���~�OИx���Kj�0D�:E�F�e} �	9A��[���2�fn�
�ŃzE�*֘`u��ّM�D�u�ב�I��nDRV9�'�b����Y�袷L�B\ьZ��m+>�����Zv�����8�.�T���F�&x�=��#�&�:��|��a����ǵ���R��˲��ϯA��R��x���K
�0E�Yś%�ӗ��Z������+�����޸���9p�D�kg�t��4
�Q���Jȭ�Fq+�eO7ѣ@k�	�;�2q�����^h�D��E�Q��������������`U�l~�}��	y\�Rqm�0��u�ֱ/��:�m�ϯ���v�s (��尃c�o�KՕx����J1��y�����?�EDEO��๓����d����ۛ}�PPE��j�Z���;+<�Qx�y�#%#�J���J�A�($�.�УwJ�AiC
�v@�po���g-x�OuB8���r���|\�[Å����u:���_e����o��������7�x}���e��-`I��g���e"�N�wہ��QU7�x����
�0��y��%i�M"J{��$�	�A���
����#F0����:�:dM}H�Z��3��ʱ�
S�b�G\���2�VY��]��Z��JdP�֒�U��Ƕ~`��6{8�:���L4�-PF��XN�JT��R�_gqc�����&�}!���ϱ_ �H��x���K
�0 �=Ż���Ӽ<Q�K7���)%.���
nf`�x�:T9�l���+�Hj�9S`e��V����d6$�g�cv�2DiE
	��:;&���ܻ>���|`����`_��Sh�e>��8�Q8H�!!v��S�鯹{�����i�^�9~��Dߔx���K
1D�9E���&Qt���If&!Aoo���(�=�V��Є�Ԉ�!=YV>IN�b�R&��?-
U^x�FZ��J�H&G^!�Nђ����3W�����g�C�p�U�B���#H3Xg�=���2����9FO�p�\����W)�6�5+�i)3o{�5�PT�x���K
1D�9E�!��"�n�{�NO7�#C\x{#��Z�+���Fֆ]�ɰ���$R1ɻr��PO�ym��(E�7��[�:�%�G)vB.6��W{l;ܷ��z�f�c�����Rm�	��>Z7�ݥ:]jk��X���*��{���F��x���K
1�}N�P:��	��q�2I�3څ�7��ԃ*ݘ�����ĎSA��h�GG��$?cj$S^�������\�\ਣ��Ѥ�׾��z������h�.����m�2���| ��7��x�340031Q�u�q��qq��MaHv��uɞ���Z呇��V,�r�!Dq@��O|�k`�kp����I���P�������T ��$���x�uVMo�8��W̭���v����Dm$�a{�-��(��D��H��7C�Q�%�(μ7��C띲{:�D���:m�ݒ�dBH���ߗ��}2����Qc6^�yݹ`��)�ڍL�y��)�4�N�\�K�5)�u�VA����'�U��qO�M�ҍ�: ���ma�K�F��s�o���@#�eM��Jޱ?a}1Mh<�vd]���&~I��6H����]F��M�c�HU����}jq/�.��b6�S�'i
�����pÑg�CLz��0�V�0��é�{ ��Ձ���L�ZeT"{AH�.<��"E}����7V��4����ɔ��+��@;�tT{&z�H�$k"k�"_p����F��޺'K��%aƊ��U���]9��/����יk��ˁ���Vy$���q��q�%�s)�	�hTC )�����-�LŤZD��\I��b�SӰ�N�{RȚ�sK��v����O�vꑽ�w& :]A��D6��L�HBށC�B��xP�b�����}v����s�͖*t�с�\��=�Q��/�u!�uf�+�^!�u�a<F�M��ڹR�Y�D�������w��*5��j����]VR����I�Jc� �BIZӠ��휻#����,���nY\^��(��$��E�-������A#��zeH���;�,�f�*�!�=t�{ �k�i����)n���*�f ��;�#g9$οd��?���lԒ�0���)_�zNk�$�G>ߒ*��F�����h�|����)D��5i��m���qt)��,��.mw̱ǋ�ͳ/�M�Մ�1�ki�A�a+T��X�6�P�B��Ԩ�>��T<�%�����ƥp���J�-�o�!��_���a'���x��p�%o_L���a"&'���|�Eދ���vc]h�\Ճ��!	7�1з r�W�`,����V_��,�`���EZ�7��&��n��m��{5V��VqZ���(�Va.�Fǜ��J�����5��E���+�i���E�"C��]��,WKgf�m�b�I�ɉA���8��_���S�L6&�����3?ߩ��o�g�����u�*�kZ�^�?͗w���X^�o�?����j]�їbY���:�`��h9�q����I��c�?��|�����������~ !��j����sHS6����pd�5�ɇT�
Sn �b��/�X]~.fŷ�b�f����X��~kBT/4�J�R�_|[䯬3,0|��ݫbT�.ק����x|{�Zc\/�sBf+�X�ο�7�d�պx�K�,.��J*��I���KMO���K�2*���SKJJ��s�u�� +��x�K+��U�sLIL+*�,�w�H,�qvQ��-�/*Q�� �{
�	x�\mSI��ί��#��V� �s�&K�(!�p��E#��w$��[2fg�~�=OfuUuK�=�ܷU��KV�UVfV�_�V�xʒ�����v�����9G�l�,Mw>^��,���d�|H��f�ΟL;i��h�%گ�l��y��M���8���}͗�n&Y�tbFQv��25�/�,Ǆ�n%�d~o"3" ��� ����1�b�(��Q����,�/�%W�$�87��Cl^\�/ve�qM/�^l�N󘀌��d1)J�F�՘x��d��58]8D. �U:�m���q2��X�[��I�P7���VK���8��Z~L3��S�`�R�1�Q\<�U9[�Y���8MV�˂93N�:Y�o�h��?I�������8!��{� ��]�9�T���E����v��tj�b�9,�́	�@��._B�hji&�V�m(gs�;ܞ�;�{m������Nۼ8���us���n#�'��O�wjN.?��v/�u����~�����@�{qu��{�:�iw/?��y����Ew ���`I����Ss��� ��C��;�T�����pO{}sb�N��n����o�n�W��Ph�e��u:��A��t~�s}vr~�� ��4�i��>����w���C؝|8��b �u~ҽ������Gb�7=�!��8�۳��	����%�i�.}|�����M��^w��߽&[N���I�bV ̼�(2]�d�!d�H/�1���9�AP����bxc'�Q�f����Ka^���=lmß;݃����������/_8�otu{�~�����t6�>�w�[�a�s�ow���O>�i��/{����n��g��N�i�tH7��t�kw�;�b�tJ��+��� �~�k����g�S7Y���I��ͥH!�-�ڍ���>t���k�nt�w��#:�e�d&��^� ��>��N&�� �u6�q}�:[�(����)u*���� �6���s�wzZ�V\[���dEFEf���!���-OI����b6�zA+�j����gM���5��h���+)f���\N6�4� �w���g���j���=��xS�
0=�ۺu�ї��vop]]{O�9����ӛL����ϴC���yC6J�w;�6`Cx�MS�&ޫc+ʿ�����pWL �&��>��3_����(H��Ag�|�f�Hֳ��AP�W:���.;�3ۇ����:�}T��=d;�V:������o��}�y��4o����N�n�}�o�7ͻ܃���'6�f1�w�ly{����Tչ�vڽ��|����U���i�ֲUr��pgg4�����ab��k�]���;��ŋ��Ve�n!�Kq}x�Y�>!Z�Y����ݞ��h�U���A�� �#����pk��a�ޤn��nb��ch�����1��)z��<Ə�h�˔�x�2��u��豿$��q�.�|g��9�V[F���n���i4����"I�<�1�b;L�l6dsmw�B�YZ���m��x�CO�~c�2�
��C����BFc����.�n6���YD��G| /~:�J�v��sG \�9��0{��	n4MG�@�G�H���|�����9��L t�*ezL��E@��$�������h ��M��ؼU��0D"�O��b�B�Y�?�$S4MF)�ҕ�!�Cxj��c�LID�NW�yNUuE��H Ju�Kv'�	p�o��,��T9~���P��$x[pDpu����.)79qA�,P�^s���8�;�� 0@��%Xgw�9�ݚ<��#���p?�~��8�؊�j�\[�s4]����1I#nlZЮ���u��g,�5�}PŢ�YD9��TP��!�����9�[i�E�$���&��"-_A� �������jA7[|�B��"K?'cH���j���N?�C�iǺ܈��-�h���1�<M�>eiw��E�hQ�%�000v��ÐZI�YLij�/��SN��Xo^ �[bf"N�$Y���`L��l.G�����[��-P� �f�<F�9DQ'o9�Uu��h5D��[�P�tAk�����C.H�$���C6E��H٭�`��И`���dz�e	a���Z�q:��+�aQ��`(Iv��ť٘�撼)�*�w��4�Fz��	Yؾ��[ �m�Za����ӳ1�)	'�?�|�Q{�TK��,lAUՁ���W��`x�a�p@�M�w�5��5�vKǎ�:>���������o���l=v���q7��w7�w07육��1��{~}�1��~7�ǁd��ԍ���9s@<�s#ѶX-�C��CA�Om�Sxe��N]-j�W_��|��ں�^}�-\+�!ѧo��_��R��p�"�`!�&�I��W˧��i4�kk�a�cIH1ܰu���T�2�����W�ւ	��

��"���?���NX��:>˴Gx��;�Vo������S�j!r�6JUWL��,�G�T�0��(����[i��D�o���������$XP���j�r��N�`V׸W�a�F�B�B�	��!�@�4�d*��ͤ[�	��6��3?g�	��Ԃ��
E��<�d��R�S�
������(�`�DY8%� 	��X�`�㌐4
�V�$�d�T���)�6I2��4�rr�W=Jv%+�N�@��s�Ei.Yq.��8���!�p���4�����fooO�H�|�YE����g�)��=��ӫ /���9P!����+em�,<y�b�������'&����8^0XV����� w�<O��P�i�^�o�X&�*]u��ץR�b*�T,%� �;��C��C�����l(�����8�m1��a�y��D�Ir�A�#�w�p��Y(�w�wj87�"&HS�'��on'���bm���e�u$veԃ�cC����l3rF�y�TH%�C��!ǢQ��*���d�<�4������x�.��*�*�򲙱�LC౬ql)��-��" a�j(8�R�F��G2�_����,�nV9hG������?�(�?��J%��y4��!4�)���Z]N���J%��u�H;���=x)���0�v&���� �fH���d��l���p���T��^��W^hK���\����[���-�?���Γ��2nËfh��V*�D�2�H���Eey*>�58ΉrjQe鷼o`���L���v��R`�)_G�0s&��j��p9�S�{}Cy�6���+E�oH!�>��b�����i� �r
9�i�=&H  5"ɜW��N[������qܾ���\�=t���(%�o�|���Fݫ��D�.3^]wQuh�Ub�����!�ۀ�&�1��<~Nl����(G�����i�8=���~�Ԭ�aLMD�\G���3�8��snIY
�����-�����q��4��k����_x��o��އ����E�2�Q\�-g)�"}(�F�h�ݡ��A|+�����i�+2����uܤ�6A��4���.B3	F�@Q���]WX�	�/��5�EJ�y����.��j��t���݉�em�C����4������5C� W��q��K��d����JƏue���I	�Fp�%y_$
Y���J�5���.��0F���o��aT"	U^��!<yԼ<*vI�|���f��09f�*�l�9<�+G�0��ϖU\���ߒ��2��1��U���CZW�:,랚�wr�e�Qp?�v��\�q:���ܴ�{��ub}�9���#\�2U��/������XG�%����1�aN�7�j�`xg��ÑǸ�	�>�%��?�*��08M��pG��a�6����8�4z����<¥aԺ��&u	A� p��ˤCXA�uMa�L��~�����Ք�?�dw�f����/�pm�X��J ���m	���8.�8� �?<���
�W�G���0�|&#���e$���A�y�eF�� ��H�eo�3��(�2g�9yi>�r\F8,�L�t�>�x�%�
�	n;�c\���������6��R���.��10���?�]�`j���?�A%�S���&�;2'���-Y@pI�Hj��+j������p6�<�/bn�����i����nXL�ײ}��!S(��f?dn���E�HhѲ�Ȱ
G{AQ��0QGƮR����)T���g�Ĳ�C1��2o�WRk�S}9E�*1�9�J��1��q뀔��J�L��Z��I�lď��#��##�G��.z��N�n�4Զ����ō�E+��keO̢�īy��_���p��k���p����X����Ђ?��_�����&�fJѕ8���
,�����G���r,���!�V�C�Ȇ���r{���)�j�p��ʷ�O�j��������@�9i֬�;]��h.xV����.3���YN[��� B��f���,��tS��)�STZh���>�A�Z��6�3M%I�pkY��V�� r��B-1�,er�TG� L
u��0��ח�4DL8V��BR�G�c�GB�԰P�睶�a͊N���|�(��jam$5���\��	�L�%�F>z�8�ÓC�l,�¢���T������׀!�eMѣ-���uY��2#�J S��r�,�4ʲk�]�L�y���eW�ڊ��Mm~WS�H$�4Ѫ���a��}�ݺްb3+��Ui�{!b	*��VI	M��MB������4Y��N	��uq�1�i\��p����Y�
�C���@8��|s� i���cǍ���Wͦ��9������mHh{�5+ߟ�����Y��I��>NP�u�(�}����1�G<��
��EZ�ꮧ(�r��C��y�������Z���5;x�A^�<��#86��n<:���;ލl(g[��'�Z�lY���[
�m!�Q�ֳ��6�LV�\���~s���y�(+д�J�(%~IZ�d{�{�a��U�FY��]�w�Q��� 1(�[{��5p���u��/_1�&�.�k����ڦ�z��MZ>R]w�߀S�&Ϣ/5�2����� g)Km'=�H�e6dG0��� oT�..�a�H����*�c�`��P/������2�1�	(V��-)ˆ_ib�c�)�.�K�p�T�ur���P�}'rHTp�n�`��C/lZ�¤��� ⥰*�?���xK(�4kk����A���Y��pWRM'F?@��.��&�"�����N�w&ё�u��>���z���)w�"�s/rƤ4�� ��hѬ�wr��v*�P%=L��^���S$�1m���!��NC��f�1ɮ�v |cuK���
�V��KP%>�AP��"�O�jˬT�� 	m������H.W>vE�l�V����ݻ����b��KI�{&�u<֋�!֍:sP��"�C�)A�7�L�C�4���AY{k�b������W|�)�����"�g�Q���Z��W(�3e��#��CH����]4�ef���r _�n�#��� �mp;D3!����}���x�yP>a��2w'�1�QOr�E<Bҵy�7mK���P�ȱ�(���T!Z�ܓ�|5�����0KQ���s`ѹ���ۀ#���,9�*n@����� pC�t���u�>�?F��30����d6Z��àF1�V���t"RIy�����x+n��2��i�K�k�W�<����M�A��i�m���|U��3�X|j�G+�Z�����j�<	�1�I�`j��n�\�k�3���U��A���,����yBm��^z�ʃ� ]�(�~JO-���$�����` �Jb���e�6�����N͈��i�s����7l��[���x�ΒG�a_��u��s9�c���#8�|ȗ�p���H 6l��^|0qG�[�e�
E�Y6@8�z�8�T��v������}C�d��,b���,��d��W7�_�d.�C��po�j&���x��F�G�V�vY&�2����M�xF��x��=�q/�xHF���g��Ofrj^q������5�I��k����I~�N6d��\��6�(�%#�d&&/V�Ĝ���L@~;���+L���}&�2�O���7��œO!�Õ+��-$�1�U � Ʃx340075UH�H,��IN�+�dX�@����o'[�r02�a}��!������҈�9vL�,��ʿf�L�mѕ�$����9{�C�����,?������$���$�RC�y���-;�����0U��������\����C7~����y���O�t9��o ��Y���)x�����4�\!)19� ��
*lT�Ll�O
V1��-��BZ�D�M C���tx�UMo1=g�D �.��C��!%M�m"%R/�����������;c/,4i�C��=���f�ٴ���5��P�r��ZE-��eE)9TV�0H�̰�q��אj�8�2p�����b0�����=��*�&�DQj�`n�_;Q�h���Xn*�sLO����o�)m@�[r�u!�k��i�P���[s�G2��B����[�j,Co�F�%	�qc��Ic˴���e��)Vk3� ���	���;9��CXP�qg��l�MG��K�%��~h��;T�!�B�20zV��k��6i�j�Hi8�,���d	%��8]Ŝx��Ӗ<�'����%�i�$��_�iD��p�I�qF�_E���p2��J:l��%s`Yf��q�*�F�Z�|8�t�2��
RԞhШ�$�LSO4�1 `g���=$�3ꑃ������C��p-h�eG�D�$�?%�	���Ar�B�=��I��� :?:�{��au�Cϗ0�:<�#�Ù��I����'~q�r)���h#���Ʉ�1ju�و.il%�eg��5/4ص��{@�����8�N%g�Dk�Y��Γ�x���%�AZb)/�7H���g�����t��E�uä��
�����E&�u�`�-�K���v��g�~�A�A��݈.�@��ajŽ�je|�\u�~���쨟�x܍����+_x8����j	�җ�*����0A���:-�D�7��u�9�q�9��+�O���P@���y(;(ڣЄD���������[�����xXWt��/�o�lT�&�#x�u��J�@Ʃ�r�U
��mL��$/�_���4]���Z�WP>�7�3�OỘlں-tn��vf�oZ_�׻x�4@�_`H�q�Џ�E�?��ox��z{�aJ(���I��}A�ѓ0��5 �h�#bB2��x"�"F �ħq�Y]��Y!�s��+�;FfV{�Re�%oE�"�j��Hv-�麖���J)(�&�� �*��/��t;m��Cw�K���@��"�mI�3�{I�+r����^9[�Z5SE��l|��A������t�]Żv��֚{�U'��,AL�:f�\���;��y��cޢ0��hx�;���o�2k�B���De���O�RS �V��+'9%>�(55*bI�)M���ؼ�q�8H��qv�sLIL+*�,�:9�ټ�K/ ����S��W����X�)�&�rF�d�ۂM..��'���$@�%���z�9��z��`C&�e��)�Y�M� ��L��sx�U�n�@}6_1U�%`��V�c�$��qEnd��ڬ�Y�.Mگ��u��86f�̙33��އ�R�s���t"3k�g��S��
�	+X�y�py�4�,��e�a�tҼk��VclY�Bφ�M~L��ea��Lh�R�N�a�b���L����J;޿D���O\p|%��Ri��hUD�U�e�.L{.�]�;^�>>�������)mW.����p�����=��WQ�x r�G��!��-�9D�@�	���@���$q���CM��&.��1�_M&J��U�0��&�OU��L�b��By���뙱���`~}�+�r�E���J�w�q8���~`w-:D�J9ϝ��c,j�ѐ5�o0����8{��l���<�nC���4
�!�>���;"=�M�H�Re��n���~`R?�M�H�Ey18/'z�N֦o�;;����qևl^j-3Pڌ��I_x��+����{�
�A.�M��Ғ����v�e���1�DW�سj@84�n�(N\�ox�cm����ݮk���G�7��_j��}�o�^��9B�[�GWw��y$����[���g��Sjv#5�&/D����6�E�qZ��؞m=%���(�����9N�B��8����T�8��#�%BAN}���,e��D�t�:��6
5��NU�)$�ǈ'U�7|.M�lU�a�s�u�0b���x�f3d�ίzg3U��Jpk�S��WV]� �DD��nx���w�o��D����X5&�c��*���IU)*M��R ���l� FZ~�BRiII~�Bf�UQ�i
9�)z���E��ũ)%���U`���� ��%�&ih�*��&΃"��� K0y�_x��S�n�0}�W܉@�(I)�&�h�Ubb��>!�\�Z�#;в����+�(�!�>�>�s|��t���b��Ey�6R-H_ض,v��50��1d�XV�������r�̪� ��9���:���T0F�.p,¸`��^���TT|��ߌr�R;^-&����&� 02�0fR��z�Xť�Y�P�B� ���k�j�5i)��8)@�Q�pϵ9����-
b�m���r��W��tub���)0�ٺ��BK%v�,vH/���Q��Q7I#�v�α�4۳��u�F��=dE[���-4l����x(��7Dh�A��������M�npō��L��0����Ϡ����h�SC�&��c4ty�gV@L���0���̘.1�0��/�ⴼ��}o�aӝ�gɨ6N�nڙi���r�V�9C��d�ᯇ���$�o"��׫z�kp������{_��Ļd��"�[�%�<����V{Oc���N��Я]�2+������5[c�=Oo�݀>ʞ.��%��Y��}��y�ޟI�9OЍ����٢3�=���Ǐ�=�n�4:�kt������a���	��=�/���*�]��x�Vmo�6�l��[��v��/q�6@$��H� iW`�mi�E�������)9r:$-��t<>|��{i�2(�,�|P��D�A��_Ŧ�$�&��$r�~sAQ"����t9{M��&t��=E*�Ze�VdIK����ĆA�)���6�e�ndP��b���.f@fLa:�X�(1ۅU�^v!�N�ֳg�f*�Jm	�%3ĩI)�d�-������Y)ɪ���q��Zʜ�X��[ؘD�YLK�>�|��V�C�t�*�D7{p�~co��G6���a�v��8�~{,�B��V�&�wu��	P�/55�ƀ;"��t����=lHĢ�2��k���`�ۅ�	aʸ��Gf�L�] ��&v���C�范��:;�!b���ͩ���z���M"Xb_o�ʔ���+Fy����yqxa��m|>_Aa�
g��A�Á���O�eV���n�C�qӠp� ���L�L�60����`� s��)�R�;�J95V�z��A�������Mx���4I�iN���T#ɴܦ�� �c
^1P�N�',{��剗�,y��襓�	D��V>%�x�97x�����|ľ]H��P���i�п6�=�\�\��`k[֌��ʑv��U�ܝj��b�j�W�'N5�U�C��W��~o�����9��{�Z�Rx���Qn�ĤՎL��@iM��� t1�V|��������1�g��9j�Vfwd
��;Ԣ���ģ���㌇U�pj�4a�wyjS�1.�L�Wd��{1���\涯���UA����W���I�{\�N�ߓ>����}=���*�)�� {��ڧ�n��e&�ns�Q����M�Un&�8�J��)4���
�����zn1ʤ�]/oP��Zv;��ם^��$4��E�(�C0�S#>��z>��p5�#p���O�9^?A�������O�����G�;����5���ޟ���x�4�{w������6}2�����_�JD��%����x�Wi����o�S���S�[���k� ������7G��U������A�B{l�}�
(���e���R�kU�Y槬Fb�o��P�4�?ͬ�^�ؿ[�Na'�%)��44%���]�`�&�
ͼ���n�Ƙ�����v<IqWnӍ�����!�Ì{�6^9�U����99h������k��ڠp ���|"��D�i�߇��p�����h/���	Q�1�t`樽�#-7�,�Һ;-
TU��� a�h:�Xr�3=d�_�����)����7��pf��/�x�}��N�@���!��Q(r�8΅ �i"
$.���5�X�xwm�Htt ?%��(x*���=�0�4�o���u�f��a��=n+��%}��)� l� A��2�a
�A�&�ú�RCH&��>z�m�E��@u������@���l�Wa��t!r�?yYp�d��i���p�b�ac�#9G1��[te��qXȕ�He��X�`�#l<'���s����S�C�<I��$�G+�hO��g�ꯤ�}/#�6I�)��,G)1�F�z*z��]�-�K�����`?q/�{�����b�~�2#�׮#8$�����dJ��-��� �V�	qYa�(E�
>���p�̠��vB��MLuѽv���R���]��Ɩ�u��׌�͊$_5�>��⼅x����۶�w������ֵ�\��\�C�$�KR`Y �m�'�*I������#)Q�|˶��hs����?H=}r�hu�.�KQ=��hv��L���4�(^3-LS)K͊J^�� 4y+Y�E�e�Xͳ{����I}��\V6�`fW�ɦ(B���{��B��Hud���s�cF��5���c|�|2a��(�g�ה�Y���2HW��Ep��xF�+�K;3�t-�bSd�A(��~��*����<�����3�H�b�4BU܈�c
�a�馆?�׵��*p��Q���j5$t�J�V�I-���dk�T���TQ\�TD��[��PA	jv�d$�һ�e�vl'��׸�����5W�}��xʄn�`+���O� F��3Y�PY�'Rd^h��h��Rn'���;e�D���]ߦw7o�'�S&@74~�ڱKZ�d�d%&��/�{����������W0>�S�M����yw�#������X�u�D��3o}�� 3q	��/��I.6,��i���/���%�oa���[� /��L��h���2!r�'����A?��$���u)�3�%M��X;E$CL���}5q�93��lW<��Z�#ν��f�ه��vZ;Y�`����)�m;�L\Uqt�N��VtѬ��T��yǏ�,r���ހ��~wr/ ��vQvP�F��>lI@� �-к��V��Z>�ᢧL|*L&���#8����3��uS�y*�����S��B<���A��]�ÈN�o!� ,��$�kϪg���FgF�hh�o�� z�D�U��nJ3��8,���������4��x��5ŀ8��M��*�U�v�
���
�B`K��k�}7�À-�h4+��C-� �1p^�� �7$�,�s�]{e4�t8cX�pCƑ��B�i�E��wy�.tk@���聗ڒ�XC�B�$+%�� ��8Tkn��z��F3&J����N����K �{tR$�-|`��dȊ���i��k�1�>�%����Y߸��Ik��J��C����V�C�0�Y�� ��`M.m]u`c#��-�}U���q��z6	�y+��w[h� �,��U~xG�K��_}���b��F��+y`��C����(sW�p0&.+�n��E�7J�V�.H�7\q�:mޖ[��6Nù(��YF��L|���Ņ^�ǋ<��0|��.XGfe��u#A�#�_�}~ s& ��u����:���R���Q?t#{D>�O�L�՜Q�v�y+��Y��C!]�h9��)z*�4
�4Y�V�-��׺0�&���^ǚ��Vݔ��x���_.)���p(!g�u��/B�E��2oJ��`[��>Z�|���/�*{�{'_f�T�.)�ZS�N��Ai:P�2�O;E[�,ѣ5�����8�����ƿq�T%����	��$
�!0@�T�oviKCh�� �H��C��u�3u����N)鑐�1�v|��B�����	i�cz.��u��x%�K�T������-"�����&��W)����7�&��h���Dm�@[~��&����ĕ���,�v����}Ơ�� ��[��9A��4����9 ?�����4�XD&�M)��`�9�K��fp<��Bi3��� ��;3[�X���	x|�(ȡ�'|�7+�{HO�ﳓE �Y��27�_�?sO��������t�1(����Y���P9�C���W��^$���������fls}Z��b'�� �	3l����;CY���	����sF�YS�e��}������������^��l�3�f��b uE��ƾb8 �e��TlI�B�e���A��M��b�>V��T��Lky -��ר�0_���鰉�tG�=�i��|1��&��"���ߪ�f��[jǰ�$q���;��1�+�ZFn��Y� r��Њ!�؍��-����4��a!�?C�bwGB�
��'��*��Y�B���oF{�	P�)�\A]o�Zo8k�V=�A�Jq��J��%���g�	�៊
�����.�9!�xy�(��@�P(9���C�
�U�%�a�a�$��ˣ~ A��1���T��3\�+��FF{܎ד~�!��k�+���d~���SȠ��1'��j�}��q�L �b���3��dP7�l~��Ў�� VX�絉��G�4x �>�A�4���)p�ˬ�[������Ƿ��&{��kG�4�-'hY<���A�q�p���%7hVV���Xa|�@T���f��dU�>�z��<�O�\K�^H�u�O;� ų��Zex����8!�B�5�����V����D��,�����K�݃Hv��+,�3%�}�+�.I,@�Rx+�/���CXqA��cg�2��'g4C<��ڙ����h�lܾ��=0{�,�7��p�����[Wg�%߯s��[�;7^���BW(��݈��%�����ss���<����Ó�y@^O������s>����wp1hM7��8�#�?W��'yV{�M$=��P��8,��eųY+��cl��n��T��}Y5��P��zҶ�%\x�K�/V�Ȧ�i�`���V�!]��vUN���.#(�WV�+ܱw��P�_y�7Q�ܜ��H��r�u��r��9�s�^���3<��.ĉ?����uīթ�V}1n��b*�o:I�$^eR�EQ�A��S�P�v
etr����)��4xF9d�n�Z�D:̰�H�g�h#xK�;7N`��k�Բ������A �g��=�cG���9��݃,Фk��y��n�=ǟ�dx��T��N��P�6�1H��9a��C(I�&� osc�Y����o��:[�E�2��>ğ�DL��L:ou�=���P��q��#u䖂G�������������op���B�.�t�8!"�s�U$�	��('k��<O-�8ho-�=�YF!�0��q��͉�sA�ޔfI\�!'�KɎq��.��X�N�tpՉ�@�
�8�j��,�#Z�{~�{a ���|$<G�hB���/r��e ��m|>Ϟ��ȉ�!�B��J�K_^���-�#�o�6��T�A�4�PQ-ܹ�x�̞���9���w�B1�`b�/�#j�eA����������X�;A� u�
D�����0r�=�h�y��c�HQ9p���Ay���h-�.oߣ7u�0|�䣊?=��V�`g.�F*��n*�?�|44C�.��Ci��Ei�rMSw(�3[i�&� �H��Fx�T]��0|��B��žk
���	������q�Z;�lI�GZ���ʉ���B�'I�ͬV.��g�� j��o�ᔪlt��"�ZF�h��B�L����h�(����h,L�)��+�k�6�9oa<�G�gt,���z�+��9!K�4�a���f�=L�B�_7HK��� ���F����Ŗh��ąt(9!���y+q�Ln0�F���up�d�����ظ��a�.��_��7X[�ED7�p?�A�(�_�}�2�3~������x]�	�S�
��f{f��y/~�:Jv�~H���<e7g ���[%������|fX3Q�t\���N�\ս4G����1�bg�i�)�Fr��r��9pau�`�M&�\uj��W��!������]�u����|�B"{��i)���B�����]�Mҕ8�mqԡe�d��/6��$����1�cU�֌^�y�e9���>y�k{�i�3�?�0x:���q��{�}v�z���+&@G'��x�M�1
�@E1��	���"6�iD�>,�h�ݰ;���W���<�I$�4���o^��ر+�zF�� �>�.�#��@iǲ(�.ؘ�A�C�d��fm�m|m�;J~��T�9������������:�Ƃ��s�$l�Fc�S����ͥ�{�î��� �͟�h�+XL��Lx�T���0��+� ���H�]�*����8.{�Xul����q�T*�|J�73o޼ɽ�C*�_�#w��<t��><���>J�q�l�0�p	Pk�����l�%j��,�!��0ǆ���-H���u��`�P�J=R��'9���ѹ8�)�#�,w��,���	:��6G��gRk�ͅ��i�7a�4X:)��6�D�,M��]�Eof�ͅ�{��H�K"C����s�T1���R�S���	��W-1�h�����̕KS�3+і<[nӌV���1�M��K��\��̵�7�>����~��2�fz%]X�_��[����=�[�,&y�n���e�S�\{7kU]��Rz0��]@Sgpq�r)@��Y%�v���mc��	���@��`[�b��9�w.�6���4�t5�妱A&.q�EŹ�D�}t� %cK�h���@�J��x�(s��Еډr(I6b
��:��f�@8�4%�0W��_d��T�jF����E�(�;��\򛢥����7J�L�Y�	�9��Cp8�#�)����t�m�,��䳰��gze�F�z�AS�Ю�#�&(I[4b����Q�|l�Ux�;�y�s��ͫ�Ę !�l�x�340075UpLIL+*�,�w�H,�qv�+�d��P9�Ǥ4���L���)I)��LL��3��Aʼ2��[�W�=����_�� � ̴x�K*��I���KMO���K�2*���SKJJ��s�u�� ޚ��x�340075UpLIL+*�,�w�H,�qv�+�d�%x˥$bI`"���nO-��Z#C3����<��x�����f�Y��������C6*� �� D�*�x�eR�o�0�+RO����N�F7��UR��q�2z@4��Kcɱ��,��虳��pG�w.��?pC�!�,۲����}�_?n|���e�OZ+���,��cR�gaBU_#��eH�b 5��&m�G��{�8)d&A����ptr<o�5�$�����4t\��T.��_�]*EStЉ�yst��|�"�Q�֒jT�+S�E� @���Z��A��2�Ģ���a)��R��0���eC�f�~U��@bL6�� os&hFy�I(�a���~-HbR�0��ZtQS.���5:=<�H�Z��w^_��;���7�m�^B&5��	q)g��+k��1������ǳ�k�tz
��@�w�7�
0�
'k����-{�{�~ݎW�͠��,��T�^�}���G�W�Ap�z�����e?G��+�]�|�y��lw��g���t���"�˾x�K+��UpLIL+*�,�w�H,�qvQ��-�/*Q� �
�� �x�]�?K�@���C����d� �&
��Q��[�$o���]��E���@�pw?��k�\�z�m�<����~�9y���RmS��V��I�0!f$�|<.j�vN�m)�L�5-�%QT��Ͳ<�����{�TI+x�E��#��YIx��|��h�r� qG��e;ǭ�]�:An4���<0ЬG3=��G�?�"��6'��-!�~B�m�i�uWQ�a��	�z0���k����L�Up,
G����3��|�}5W��9I��Ml���Zo�wQ���/x�;η�o�2k�B���Fe=Fâ��U0��IN�O/JM̓���E�rJSaj,6od\���>9�9Z�]G��)߼��� t� ��,x��"vNl�3�kEbnAN�d_�0�fM�4��K�� ��s�+x�;'��{��AQj�BJfQjrIN�BI�BPbqARjQQ�B@�B~��SjbzN�S~^��SNbr��F�ɡ�w'[�,Գ�7W�RV�IN�O/JM�S�UP����	&唦*@'s�bKL�/K՛|��ks!� P�,>�$x���Ak�0��ͯ��ڤ��-�B�z�m���J"�ؙ��_?7n�������zOVaM��;�m\7�zhE��\r�;�&��ҟ2\��eޠ8bI.Izu��&�o	���m��
�v�ϒ���c�!2��"]���26�{�;X��(�.�T#���E�>��$���$',7>���mހ�|"!
OB(��������F� �(�y���Zu���q�YV�����>�d���[�Ғ��r���B���{�m�3���Je5�0���r��g`�H��~����pn�eK��Z^��Z�n6=�N���i�x31 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���yIy�.G���\�k��X�y�9�9�)�iE��%���E>�.':w5L�n|�����k��qq��>�ή~����c�����̹P�;�~�����J�\]|]�rSV+�|�ɓ�6�H=�ˎ�1���Ԋ�܂��b�7�o藖�Q���#ȴ���3u�9PsR��SKJ�
*�_�Ү���c�ݥ��Ռb��ZUW�����ÜO3m�z�K��" �ct���x�K �����_yЭ�+<_�O���S�d�q�sW��clO���;��ĖuN����7\��ki�xf	���O�͝�&+�x340031Q�K�,�L��/Je(��`e�̂�n��l�*�9_L�@�1%1��4�$�9#���م!덖��3Wzl"t�Ե�.�~1��������`�8�ho�̜5���'p�^� �$�����U/7�a�XJT�ڔ�]����YjpA�L�H�-�I-f�s���;���!�}���$�6q@�I��/N-)-�+�dP~5K�n�ۏMv���W3����j-T\����Wf�z�{tJxy�l�=�~j� _eB��yx�kgjg��*�Z�P��H����E�^v̍�&�� � J�x340075UH�H,��IN�+�d`���YrϚ�5�RM�,���*��M. )�+���9�@����>g����f@WZ��X�
R�����;��rEiҺ+�gר�+.JO)t�;'�Ц�f?}sL2�mâ4��<�<Q��V�����?;��e�e����  ��S�� �:x�]��N�0�cH<p���/r�`$�l�%��G����o�ۥ���H|o������1;z���ߟo�f�������f(��(p	��Ƅ3��&�����ƶ�Ӈ[� �lM�A��ή�"g	A��#W���iY)`�(B^V���u7��
���k��q���mRdF�@�*B�47P8���n�#?�(��z�%�}��_h��4�Ӽ�*Nc� �}{�ߌ�\[�c���6��<�)�
�E���13�&r�ﳯ�ʺ8'ߡ�&��ϯ�n��ʏ<��Ux�;η�o�2k�B���De���O�RS �V��+'9%>�(55*bI�)M���ؼ�q)#3Ѐ�a��@�:
p]&H��]̽� %!�j�x�����o��F�'l  (�]x�S]o�0}^~ŝx�J(����>"V�u�u��T��ւ١-����N�ZM ��}|��񹳷����SʭVA�W�+r���jB�r6�t+�HK40�L�E� �oZ�(5,�-Vh���1�M�c�ƹH����ڔP��d������iB�,,,��x��j�������k��ٓ���@�� �[i�K!�h:�ȱ�gi��;ɦu*�X%v8�1����q��>�k����Ü����tb��-��=�3� G w�$��>��k����b�4l�f��Dݚr�uܕ�wG����G��W⨸�ꂘ�d]�_j��Ν��\�ג^�_1��~��u20����������1o]B~�b��y�K���(�vS���H=fL�� ��kϫ�P�t�n��Z)�X�V�R��m�[o�77Ϩ[,��~Fg�ng��Τ毚��ߤ]���^5�Tc���S��s�I���*��.e9�+��k����JX�r��X�2�X��6�(춡[}�8�0�Q���;�Vl��\&��U����E�:��5��M��Ԋ'�f�$��P��<!7��NΫ9_�{L����jcm ��&��j���S�1�%w������=m��������r����4x�[ɴ�i�(�HLӗ����i��-w���p �uf�x�340075UpLIL+*�,�w�H,�qv�+�d�%x˥$bI`"���nO-��Z#C3����<��x�2��E����gO������oA?� 2��;x�[ɴ�I�� ��3K2J���<��b����~�����ٮ���?�P�x�340031Q�u�q��qq��MaHv��uɞ���Z呇��V,�r� J9Xh�)x�[��δQ�� ���Tx�K �����=ȉ��P�{��Mg[-���,��QW���/uu� ��R5r���~Yl��7MU����	�i= �qK�c
�[P#3�Zx�kgjg��Y����+�Z=�=:%�<m��[?5� �r��x340031Q�K�,�L��/Je(��`e�̂�n��l�*�9_L�@�1%1��4�$�9#���م�dm���wZ�ݦ�J������
C��>�ή~����c�����̹P�;�~�����J�\]|]�rSv��D��M�� �-@/���f��Ԋ�܂��b����޽>�X�zu��#��>&�삚�Z_�ZRZ�WPɠ�j�v�޷��.���f;?w�Z�2��ϧ���j�|����ٚ{n�� �Jj0��zx�6 �����=j�*A��Ԍ<X,&'+N���QWK]�sC����;6���h�Ƒ�K</��x340075UH�H,��IN�+�d8����Z�51����m��Q�UY|nrH�t��%-~N�N�=��sۥo�mЕ�$���/N[%�jV|ګE�Y߯�iIϝ���(=	���%�6�'���O����w�����\��'M�\����t�Rw��֜�3  rZ>��(x�3 �����kZ�L����i8(�:�W��Fa!��Q ���ʺ������+���)x�6 �����=;H�1^M�]�V+��`��Q��QWK]�sC����;6���h�Ƒ�K0oͦx�340075UpLIL+*�,�w�H,�qv�+�dhy�{QFW��4�K���l|��o�oh``fb���TRv�7u��7�6��9bs��z�F� P�"��)��x�eQAk�@�����(�=�<�`\fS,�vi�Э���AP)��%��ę�i@ܳ���� �ы�����l���c�f����}��ǭ��;��|�&;�o���~{8������_<���	�+�/�*_#O��eL�b%5��t1��0�A
���R������G��d539ĕ6��;��&���t�ஔ�:�\V<�Kt�ԈB�"�i�w�:T��T�-K�A�*E���\65�R�Y��7�J8%�FV�4���MO��f������ j 7��O&u]�7����$��$O���J2�����K�]w��9+��N�R��4C��U����~�u3��R�����rp.k������1�W�����:|~�l�-���zt��뺩T��	PT8Y��Fwo�{���q�d��m/�L�x�*<ϳ?����t{=\�~y9�8��x�kgjg�`'����xeՊ�w�8��}\=1p ���x�340075UpLIL+*�,�w�H,�qv�+�d������������U�ZMW����(��g�ǃ��M�0�ͪ��g�؜�<��Q� �T#����Vx��=��������6뉖jL�tt�|@�mr��3�~�h�9��17 i0���x� ������a!��Q ���ʺ�������:��9x�;'�Yd�s=���KjZf^�BAf^�Br~^^jrIj�BI�BIF�����WNrJ|Q����z�E��:����@RL`P)�03��L�*`1R�B8%)19;'3=�螜�"�Ӡ� �L��nlzQ*�1�`�7�d	e YGAg�(�x�m��N�@�#��p1�<M�a�d�)��ы�hR��DCȲ,��vIwo}���=����0�=lg���������_*e`>�)S<�ހYH�?Y~��꺤�m��?�����/0�+%"�J���p��c.e����XV��CHb���h8�Vh4�!e�0��
�EL��N�[_O�M�Y�ŀ�<�L!v��q�铬�����@+��.v7��k�4@�2��5�m�7n�S�XD(�������\�.L#�c~�}hkp���I<!f��X�'>p��|Ff,��l
����0�8q�Q>�c�X�l�F$���W���z�g�.�K����	�}px�2������1f!����a�T���j��2������j��:�i�/e��x�340075UpLIL+*�,�w�H,�qv�+�dp���9WY<De��ϟWM)�640031Q����*�);蛺a��U���9�y\=d��? P�"����@x��=�����m'k:�O>��6���L?u4�a��  �P��;x�kgjg��Bd}���c/<��Pc(��&��;q�7 ˔>��x�;'�Ol���0�;��XD�7.��Gx�kgjg��B���M��\���$9S��/�&��{������mx�/ ����'100755 char_lcd.py S��d���7��V��un�b�'��C� �&x�]��N�0F�"1d��zQ�H	i�V��20���-r���jjWv�`���� �l�g@���7�|������������%(��	���Hp�� t����l�9}�c��k�=IR2�vA�X*8�%�!���D(s�`˲���B) A�9�Yw�=X7�E���{����W�۾U��h��Yi`�I�&
:45�M����4J����o	A��*��u`��]��{澭�{c��ͱ��^�io��ZǢp`�ޘ�Z����g}e]��D�q\G�����j�z:� ��Lx�kgjg��B��Z�%�ٌ���!f��;���L�� �z���x� �����>� ����F����׫��G��19�R��n��$x�6 �����=���: ��yY ��;ȑ=�QWf��ǣ/P�w�n�\U���-��Kh�Ŧx�340075UpLIL+*�,�w�H,�qv�+�d�s5�=��fn�t˭g��BnW���(��g�ǃ��M�0�ͪ��g�؜�<��Q� \N#&��Qx�3 ��������B�J�KYH���U�~����R��
��3�7#�R	���4r+��_x��'��{��AQj�BJfQjrIN�BI�BPbqARjQQ�B@�B~��SjbzN�S~^��SNbr��Ne׊�܂��ɾ�w�alM�Ez���\�
9�)��E��y
�
��0����T������,>���\� ��.A��nx�kgjg��B���{�#�>tM3�8ݐ0�3+ӳ�{��'�g�ux��ɸ�q��& -���+x�Y �����=?��8?������3���j�Q47�HGO��2��ou��Fl40000 examples L��riHRQ[�'�TJf�|��K�i&��hx�6 �����=���: ��yY ��;ȑ=�QW����XB�0��0hˀ`��摼K|y�f�7x�;���8� �z�x�340075UpLIL+*�,�w�H,�qv�+�dh>����=�Z�A�3]W��Y1���(��g�ǃ��M�0�ͪ��g�؜�<��Q� "�!����Xx��=��@3��,����l�˵�����(O�Za������l�;���SG��v�Y'�U�x�340031QH�H,��IN��M.�+�d8���Ǿ�n��-�u}����OZ�)-JO�/(�)�xyl]�"k���;��Ӿ� oj%N�x�340031Q��tv�ve0]k�7�mf΅����8l/_`Q����몗�°C����������n�/��ߍ% j�əx���K
1�9E_@��wDԍ����V��$F����oQ��E�Q_�\�Y���ض����F
y��z�,c
�,K�������\�G�Mk�y*��mʰ�#�2��]�߻o�CL����5T֒&D`�Q�vH�ȟ�:��0<��i���<?I#����i����KE�Xx�mT�r�0���ʏ��>�3�$e
Ϥ�ȣxC`��h�}�@J�W�n�����αP���J8���L%�]8+i�6Mr(���ҹ>��L�E��;�k�0`��ř��W�yb���$�ԕ>NS\��X��Igr�#�9��x�I�L�p ә$(�S�>7͎���rn!�+jnAM�7��G��d�{Z�u�����օ�%�ٯu��ɸ;酻���� �A:U]�TB�)��p�$y�r�	�@�@���l��!.�&����pk�RÈ��y$I���Y	�Jn��F�(�y�	)!z���X��\:_F�9+�����FUB��]�1˫u_8��y�z	j5j�����joB�0Q��!�wQ[~`և���JgIo�(��b�9C�����$�=��Xw&b�����W�k�n�t�rDx.l�	@VA��d������d��'�c�I,�hk�X5 �T�{�L�M�<G+y$>q:_�޺euC��b�{�ϖ};p;Brc����j���*�j��ܖ�m�[���G��2�ʘ4[bJ65y��t�S�X �M����r���k������}�}|;�w���~��/lE��q�������&��2��Z�����.��&������D1����Р�z�7QލXAvS�12Ϸ������l�]o	��X�*�o��C<��|�Z/d��fz���M�La���
��6x�;η�s�gRbrv�ML՝��1d���WNr��������cJbZQifI�sFbP�	�^C��KY!��(OdDNfzF�B~��lb��3�0I( AIfn�^qNjj�����&Hl�]VkܒZl�'_e�g2� h�0��M��8x�eS�n�@U-`���, ]��&��mڄ�AJ�$D��Y�xX{�X�3�3&������$�HY��X����?�������{�̹s�}���y��i��ra��B�1��l<��m�2E��W�<l����)��,V}4�m�bj~
ۜ`�ܚ���)l+����Yl�Ѫ�Xat"�K�����r}qq����ǚ.H3lud����I���$�#��XZZ����`��=�e�P���d}��@��6�H硗�Db��H���\dc�G=ˀ6/�cL �P���(*���i`�u� W���c:%��$�P�)Ð(PU�
��HÈ�ALh`fvI������N6����מI��,�):��=#�/s��Uzܶb�D�#�a��c��c�bc�P�W���W2����ˢ� �������\a�e�>�X[|���B���H]�wTm�U+��!��t����ɾ�	&!����7���R��D�xf��óh65p��z8#I�+��\�6j���~�\���.�ʕp�[^=��e��--��̏R����P߉�:�u���*�K��Zc�Y8j6B�XP`��]}T��]J~Pinl�rE�vm匘�U�G]��en~F�4qM����.C���ؚH�t�'�խ��v��t�ĳ�:���C�`��ZZLP�ӷK5d1,C�1i)8��ٺ��r�j�+x�u�Ko�0 ���
�Q&<�Ԯ
4BBi�47c�7$qLI����^w�2�'�4��1 �4�3�Lj"S�95l�f�
3�k&24;�Θ�^��Ьܲsf�BBD�EH�4l���� d�Kx剃�W���Lq·J<�S�@C����TTCU�o�UB0�JC��g���RT���Ċsq�
��G��c��	؆~������ƫK\�q=�ٸ�Efe�R7��Z_�x8:��q��Z1e�s�������@�_���'%�A�G֚i2v�P�n�ڧ�u���/��C[/��<T�`�8��>?��͹�	_���@x^g>�k�8����K�3��_�ٓ�O�_��w���]�'����*8��Q�����|��!�ǋ�ou��u$��:'����tX�h�ȻG�r2��8\�x4�S�>��U����_��$(w���j��&�~��U͸V]h�S67����nL\�Y�ɧ��djLn�%oe���4E]���1���V��Y��f������?&g���3L;��ò՚�+x�u��n�@ D�|E߭��R2J��ccBn�֐�����d�3u)�I%��h�e@TCNI��H|&���)R,�
�*�i�@�iq��(���,TE���g"L /�8WY(����9�g����M\L�/_?��S��cI����8I�A�d	<��2ߴ.)�z`�t3�����Y[-o����gFZ2�<��f��x�Ύ}@��780Z�!�����6V������O�xzgB(�8���d�7�G#�v$o�C<0  ���8��?k�X#�?z�Q�x-��X/Qt�a��N��pJw�mj�R�s�����i�D������|9�X�jAݬ4h�~Pm\k���q��ާ��Ñ����]5���i՗bl6m���K��.��f띐�9N��D%	;]�q���4\1���aY<�ủ�N���C:e�ޥ�k����;+����h�}1�_���7�π�]���UU�s�֙t�� a66�h���wh���F0c�f�%�C߼2�u9�יy0�m�	���&2��s��&��o�3x�u�Io�@���-�e�oR2�l�0�%j����&6��a2�m�]J�TU�z� �$SW@2�D6u]�b�	�: ���%�-\0���$5���L�P4IS��b��3�4"�8��T��o�b��m[���V��a[�����b[@T��o�T3b�+�^�/}�ٍ�i]�B��)�����^$]��'-)��Ј��-A�U��R��3�O��?��54C/��F�-F��G3g���/. �������g�.��N�~����?U淎Cƾ︣��j ��n�l�up��z88%p�󌶻��G���7s�w��Z��l����Ir�j�yE�bo�7\@S���I�i#�j���G�m�6�%�iE$�,f�_fp���p��E��h����^�M��Ɲ�aU��[k߳��;��rbj��.�F#p?�-Xd�Ĭ]���OA���6�z3kJ ���E��X����8C����^M��c�U��Z^׍�*��2�E}y}�u��+�8Ƙ;A���:�gя�,rﻕ+z�4Ob�M@o��	7�f�/&L�e�.��@�7h8�!k����s^�mr*2�����EA���H;A��f{�#�P�9����$�^q���x�31 ��̒��$��{�,&�_�v����z���ņf&&`%��y�E���yIy�.G���\�k��X�y�9�9�)�iE��%���E>�.��~�Զ�?�����y�oS��B��tv�ve0]k�7�mf΅����8l/_ U����몗��p��IQ�+�Ό��̹y;�5�@�L�H�-�I-f�}'9����,�B~�V�׵jNjU|qjIi�^A%��Y�u{�~l��Զ��Q���U0ep51M_Z�3�W�q�<��J�_��Y ̋vk�gx��Tˎ7��W�OI���@�Y�]	ZFNE�4�(��C���S��-�{�$�����]��f��?�z^Ͷ����������rKo�6���S������Վ�~yY�.p\���v��d�>��P-"�-)���H�>�g&����GJ�=\ �L.h)	�(pddM>�"#YNTNte��F�L��Omݕ�5��i�͑���@sd�iӤ��^�AQQ®:���N���5����{�Zq�����B"k�L�y��]�B�3���||��G+��
%QS���c���*��9�]��_UUww�=�K���8p��U�-[�VHɱU:�~�|�L��"�=�6� ��8�9�43B���G}��(z��PO��.������_��w�p�|���K!Ɛ7"��s��o�����G��Y���h\�`^��wpƸk�F��b+1U�/�*f�H�49r*�홶1-������l������2���}���}G�s��w�n7z��Y���7�_Y�2�7��}6�n�~|��(���~��ړ������d�]�qB�G�f8D�=�kw]�����O{?,ug��,��(�e������IiXP1�vB�)�ۙ�)��o�r�ޘ�goZ�Q!-O^�(X�q�pL��>��k� �"��.Z�6�0��ݑt
E!��<ٷm*iJ���Ʋ�k�>4n��i��U�����NtJ C��نz�hMb�XY�c*��j^V;�R��Pվ"��=����ϣPi��%�'I+]��5���UF���x����g���cJbZQif�B@eIF~��sFb����DG��arl �	��Tx� ���������᧗0��{.|��ٻ�Zp��n�_<\g-�-x��(|�kn��sH�tOc                                                                                          	   	   	   	   
   
   
   
                                                                                                                                                     #   $   $   $   $   %   %   %   %   &   &   &   &   '   )   )   *   *   *   +   ,   ,   -   .   /   /   /   0   0   0   0   0   0   2   2   3   3   3   4   4   5   6   6   7   7   7   7   8   9   ;   ;   ;   ;   ;   <   =   =   =   =   >   ?   ?   ?   ?   ?   ?   A   A   B   B   B   C   D   D   D   D   D   D   D   D   E   E   E   F   G   H   H   H   I   J   J   J   K   L   L   L   L   L   M   M   M   N   P   P   P   Q   R   S   S   S   V   V   V   V   W   Y   Z   [   \   \   \   \   \   \   \   ^   ^   ^   ^   _   _   _   b   c   d   d   e   e   g   h   h   h   i   i   i   j   k   k   k   m   m   m   m   n   n   n   n   n   o   o   p   p   r   r   r   s   s   s   t   u   v   w   xG�Į�U��Т,_/mR�P�i����|(�58_a���H�6Q��g���C�B�
�g�,��T6Ai�/qz�����FR��c���dI�[z���9�U9�ܡ?O�ͶOi���
�Qd�"zy�\��-Z�L����i8(�:�W�w���NB�ɯUɵI����=P1^���ֆ�Y��BhR�#�+~���>҆�{ϝ��)�q;�M�p,ҁ���$��3�*S�wy��r�O)�c��f1*�Mh�{9�&&�{���5�]2�V�l�|-���@�w�:��yAp	�G�#{�0%����;H�1^M�]�V+��`��Q�<$����bS$5V��W� f`?��8?������3���jA@�ߕkL��}�-��b�E��\�[�C�xub�ԇͬ%E�!b��	/�F2�*����\bG�UleXI�#T$����wKI���\R�ON��jsz����xJi�EW9'xÛ�z�����R�K]�sC����;6���h��L��riHRQ[�'�TJf�|MU����	�i= �qK�c
�[M����f]<��'�D��_mP[-P!t\9���5
��E0'�Q3��ȕ�'��"[mq{mLQC��W²�6�Mm`4� N�SX�Ʈ�!jE��o�f�qS�Ye�z2�A �X��I5��S��d���7��V��un�bT�ņ��r���N5��O�s/<X�����%WE����8��\��ki�xf	���O��`�s�o�~_�x��{��OK�a!��Q ���ʺ������aX?-S�jF9��G]��Ǳ�7cD������9*wY�^^�����f��ǣ/P�w�n�\U���-g(�*�%pB9�Z(A�^���i�ĺ�?��%�/�g�ss�j�*A��Ԍ<X,&'+N��k)�j�U\R���{��-��|n2�9�`��Y��%6i�tG��yz�x�	��=�yW[t�nÿ݀�F�%Û��L�v� ::[S�8>�C�z4�l�yЭ�+<_�O���S�d�q{d�b�^n��"���3�Z|x���M��S�Oz��q40��w~!��������WMAK�և���_��fb.B�o[�e�Ķ���O*kRI�E�uf:����ߖ邜̥���&?�=��-�-ܖ�s+�<Msﱿ�3nbn��YT��-4��C�Ί�l9���Pb/i�{g��=�E0H��<�m���P�T�x�o±������J����D�o�?���᧗0��{.|��ٻ�Zp���3g�/⣨��(�?է��0�iMᲈ�۰vm�U6	��1�Q�DtX�Qa;��I*Y}2��clO���;��ĖuN���f��_f�qj��.V*�����C)D�wW䉯�V����c��8e��Q���L�&���^)����Q-�s�� �i��Yd��r'YJ>�cЬ��: ��yY ��;ȑ=�^5�>����H8& t�^F�M������h+1�,~r���6��'���H�Q�|��
�̈���HGO��2��ou��Fl� y�L4u_�6���bdιdZV�d��P�P.o{|�
�u�҄vb@BO)܎{���η.�������Jj�bL,u����|��H��������U���&�sL�?K�j�/�r4�Me��쪱���<�	�'T� ���O��}&�|\��[0����'� ����F����׫��G��19�>䙁�FOϬ�Tv�~�ƣ�3,�yU��W�=-~��3����XB�0��0hˀ`���ȉ��P�{��Mg[-���,����t��_aDu��bcR��)�
8W"�gԖ�}yͯw�s�/�WE#��L��p�ʗ0Yf$ԈN��8�D^$ ��*�=׏�4r�E ,��7mn�(�׸��<Fi p&$�Di�;�׾9^[�eb޴צ�M����#��鲑�ҵ^�ci+���Lف�2�'��%��KV�bp��Z�:�Är\��SOp�x@�)��Ck�q����iw�-E�k ݙ�O3�5�/vE0��X4��ޙ�Z���%!1wM�J����e�u.kUPmw������B�d�	��"�ȅlV��.���=]��|�>���3��"�0BF��= ��h3����R��
��3�7#�R	���4���/uu� ��R5r���~Yl��r1i#e+�����1�z��J��kԚ�I����f�)���(V�y9N�*�h�N\�X�G����?�3����̆9Z�L�޶1��B�J�KYH���U�~���S���{ ��eL�
��x��R�Γ:�G�X �s��m|��w���F��*���)s����\����+T)�A��cp����r���au%Օ�č��al�fv���dt	��[Mj-�t���Oyb�V�a�D{�+�W�+�"�n
N.���s~�뛑B��S��.k<�MZ���7�,ٯ��6���$y�S��L��`!��-Y͞VE��`�u`�&�5��V��ʽ��^먷��d*!��j@�_�E!�8����G����g���D1��R�}*T^ƚ������>���)Ō���r���U�ۣ�+I��bp�s��`�0����1rU��U����4���l����7��o�1��4�F_�W#�E2bK�9�x��k�U�[X�5)@o �؊յg6����%L�S�yB�%0)W%Dz;o����_̵���bj�ȁ��iﮡMX��^�{}��nL���X�zC�Dō��(�v�x �sk��_�s��&�6������a��V1D�`��-�jcH���E`u7�O���� ��o���-�bay0(��wNꇧ@�*T-	^��ً�TT�    `3  �  o�    e4  �  8  Z�  �7  Dz  l  o�  ;~  1�  ~�  h#  w/  r|  m�  a�  sr  m�  ��  �  g�  s  Qz  p  �  �  a�  k9  e!  n�  3  7a  S}  �  =�  d�  �  p�  e�  \  W+  �  ^g  jz  md  V�  V�  tp  j�  �  9  r�  	�  h�  �  s�    B�  �K    E  W�  2�  k�  g�  6  r'  V�  pY  f�  q�  |�  rk  w�  T4     d,  :�  z�  Yd  Y�  2�  q�  e�  q�  dU  [+  ;  _`  	  �Y  jP  �  na  $  n7  aN  d�  e  ^  n  l  �  [   2  
�  [�  f�  �  p�  �  \�  �  _�  k\g-�-x��(|�kn��sH�vs�1k�UPO��89��#!/bin/sh
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
�
���[c           @   s�  d  Z  d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l Z d d l	 Z	 d d l
 Z
 d d l m Z y d d l m Z Wn e k
 r� d Z n Xd Z d Z d �  Z d d � Z d	 �  Z d
 �  Z e
 j d �  � Z d �  Z e e e j d d � Z d �  Z d �  Z d �  Z e e _ d �  Z  d �  Z! e! e  _ d �  Z" d �  Z# e# e" _ d �  Z$ d �  e$ _ d �  Z% e e e j d e% d � Z& d �  Z' d �  Z( d �  Z) e* d k r�e j+ e) �  � n  d S(   s�  Bootstrap setuptools installation

To use setuptools in your package's setup.py, include this
file in the same directory and add this to the top of your setup.py::

    from ez_setup import use_setuptools
    use_setuptools()

To require a specific version of setuptools, set a download
mirror, or use an alternate download directory, simply supply
the appropriate options to ``use_setuptools()``.

This file can also be run as a script to install or upgrade setuptools.
i����N(   t   log(   t	   USER_SITEs   3.5.1s5   https://pypi.python.org/packages/source/s/setuptools/c          G   s#   t  j f |  }  t j |  � d k S(   s/   
    Return True if the command succeeded.
    i    (   t   syst
   executablet
   subprocesst   call(   t   args(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _python_cmd%   s    c         C   sT   t  |  � �B t j d � t d d | � sJ t j d � t j d � d SWd  QXd  S(   Ns   Installing Setuptoolss   setup.pyt   installs-   Something went wrong during the installation.s   See the error message above.i   (   t   archive_contextR    t   warnR   (   t   archive_filenamet   install_args(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _install-   s    c      
   C   sk   t  | � �+ t j d | � t d d d d | � Wd  QXt j |  � t j j |  � sg t d � � n  d  S(   Ns   Building a Setuptools egg in %ss   setup.pys   -qt	   bdist_eggs
   --dist-dirs   Could not build the egg.(   R	   R    R
   R   t   ost   patht   existst   IOError(   t   eggR   t   to_dir(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt
   _build_egg8   s    c          C   s6   d t  j f d �  �  Y}  t t  j d � r2 t  j S|  S(   sL   
    Supplement ZipFile class to support context manager for Python 2.6
    t   ContextualZipFilec           B   s   e  Z d  �  Z d �  Z RS(   c         S   s   |  S(   N(    (   t   self(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt	   __enter__H   s    c         S   s   |  j  d  S(   N(   t   close(   R   t   typet   valuet	   traceback(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   __exit__J   s    (   t   __name__t
   __module__R   R   (    (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyR   G   s   	R   (   t   zipfilet   ZipFilet   hasattr(   R   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   get_zip_classC   s    c         c   s�   t  j �  } t j d | � t j �  } zw t j | � t �  |  � � } | j �  Wd  QXt j	 j
 | t j | � d � } t j | � t j d | � d  VWd  t j | � t j | � Xd  S(   Ns   Extracting in %si    s   Now working in %s(   t   tempfilet   mkdtempR    R
   R   t   getcwdt   chdirR#   t
   extractallR   t   joint   listdirt   shutilt   rmtree(   t   filenamet   tmpdirt   old_wdt   archivet   subdir(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyR	   P   s    "	c         C   s�   t  j j | d |  t j d t j d f � } t  j j | � sj t |  | | | � } t | | | � n  t j j d | � d t j	 k r� t j	 d =n  d d  l
 } | | _ d  S(   Ns   setuptools-%s-py%d.%d.eggi    i   t   pkg_resourcesi����(   R   R   R)   R   t   version_infoR   t   download_setuptoolsR   t   insertt   modulest
   setuptoolst   bootstrap_install_from(   t   versiont   download_baseR   t   download_delayR   R0   R7   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _do_downloadf   s    !	i   c   	      C   s!  t  j j | � } d	 } t t j � j | � } y d d  l } Wn! t k
 rc t	 |  | | | � SXy | j
 d |  � d  SWn� | j k
 r� t	 |  | | | � S| j k
 r} | r� t j d � j d | d |  � } t j j | � t j d � n  ~ t j d =t	 |  | | | � SXd  S(
   NR2   R7   i����s   setuptools>=sO  
                The required version of setuptools (>={version}) is not available,
                and can't be installed while this script is running. Please
                install a more recent version first, using
                'easy_install -U setuptools'.

                (Currently using {VC_err.args[0]!r})
                t   VC_errR9   i   (   R2   R7   (   R   R   t   abspatht   setR   R6   t   intersectionR2   t   ImportErrorR<   t   requiret   DistributionNotFoundt   VersionConflictt   textwrapt   dedentt   formatt   stderrt   writet   exit(	   R9   R:   R   R;   t   rep_modulest   importedR2   R=   t   msg(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   use_setuptoolsx   s(    c         C   sT   y t  j |  � Wn< t  j k
 rO t j | t j � rI t j | � n  �  n Xd S(   sm   
    Run the command to download target. If the command fails, clean up before
    re-raising the error.
    N(   R   t
   check_callt   CalledProcessErrorR   t   accesst   F_OKt   unlink(   t   cmdt   target(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _clean_check�   s    c         C   s9   t  j j | � } d d d t �  g } t | | � d S(   s�   
    Download the file at url to target using Powershell (which will validate
    trust). Raise an exception if the command cannot complete.
    t
   powershells   -CommandsC   (new-object System.Net.WebClient).DownloadFile(%(url)r, %(target)r)N(   R   R   R>   t   varsRV   (   t   urlRU   RT   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   download_file_powershell�   s
    c          C   s�   t  j �  d k r t Sd d d g }  t t j j d � } z6 y t j |  d | d | �Wn t	 k
 rn t SXWd  | j
 �  Xt S(   Nt   WindowsRW   s   -Commands	   echo testt   wbt   stdoutRH   (   t   platformt   systemt   Falset   openR   R   t   devnullR   RO   t	   ExceptionR   t   True(   RT   Rb   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   has_powershell�   s    	c         C   s&   d |  d d | g } t  | | � d  S(   Nt   curls   --silents   --output(   RV   (   RY   RU   RT   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   download_file_curl�   s    c          C   si   d d g }  t  t j j d � } z6 y t j |  d | d | �Wn t k
 rU t SXWd  | j �  Xt	 S(   NRf   s	   --versionR\   R]   RH   (
   Ra   R   R   Rb   R   RO   Rc   R`   R   Rd   (   RT   Rb   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   has_curl�   s    	c         C   s&   d |  d d | g } t  | | � d  S(   Nt   wgets   --quiets   --output-document(   RV   (   RY   RU   RT   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   download_file_wget�   s    c          C   si   d d g }  t  t j j d � } z6 y t j |  d | d | �Wn t k
 rU t SXWd  | j �  Xt	 S(   NRi   s	   --versionR\   R]   RH   (
   Ra   R   R   Rb   R   RO   Rc   R`   R   Rd   (   RT   Rb   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   has_wget�   s    	c         C   s�   y d d l  m } Wn! t k
 r7 d d l m } n Xd } } z8 | |  � } | j �  } t | d � } | j | � Wd | r� | j �  n  | r� | j �  n  Xd S(   sa   
    Use Python to download the file, even though it cannot authenticate the
    connection.
    i����(   t   urlopenR\   N(	   t   urllib.requestRl   RA   t   urllib2t   Nonet   readRa   RI   R   (   RY   RU   Rl   t   srct   dstt   data(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   download_file_insecure�   s    
c           C   s   t  S(   N(   Rd   (    (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   <lambda>�   s    c          C   s7   t  t t t g }  x |  D] } | j �  r | Sq Wd  S(   N(   RZ   Rg   Rj   Rt   t   viable(   t   downloaderst   dl(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   get_best_downloader�   s    	c   	      C   s�   t  j j | � } d |  } | | } t  j j | | � } t  j j | � sv t j d | � | �  } | | | � n  t  j j | � S(   s  
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
    s   --user(   t   user_install(   t   options(    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _build_install_args"  s    c          C   s�   t  j �  }  |  j d d d d d d t d d �|  j d	 d d
 d d d t d d �|  j d d d d d d d �  d t d d �|  j d d d d t �|  j �  \ } } | S(   s,   
    Parse the command line for options
    s   --usert   destR�   t   actiont
   store_truet   defaultt   helps;   install in user site package (requires Python 2.6 or later)s   --download-baseR:   t   metavart   URLs=   alternative URL from where to download the setuptools packages
   --insecureR|   t   store_constt   constc           S   s   t  S(   N(   Rt   (    (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyRu   6  s    s'   Use internal, non-validating downloaders	   --versions!   Specify which version to download(   t   optparset   OptionParsert
   add_optionR`   t   DEFAULT_URLRy   t   DEFAULT_VERSIONt
   parse_args(   t   parserR�   R   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   _parse_args(  s"    c          C   s@   t  �  }  t d |  j d |  j d |  j � } t | t |  � � S(   s-   Install or upgrade setuptools and EasyInstallR9   R:   R|   (   R�   R4   R9   R:   R|   R   R�   (   R�   R0   (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   mainA  s    			t   __main__(    (,   t   __doc__R   R+   R   R$   R    R�   R   R^   RE   t
   contextlibt	   distutilsR    t   siteR   RA   Ro   R�   R�   R   R   R   R#   t   contextmanagerR	   R<   t   curdirRN   RV   RZ   Re   Rv   Rg   Rh   Rj   Rk   Rt   Ry   R4   R�   R�   R�   R   RJ   (    (    (    s7   /home/pi/src/python/Adafruit_Python_CharLCD/ez_setup.pyt   <module>   sZ   
																			
�
���[c           @   s   d  d l  Td S(   i   (   t   *N(   t   Adafruit_CharLCD(    (    (    sH   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/__init__.pyt   <module>   s    
���[    �               @   s   d  d l  Td S)�   )�*N)�Adafruit_CharLCD� r   r   �H/home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/__init__.py�<module>   s    
���[QQ  �               @   s�  d  d l  Z  d  d l Z d  d l j Z d  d l j Z d  d l j	 Z	 d Z
 d Z d Z d Z d Z d Z d Z d	 Z d  Z d Z d Z d  Z d Z d  Z d Z d  Z d Z d  Z d Z d  Z d Z d  Z d Z  d  Z! d Z" d  Z# d Z$ d  Z% d Z& d Z' d Z( d Z) d Z* d Z+ d Z, d Z- d Z. d Z/ d Z0 d  Z1 d Z2 d Z3 d Z4 d Z5 d Z6 d Z7 d Z8 d Z9 d Z: d Z; d Z< Gd d �  d e= � Z> Gd d �  d e> � Z? Gd d �  d e? � Z@ Gd d �  d e> � ZA d S) �    N�   �   �   �   �   �    �@   �   �   �T   �   �   �   �   �   �
   �	   �   �   �   �   c               @   s  e  Z d  Z d Z d d d e j �  e j �  d d d � Z d d	 �  Z	 d
 d �  Z
 d d �  Z d d �  Z d d �  Z d d �  Z d d �  Z d d �  Z d d �  Z d d �  Z d d �  Z d d �  Z d  d! �  Z d d" d# � Z d$ d% �  Z d& d' �  Z d( d) �  Z d* d+ �  Z d S),�Adafruit_CharLCDzFClass to represent and interact with an HD44780 character LCD display.NTFg      �?c             C   s�  | |  _  | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ |	 |  _	 | |  _
 | |  _ |
 |  _ x3 | | | | | | f D] } | j | t j � q� W|	 d k	 r| r� | j |	 |  j | � � n6 | j |	 t j � | j |	 | r|  j n |  j � |  j d � |  j d � t t Bt B|  _ t t Bt Bt B|  _ t t B|  _ |  j t  |  j B� |  j t! |  j B� |  j t" |  j B� |  j# �  d S)a�  Initialize the LCD.  RS, EN, and D4...D7 parameters should be the pins
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
        N�3   �2   )$�_cols�_lines�_gpio�_rs�_en�_d4�_d5�_d6�_d7�
_backlight�_pwm_enabled�_pwm�_blpol�setup�GPIO�OUT�start�_pwm_duty_cycle�output�write8�LCD_DISPLAYON�LCD_CURSOROFF�LCD_BLINKOFF�displaycontrol�LCD_4BITMODE�	LCD_1LINE�	LCD_2LINE�LCD_5x8DOTSZdisplayfunction�LCD_ENTRYLEFT�LCD_ENTRYSHIFTDECREMENT�displaymode�LCD_DISPLAYCONTROL�LCD_FUNCTIONSET�LCD_ENTRYMODESET�clear)�self�rs�en�d4�d5�d6�d7�cols�lines�	backlight�invert_polarity�
enable_pwm�gpio�pwmZinitial_backlight�pin� rL   �P/home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.py�__init__e   s:    "												
#zAdafruit_CharLCD.__init__c             C   s   |  j  t � |  j d � d S)z?Move the cursor back to its home (first line and first column).i�  N)r-   �LCD_RETURNHOME�_delay_microseconds)r=   rL   rL   rM   �home�   s    zAdafruit_CharLCD.homec             C   s   |  j  t � |  j d � d S)zClear the LCD.i�  N)r-   �LCD_CLEARDISPLAYrP   )r=   rL   rL   rM   r<   �   s    zAdafruit_CharLCD.clearc             C   s9   | |  j  k r |  j  d } |  j t | t | B� d S)z7Move the cursor to an explicit column and row position.r   N)r   r-   �LCD_SETDDRAMADDR�LCD_ROW_OFFSETS)r=   �col�rowrL   rL   rM   �
set_cursor�   s    zAdafruit_CharLCD.set_cursorc             C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  B� d S)z=Enable or disable the display.  Set enable to True to enable.N)r1   r.   r-   r9   )r=   �enablerL   rL   rM   �enable_display�   s    zAdafruit_CharLCD.enable_displayc             C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  B� d S)z:Show or hide the cursor.  Cursor is shown if show is True.N)r1   �LCD_CURSORONr-   r9   )r=   �showrL   rL   rM   �show_cursor�   s    zAdafruit_CharLCD.show_cursorc             C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  B� d S)zFTurn on or off cursor blinking.  Set blink to True to enable blinking.N)r1   �LCD_BLINKONr-   r9   )r=   �blinkrL   rL   rM   r^   �   s    zAdafruit_CharLCD.blinkc             C   s   |  j  t t Bt B� d S)zMove display left one position.N)r-   �LCD_CURSORSHIFT�LCD_DISPLAYMOVE�LCD_MOVELEFT)r=   rL   rL   rM   �	move_left�   s    zAdafruit_CharLCD.move_leftc             C   s   |  j  t t Bt B� d S)z Move display right one position.N)r-   r_   r`   �LCD_MOVERIGHT)r=   rL   rL   rM   �
move_right�   s    zAdafruit_CharLCD.move_rightc             C   s'   |  j  t O_  |  j t |  j  B� d S)z!Set text direction left to right.N)r8   r6   r-   r;   )r=   rL   rL   rM   �set_left_to_right�   s    z"Adafruit_CharLCD.set_left_to_rightc             C   s(   |  j  t M_  |  j t |  j  B� d S)z!Set text direction right to left.N)r8   r6   r-   r;   )r=   rL   rL   rM   �set_right_to_left�   s    z"Adafruit_CharLCD.set_right_to_leftc             C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  B� d S)z}Autoscroll will 'right justify' text from the cursor if set True,
        otherwise it will 'left justify' the text.
        N)r8   �LCD_ENTRYSHIFTINCREMENTr-   r;   )r=   �
autoscrollrL   rL   rM   rh   �   s    zAdafruit_CharLCD.autoscrollc             C   s�   d } xs | D]k } | d k rb | d 7} |  j  t @d k rB d n
 |  j d } |  j | | � q |  j t | � d � q Wd S)z<Write text to display.  Note that text can include newlines.r   �
r   TN)r8   r6   r   rW   r-   �ord)r=   �text�line�charrU   rL   rL   rM   �message�   s    
&zAdafruit_CharLCD.messagec             C   sg   |  j  d k	 rc |  j r: |  j j |  j  |  j | � � n) |  j j |  j  | rX |  j n |  j � d S)a%  Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.
        N)r#   r$   r%   �set_duty_cycler+   r   r,   r&   )r=   rF   rL   rL   rM   �set_backlight  s    	"zAdafruit_CharLCD.set_backlightc          
   C   s  |  j  d � |  j j |  j | � |  j j |  j | d ?d @d k |  j | d ?d @d k |  j | d ?d @d k |  j | d ?d @d k i � |  j	 �  |  j j |  j | d @d k |  j | d ?d @d k |  j | d ?d @d k |  j | d	 ?d @d k i � |  j	 �  d
 S)z�Write 8-bit value in character or data mode.  Value should be an int
        value from 0-255, and char_mode is True if character data or False if
        non-character data (default).
        i�  r   r   r   r   r   r   r   r   N)
rP   r   r,   r   �output_pinsr   r    r!   r"   �_pulse_enable)r=   �value�	char_moderL   rL   rM   r-     s     
zAdafruit_CharLCD.write8c             C   sQ   | d M} |  j  t | d >B� x+ t d � D] } |  j  | | d d �q, Wd S)au  Fill one of the first 8 CGRAM locations with custom characters.
        The location parameter should be between 0 and 7 and pattern should
        provide an array of 8 bytes containing the pattern. E.g. you can easyly
        design your custom character at http://www.quinapalus.com/hd44780udg.html
        To show your custom character use eg. lcd.message('')
        r   r   r   rt   TN)r-   �LCD_SETCGRAMADDR�range)r=   �location�pattern�irL   rL   rM   �create_char$  s    
zAdafruit_CharLCD.create_charc             C   s1   t  j  �  | d } x t  j  �  | k  r, q Wd  S)Ng    ��.A)�time)r=   Zmicroseconds�endrL   rL   rM   rP   1  s    z$Adafruit_CharLCD._delay_microsecondsc             C   sm   |  j  j |  j d � |  j d � |  j  j |  j d � |  j d � |  j  j |  j d � |  j d � d  S)NFr   T)r   r,   r   rP   )r=   rL   rL   rM   rr   7  s    zAdafruit_CharLCD._pulse_enablec             C   s!   d | } |  j  s d | } | S)Ng      Y@)r&   )r=   Z	intensityrL   rL   rM   r+   @  s    
	
z Adafruit_CharLCD._pwm_duty_cycle)�__name__�
__module__�__qualname__�__doc__r(   �get_platform_gpio�PWM�get_platform_pwmrN   rQ   r<   rW   rY   r\   r^   rb   rd   re   rf   rh   rn   rp   r-   rz   rP   rr   r+   rL   rL   rL   rM   r   b   s2   		C
	r   c                   ss   e  Z d  Z d Z e j �  d d e j �  d �  f d d � Z d d �  Z	 d	 d
 �  Z
 d d �  Z d d �  Z �  S)�Adafruit_RGBCharLCDz`Class to represent and interact with an HD44780 character LCD display with
    an RGB backlight.TF�      �?c                s  t  t |  � j | | | | | | | | d | d d d | d | d | �|	 |  _ |
 |  _ | |  _ | r� |  j | � \ } } } | j |	 | � | j |
 | � | j | | � nR | j |	 t	 j
 � | j |
 t	 j
 � | j | t	 j
 � |  j j |  j | � � d S)a  Initialize the LCD with RGB backlight.  RS, EN, and D4...D7 parameters 
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
        rH   rF   NrG   rI   rJ   )�superr�   rN   �_red�_green�_blue�_rgb_to_duty_cycler*   r'   r(   r)   r   rq   �_rgb_to_pins)r=   r>   r?   r@   rA   rB   rC   rD   rE   �red�green�bluerI   rG   rH   rJ   Zinitial_color�rdc�gdc�bdc)�	__class__rL   rM   rN   M  s(    !			zAdafruit_RGBCharLCD.__init__c             C   s   | \ } } } t  d t d | � � } t  d t d | � � } t  d t d | � � } |  j | � |  j | � |  j | � f S)Ng        g      �?)�max�minr+   )r=   �rgbr�   r�   r�   rL   rL   rM   r�   �  s    z&Adafruit_RGBCharLCD._rgb_to_duty_cyclec             C   sg   | \ } } } |  j  | r$ |  j n |  j |  j | r@ |  j n |  j |  j | r\ |  j n |  j i S)N)r�   r&   r�   r�   )r=   r�   r�   r�   r�   rL   rL   rM   r�   �  s    z Adafruit_RGBCharLCD._rgb_to_pinsc             C   s�   |  j  ro |  j | | | f � \ } } } |  j j |  j | � |  j j |  j | � |  j j |  j | � nd |  j j |  j | r� |  j	 n |  j	 |  j | r� |  j	 n |  j	 |  j | r� |  j	 n |  j	 i � d S)z�Set backlight color to provided red, green, and blue values.  If PWM
        is enabled then color components can be values from 0.0 to 1.0, otherwise
        components should be zero for off and non-zero for on.
        N)
r$   r�   r%   ro   r�   r�   r�   r   rq   r&   )r=   r�   r�   r�   r�   r�   r�   rL   rL   rM   �	set_color�  s    	!%zAdafruit_RGBCharLCD.set_colorc             C   s   |  j  | | | � d S)as  Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.  On an RGB display this
        function will set the backlight to all white.
        N)r�   )r=   rF   rL   rL   rM   rp   �  s    z!Adafruit_RGBCharLCD.set_backlight)r�   r�   r�   )r}   r~   r   r�   r(   r�   r�   r�   rN   r�   r�   r�   rp   rL   rL   )r�   rM   r�   I  s   		.r�   c                   sF   e  Z d  Z d Z d e j �  d d �  f d d � Z d d �  Z �  S)	�Adafruit_CharLCDPlatezVClass to represent and interact with an Adafruit Raspberry Pi character
    LCD plate.r   r   r   c                s�   t  j d | d | � |  _ |  j j t t j � |  j j t t j � xF t	 t
 t t t f D]/ } |  j j | t j � |  j j | d � q] Wt t |  � j t t t t t t | | t t t d d d |  j �d S)a  Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        �address�busnumTrH   FrI   N)�MCPZMCP23017�_mcpr'   �LCD_PLATE_RWr(   r)   r,   �LOW�SELECT�RIGHT�DOWN�UP�LEFT�INZpullupr�   r�   rN   �LCD_PLATE_RS�LCD_PLATE_EN�LCD_PLATE_D4�LCD_PLATE_D5�LCD_PLATE_D6�LCD_PLATE_D7�LCD_PLATE_RED�LCD_PLATE_GREEN�LCD_PLATE_BLUE)r=   r�   r�   rD   rE   �button)r�   rL   rM   rN   �  s    zAdafruit_CharLCDPlate.__init__c             C   sF   | t  t t t t t f � k r- t d � � |  j j | � t	 j
 k S)z?Return True if the provided button is pressed, False otherwise.z9Unknown button, must be SELECT, RIGHT, DOWN, UP, or LEFT.)�setr�   r�   r�   r�   r�   �
ValueErrorr�   �inputr(   r�   )r=   r�   rL   rL   rM   �
is_pressed�  s    !z Adafruit_CharLCDPlate.is_pressed)r}   r~   r   r�   �I2C�get_default_busrN   r�   rL   rL   )r�   rM   r�   �  s   $r�   c                   s:   e  Z d  Z d Z d e j �  d d �  f d d � Z �  S)�Adafruit_CharLCDBackpackzVClass to represent and interact with an Adafruit I2C / SPI
    LCD backpack using I2C.r   r   r   c                s\   t  j d | d | � |  _ t t |  � j t t t t	 t
 t | | t d d d |  j �	d S)a  Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        r�   r�   rH   FrI   N)r�   ZMCP23008r�   r�   r�   rN   �LCD_BACKPACK_RS�LCD_BACKPACK_EN�LCD_BACKPACK_D4�LCD_BACKPACK_D5�LCD_BACKPACK_D6�LCD_BACKPACK_D7�LCD_BACKPACK_LITE)r=   r�   r�   rD   rE   )r�   rL   rM   rN   �  s    z!Adafruit_CharLCDBackpack.__init__)r}   r~   r   r�   r�   r�   rN   rL   rL   )r�   rM   r�   �  s   r�   )r   r   r
   r   )Br{   ZAdafruit_GPIOr(   ZAdafruit_GPIO.I2Cr�   ZAdafruit_GPIO.MCP230xxZMCP230xxr�   ZAdafruit_GPIO.PWMr�   rR   rO   r;   r9   r_   r:   ru   rS   ZLCD_ENTRYRIGHTr6   rg   r7   r.   ZLCD_DISPLAYOFFrZ   r/   r]   r0   r`   ZLCD_CURSORMOVErc   ra   ZLCD_8BITMODEr2   r4   r3   ZLCD_5x10DOTSr5   rT   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   r�   �objectr   r�   r�   r�   rL   rL   rL   rM   �<module>   sv   �e from .Adafruit_CharLCD import *
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
            cols, lines, LCD_BACKPACK_LITE, enable_pwm=False, gpio=self._mcp)�
���[c           @   s�  d  d l  Z  d  d l Z d  d l j Z d  d l j Z d  d l j	 Z	 d Z
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
 Z1 d Z2 d Z3 d Z4 d Z5 d Z6 d Z7 d Z8 d Z9 d Z: d Z; d Z< d e= f d �  �  YZ> d e> f d �  �  YZ? d e? f d �  �  YZ@ d e> f d �  �  YZA d S(!   i����Ni   i   i   i   i   i    i@   i�   i    i   iT   i   i   i   i   i   i
   i	   i   i   i   i   t   Adafruit_CharLCDc           B   s�   e  Z d  Z d e e e j �  e j	 �  d d � Z
 d �  Z d �  Z d �  Z d �  Z d �  Z d �  Z d	 �  Z d
 �  Z d �  Z d �  Z d �  Z d �  Z d �  Z e d � Z d �  Z d �  Z d �  Z d �  Z RS(   sF   Class to represent and interact with an HD44780 character LCD display.g      �?c         C   s�  | |  _  | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ | |  _ |	 |  _	 | |  _
 | |  _ |
 |  _ x3 | | | | | | f D] } | j | t j � q� W|	 d k	 r| r� | j |	 |  j | � � q| j |	 t j � | j |	 | r|  j n |  j � n  |  j d � |  j d � t t Bt B|  _ t t Bt Bt B|  _ t t B|  _  |  j t! |  j B� |  j t" |  j B� |  j t# |  j  B� |  j$ �  d S(   s�  Initialize the LCD.  RS, EN, and D4...D7 parameters should be the pins
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
&c         C   s   |  j  t � |  j d � d S(   s?   Move the cursor back to its home (first line and first column).i�  N(   R   t   LCD_RETURNHOMEt   _delay_microseconds(   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   home�   s    c         C   s   |  j  t � |  j d � d S(   s   Clear the LCD.i�  N(   R   t   LCD_CLEARDISPLAYR8   (   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR%   �   s    c         C   s<   | |  j  k r |  j  d } n  |  j t | t | B� d S(   s7   Move the cursor to an explicit column and row position.i   N(   R   R   t   LCD_SETDDRAMADDRt   LCD_ROW_OFFSETS(   R&   t   colt   row(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt
   set_cursor�   s    c         C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  B� d S(   s=   Enable or disable the display.  Set enable to True to enable.N(   R   R   R   R"   (   R&   t   enable(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   enable_display�   s    c         C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  B� d S(   s:   Show or hide the cursor.  Cursor is shown if show is True.N(   R   t   LCD_CURSORONR   R"   (   R&   t   show(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   show_cursor�   s    c         C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  B� d S(   sF   Turn on or off cursor blinking.  Set blink to True to enable blinking.N(   R   t   LCD_BLINKONR   R"   (   R&   t   blink(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRF   �   s    c         C   s   |  j  t t Bt B� d S(   s   Move display left one position.N(   R   t   LCD_CURSORSHIFTt   LCD_DISPLAYMOVEt   LCD_MOVELEFT(   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt	   move_left�   s    c         C   s   |  j  t t Bt B� d S(   s    Move display right one position.N(   R   RG   RH   t   LCD_MOVERIGHT(   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt
   move_right�   s    c         C   s'   |  j  t O_  |  j t |  j  B� d S(   s!   Set text direction left to right.N(   R!   R   R   R$   (   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   set_left_to_right�   s    c         C   s(   |  j  t M_  |  j t |  j  B� d S(   s!   Set text direction right to left.N(   R!   R   R   R$   (   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   set_right_to_left�   s    c         C   s@   | r |  j  t O_  n |  j  t M_  |  j t |  j  B� d S(   s}   Autoscroll will 'right justify' text from the cursor if set True,
        otherwise it will 'left justify' the text.
        N(   R!   t   LCD_ENTRYSHIFTINCREMENTR   R$   (   R&   t
   autoscroll(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRP   �   s    c         C   s�   d } xs | D]k } | d k rb | d 7} |  j  t @d k rB d n
 |  j d } |  j | | � q |  j t | � t � q Wd S(   s<   Write text to display.  Note that text can include newlines.i    s   
i   N(   R!   R   R   R?   R   t   ordt   True(   R&   t   textt   linet   charR=   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   message�   s    
&c         C   sj   |  j  d k	 rf |  j r: |  j j |  j  |  j | � � qf |  j j |  j  | rX |  j n |  j � n  d S(   s%  Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.
        N(	   R
   R   R   R   t   set_duty_cycleR   R   R   R   (   R&   R/   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   set_backlight  s    	"c         C   s  |  j  d � |  j j |  j | � |  j j i | d ?d @d k |  j 6| d ?d @d k |  j 6| d ?d @d k |  j 6| d ?d @d k |  j 6� |  j	 �  |  j j i | d @d k |  j 6| d ?d @d k |  j 6| d ?d @d k |  j 6| d	 ?d @d k |  j 6� |  j	 �  d
 S(   s�   Write 8-bit value in character or data mode.  Value should be an int
        value from 0-255, and char_mode is True if character data or False if
        non-character data (default).
        i�  i   i   i    i   i   i   i   i   N(
   R8   R   R   R   t   output_pinsR   R   R   R	   t   _pulse_enable(   R&   t   valuet	   char_mode(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR     s    $
 c         C   sQ   | d M} |  j  t | d >B� x+ t d � D] } |  j  | | d t �q, Wd S(   su  Fill one of the first 8 CGRAM locations with custom characters.
        The location parameter should be between 0 and 7 and pattern should
        provide an array of 8 bytes containing the pattern. E.g. you can easyly
        design your custom character at http://www.quinapalus.com/hd44780udg.html
        To show your custom character use eg. lcd.message('')
        i   i   i   R\   N(   R   t   LCD_SETCGRAMADDRt   rangeRR   (   R&   t   locationt   patternt   i(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   create_char$  s    
c         C   s1   t  j  �  | d } x t  j  �  | k  r, q Wd  S(   Ng    ��.A(   t   time(   R&   t   microsecondst   end(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR8   1  s    c         C   sm   |  j  j |  j t � |  j d � |  j  j |  j t � |  j d � |  j  j |  j t � |  j d � d  S(   Ni   (   R   R   R   t   FalseR8   RR   (   R&   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRZ   7  s    c         C   s$   d | } |  j  s  d | } n  | S(   Ng      Y@(   R   (   R&   t	   intensity(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR   @  s    
	N(   t   __name__t
   __module__t   __doc__R   RR   Rf   R   t   get_platform_gpiot   PWMt   get_platform_pwmR6   R9   R%   R?   RA   RD   RF   RJ   RL   RM   RN   RP   RV   RX   R   Rb   R8   RZ   R   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR    b   s2   		C											
						t   Adafruit_RGBCharLCDc           B   sV   e  Z d  Z e j �  e e e j �  d d � Z	 d �  Z
 d �  Z d �  Z d �  Z RS(   s`   Class to represent and interact with an HD44780 character LCD display with
    an RGB backlight.g      �?c         C   s  t  t |  � j | | | | | | | | d | d d d | d | d | �|	 |  _ |
 |  _ | |  _ | r� |  j | � \ } } } | j |	 | � | j |
 | � | j | | � nR | j	 |	 t
 j � | j	 |
 t
 j � | j	 | t
 j � |  j j |  j | � � d S(   s  Initialize the LCD with RGB backlight.  RS, EN, and D4...D7 parameters 
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
        R1   R/   R0   R2   R3   N(   t   superRn   R6   R   t   _redt   _greent   _bluet   _rgb_to_duty_cycleR   R   R   R   R   RY   t   _rgb_to_pins(   R&   R'   R(   R)   R*   R+   R,   R-   R.   t   redt   greent   blueR2   R0   R1   R3   t   initial_colort   rdct   gdct   bdc(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR6   M  s(    !			c         C   s   | \ } } } t  d t d | � � } t  d t d | � � } t  d t d | � � } |  j | � |  j | � |  j | � f S(   Ng        g      �?(   t   maxt   minR   (   R&   t   rgbRu   Rv   Rw   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRs   �  s    c         C   sj   | \ } } } i | r! |  j  n |  j  |  j 6| r> |  j  n |  j  |  j 6| r[ |  j  n |  j  |  j 6S(   N(   R   Rp   Rq   Rr   (   R&   R~   Ru   Rv   Rw   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRt   �  s     c         C   s�   |  j  ro |  j | | | f � \ } } } |  j j |  j | � |  j j |  j | � |  j j |  j | � ng |  j j i | r� |  j	 n |  j	 |  j 6| r� |  j	 n |  j	 |  j 6| r� |  j	 n |  j	 |  j 6� d S(   s�   Set backlight color to provided red, green, and blue values.  If PWM
        is enabled then color components can be values from 0.0 to 1.0, otherwise
        components should be zero for off and non-zero for on.
        N(
   R   Rs   R   RW   Rp   Rq   Rr   R   RY   R   (   R&   Ru   Rv   Rw   Ry   Rz   R{   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt	   set_color�  s    	!)c         C   s   |  j  | | | � d S(   ss  Enable or disable the backlight.  If PWM is not enabled (default), a
        non-zero backlight value will turn on the backlight and a zero value will
        turn it off.  If PWM is enabled, backlight can be any value from 0.0 to
        1.0, with 1.0 being full intensity backlight.  On an RGB display this
        function will set the backlight to all white.
        N(   R   (   R&   R/   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRX   �  s    (   g      �?g      �?g      �?(   Rh   Ri   Rj   R   Rk   RR   Rf   Rl   Rm   R6   Rs   Rt   R   RX   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyRn   I  s   		.			t   Adafruit_CharLCDPlatec           B   s2   e  Z d  Z d e j �  d d d � Z d �  Z RS(   sV   Class to represent and interact with an Adafruit Raspberry Pi character
    LCD plate.i    i   i   c         C   s�   t  j d | d | � |  _ |  j j t t j � |  j j t t j � xF t	 t
 t t t f D]/ } |  j j | t j � |  j j | t � q] Wt t |  � j t t t t t t | | t t t d t d |  j �d S(   s  Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        t   addresst   busnumR1   R2   N(   t   MCPt   MCP23017t   _mcpR   t   LCD_PLATE_RWR   R   R   t   LOWt   SELECTt   RIGHTt   DOWNt   UPt   LEFTt   INt   pullupRR   Ro   R�   R6   t   LCD_PLATE_RSt   LCD_PLATE_ENt   LCD_PLATE_D4t   LCD_PLATE_D5t   LCD_PLATE_D6t   LCD_PLATE_D7t   LCD_PLATE_REDt   LCD_PLATE_GREENt   LCD_PLATE_BLUERf   (   R&   R�   R�   R-   R.   t   button(    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR6   �  s    c         C   sI   | t  t t t t t f � k r0 t d � � n  |  j j | � t	 j
 k S(   s?   Return True if the provided button is pressed, False otherwise.s9   Unknown button, must be SELECT, RIGHT, DOWN, UP, or LEFT.(   t   setR�   R�   R�   R�   R�   t
   ValueErrorR�   t   inputR   R�   (   R&   R�   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt
   is_pressed�  s    !(   Rh   Ri   Rj   t   I2Ct   get_default_busR6   R�   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR�   �  s   t   Adafruit_CharLCDBackpackc           B   s)   e  Z d  Z d e j �  d d d � Z RS(   sV   Class to represent and interact with an Adafruit I2C / SPI
    LCD backpack using I2C.i    i   i   c         C   s\   t  j d | d | � |  _ t t |  � j t t t t	 t
 t | | t d t d |  j �	d S(   s  Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        R�   R�   R1   R2   N(   R�   t   MCP23008R�   Ro   R�   R6   t   LCD_BACKPACK_RSt   LCD_BACKPACK_ENt   LCD_BACKPACK_D4t   LCD_BACKPACK_D5t   LCD_BACKPACK_D6t   LCD_BACKPACK_D7t   LCD_BACKPACK_LITERf   (   R&   R�   R�   R-   R.   (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR6   �  s    (   Rh   Ri   Rj   R�   R�   R6   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyR�   �  s   (   i    i@   i   iT   (B   Rc   t   Adafruit_GPIOR   t   Adafruit_GPIO.I2CR�   t   Adafruit_GPIO.MCP230xxt   MCP230xxR�   t   Adafruit_GPIO.PWMRl   R:   R7   R$   R"   RG   R#   R]   R;   t   LCD_ENTRYRIGHTR   RO   R    R   t   LCD_DISPLAYOFFRB   R   RE   R   RH   t   LCD_CURSORMOVERK   RI   t   LCD_8BITMODER   R   R   t   LCD_5x10DOTSR   R<   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   R�   t   objectR    Rn   R�   R�   (    (    (    sP   /home/pi/src/python/Adafruit_Python_CharLCD/Adafruit_CharLCD/Adafruit_CharLCD.pyt   <module>   sv   �e dist/
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
