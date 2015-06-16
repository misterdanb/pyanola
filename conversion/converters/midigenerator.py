#!/usr/bin/env python2
from mido import Message, MidiFile, MidiTrack, MetaMessage, merge_tracks
import toml

class MidiGenerator():
    CONFIG_FILE = "midi.conf"

    def __init__(self):
        self.config = toml.load(MidiGenerator.CONFIG_FILE)
        self.debug = self.config["settings"]["debug"]
        self.filename = self.config["settings"]["filename"]
        self.speed = self.config["settings"]["speed"]

    def create(self, data):
        with MidiFile() as outfile:
            start_track = MidiTrack()
            start_track.append(MetaMessage('set_tempo'))
            start_track.append(Message('program_change', program=1))

            last_track=start_track

            for line in data["lines"]:
                track = MidiTrack()
                pitch=127-line["level"]/4 #TODO
                delta = 0

                last_note=(0,0)

                for note in line["notes"]:
                    delta=int((self.speed*10.)*(note[0]-last_note[1]))
                    track.append(Message('note_on', note=pitch, velocity=100, time=delta))
                    delta=int((self.speed*10.)*(note[1]-note[0]))
                    track.append(Message('note_off', note=pitch, velocity=100, time=delta))

                    last_note = note

                track=merge_tracks([track, last_track])
                last_track = track

            outfile.tracks.append(track)
            outfile.save(self.filename)
