from songLibs import Collection, GooglePlayCollection, LocalCollection, TunesCollection
import random
import re

class ClassyMixer(object):
    '''
    An object for managing music and looking through track info using regex.
    '''
    def __init__(self, collection):
        if not issubclass(collection, Collection):
            raise Exception("Give me a real collection")
        
        self.collection = collection()
        
        # Load the library
        self.library = self.collection.loadLibrary()
               
        # Load the list of playlists
        self.playlists = self.collection.loadPlaylists()
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
                data = song[label]
                if isinstance(crit, re._pattern_type):
                    itMatches = (crit.match(data) is not None)
                else:
                    itMatches = (data == crit)
                
                if not itMatches:
                    break # Do nothing
            else: # Add the song to the list
                songList.append(song)
        return songList
    
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
        (Note: please provide only one. songList takes precedence. If neither is
        provided, then the entire library will be used.)
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
        
        # Define the regex patterns to pick out movements of larger pieces.
        pattList = []
        # With numbers (including roman numerals)
        pattList.append(re.compile("(.*) *?(?:[-:]|^) *?(\d+)[.:]? *?(.*)$"))
        pattList.append(re.compile("(.*) *?(?:[-:]|^) *?([IVX]+)[^\w]+?(\w+.*)$"))
        # Without numbers
        pattList.append(re.compile("(.*) *?([:;]) *?(\w+.*)$"))
        pattList.append(re.compile("(.*)( +?- *?| *?- +?)(\w+.*)$"))
        
        # Build the songDict.
        songDict = {}
        for song in songList:
            # Get the full title.
            fulltitle = song['title']
            
            # Get the matches to the patterns. Only keep the ones where we
            # actually got a match.
            mList = []
            for i, patt in enumerate(pattList):
                m = patt.match(fulltitle)
                if m is not None:
                    mList.append((m.groups(),i))
            
            # This is the core of where we decide how to sort the pieces.
            #TODO: Make this better.
            for m in mList:
                if (m[0][0] is not None) and  (m[0][0] in song['composer']):
                    continue
                
                toptitle = (song['album'], mList[0][0][0], mList[0][1])
                subtitle = (song['discNumber'], song['trackNumber'], mList[0][0][-1])
                break
                
            else:
                toptitle = (song['album'], fulltitle, -1)
                subtitle = (song['discNumber'], song['trackNumber'], -1)
            
            # Here we actually make the entry in the dict.
            entry = (subtitle, song['id'])
            if songDict.has_key(toptitle):
                songDict[toptitle].append(entry)
            else:
                songDict[toptitle] = [entry]
        
        return songDict
    
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
            for subtitle, sid in songDict[toptitle]:
                subList.append((subtitle, sid))
            subList.sort()
            for _, sid in subList:
                playlist.append(sid)
        
        # Now actually create the playlist.
        self.collection.writePlaylist(name, playlist, update)
        
        return lop
