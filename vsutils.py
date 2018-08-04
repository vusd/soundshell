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

class PlaybackEngine():
    def __init__(self, volume):
        self.chunk = 1024
        self.sys_volume = volume

    def playAll(self, poem, verbose=False):
        if type(poem) is list:
            for p in poem:
                if verbose is True:
                    print("----------------------------------------")
                    print(p.author,": ", p.title, " : ", p.total_duration)
                for i, media in enumerate(p.rec_paths):
                    if verbose is True:
                        print(p.text[i], " : ", p.durations[i])
                    self.playPart(p, i)
                v = GPIO.input(but_pin)
                print("skipp button reads: ", v)
                if v > 0:
                    sleep(3)
        elif type(poem) is Poem:
            self.playTitle(poem)
            if verbose is True:
                print(poem.author, ": ", poem.title, " : ", poem.total_duration)
            for i, media in enumerate(poem.rec_paths):
                if verbose is True:
                    print(poem.text[i])
                    self.playPart(poem, i)
        else:
            print("Please pass a Poem object into the play function")

    def playPart(self, poem, part, verbose=False):
            p = pyaudio.PyAudio()
            if verbose is True:
                print(poem.author,": ", poem.title,
                      " : line number ", part, " : ", poem.text[part])
            f = wave.open(r""+poem.rec_paths[part],"rb")
            stream = p.open(format=p.get_format_from_width(f.getsampwidth()),
                            channels=f.getnchannels(),
                            rate=f.getframerate(),
                            output=True)
            data = f.readframes(self.chunk)
            while data:
                self.sys_volume = checkVolumeKnob(self.sys_volume)
                checkPowerSwitch()
                v = GPIO.input(but_pin)
                data = f.readframes(self.chunk)
                # if the skip button is not being pressed play back the audio
                if v > 0:
                    stream.write(data)
                else:
                    break
            stream.stop_stream()
            stream.close()

    def playTitle(self, poem, verbose=False):
        if verbose is True:
            print("poet: ", poem.author," : ", poem.title)
        self.playPart(poem, 0)

class Poem():
    def __init__(self, first_line):
        """take in the first line which contains the name of the
        poem as well a the path to a recording of the name of the poem"""
        self.title = first_line[0]
        self.durations = []
        self.rec_paths = ["/home/pi/voiceshell/" + first_line[1]]
        self.text = [first_line[0]]
        self.full_text = ''

        # get the authors name from folder name, add space between first and last
        a = os.path.dirname(first_line[1][6:])
        last_name_index = re.search(r'^([^A-Z]*[A-Z]){2}', a).span()[1] - 1
        self.author = a[:last_name_index] + " " + a[last_name_index:]

        # for keeping track of the media
        # self.media = []
        self.total_duration = None

        with contextlib.closing(wave.open(self.rec_paths[0],'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            self.durations.append(frames / float(rate))

        self.total_duration = self.calculateTotalDuration(self.durations)
        # self.media.append(self.instance.media_new(self.rec_paths[-1]))

    def calculateTotalDuration(self, durs):
        total_duration = 0.0
        for dur in durs:
            total_duration = total_duration + dur
        return total_duration

    def loadLine(self, line):
        """load in each individual line in the poem"""
        self.text.append(line[0])
        self.full_text = self.full_text + " " + line[0]
        self.rec_paths.append("/home/pi/voiceshell/" + line[1])
        with contextlib.closing(wave.open(self.rec_paths[-1],'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            self.durations.append(frames / float(rate))

        # self.media.append(self.instance.media_new(self.rec_paths[-1]))
        self.total_duration = self.calculateTotalDuration(self.durations)

    def printStats(self, verbose=2):
        print("author : ", self.author)
        print("title : ", self.title)
        print("paths : ", self.rec_paths[:verbose])
        print("text : ", self.text[:verbose])
        print("full text : ", self.full_text)
        print("dur  : ", self.durations[:verbose])
        print("total duration : ", self.total_duration)
        # print("media : ", self.media[:verbose])

def loadCSV(csv_file):
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        all_lines = list(reader)

    poems = []
    last_author = None
    current_author = None
    for line in all_lines:
        last_author = current_author
        current_author = os.path.dirname(line[1][6:])
        if current_author == "":
            pass
            # print("blank line :  ", line)
        elif current_author != last_author:
            if len(poems) > 0:
                pass
                # poems[-1].printStats()
            poems.append(Poem(line))
        else:
            poems[-1].loadLine(line)
    return poems

def roboVoice(statement):
    engine = pyttsx3.init();
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-25)
    engine.setProperty('voice', 'en-uk-rp')
    engine.say(statement)
    engine.runAndWait()

def setMixerAmp(val):
    command  = ["amixer", "sset", "'Master'", "{}%".format(val)]
    subprocess.run(command)

def checkVolumeKnob(sys_volume):
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
    if GPIO.input(pwr_pin) == 0:
        powerDownSystem()

def powerDownSystem():
    roboVoice("shutting down system, please wait 5 seconds before unplugging power")
    command = ["sudo", "shutdown", "-h", "now"]
    subprocess.run(command)

