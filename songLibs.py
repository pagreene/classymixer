
class SongData(object):
    '''
    Abstract object that allows access to different types of song data
    '''
    def __init__(self):
        pass

class Collection(object):
    '''
    Abstract object that defines the methods that must be present in an object
    used to interface with one's music collection.
    '''
    def __init__(self):
        self.library = None
        self.playlists = None
        return
    
    def loadLibrary(self):
        '''
        This function is used to load all the song data
        '''
        raise NotImplementedError()
    
    def loadPlaylists(self):
        '''
        This function should be used to get all the playlists
        '''
        raise NotImplementedError()
    
    
class GooglePlayCollection(Collection):
    '''
    Concrete object used to interface with google play.
    
    Capabilities:
    - Read Song data
    - Read playlist data
    - Write playlist data
    '''
    def __init__(self):
        # Acquire the api
        self.__api = Mobileclient()
        
        # Get the user's login info (username and password)
        username = raw_input("Google username:")
        if re.match(".*?@gmail.com", username) is None:
            username += "@gmail.com"
        password = getpass.getpass("Google password:")
        
        # Log into the api. Note that there is a warning that states the
        # connection is insecure when using Python 2.7. This should only be
        # mentioned once, not 3+ times, unfortunately I can't seem to catch the
        # exception.
        self.__api.login(username,password,Mobileclient.FROM_MAC_ADDRESS)
        
        return Collection.__init__(self)
    
    def __del__(self):
        self.__api.logout()
        return
    
    #TODO: This object will I think manage the library in the future, but
    # for now I am doing it this way so that the code still works. 
    def loadLibrary(self):
        self.library = self.__api.get_all_songs()
        return self.library[:]
    
    def loadPlaylists(self):
        self.playlists = self.__api.get_all_playlists()
        return self.playlists[:]

    def writePlaylist(self, name, playlist, update = False):
        '''
        This is the function to actually writes the playlist.
        
        INPUTS:
        name        -- the name of the new playlist
        playlist    -- the actualy list of pid's to be used to create the playlist
        
        OUTPUS:
        None
        '''
        # Check to see if the playlist already exists.
        nOld = 0
        pattStr = '%s {0,1}\({0,1}(\d*)\){0,1}' % name
        for plDesc in self.playlists:
            # If it does (or some number <name> (#) of the name does)
            if re.match(pattStr, plDesc['name']) is not None:
                # If this program made it, and we're updating, then overwrite.
                if plDesc['description'] == plistDescStr and update:
                    self.__api.delete_playlist(plDesc['id'])
                    break
                # Otherwise, make a one with a higher number. More particularly
                # I'm just seeing what numbers are out there, and over the course
                # of this for-loop, I recall which was the biggest, and I make one
                # that is one bigger.
                else:
                    nRe = re.findall(pattStr, plDesc['name'])
                    if nRe[0] != '':
                        nNew = int(nRe[0]) + 1
                    else:
                        nNew = 1
                    if nNew > nOld:
                        nOld = nNew
        
        # Set the name based on what we decided above.
        name = '%s (%d)' % (name, nOld)
        
        # Make the playlist
        pid = self.__api.create_playlist(name, description = plistDescStr)
        
        # Populate the playlist.
        self.__api.add_songs_to_playlist(pid, playlist)
        
        return

import os
class LocalCollection(Collection):
    '''
    Concrete object used to interface with a local music collection
    
    Capabilities:
    - Read songdata
    - Write songdata
    - Read playlist data
    - Write playlist data
    
    Note that this looks at and edits the actual mp3/mp4 tag info on the files.
    '''
    def __init__(self):
        self.musicDir = raw_input("Music directory:")
        self.playlistDir = raw_input("Playlist directory:")
        return Collection.__init__(self)
    
    def loadLibrary(self):
        songList = []
        # This is a recursive function to search through directories, starting
        # at the top-most Music dir and working down, looking for musci files...
        def rLook(dirpath):
            subItemList = os.listdir(dirpath)
            for subItem in subItemList:
                subPath = dirpath +'/'+ subItem
                if os.path.isdir(subPath):
                    rLook(subPath + '/')
                elif re.match(".*?\.mp.*?", subPath) is not None:
                    # Then loading them into a path.
                    songList.append(taglib.File(subPath))
        
        rLook(self.musicDir)
                    
        return songList
    
    def loadPlaylists(self):
        pass

class TunesCollection(Collection):
    '''
    Concrete object to read the iTunes xml file. Note that this is effectively
    read-only.
    
    Capabilities:
    - Read song data
    - Read playlist data
    '''
    def __init__(self):
        self.xmlPath = raw_input("iTunes xml file path:")
        return Collection.__init__(self)
    
    def loadLibrary(self):
        '''
        Load iTune's library data.
        '''
