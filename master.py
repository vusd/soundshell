import os, re, wave, pyaudio, contextlib, csv, spacy, pyttsx3, random
import numpy as np
import speech_recognition as sr
from fuzzywuzzy import process
from numpy.linalg import norm
from numpy import dot


# class to handle the Poems
class Poem():
    def __init__(self, first_line):
        """take in the first line which contains the name of the
        poem as well a the path to a recording of the name of the poem"""
        self.title = nlp(first_line[0])
        self.durations = []
        self.rec_paths = [first_line[1]]
        self.text = [first_line[0]]
        self.lookup = {self.text[0]: self.rec_paths[0]}
        self.full_text = ''

        # get the authors name from folder name, add space between first and last
        a = os.path.dirname(first_line[1][6:])
        last_name_index = re.search(r'^([^A-Z]*[A-Z]){2}', a).span()[1] - 1
        self.author = a[:last_name_index] + " " + a[last_name_index:]

        # for keeping track of the media
        # self.media = []
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
        self.lookup[self.text[-1]] = self.rec_paths[-1]
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

# helper functions from voiceshell.py
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

# a class to handle playback
class PlaybackEngine():
    def __init__(self):
        self.chunk = 1024
        self.p = pyaudio.PyAudio()

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
            if verbose is True:
                print(poem.author, ": ", poem.title, " : ", poem.total_duration)
            for i, media in enumerate(poem.rec_paths):
                if verbose is True:
                    print(poem.text[i])
                self.playPart(poem, i)
        else:
            print("Please pass a Poem object into the play function")

    def playPart(self, poem, part, verbose=False):

        if verbose is True:
            print(poem.author,": ", poem.title,
                  " : line number ", part, " : ", poem.text[part])
        f = wave.open(r""+poem.rec_paths[part],"rb")
        stream = self.p.open(format=self.p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)
        data = f.readframes(self.chunk)
        while data:
            stream.write(data)
            data = f.readframes(self.chunk)

        stream.stop_stream()
        stream.close()
        # self.p.terminate()
        # time.sleep(poem.durations[part])

    def playTitle(self, poem, verbose=False):
        if verbose is True:
            print("poet: ", poem.author," : ", poem.title)
        self.playPart(poem, 0)

    def playFile(self, path):
        f = wave.open(r""+path,"rb")
        stream = self.p.open(format=self.p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)
        data = f.readframes(self.chunk)
        while data:
            stream.write(data)
            data = f.readframes(self.chunk)

        stream.stop_stream()
        stream.close()

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
        elif current_author != last_author:
            if len(poems) > 0:
                pass
                # poems[-1].printStats()
            poems.append(Poem(line))
        else:
            poems[-1].loadLine(line)
    return poems


def getAllLines(poems, tokens=False):
    sents = []
    for p in poems:
        for line in p.text:
            # print("line: ", line)
            if tokens is True:
                sents.append(line)
            else:
                sents.append(line.text)

    return sents

def getAllAuthors(poems):
    a = []
    for p in poems:
        a.append(p.author)
    return a

def getAllTitles(poems, tokens=False):
    titles = []
    for p in poems:
        if tokens is True:
            titles.append(p.text[0])
        else:
            titles.append(p.text[0])
    return titles

def matchPoemFromAllText(rec, poems):
    best = random.randint(0, len(poems))
    best_points = 0
    for i, poem in enumerate(poems):
        points = 0
        for line in poem.text:
            if type(line) == str:
                for word in rec.lower().split(" "):
                    if word == line.lower():
                        points = points + 1
            else:
                for word in rec.lower().split(" "):
                    if word == line.text.lower():
                        points = points + 1

        if points > best_points:
            best_points = points
            best = i
            print("new best: ", poems[best].title)
    return poems[best]

def matchPoemFromTitle(rec, poems):
    best = random.randint(0, len(poems))
    best_points = 0
    # if a word is in the title it gets a point
    for i, poem in enumerate(poems):
        points = 0
        for word in rec.lower().split(" "):
            if word == poem.title.text.lower():
                points = points + 1
                print(points, " ", word, " ", poem.title.text)
        if points > best_points:
            best_points = points
            best = i
    return poems[best]

def getBestOfBests(bests):
    top_score = 0
    best = None
    for b in bests:
        if b[1] > top_score:
            best = b
            top_score = b[1]
    return best

def createAudioLookupTable():
    audio_lookup_table = {}
    for poem in poems:
        for i, text in enumerate(poem.text):
            audio_lookup_table[text] = poem.rec_paths[i]
    return audio_lookup_table

def roboVoice(statement):
    engine = pyttsx3.init();
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-25)
    # voices = engine.getProperty('voices')
    engine.setProperty('voice', 'en-uk-rp')
    engine.say(statement)
    engine.runAndWait()

def runLoop(mode="title", logic=None, playback_mode="all", recognizer="google"):
    print("------------------------------")
    if mode == "title":
        userInput = listenToMicrophone(mode=recognizer)
        if userInput is None:
            print("no speech detected, listening again")
            return 0
        if logic == 'entire-poem':
            the_poem = matchPoemFromAllText(userInput, poems)
        else:
            the_poem = matchPoemFromTitle(userInput, poems)
        print("new match: ", the_poem.title)
        pe.playAll(the_poem)
    elif mode == "line":
        userInput = listenToMicrophone(mode=recognizer)
        if userInput is None:
            print("no speech detected, listening again")
            return 0
        # matched = process.extractBests(userInput, sentences, score_cutoff = 60)
        matched = process.extractOne(userInput, sentences, score_cutoff = 60)
        if matched is None:
            for sent in spacy_closest_sent(sentences, userInput):
                output = sent.text
            audioFile = audio_lookup_table[output]
            print("from sent: ", audioFile)
            pe.playFile(audioFile)
        else:
            cleaned_output = matched[0]
            print(cleaned_output)
            audioFile = audio_lookup_table[cleaned_output]
            print("from match: ", audioFile)
            pe.playFile(audioFile)
        print("-----------------------------")
    elif mode == "interactive":
        rand_poem = poems[random.randint(0,len(poems))]
        print("would you like to hear : " + rand_poem.title.text + " by " + rand_poem.author + "?")
        try:
            roboVoice("would you like to hear : " + rand_poem.title.text + " by " + rand_poem.author + "?")
        except:
            pass
        userInput = listenToMicrophone(mode=recognizer)
        if userInput is None:
            print("no speech detected, listening again")
            return 0
        if "yes" in userInput:
            if playback_mode == "all":
                pe.playAll(rand_poem)
            elif playback_mode == "title":
                pe.playTitle(rand_poem)

def listenToMicrophone(mode='sphinx'):
    print("listening")
    with sr.Microphone() as source:
        audio = r.listen(source)

    userInput = None
    try:
        if mode == 'google':
            userInput = r.recognize_google(audio)
            print("Google thinks you said : ", userInput)
        else:
            userInput = r.recognize_sphinx(audio)
            print("Sphinx thinks you said:", userInput)
    except sr.UnknownValueError:
        print("Not understood")
    except sr.RequestError as e:
        if mode == 'google':
            print("Could not request results from Google Speech Recognition service; {0}".format(e))
            userInput = r.recognize_sphinx(audio)
            print("Sphinx thinks you said:", userInput)
        else:
            print("REQUEST ERROR : ", e)
    return userInput

if __name__ == "__main__":
    nlp = spacy.load('en')
    csv_file = 'voiceshell_audio_LUT.csv'
    print("loading poems")
    poems = loadCSV(csv_file)
    print("creating audio lookup table")
    audio_lookup_table = createAudioLookupTable()
    r = sr.Recognizer()
    pe = PlaybackEngine()
    sentences = getAllLines(poems, tokens=True)
    titles = getAllTitles(poems, tokens=True)
    authors = getAllAuthors(poems)
    print("authors: ", authors)

    with sr.Microphone() as source:
        print("Calibrating microphone for ambient noise... (this will take 5 seconds)")
        r.adjust_for_ambient_noise(source, duration=5)
        print("Done, starting program.")

    while True:
        # runLoop(mode="interactive")
        # runLoop(mode="line")
        runLoop(mode='title', logic='entire-poem')
        # runLoop(mode='title', logic='title')
