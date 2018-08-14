from __future__ import unicode_literals
from time import sleep
import pyttsx3
import csv
import wave, pyaudio, os, contextlib
import regex as re
import RPi.GPIO as GPIO
import subprocess
import Adafruit_ADS1x15

# for the button
but_pin = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(but_pin, GPIO.IN)
print("Voiceshell starting...")

# for the volume pot
adc = Adafruit_ADS1x15.ADS1015()
GAIN = 1

# for the power switch
pwr_pin = 13
GPIO.setup(pwr_pin, GPIO.IN)

# for the proximity sensor
prox_pin = 5
GPIO.setup(prox_pin, GPIO.IN)


class PlaybackEngine():
    def __init__(self, volume=35):
        """
        Object init function

        INPUTS
        --------------------
        volume  - Int   - The volume level to set alsamixer to
        """
        # the chunk is basically the buffer, 1024 is about 2.5% of a second
        # this allows us to check the sensors between buffers to adjust volume and other things
        self.chunk = 1024
        self.sys_volume = volume # make the volume variable passed into the init function a member variable


    def playAll(self, poem, verbose=False):
        """
        This method handles the logic for playing back the poems,
        it is perhaps a little sloppy as it handles lots of logic in embeded
        if/else/for statements

        INPUTS
        --------------------------
        poem - list of Poem objects or a singular Poem object
        verbose - boolean - if true will print extra information to the user
        """
        # if poem is a list (as oppose to a single intance of the poem class)
        if type(poem) is list:
            # take each poem in the list
            for p in poem:
                # if someone is detected then play the next poem
                # else simply wait for someone to arrive
                if checkProximitySensor(): # will return 1 if someone is around and 0 if someone is not
                    if verbose is True: # print some extra information if the verbose flag is set
                        print("----------------------------------------")
                        print(p.author,": ", p.title, " : ", p.total_duration)
                    # play each line back from the poem one by one
                    for i, media in enumerate(p.rec_paths):
                        if verbose is True: # if verbose flag is set print some extra information to terminal
                            print(p.text[i], " : ", p.durations[i])
                        self.playPart(p, i)
                    # Check to see if the skip button is pressed down, if not then sleep for 3 seconds between each poem
                    # this is to make sure that the skip does not wait for 3 seconds inbetween poems
                    v = GPIO.input(but_pin)
                    print("skip button reads: ", v)
                    if v > 0:
                        sleep(3)
                else:
                    # if noone is detected from the proximity sensor then simply wait for 0.1 seconds
                    sleep(0.1)
        # if poem is an instance of a Poem object instead of a list of poem objects
        elif type(poem) is Poem:
            if verbose is True: # if verbose is set to true print out some addtional information
                print(poem.author, ": ", poem.title, " : ", poem.total_duration)
            # just like above, playback the poem line by line
            for i, media in enumerate(poem.rec_paths):
                if verbose is True:
                    print(poem.text[i])
                    self.playPart(poem, i)
        # if we dont get a poem object print out the error message and exit
        else:
            print("ERROR - Please pass a Poem object into the play function")


    def playPart(self, poem, part, verbose=False):
        """
        This method will playback a line from a poem object
        It will also check the "skip button" as well as the volume pot
        and the shutdown switch between chunks (40x a second)

        INPUTS
        --------------------
        poem    - object    - an instance of a Poem object
        part    - int       - the line number from the poem to playback
        verbose - boolean   - if true the function will print information during execution
        """
        p = pyaudio.PyAudio() # create an instance of the pyAudio playback engine
        if verbose is True: # print info if verbose is true
            print(poem.author,": ", poem.title,
                  " : line number ", part, " : ", poem.text[part])
        # open the appropiate wav file for reading
        f = wave.open(r""+poem.rec_paths[part],"rb")
        # convert the .wav file into a stream which allows us to read the contents chunk by chunk
        stream = p.open(format=p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)
        # get the data broken up by the chunk size
        data = f.readframes(self.chunk)
        while data: # for as long as we have chunks left in our data stream
            self.sys_volume = checkVolumeKnob(self.sys_volume) # make sure that the volume pot did not change position
            checkPowerSwitch() # check to see if the "shutdown" switch has been toggled
            v = GPIO.input(but_pin) # read the skip button, store in v
            data = f.readframes(self.chunk) # get another chunk
            if v > 0: # if the skip button is not being pressed play back the audio
                stream.write(data) # actually playback the audio from the stream
            else:
                break
        # before exiting the function, stop and close the stream
        stream.stop_stream()
        stream.close()


    def playTitle(self, poem, verbose=False):
        """
        This method will playback the title of the given poem (which
        corresponds to the first (index 0) part in the poem object)

        INPUTS
        -----------------
        poem    - Poem object   - The poem whos title you want to playback
        verbose - boolean       - If true method will print out the poems author and the poem title
        """
        if verbose is True: # if verbose is true print out some info
            print("poet: ", poem.author," : ", poem.title)
        self.playPart(poem, 0) # play back the first "part" of the poem object which is the title


class Poem():
    def __init__(self, first_line):
        """
        initalization method for the poem class
        take in the first line which contains the name of the
        poem as well as the path to a recording of the name of the poem

        It is assumed that when creating a Poem object you pass the first csv line into the method
        This contains the title of the poem in index 0 and the path to the .wav recording of the title
        in index 1

        INPUTS
        --------------------
        first_line  - list  - index 0 is a string corresponding to the name of the poem
                              index 1 is a string which corresponds to the path
                                      to the recording of the name of the poem
        """
        # ---------------------------------------------------------------
        # member variables to keep track of different aspects of the Poem
        # ---------------------------------------------------------------
        self.title = first_line[0]
        self.durations = [] # list of floats which describes how long each line of the poem is (in seconds)
        self.rec_paths = ["/home/pi/voiceshell/" + first_line[1]] # list of strings which describe paths to the poem recordings
        self.text = [first_line[0]] # list of strings corresponding to the title and content of the poem
        self.full_text = '' # all the text of the poem in a single string (appended to when loading more lines)
        # get the authors name from folder name, add space between first and last
        a = os.path.dirname(first_line[1][6:])
        last_name_index = re.search(r'^([^A-Z]*[A-Z]){2}', a).span()[1] - 1 # some fancy regex to get the authors last name from the containing folder
        self.author = a[:last_name_index] + " " + a[last_name_index:]
        # for keeping track of the media
        self.total_duration = None
        # update the durations member variable with the length of the title
        with contextlib.closing(wave.open(self.rec_paths[0],'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            self.durations.append(frames / float(rate))
        # update the total_duration member variable with the length of the title
        self.total_duration = self.calculateTotalDuration(self.durations)

    def calculateTotalDuration(self, durs):
        """
        Simple helper method for recalculating the total duration of the poem using the individual values in the
        self.durations list (or another list of floats)
        """
        total_duration = 0.0 # start with 0.0 and add the durations one by one
        for dur in durs:
            total_duration = total_duration + dur
        return total_duration # return the total_duration

    def loadLine(self, line):
        """
        load a new line into the Poem object

        INPUTS
        ------------------------
        line    - list  - index 0 corresponds to the text contained in the recording while
                          index 1 corresponds to the relative path to the recording
        """
        self.text.append(line[0]) # add the poems text to the self.text list
        self.full_text = self.full_text + " " + line[0] # add the text to the full_text string
        self.rec_paths.append("/home/pi/voiceshell/" + line[1]) # convert the relative path to an absolute path and append to rec_paths list
        # caalculate the duration of the recording and update the durations list
        with contextlib.closing(wave.open(self.rec_paths[-1],'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            self.durations.append(frames / float(rate))
        # recalculate the total_duration of the poem
        self.total_duration = self.calculateTotalDuration(self.durations)

    def loadLines(self, lines):
        """
        This helper function allows you to pass a list of lines into the object to be loaded

        INPUTS
        -----------------------
        lines   - list of lists     - a list of "line" lists where each item contains two elements
                                      index 0 corresponds to the text contained in the lines recording
                                      index 1 corresponds to the relative path of the lines recording
        """
        for line in lines:
            self.loadLine(line)

    def printStats(self, verbose=100):
        """
        This method simply prints out information about the Poem object

        INPUTS
        ------------------------
        verbose     - int   - this is how much information will be printed out
                              if a 2, for instance, is passed into the method
                              it will print out the first two recording paths, first
                              two lines of text, etc. and neglect the rest of the information
        """
        print("author : ", self.author)
        print("title : ", self.title)
        print("paths : ", self.rec_paths[:verbose])
        print("text : ", self.text[:verbose])
        print("full text : ", self.full_text)
        print("dur  : ", self.durations[:verbose])
        print("total duration : ", self.total_duration)

def loadCSV(csv_file):
    """
    This helper function reads the CSV file and populates the all_lines global list
    as well as creating poem objects for each poem contained in the CSV
    """
    with open(csv_file, 'r') as f:
        reader = csv.reader(f) # read the CSV file
        all_lines = list(reader) # convert contents into a list and then assign to all_lines

    poems = []
    last_author = None
    current_author = None
    for line in all_lines:
        last_author = current_author
        current_author = os.path.dirname(line[1][6:])
        # just some funky logic to handle the format of the CSV file
        if current_author == "":
            pass
        elif current_author != last_author: # if we have a new author then create a new poem object
            if len(poems) > 0:
                pass
            poems.append(Poem(line))
        else: # if it is the same author as the last line then append the line to the last poem object
            poems[-1].loadLine(line)
    return poems

def roboVoice(statement):
    """
    This function allows for an easy to use interface to the pyttsx3 text-speech library
    Please note that this only works on a raspberry pi or on a linux system, it will not
    work on OSX, not sure about windows though

    Please note that this function is blocking, if you want it to speak while still
    processing tasks in the background call this function using a subprocess call

    INPUTS
    -------------------------
    statement   - string    - A string corresponding to the text you want the computer to speak
    """
    engine = pyttsx3.init(); # create instance of the engine
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-25) # change the playback rate to be a little slower
    engine.setProperty('voice', 'en-uk-rp') # choose the language and accent
    engine.say(statement) # tell the engine what to say
    engine.runAndWait() # actually say it

def setMixerAmp(val):
    """
    This function sets the amplitude of the alsa mixer which controls the overall output
    volume of the raspberry pi (please note that this will not work on Windows or OsX

    INPUTS
    ------------------------
    val     - int - corresponding to the amplitude (in percent of max amplitude)
                    a value of 35 will set the mixer to playback audio at 35% of its max gain
    """
    command  = ["amixer", "sset", "'Master'", "{}%".format(val)]
    subprocess.run(command)

def checkVolumeKnob(sys_volume):
    """
    This function checks the value of the potentiometer (channel 0 of the I2C ADC)
    It then normalizes the reading to a value between 0 and 80 and checks to see if
    the current value is more than 2 points different from the last value.
    This basically prevents sensor jitter from sending uneeded subprocess calls
    to adjust the volume when the pot was not actually used

    INPUTS
    ------------------------------
    sys_volume  - int   - the current amplitude of the ALSA mixer, to compare to current value

    OUTPUTS
    -----------------------------
    sys_volume  - int   - the new or unaltered sys_volume value
    """
    # read the potentiometer
    temp = adc.read_adc(0, gain=GAIN)
    # scale the value from 0 -80
    # we dont want to push the system too hard
    normalized = temp/2047 * 80
    # if there is a 2 point or greater change
    # basically adding historesis
    if abs(normalized - sys_volume) > 2:
        print("adjusting system volume to :", normalized)
        setMixerAmp(normalized)
        return normalized
    return sys_volume

def checkPowerSwitch():
    """
    This function checks the power switch to see if it was toggled
    If it has been then the program will send a subprocess call to shutdown the system safely
    """
    if GPIO.input(pwr_pin) == 0:
        powerDownSystem()

def powerDownSystem():
    """
    This function will send a subprocess call to the command line which shutsdown the pi safely
    """
    roboVoice("shutting down system, please wait 15 seconds before unplugging power")
    command = ["sudo", "shutdown", "-h", "now"]
    subprocess.run(command)

def checkProximitySensor():
    """
    This function just reads the proximity sensor and returns a 1 if someone is detect and a 0 if not.
    It really does not do much, but just allows for easier to understand code in other parts of the program
    """
    if GPIO.input(prox_pin) > 0:
        return 1
    return 0
