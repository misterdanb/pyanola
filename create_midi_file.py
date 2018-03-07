#!/usr/bin/env python
"""
Create a new MIDI file with some random notes.

The file is saved to test.mid.
"""

import random
from mido import Message, MidiFile, MidiTrack

notes = [64, 64+3, 64+7, 64+12]
bass = [32, 32+7, 32+12]

with MidiFile() as outfile:
	track = MidiTrack()
	snd_track = MidiTrack()

	track.append(Message('program_change', program=1))
	snd_track.append(Message('program_change', program=1))

	delta = 128
	for i in range(50):
		note = random.choice(notes)
		track.append(Message('note_on', note=note, velocity=100, time=delta))
		track.append(Message('note_off', note=note, velocity=100, time=delta))

	for i in range(50):
		note = random.choice(bass)
		snd_track.append(Message('note_on', note=note, velocity=100, time=delta))
		snd_track.append(Message('note_off', note=note, velocity=100, time=delta))


	outfile.tracks.append(track)
	outfile.tracks.append(snd_track)
	outfile.save('test.mid')
