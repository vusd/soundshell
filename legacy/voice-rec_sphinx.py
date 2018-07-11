import speech_recognition as sr
from pocketsphinx import LiveSpeech

r = sr.Recognizer()

for phrase in LiveSpeech(): print(phrase)

print("loading up a LiveSpeech model, please wait...")
speech = LiveSpeech(lm=False, keyphrase='forward', kws_threshold=1e-20)
print("loaded a sphinx voice detector, please say something")
for phrase in speech:
    print(phrase.segments(detailed=True))

"""
while True:
    with sr.Microphone() as source:
        audio=r.listen(source)
    try:
        text = r.recognize_sphinx(audio)
        if "love" in text.lower():
            print("LOVE BABY!!!")
        else:
            print(text)
    except sr.UnknownValueError:
        print("Sphinx could not understand audio")
        pass
    except sr.RequestError as e:
        print("Sphinx error; {0}".format(e))

"""

