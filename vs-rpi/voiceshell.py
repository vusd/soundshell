from __future__ import unicode_literals
import math
import random
import spacy
import time
import csv
import numpy as np
from numpy import dot
from numpy.linalg import norm
import wave, sys, pyaudio
import speech_recognition as sr
import pyttsx3
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def roboVoice(statement):
    engine = pyttsx3.init();
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-25)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', 'en-uk-rp')
    engine.say(statement)
    engine.runAndWait()


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

nlp = spacy.load('en')

print("Loading text...")
roboVoice("Loading text files...")
corpusFile = 'voiceshell_audio_LUT.csv'

with open(corpusFile, 'r') as f:
    reader = csv.reader(f)
    all_lines = list(reader)

audio_lookup_table = {}
sentences = []
for line in all_lines:
    sentence = line[0]
    if not sentence.isspace():
        sentences.append(nlp(sentence))
    filename = line[1]
    audio_lookup_table[sentence] = filename
print("Done.")
roboVoice("Starting speech recognition...")
print("Starting up speech recognition...")
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Calibrating microphone for ambient noise... (this will take 5 seconds)")
    roboVoice("Calibrating microphone for ambient noise... (this will take 5 seconds)")
    r.adjust_for_ambient_noise(source, duration=5)
    print("Done, starting program.")
    roboVoice("Done, starting program.")

def runLoop():
    roboVoice("I'm listening...")
    print("Say something!")

    with sr.Microphone() as source:
        audio = r.listen(source)
    try:
        userInput = r.recognize_sphinx(audio)
        print(userInput)

        matched = process.extractBests(userInput, sentences, score_cutoff = 60)

        if(userInput == 'open the pod bay doors'):
            audioFile = 'PoemsAudio/sorry.wav'

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
    except sr.UnknownValueError:
        roboVoice("Sorry, I couldn't understand that.")
        print("Sorry, I didn't understand that.")
    except sr.RequestError as e:
        roboVoice("Sphinx Error {0}".format(e))
        print("Sphinx recognition error; {0}".format(e))

# setup()
while True:
    runLoop()
#  >initial start announcement, mic level once, error checking, speech recog and playback
