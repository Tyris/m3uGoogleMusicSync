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
import mutagen
import json
import os
import time
import re
import codecs
from getpass import getpass
from httplib import BadStatusLine, CannotSendRequest

MAX_UPLOAD_ATTEMPTS_PER_FILE = 3
MAX_CONNECTION_ERRORS_BEFORE_QUIT = 5
STANDARD_SLEEP = 5

class MusicSync(object):
    def __init__(self, email=None, password=None):
        self.api = Api()
        if not email:
            email = raw_input("Email: ")
        if not password:
            password = getpass()

        self.email = email
        self.password = password

        self.logged_in = self.auth()

        print "Fetching playlists from Google..."
        self.playlists = self.api.get_all_playlist_ids(auto=False, always_id_lists=True)
        print "Got %d playlists." % len(self.playlists['user'])
        print ""


    def auth(self):
        self.logged_in = self.api.login(self.email, self.password)
        if not self.logged_in:
            print "Login failed..."
            exit()

        print ""
        print "Logged in as %s" % self.email
        print ""


    def sync_playlist(self, filename, remove_missing=False):
        filename = self.get_platform_path(filename)
        os.chdir(os.path.dirname(filename))
        title = os.path.splitext(os.path.basename(filename))[0]
        print "Synching playlist: %s" % filename
        if title not in self.playlists['user']:
            print "   didn't exist... creating..."
            self.playlists['user'][title] = [self.api.create_playlist(title)]
        print ""

        plid = self.playlists['user'][title][0]
        goog_songs = self.api.get_playlist_songs(plid)
        print "%d songs already in Google Music playlist" % len(goog_songs)
        pc_songs = self.get_files_from_playlist(filename)
        print "%d songs in local playlist" % len(pc_songs)

        existing_files = 0
        added_files = 0
        failed_files = 0
        removed_files = 0
        fatal_count = 0

        for fn in pc_songs:
            if self.file_already_in_list(fn, goog_songs):
                existing_files += 1
                continue
            print ""
            print "Adding: %s" % os.path.basename(fn)
            online = self.find_song(fn)
            song_id = None
            if online:
                song_id = online['id']
                print "   already uploaded [%s]" % song_id
            else:
                attempts = 0
                result = []
                while not result and attempts < MAX_UPLOAD_ATTEMPTS_PER_FILE:
                    print "   uploading... (may take a while)"
                    attempts += 1
                    try:
                        result = self.api.upload(fn)
                    except (BadStatusLine, CannotSendRequest):
                        # Bail out if we're getting too many disconnects
                        if fatal_count >= MAX_CONNECTION_ERRORS_BEFORE_QUIT:
                            print ""
                            print "Too many disconnections - quitting. Please try running the script again."
                            print ""
                            exit()

                        print "Connection Error -- Reattempting login"
                        fatal_count += 1
                        self.api.logout()
                        result = []
                        time.sleep(STANDARD_SLEEP)

                    except:
                        result = []
                        time.sleep(STANDARD_SLEEP)

                if not result:
                    print "      upload failed - skipping"
                else:
                    song_id = result[fn]
                    print "   upload complete [%s]" % song_id

            if not song_id:
                failed_files += 1
                continue

            added = self.api.add_songs_to_playlist(plid, song_id)
            time.sleep(.3) # Don't spam the server too fast...
            print "   done adding to playlist"
            added_files += 1

        if remove_missing:
            for s in goog_songs:
                print ""
                print "Removing: %s" % s['title']
                self.api.remove_songs_from_playlist(plid, s.id)
                time.sleep(.3) # Don't spam the server too fast...
                removed_files += 1

        print ""
        print "---"
        print "%d songs unmodified" % existing_files
        print "%d songs added" % added_files
        print "%d songs failed" % failed_files
        print "%d songs removed" % removed_files


    def get_files_from_playlist(self, filename):
        files = []
        f = codecs.open(filename, encoding='utf-8')
        for line in f:
            line = line.rstrip().replace(u'\ufeff',u'')
            if line == "" or line[0] == "#":
                continue
            path  = os.path.abspath(self.get_platform_path(line))
            if not os.path.exists(path):
                print "Failed on: %s" % line
                continue
            files.append(path)
        f.close()
        return files

    def file_already_in_list(self, filename, goog_songs):
        tag = self.get_id3_tag(filename)
        i = 0
        while i < len(goog_songs):
            if self.tag_compare(goog_songs[i], tag):
                goog_songs.pop(i)
                return True
            i += 1
        return False

    def get_id3_tag(self, filename):
        data = mutagen.File(filename, easy=True)
        r = {}
        if 'title' not in data:
            title = os.path.splitext(os.path.basename(filename))[0]
            print 'Found song with no ID3 title, setting using filename:'
            print '  %s' % title
            print '  (please note - the id3 format used (v2.4) is invisible to windows)'
            data['title'] = [title]
            data.save()
        r['title'] = data['title'][0]
        r['track'] = int(data['tracknumber'][0].split('/')[0]) if 'tracknumber' in data else 0
        # If there is no track, try and get a track number off the front of the file... since thats
        # what google seems to do...
        # Not sure how google expects it to be formatted, for now this is a best guess
        if r['track'] == 0:
            m = re.match("(\d+) ", os.path.basename(filename))
            if m:
                r['track'] = int(m.group(0))
        r['artist'] = data['artist'][0] if 'artist' in data else ''
        r['album'] = data['album'][0] if 'album' in data else ''
        return r

    def find_song(self, filename):
        tag = self.get_id3_tag(filename)
        results = self.api.search(tag['title'])
        # NOTE - dianostic print here to check results if you're creating duplicates
        #print results['song_hits']
        #print "%s ][ %s ][ %s ][ %s" % (tag['title'], tag['artist'], tag['album'], tag['track'])
        for r in results['song_hits']:
            if self.tag_compare(r, tag):
                # TODO: add rough time check to make sure its "close"
                return r
        return None

    def tag_compare(self, g_song, tag):
        # If a google result has no track, google doesn't return a field for it
        if 'track' not in g_song:
            g_song['track'] = 0
        return g_song['title'].lower() == tag['title'].lower() and\
               g_song['artist'].lower() == tag['artist'].lower() and\
               g_song['album'].lower() == tag['album'].lower() and\
               g_song['track'] == tag['track']

    def delete_song(self, sid):
        self.api.delete_songs(sid)
        print "Deleted song by id [%s]" % sid

    def get_platform_path(self, full_path):
        # Try to avoid messing with the path if possible
        if os.sep == '/' and '\\' not in full_path:
            return full_path
        if os.sep == '\\' and '\\' in full_path:
            return full_path
        if '\\' not in full_path:
            return full_path
        return os.path.normpath(full_path.replace('\\', '/'))
