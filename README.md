# midi2audio-renderer
A Python script to render MIDI files to audio from the command line using Spotify [Pedalboard library](https://spotify.github.io/pedalboard/).

Before using the script, install the requirements:
`pip install -r requirements.txt`

Usage:
`python midi2audio-renderer.py -i [MIDI INPUT] -j [JSON CONFIG FILE] -o [AUDIO OUTPUT] -r [SAMPLE RATE] -c [AUDIO CHANNELS] -t [TAIL AFTER LAST NOTE]`

The JSON should be formatted according to the included `example_json.json`, which should be pretty self-explainatory. You should insert the path to a synthesizer plugin (VST3 or AU) and to an optional preset for each track of your MIDI file. You can add all the effects you want, following the same syntax. The bottom section, that works in the same way, is for master effects. It is not necessary to remove blank effect slots: they are simply ignored.

MIDI input file and JSON config file must be provided, the other parameters are optional and have default values. Use `--help` option for further information.

Currently tested on Linux with VST3 plugins.