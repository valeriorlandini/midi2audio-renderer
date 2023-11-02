#   Copyright © 2023 Valerio Orlandini <valeriorlandini@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import json
import mido
import numpy as np
import pedalboard

def read_json_file(filename):
    json_file = json.load(open(filename))

    synth_settings = []
    effect_chains = []
    master_chain = []

    for track in json_file["tracks"]:
        track_synth_settings = {"plugin": track["synthesizer"],
                                "preset": track["preset"]}
        synth_settings.append(track_synth_settings)
        track_effect_chain = []
        for effect in track["effect_chain"]:
            effect_chain = {"plugin": effect["effect"],
                            "preset": effect["preset"]}
            track_effect_chain.append(effect_chain)
        effect_chains.append(track_effect_chain)
    for effect in json_file["master_effects"]:
        master_effect = {"plugin": effect["effect"],
                        "preset": effect["preset"]}
        master_chain.append(master_effect)

    return synth_settings, effect_chains, master_chain

def read_midi_file(filename):
    midi_file = mido.MidiFile(filename)
    length = midi_file.length
    tracks = []
    tempo = 500000

    for event in midi_file:
        if event.type == "set_tempo":
            tempo = event.tempo
            break

    for track in midi_file.tracks:
        current_track = get_track_events(midi_file, track, tempo)
        if current_track:
            tracks.append(current_track)
    
    return midi_file, tracks, length

def get_track_events(midi_file, midi_track, tempo=500000):
    track_events = []
    last_time = 0
    for msg in midi_track:
        if not msg.is_meta:
            m_time = mido.tick2second(msg.time, midi_file.ticks_per_beat, tempo)
            msg.time = mido.tick2second(msg.time, midi_file.ticks_per_beat, tempo) + last_time
            last_time += m_time
            track_events.append(msg)
    
    return track_events
  
def generate_track(id, track_events,
                   length,
                   synth_settings,
                   effect_chain,
                   sample_rate = 44100,
                   channels = 2):
    synthesizer = pedalboard.load_plugin(synth_settings["plugin"])
    if (synth_settings["preset"]):
        synthesizer.load_preset(synth_settings["preset"])
    if not synthesizer.is_instrument:
        print("The specified synthesizer plugin does not accept MIDI input")
        return
    
    output = synthesizer(track_events, sample_rate=sample_rate, duration=length, num_channels=channels)
    for effect_settings in effect_chain:
        if effect_settings["plugin"]:
            effect = pedalboard.load_plugin(effect_settings["plugin"])
            if (effect_settings["preset"]):
                effect.load_preset(effect_settings["preset"])
            output = effect(output, sample_rate=sample_rate)

    with pedalboard.io.AudioFile(f"track_{id}.wav", "w", sample_rate, channels) as f:
        f.write(output)
    return output

def apply_master_effects(mix, effect_chain, sample_rate = 44100):
    for effect_settings in effect_chain:
        if effect_settings["plugin"]:
            effect = pedalboard.load_plugin(effect_settings["plugin"])
            if (effect_settings["preset"]):
                effect.load_preset(effect_settings["preset"])
            mix = effect(mix, sample_rate=sample_rate)
    return mix

def audio_render(midi_in, json_in, audio_out, sample_rate = 44100, channels = 2, tail = 0):
    midi_file, tracks, length = read_midi_file(midi_in)
    synth_settings, effect_settings, master_chain = read_json_file(json_in)
    audio_mix = np.zeros((channels, int((length + tail) * sample_rate)))
    
    for track_id, track in enumerate(tracks):
        if track and len(synth_settings) > track_id:
            track_out = generate_track(track_id, track,
                                       length + tail,
                                       synth_settings[track_id],
                                       effect_settings[track_id],
                                       sample_rate,
                                       channels)
            audio_mix += track_out

    with pedalboard.io.AudioFile(audio_out, "w", sample_rate, channels) as f:
        f.write(apply_master_effects(audio_mix, master_chain))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MIDI to audio renderer")
    parser.add_argument('-i', '--input', help="MIDI input", default=None)
    parser.add_argument('-j', '--json', help="JSON file with export settings", default=None)
    parser.add_argument('-o', '--output', help="Audio output (default out.wav)", default="out.wav")
    parser.add_argument('-r', '--srate', help="Sample rate (default 44100)", type=int, default=44100)
    parser.add_argument('-c', '--channels', help="Audio channels (default 2)", type=int, default=2)
    parser.add_argument('-t', '--tail', help="Tail of the file after the last note, in seconds (default 0.0)", type=float, default=0.0)
    args = parser.parse_args()

    if args.input and args.json:
        audio_render(args.input, args.json, args.output, args.srate, args.channels, args.tail)
