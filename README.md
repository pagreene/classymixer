#Classy Mixer

Overview and Capabilities:
-------------------------
Created by Patrick Greene

This is a project to create an ipython (for now) tool for creating playlists 
of classical music, such that multi-movement (and hence multi-track) pieces are
kept together. This currently works only with google play, but will soon be 
expanded to work for local file systems.

I look at the song title with regular expressions to try to decide if they are 
part of a piece or not. When sorting into pieces, I also take into account the 
album title, so if you have "Sonata in G" on two different albums, they will
still be listed separately. Within the piece, the tracks are sorted by track
number.

This system is not perfect, as it requires some basically decent labelling of
tracks and albums. There are some tracks that should be together but aren't, and
there are some that shouldn't be together but are, however it works very well
for the most part, working on my music collection. Some labels that it should
recognize:
  
- Sympony No. 2: I. Adagio
  
- Strawinsky: The Right of Spring: Introduction
  
- Quartet in A - Minuet

and this is an example of something that might confuse it:
  
- Quartet in A - Minuet - Trio

Of course for a music shuffler, especially of classical music, it is not critical
that every piece remain together, however I do try my best.

Install:
-------

This has only been tested on Linux, however the packages should (they claim) 
work in Windows and Mac as well. 

There's really nothing to install for this projet in itself, besides downloading
the file(s), however there are some requirements

- Python (2.7 for now, however I will be switching over to 3.x in the near future)
- gmusicapi (if you want to use google play)
- pytaglib (if you want to run the shuffler on a local file library)

Usage Example:
-------------

Suppose you want to create a playlist on google play, you would enter the ipython
environment and type:

```python
  import classyMixer
  mixer = classyMixer.ClassyMixer() # You will be prompted for username and password, and it will then complain the Python 3 is better.
  mixer.mix('Classy playlist', 100, genre='Classical')
```

and that's it. You have created a playlist with 100 pieces (not 100 tracks) using 
only music marked as genre 'Classical' in the song metadata.
