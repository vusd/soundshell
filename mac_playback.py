import vlc, time

p = vlc.MediaPlayer('rnb.wav')
p.play()
time.sleep(10)
