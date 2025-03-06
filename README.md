# Media controller, that observes and playes media on a dlna renderer.

Scripts are written for Python3.

Has endpoints to control a dlna media renderer via REST-ful commands.
/pause and /stop endpoints, as well as /state (to retrieve the current state) for renderer.

/play allowes to:
- define a url to play
- allowes to loop the playback
- allowes to define a title and/or artist search that is run against a mediaserver and play a random result

It is somehow interconnected to these other projects of mine:
- https://github.com/derHeinz/dlna (this project has a copy of this within it's own sources)
- https://github.com/derHeinz/voicecommand (that uses this project's server)

TODOs
- [X] has a /info endpoint to see config
- [X] should also observe "non-looping" playback, because it otherways thinks it's always running!
- [X] play should return a "description" describing the current state (e.g. 'spiele Lieder von Queen').
- [X] add started_timestamp to /state endpoint to see when the command was invoked.
- [X] add exit reason for better understanding.
- [x] possibility to control 2 or more media renderers.
- [X] fix bug where started_timestamp is recalculated for every song.
- [ ] ability to search/play video also
- [ ] allow several media servers
