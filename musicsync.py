"""
    musicsync.py

    Provides a utility class around the Google Music API that allows for easy synching of playlists.
    Currently it will look at all the files already in the playlist and:
     Upload any missing files (and add them to the playlist)
     Add any files that are already uploaded but not in the online playlist
     Optionally remove any files from the playlist that are not in the local copy (does not delete
     files!)
     Uploads are done one by one followed by a playlist update for each file (rather than as a
     batch)
    It does not remove duplicate entries from playlists or handle multiple entries.

    TODO: Add optional duplicate remover

    API used: https://github.com/simon-weber/Unofficial-Google-Music-API
    Thanks to: Kevion Kwok and Simon Weber

    Use at your own risk - especially for existing playlists

    Free to use, reuse, copy, clone, etc

    Usage:
     ms = MusicSync()
     # Will prompt for Email and Password - if 2-factor auth is on you'll need to generate a one-
       time password
     ms.sync_playlist("c:/path/to/playlist.m3u")

     ms.delete_song("song_id")
"""
__author__ = "Tom Graham"
__email__ = "tom@sirwhite.com"


from gmusicapi.api import Api
import eyeD3
import json
import os
from getpass import getpass

MAX_UPLOAD_ATTEMPTS_PER_FILE = 3

class MusicSync(object):
    def __init__(self, email=None, password=None):
        self.api = Api()
        if not email:
            email = raw_input("Email: ")
        if not password:
            password = getpass()
        self.logged_in = self.api.login(email, password)

        if not self.logged_in:
            print "Login failed..."
            return

        print "Logged in as %s" % email

        print "Fetching playlists from Google..."
        self.playlists = self.api.get_all_playlist_ids(auto=False, always_id_lists=True)
        print "Got %d playlists." % len(self.playlists['user'])

    def sync_playlist(self, filename, remove_missing=False):
        title = os.path.splitext(os.path.basename(filename))[0]
        print "Synching playlist: %s" % filename
        if title not in self.playlists['user']:
            print " didn't exist... creating..."
            self.playlists['user'][title] = [self.api.create_playlist(title)]

        plid = self.playlists['user'][title][0]
        goog_songs = self.api.get_playlist_songs(plid)
        print "%d songs already in Google Music playlist" % len(goog_songs)
        pc_songs = self.get_files_from_playlist(filename)
        print "%d songs in local playlist" % len(pc_songs)

        existing_files = 0
        added_files = 0
        failed_files = 0
        removed_files = 0

        for fn in pc_songs:
            if self.file_already_in_list(fn, goog_songs):
                existing_files += 1
                continue
            print "Adding: %s" % os.path.basename(fn)
            online = self.find_song(fn)
            song_id = None
            if online:
                song_id = online['id']
                print " already uploaded [%s]" % song_id
            else:
                attempts = 0
                result = []
                while not result and attempts < MAX_UPLOAD_ATTEMPTS_PER_FILE:
                    print " attempting upload..."
                    attempts += 1
                    result = self.api.upload(fn)
                if not result:
                    print " upload failed - skipping"
                else:
                    song_id = result[fn]
                    print " upload complete [%s]" % song_id

            if not song_id:
                failed_files += 1
                continue

            added = self.api.add_songs_to_playlist(plid, song_id)
            print added
            print " done adding to playlist"
            added_files += 1

        if remove_missing:
            for s in goog_songs:
                print "Removing: %s" % s['title']
                self.api.remove_songs_from_playlist(plid, s.id)
                removed_files += 1

        print ""
        print "%d songs unmodified" % existing_files
        print "%d songs added" % added_files
        print "%d songs failed" % failed_files
        print "%d songs removed" % removed_files


    def get_files_from_playlist(self, filename):
        files = []
        f = open(filename, 'r')
        for line in f:
            line = line.rstrip().replace('\xef','').replace('\xbb','').replace('\xbf','')
            if line == "" or line[0] == "#" or not os.path.exists(line):
                continue
            files.append(line)
        f.close()
        return files

    def file_already_in_list(self, filename, goog_songs):
        tag = self.get_id3_tag(filename)
        i = 0
        while i < len(goog_songs):
            if goog_songs[i]['title'] == tag.getTitle() and\
            goog_songs[i]['artist'] == tag.getArtist() and\
            goog_songs[i]['album']  == tag.getAlbum() and\
            goog_songs[i]['track'] == tag.getTrackNum()[0]:
                goog_songs.pop(i)
                return True
            i += 1
        return False

    def get_id3_tag(self, filename):
        tag = eyeD3.Tag()
        tag.link(filename)
        if not tag.getTitle():
            tag.setTitle(os.path.splitext(os.path.basename(filename))[0])
        return tag

    def find_song(self, filename):
        tag = self.get_id3_tag(filename)
        results = self.api.search(tag.getTitle())
        # NOTE - dianostic print here to check results if you're creating duplicates
        for r in results['song_hits']:
            if r['title'] == tag.getTitle() and\
            r['artist'] == tag.getArtist() and\
            r['album'] == tag.getAlbum() and\
            r['track'] == tag.getTrackNum()[0]:
                # TODO: add rough time check to make sure its "close"
                return r
        return None

    def delete_song(self, sid):
        self.api.delete_songs(sid)
        print "Deleted song by id [%s]" % sid
