import os, vlc, time, subprocess, re


class Poem():
    def __init__(self, rec_path=None, poem_text=None):
        self.rec_path = rec_path

        args=("ffprobe","-show_entries", "format=duration","-i",rec_path)
        popen = subprocess.Popen(args, stdout = subprocess.PIPE)
        popen.wait()
        output = str(popen.stdout.read(), 'utf-8')
        self.rec_length = float(re.findall("\d+\.\d+", output)[0])

        instance = vlc.Instance()
        self.media = instance.media_new(self.rec_path)

class PlaybackEngine():
    def __init__(self):
        instance = vlc.Instance()
        self.player = instance.media_player_new()

    def play(self, poem):
        if type(poem) is list:
            for p in poems:
                self.player.set_media(p.media)
                self.player.play()
                time.sleep(p.rec_length)
        elif type(poem) is Poem:
            self.player.set_media(poem.media)
            self.player.play()
            time.sleep(poem.rec_length)
        else:
            print("Please pass a Poem object into the play function")

if __name__ == '__main__':
    file_names = []
    for f in os.listdir('samples'):
        if f.lower().endswith(".wav"):
            file_names.append("samples/"+f)

    pe = PlaybackEngine()

    poems = [Poem(rec_path=path, poem_text="Poem Text")
             for path in file_names]

    # play through all the recordings
    for poem in poems:
        pe.play(poem)
