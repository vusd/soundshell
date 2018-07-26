from __future__ import unicode_literals
import random
import spacy
import csv
import numpy as np
import os
import re
import contextlib
from numpy import dot
from numpy.linalg import norm
import wave, pyaudio
import speech_recognition as sr
import pyttsx3
from fuzzywuzzy import process


############################## Voice Stuff #################################
print("Voiceshell starting...")
# roboVoice("Ahem. Starting...")
def meanv(coords):
    sumv = [0] * len(coords[0])
    for item in coords:
        for i in range(len(item)):
            sumv[i] += item[i]
    mean = [0] * len(sumv)
    for i in range(len(sumv)):
        mean[i] = float(sumv[i]) / len(coords)
    return mean

def cosine(v1, v2):
    if norm(v1) > 0 and norm(v2) > 0:
        return dot(v1, v2) / (norm(v1) * norm(v2))
    else:
        return 0.0

def sentvec(s):
    sent = nlp(s)
    word_vectors = [w.vector for w in sent]
    return meanv(word_vectors)

def spacy_closest_sent(space, input_str, n=1):
    input_vec = sentvec(input_str)
    return sorted(space,
                  key=lambda x: cosine(np.mean([w.vector for w in x], axis=0), input_vec), reverse=True)[:n]

def matchPoemFromTitle(rec, poems):
    best = 0
    best_points = 0
    for i, poem in enumerate(poems):
        points = 0
        for word in rec:
            if word in poem.title:
                points = points + 1
        if points > best_points:
            best_points = points
            best = i
    return poems[best]

def listenToMicrophone():
    print("listening")
    with sr.Microphone() as source:
        audio = r.listen(source)

    userInput = None
    # try with google first
    try:
        userInput = r.recognize_google(audio)
        print("Google thinks you said : ", userInput)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")

    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        try:
            userInput = r.recognize_sphinx(audio)
            print("Sphinx thinks you said")
        except sr.UnknownValueError:
            # roboVoice("Sorry, I couldn't understand that.")
            print("Sorry, I didn't understand that.")
        except sr.RequestError as e:
            # roboVoice("Sphinx Error {0}".format(e))
            print("Sphinx recognition error; {0}".format(e))
    return userInput

def getAllSentences(poems):
    sents = []
    for p in poems:
        for line in p.text:
            sents.append(line)
    return sents

# taken from voiceshell.py but now tries google if google is down then it uses sphinx
def runLoop():
    # roboVoice("I'm listening...")
    print("------------------------------")
    userInput = listenToMicrophone()
    if userInput is None:
        print("no speech detected, listening again")
        return 0

    matched = process.extractBests(userInput, sentences, score_cutoff = 60)
    print("old match : ", matched)

    the_poem = matchPoemFromTitle(userInput, poems)
    print("new match: ", the_poem.title)
    audio_files = the_poem.rec_paths

    """
    if(userInput == 'open the pod bay doors'):
        audioFile = 'Audio/sorry.wav'

    elif not matched:
        for sent in spacy_closest_sent(sentences, userInput):
            output = sent.text
            print(output)

        audioFile = audio_lookup_table[output]
        print(audioFile)

    else:
        output = random.choice(matched)
        cleaned_output = str(output[0])
        print(cleaned_output)

        audioFile = audio_lookup_table[cleaned_output]
        print(audioFile)
    """

    for audioFile in audio_files:
        sound = wave.open(audioFile)
        p = pyaudio.PyAudio()
        chunk = 1024
        stream = p.open(format = p.get_format_from_width(sound.getsampwidth()), channels = sound.getnchannels(), rate = sound.getframerate(), output = True)
        data = sound.readframes(chunk)
        while len(data) > 0:
            stream.write(data)
            data = sound.readframes(chunk)
        stream.stop_stream()
        stream.close()

        p.terminate

class Poem():
    def __init__(self, first_line):
        """take in the first line which contains the name of the
        poem as well a the path to a recording of the name of the poem"""
        self.title = nlp(first_line[0])
        self.durations = []
        self.rec_paths = [first_line[1]]
        self.text = [first_line[0]]
        self.full_text = ''

        # get the authors name from folder name, add space between first and last
        a = os.path.dirname(first_line[1][6:])
        last_name_index = re.search(r'^([^A-Z]*[A-Z]){2}', a).span()[1] - 1
        self.author = a[:last_name_index] + " " + a[last_name_index:]

        # for keeping track of the media
        self.media = []
        self.total_duration = None
        # self.instance = vlc.Instance()

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
        self.text.append(nlp(line[0]))
        self.full_text = self.full_text + " " + line[0]
        self.rec_paths.append(line[1])
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
        print("media : ", self.media[:verbose])

def roboVoice(statement):
    engine = pyttsx3.init();
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-25)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', 'en-uk-rp')
    engine.say(statement)
    engine.runAndWait()

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

if __name__ == "__main__":
    print("Loading text...")
    # roboVoice("Loading text files...")
    nlp = spacy.load('en')
    corpusFile = 'voiceshell_audio_LUT.csv'
    pe = PlaybackEngine()
    poems = loadCSV(corpusFile)
    sentences = getAllSentences(poems)
    # roboVoice("Starting speech recognition... and Calibrating the microphone, please wait")
    print("Starting up speech recognition...")
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Calibrating microphone for ambient noise... (this will take 5 seconds)")
        r.adjust_for_ambient_noise(source, duration=5)
        print("Done, starting program.")
        # roboVoice("Done, starting program.")

    while True:
        # setStripColor(random.randint(0,255))
        runLoop()
