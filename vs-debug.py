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
import pyttsx3;
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

print("Voiceshell starting...")

# def meanv(coords):
#     sumv = [0] * len(coords[0])
#     for item in coords:
#         for i in range(len(item)):
#             sumv[i] += item[i]
#     mean = [0] * len(sumv)
#     for i in range(len(sumv)):
#         mean[i] = float(sumv[i]) / len(coords)
#     return mean
#
# def cosine(v1, v2):
#     if norm(v1) > 0 and norm(v2) > 0:
#         return dot(v1, v2) / (norm(v1) * norm(v2))
#     else:
#         return 0.0
#
# def sentvec(s):
#     sent = nlp(s)
#     word_vectors = [w.vector for w in sent]
#     return meanv(word_vectors)
#
# def spacy_closest_sent(space, input_str, n=1):
#     input_vec = sentvec(input_str)
#     return sorted(space, key=lambda x: cosine(np.mean([w.vector for w in x], axis=0), input_vec), reverse=True)[:n]
#
nlp = spacy.load('en')

print("Loading text...")

corpusFile = "voiceshell_audio_LUT.csv"

with open(corpusFile, 'r') as f:
    reader = csv.reader(f)
    all_lines = list(reader)

sentences = []

for line in all_lines:
    sentence = line[0]
    if not sentence.isspace():
        sentences.append(nlp(sentence))
    filename = line[1]

print("Done.")

def runLoop():
    print("Say something! (Type it in)")
    # play "yes, go on" sound

    userInput = input()
    # play acknowledgement sound

    # print(userInput)
    # if input (word)= poem line then return. if multiple, make list, then pick random from it
    matched = process.extractBests(userInput, sentences, score_cutoff = 75)
    if not matched:
        # play "uh uh" sound
        pass
    else:
        # play yes sound, then audio file? Or just audio file?
        output = random.choice(matched)
        print(output[0])

    # for sent in spacy_closest_sent(sentences, userInput):
    #     print(sent.text)
    #     confidence = np.mean(sentvec(sent.text))
    #     print("Average vector proximity: ",confidence)

while True:
    runLoop()
