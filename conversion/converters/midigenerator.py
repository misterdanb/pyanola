from mido import Message, MidiFile, MidiTrack, MetaMessage, merge_tracks
import toml

class MidiGenerator():
    CONFIG_FILE = "midigenerator.conf"
    SPECS_FILE = ".specs.conf"

    def __init__(self):
        self.config = toml.load(MidiGenerator.CONFIG_FILE)
        self.debug = self.config["settings"]["debug"]
        self.filename = self.config["settings"]["filename"]

        self.specs = toml.load(MidiGenerator.SPECS_FILE)
        self.highest_tone = self.specs["role"]["highest_tone"]
        self.lowest_tone = self.specs["role"]["lowest_tone"]
        self.control_top = self.specs["role"]["control_lines_top"]
        self.control_bottom = self.specs["role"]["control_lines_bottom"]

    def create(self, data):
        with MidiFile() as outfile:
            start_track = MidiTrack()
            start_track.append(MetaMessage("set_tempo"))
            start_track.append(Message("program_change", program=1))

            last_track = start_track

            for line in data["lines"][self.control_top:len(data["lines"])-self.control_bottom]:
                # only add those who have a level attached
                if "level" in line:
                    track = MidiTrack()
                    pitch = int(self.highest_tone-(line["level"]-self.control_top))

                    delta = 0
                    last_note = (0,0)

                    for note in line["notes"][1:]:
                        delta = int((note[0] - last_note[1]))
                        track.append(Message("note_on", note=pitch, velocity=100, time=delta))
                        delta = int((note[1] - note[0]))
                        track.append(Message("note_off", note=pitch, velocity=100, time=delta))

                        last_note = note

                    track = merge_tracks([ track, last_track ])
                    last_track = track

            outfile.tracks.append(track)
            outfile.save(self.filename)
