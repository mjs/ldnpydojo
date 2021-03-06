"""
file: sounds.py
purpose: to load all the sounds, and manage the playing of them.

Probably have different sets of sounds in here somehow.

NOTE: not using pygames channel queueing as it only allows one sound to be 
  queued.  Also the sound can only be queued on a certain channel.

"""


from pygame import mixer
import os
import glob

#the as alias allows re-imports
from cyclic_list import cyclic_list as cyclic_list_func
from data import data_dir

SOUND_PATH = os.path.join(data_dir(), "sounds")


def get_sound_list(path = SOUND_PATH):
    """ gets a list of sound names without thier path, or extension.
    """
    # load a list of sounds without path at the beginning and .ogg at the end.
    sound_list = []
    for ext in ['.wav', '.ogg']:
        sound_list += map(lambda x:x[len(path)+1:-4], 
                         #glob.glob(os.path.join(path,"*.ogg")) 
                         glob.glob(os.path.join(path,"*" + ext)) 
                        )

    return sound_list
       

SOUND_LIST = get_sound_list()



class Sounds:
    """ Controls loading, mixing, and playing the sounds.
        Having seperate classes allows different groups of sounds to be 
         loaded, and unloaded from memory easily.

        Useage:
            sm = Sounds()
            sm.load()
    """

    sounds = None

    def __init__(self, sound_list = SOUND_LIST, sound_path = SOUND_PATH):
        """
        """
        self.sounds = {}
        self.chans = {}

        self._debug_level = 0

        self.sound_list = sound_list
        self.sound_path = sound_path

        # sounds which are queued to play.
        self.queued_sounds = []

        Sounds.sounds = self


    def _debug(self, x, debug_level = 0):
        if self._debug_level > debug_level:
            print (x)


    def init(self):
        #mixer.pre_init(22050, -16, 2, 1024)
        mixer.init()
        self.load()


    def load(self, sound_list = [], sound_path = SOUND_PATH):
        """loads sounds."""
        sounds = self.sounds
        class NoneSound:
            def play(self): pass
            
        if not mixer:
            for name in sound_list:
                sounds[name] = NoneSound()
            return
        for name in sound_list:
            if not sounds.has_key(name):

                for ext in ['.wav', '.ogg']:
                    fullname = os.path.join(sound_path, name+ext)
                    if os.path.exists(fullname):
                        break

                try: 
                    sound = mixer.Sound(fullname)
                except: 
                    sound = None
                    self._debug("Error loading sound %s" % fullname)
                sounds[name] = sound


    def get_sound(self, name):
        """ Returns a Sound object for the given name.
        """
        if not self.sounds.has_key(name):
            self.load([name])

        return self.sounds[name]


    def stop(self, name):
        if self.chans.has_key(name):
            if self.chans[name]:
                if self.chans[name].get_busy():
                    self.chans[name].stop()


    def stop_all(self):
        """ stops all sounds.
        """

        for name in self.chans.keys():
            self.stop(name)


    def play(self, name, 
                   volume=[1.0, 1.0], 
                   wait = 0,
                   loop = 0):
        """ plays the sound with the given name.
            name - of the sound.
            volume - left and right.  Ranges 0.0 - 1.0
            wait - used to control what happens if sound is allready playing:
                0 - will not wait if sound playing.  play anyway.
                1 - if there is a sound of this type playing wait for it.
                2 - if there is a sound of this type playing do not play again.
            loop - number of times to loop.  -1 means forever.
        """

        vol_l, vol_r = volume

        sound = self.get_sound(name)

        if sound:
            if wait in [1,2]:

                if self.chans.has_key(name) and self.chans[name].get_busy():
                    if wait == 1:
                        # sound is allready playing we wait for it to finish.
                        self.queued_sounds.append((name, volume, wait))
                        return
                    elif wait == 2:
                        # not going to play sound if playing.
                        return
                        
            self.chans[name] = sound.play(loop)

            if not self.chans[name]:
                if loop == 1:
                    # forces a channel to return. we fade that out,
                    #  and enqueue our one.
                    self.chans[name] = mixer.find_channel(1)

                    #TODO: does this fadeout block?
                    self.chans[name].fadeout(100)
                    self.chans[name].queue(sound)
                else:
                    # the pygame api doesn't allow you to queue a sound and
                    #  tell it to loop.  So we hope for the best, and queue
                    #  the sound.
                    self.queued_sounds.append((name, volume, wait))
                    # delete the None channel here.
                    del self.chans[name]

            elif self.chans[name]:
                self.chans[name].set_volume(vol_l, vol_r)
        else:
            raise 'not found'


    def update(self, elapsed_time):
        """
        """
        for name in self.chans.keys():
            if not self.chans[name]:
                # it may be a NoneType I think.
                del self.chans[name]
            elif not self.chans[name].get_busy():
                del self.chans[name]
        old_queued = self.queued_sounds
        self.queued_sounds = []

        for snd_info in old_queued:
            self.play(*snd_info)

        self.update_music(elapsed_time)

    def set_music_tracks(self, music_tracks):
        ''' music_tracks([]) loops over the given music tracks.
        '''
        if not hasattr(self, 'music_tracks'):
            self.music_tracks = cyclic_list_func(music_tracks)

    def update_music(self, elapsed_time):
        if hasattr(self, 'music_tracks'):
            if not mixer.music.get_busy():
                # get next track.
                musicname = self.music_tracks.cur()
                self.play_music(musicname, loop=0)
                self.music_tracks.next()


    def play_music(self, musicname, loop=-1):
        """ plays a music track.  Only one can be played at a time.
            So if there is one playing, it will be stopped and the new 
             one started.
        """
        music = mixer.music

        if not music: return
        if music.get_busy():
            #we really should fade out nicely and
            #wait for the end music event, for now, CUT 
            music.stop()

        fullname = os.path.join(data_dir(), 'music', musicname)
        fullname_ogg = fullname + ".ogg"
        if os.path.exists(fullname_ogg):
            fullname = fullname_ogg
    
        music.load(fullname)
        music.play(loop)
        music.set_volume(1.0)


