Provides a utility class around the Google Music API that allows for easy synching of m3u playlists.

##Features

Currently it will look at all the files already in the playlist and:
* Upload any missing files (and add them to the playlist)
* Add any files that are already uploaded but not in the online playlist
* Optionally remove any files from the playlist that are not in the local copy (does not delete
* files!)
* Uploads are done one by one followed by a playlist update for each file (rather than as a
 batch)

It does not remove duplicate entries from playlists or handle multiple entries.

**TODO:** Add optional duplicate remover

##Usage

    from musicsync import MusicSync
    ms = MusicSync()
    # Will prompt for Email and Password - if 2-factor auth is on you'll need to generate a one-time password

    # To sync a playlist
    ms.sync_playlist("c:/path/to/playlist.m3u")

    # To sync a playlist including removing files that are no longer listed locally
    ms.sync_playlist("/path/to/playlist.m3u", remove_missing=True)

    # To delete a song from the cloud (provided only as convenience - must know the song ID)
    ms.delete_song("song_id")


##Requirements
Requires:
* gmusicapi (can use: pip install gmusicapi - or get it from https://github.com/simon-weber/Unofficial-Google-Music-API)
* eyeD3 (pip doesn't seem to install it properly, at least on Windows... can get from http://eyed3.nicfit.net/)

- - -

API used: https://github.com/simon-weber/Unofficial-Google-Music-API

Thanks to: Kevin Kwok and Simon Weber

Use at your own risk - especially for existing playlists

Free to use, reuse, copy, clone, etc
