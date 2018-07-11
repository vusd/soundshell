import speech_recognition as sr

print(sr.Microphone.list_microphone_names())
mic = sr.Microphone()
r = sr.Recognizer()

def startR():
    with mic as source:
        r.adjust_for_ambient_noise(source)
        print("Listening 1")
        audio = r.listen(source)
        print("Done Listening")
    try:
        text = r.recognize_sphinx(audio)
        if "love" in text.lower():
            print("LOVE BABY!!!")
        else:
            print(text)
    except sr.UnknownValueError:
        print("could not understand audio")
        pass
    except sr.RequestError as e:
        print("error; {0}".format(e))

while True:
    startR()
