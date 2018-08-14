#!/usr/bin/python3
# dont tell anyone about my * import - very bad practice
from vsutils import *

if __name__ == "__main__":
    sleep(1)
    # set the amplitude to 35% for the introduction robot voice
    setMixerAmp(35)
    roboVoice("booting system... please wait")
    print("Loading text...")
    csv_file = '/home/pi/voiceshell/voiceshell_audio_LUT.csv'
    # create an instance of the playback engine with 35% amplitude
    pe = PlaybackEngine(35)
    # load the csv file into a list of poem objects
    poems = loadCSV(csv_file)
    print("Done.")

    while True:
        # for ever and always run the "playAll" method of the playbackengine object
        pe.playAll(poems, verbose=True)
