import os, vlc, time, subprocess, re


class Poem():
    def __init__(self, vlc_instance=None, rec_path=None, poem_text=None):
        self.rec_path = rec_path

        args=("ffprobe","-show_entries", "format=duration","-i",rec_path)
        popen = subprocess.Popen(args, stdout = subprocess.PIPE)
        popen.wait()
        output = str(popen.stdout.read(), 'utf-8')
        self.rec_length = float(re.findall("\d+\.\d+", output)[0])

        self.media = vlc_instance.media_new(self.rec_path)


if __name__ == '__main__':
    file_names = []
    for f in os.listdir('samples'):
        if f.lower().endswith(".mp3"):
            file_names.append("samples/"+f)

    instance = vlc.Instance()
    player = instance.media_player_new()

    poems = [Poem(rec_path=path, vlc_instance=instance, poem_text="Poem Text")
             for path in file_names]

    # play through all the recordings
    for poem in poems:
        player.set_media(poem.media)
        player.play()
        time.sleep(poem.rec_length)

