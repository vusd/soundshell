------------------------------------------------------
Please note that the Audio files are stored using git LFS you will need to install LFS to work with the audio files in this repo

The recordings of the Poets reading their poems can be found in the Audio folder

The code in development is within the Jupyter Notebooks, you can run them by entering "Jupyter Notebook" into a terminal window. This will open the Jupyter interface within a web browser. From there you can open the notebooks and run the code block by block.

dependancies (warning! these are not up to date)
---------------------------------------
linux : 
sudo pip install python-vlc
sudo apt-get install vlc portaudio

mac : 
brew install portaudio 
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" < /dev/null 2> /dev/null ; brew install caskroom/cask/brew-cask 2> /dev/null
brew cask install vlc

pip install python-vlc pyaudio speech_recognizer spacy
