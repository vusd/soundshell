#!/usr/bin/python3
# this notebook is for developing the speech_recognition system
from __future__ import unicode_literals
import csv
import numpy as np
from numpy import dot
from numpy.linalg import norm
import wave, pyaudio, os, contextlib
import regex as re
import speech_recognition as sr
from fuzzywuzzy import process
import RPi.GPIO as GPIO
from time import sleep

print("Voiceshell starting...")
# roboVoice("Ahem. Starting...")

# a class to handle playback
class PlaybackEngine():
    def __init__(self):
        self.chunk = 1024
        # self.player = instance.media_player_new()

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
                v = GPIO.input(pot_pin)
                # print("volume : ", v)
                if v > 0:
                    stream.write(data)
                    data = f.readframes(self.chunk)

            stream.stop_stream()
            stream.close()
            p.terminate()
            # time.sleep(poem.durations[part])

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

if __name__ == "__main__":
    # for the pot
    time.sleep(1)
    pot_pin = 26
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pot_pin, GPIO.IN)
    # more code taken from voiceshell.py
    print("Loading text...")
    # roboVoice("Loading text files...")
    csv_file = '/home/pi/voiceshell/voiceshell_audio_LUT.csv'
    pe = PlaybackEngine()
    poems = loadCSV(csv_file)
    print("Done.")

    while True:
        pe.playAll(poems[1:], verbose=True)
