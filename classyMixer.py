from songLibs import Collection, GooglePlayCollection, LocalCollection, TunesCollection
import random
import re

class ClassyMixer(object):
    '''
    An object for managing music and looking through track info using regex.
    
    mixer = ClassyMixer(collection)
    
    where "collection" is selected from one of the collections available in songLibs.
    '''
    def __init__(self, collection):
        if not issubclass(collection, Collection):
            raise Exception("Give me a real collection")
        
        self.collection = collection()
        
        # Load the library
        self.library = self.collection.loadLibrary()
               
        # Load the list of playlists
        self.playlists = self.collection.loadPlaylists()
        
        # Define the regex patterns to pick out movements of larger pieces.
        self.pattList = []
        # With numbers (including roman numerals)
        self.pattList.append(re.compile("(.*) *?(?:[-:]|^) *?(\d+)[.:]? *?(.*)$"))
        self.pattList.append(re.compile("(.*) *?(?:[-:]|^) *?([IVX]+)[^\w]+?(\w+.*)$"))
        # Without numbers
        self.pattList.append(re.compile("(.*) *?([:;]) *?(\w+.*)$"))
        self.pattList.append(re.compile("(.*)( +?- *?| *?- +?)(\w+.*)$"))
        
        return
    
    def update(self):
        self.library = self.collection.loadLibrary()
        self.playlists = self.collection.loadPlaylists()
        return
    
    def getList(self, initSongList = None, **criteria):
        '''
        Gets a list of song data entries given some set of criteria.
        
        Inputs:
        initSongList -- a list of songs to look through. If not given, then the
                        entire library is used.
        **criteria   -- enter either strings or regex patterns.
        '''
        if initSongList is None:
            initSongList = self.library
        
        songList = []
        for song in initSongList:
            # If any of the criteria are not met...
            for label, crit in criteria.iteritems():
                # determine if it matches
                data = song.__getattribute__(label)
                if isinstance(crit, re._pattern_type):
                    itMatches = (crit.match(data) is not None)
                else:
                    itMatches = (data == crit)
                
                if not itMatches:
                    break # Do nothing
            else: # Otherwise, add the song to the list
                songList.append(song)
        return songList
    
    def analyzeTitle(self, song, pattList):
        '''
        Uses RegEx to analyze the title and extract valuable features.
        
        INPUTS:
        title -- the title of a song
        
        OUTPUTS:
        titleList -- a tuple with the items from the title
        '''
        # Get the matches to the patterns. Only keep the ones where we
        # actually got a match.
        matchList = []
        for i, patt in enumerate(pattList):
            match = patt.match(song.mvmtLabel)
            if match is not None:
                matchList.append((match.groups(),i))
        
        # This is the core of where we decide how to sort the pieces.
        #TODO: Make this better.
        for match in matchList:
            if (match[0][0] is not None) and  (match[0][0] in song.composer):
                continue
            
            song.pieceLabel = match[0][0]
            song.mvmtLabel = match[0][-1]
            #toptitle = (song.album, m[0][0], m[0][1])
            #subtitle = (song.discNum, song.trackNum, m[0][-1])
            ret = True
            break
        else:
            ret = False
            
        #else:
        #    toptitle = (song['album'], fulltitle, -1)
        #    subtitle = (song['discNumber'], song['trackNumber'], -1)
        
        return ret
    
    def getPieceDict(self, songList = None, **criteria):
        '''
        Create a dictionary of pieces, indexced by a tuple of album name and
        title. This will attempt to put movements of a piece together into
        one dictionary entry.
        
        For example: `Symphony No. 3 - 1. Allegro` and `Symphony No. 3 - 2. Adagio`
        on the album `Beethoven's Symphonies` should show up in the entry with key
        ('Beethoven's Symphonies', 'Symphony No. 3'), with a list of the movements
        as the item. Each element of the list is a tuple of the track number and
        the title.
        
        There are three regex patterns used to pick out these pieces.
        
        INPUTS: 
        songList -- (default None) a list of song data compiled by the user. This 
                    must at least have the entries: 'album', 'title', and 
                    'trackNumber'.
        **criteria -- add arguments (e.g. genre = 'Classical') to limit the scope
                    of this function based off of track metadata. This argument is
                    passed direction to the getList method. If songList is given,
                    then criteria are applied to the songList
        
        OUTPUTS:
        songDict -- a dictionary indexed by a tuple with the album and song titles
                    containing lists of tracks that belong in each piece.
        '''
        # Get the songList, if not provided.
        songList = self.getList(initSongList = songList, **criteria)
        
        def recursiveSort(songList, level):
            # Build the songDict.
            songDict = {}
            for song in songList:
                if isinstance(song, dict):
                    print song
                # Get the full title.
                if level:
                    self.analyzeTitle(song, self.pattList[:2])
                else:
                    self.analyzeTitle(song, self.pattList)
                
                # Check if a pieceLabel was defined.
                if song.pieceLabel is None:
                    lastKey = song.mvmtLabel
                else:
                    lastKey = song.pieceLabel
                
                # Here we actually make the entry in the dict.
                key = (song.album, song.discNum, lastKey)
                if songDict.has_key(key):
                    songDict[key].append(song)
                else:
                    songDict[key] = [song]
            
            keys = songDict.keys()
            #NOTE:this could backfire if the entire collection was identified as one piece.
            # The idea is that if I can't break it down any further, stop trying.
            if len(keys) > 1: 
                for key in keys:
                    if len(songDict[key]) > 5:
                        mvmtList = songDict.pop(key)
                        songDict.update(recursiveSort(mvmtList, level + 1))
            
            return songDict
        
        return recursiveSort(songList, 0)
    
    def mix(self, name, numPieces, *args, **kwargs):
        '''
        This is the function that actually creates the shuffled playlist.
        
        Inputs:
        name         -- the name of the playlist
        numPieces    -- the number of pieces to be included in the playlist (note
                        that google play can only make a playlist of at most 1000
                        songs).
        update       -- If we are updating an earlier playlist, than we will over-
                        write it.
        Further arguments will be passed to getPieceDict to select what set of
        pieces will be used in the shuffling. See that documentation for details.
        
        Outputs:
        lop          -- the list of pieces in the order entered into the playlist
        '''
        # Get the value for update, or set it to its default.
        if kwargs.has_key('update'):
            update = kwargs.pop('update')
        else:
            update = False
        
        # Get the dictionary of relevant songs (indicated by *args and **kwargs)
        # indexed by piece (e.g. 'Beethoven Symphony No. 3').
        songDict = self.getPieceDict(*args, **kwargs)
        
        # Get the List Of Pieces (lop) and shuffle it.
        lop = songDict.keys()
        random.seed(random.randint(0,1000))
        random.shuffle(lop)
        
        # Now build the playlist.
        playlist = []
        for toptitle in lop[:numPieces]:
            subList = []
            for song in songDict[toptitle]:
                subList.append(song)
            subList.sort()
            for song in subList:
                playlist.append(song)
        
        # Now actually create the playlist.
        self.collection.writePlaylist(name, playlist, update)
        
        return lop
