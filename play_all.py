#!/usr/bin/python3
# this notebook is for developing the speech_recognition system
from vsutils import *

if __name__ == "__main__":
    # for the pot
    sleep(1)
    setMixerAmp(35)
    roboVoice("booting system... please wait")
    print("Loading text...")
    csv_file = '/home/pi/voiceshell/voiceshell_audio_LUT.csv'
    pe = PlaybackEngine(35)
    poems = loadCSV(csv_file)
    print("Done.")

    while True:
        pe.playAll(poems, verbose=True)
