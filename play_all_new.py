#!/usr/bin/python3
# this notebook is for developing the speech_recognition system
from vsutils import loadCSV, PlaybackEngine, roboVoice, setMixerAmp
from time import sleep

print("Voiceshell starting...")
# roboVoice("Ahem. Starting...")

# a class to handle playback

if __name__ == "__main__":

    # for the pot
    sleep(1)
    setMixerAmp(20)
    roboVoice("booting system... please wait")
    # more code taken from voiceshell.py
    print("Loading text...")
    # roboVoice("Loading text files...")
    csv_file = '/home/pi/voiceshell/voiceshell_audio_LUT.csv'
    pe = PlaybackEngine()
    poems = loadCSV(csv_file)
    print("Done.")

    while True:
        pe.playAll(poems, verbose=True)
