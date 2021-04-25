from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo

from io import BytesIO

from dataclasses import dataclass


# This is for testing. mido's MetaMessage's __repr__ isn't doesn't produce
# python I can copy and paste to create integration tests, so here is a 
# wrapper that does. We use this internally in the main tested function, then
# convert to MetaMessage at the end.
@dataclass
class SetTempo:
    tempo: int
    time: int

    def to_mido(self):
        return MetaMessage('set_tempo', tempo=self.tempo, time=self.time)

class MidiTempoMap:
    def __init__(self, project):
        self.project = project
        self.mid = MidiFile()

    def generate(self):
        tempo_map_bytes = BytesIO()
        track = self._generate_track(self.project.tempo_automation_events, self.project.TEMPO_QUANT)
        self.mid.tracks.append(track)
        self.mid.save(file=tempo_map_bytes)
        return tempo_map_bytes.getvalue()
    
    def _beats2ticks(self, beats):
        return beats * self.mid.ticks_per_beat
    
    def _generate_track(self, tempo_automation_events, tempo_quant):
        track = MidiTrack()
        track.append(Message('note_on', note=64, velocity=64, time=0))
        track += [x.to_mido() for x in self._render_map(tempo_automation_events, tempo_quant)]
        track.append(Message('note_off', note=64, velocity=127, time=32))
        return track
    
    def _render_map(self, tempo_automation_events, quant):
        messages = []
        
        if tempo_automation_events is None:
            # if no tempo auto, our map is a single point at the start. we may encounter
            # that issue with live where it revert back to the original bpm with 1
            # point you need to click away.
            messages.append(SetTempo(bpm2tempo(self.project.beats_per_min), 0))
            # messages.append(MetaMessage('set_tempo', tempo=bpm2tempo(self.project.beats_per_min), time=0))
            return messages

        for i, event in enumerate(tempo_automation_events):
            curr_bpm = event.bpm
            curr_beat = max(event.beat, 0)  # due to Ableton negative point

            if i == 0:
                beats_elapsed = curr_beat 
                time_elapsed_tick = self._beats2ticks(beats_elapsed)
                messages.append(SetTempo(bpm2tempo(curr_bpm), int(time_elapsed_tick)))
                continue

            prev = tempo_automation_events[i-1]
            beats_elapsed = curr_beat - max(prev.beat, 0)
            time_elapsed_tick = self._beats2ticks(beats_elapsed)

            if prev.bpm != curr_bpm and beats_elapsed:
                messages += self._render_slope(curr_bpm, prev.bpm, beats_elapsed, quant)
            else:
                # if we are on a horizontal line or vertical line
                messages.append(SetTempo(bpm2tempo(curr_bpm), int(time_elapsed_tick)))
        
        return messages

    def _render_slope(self, curr_bpm, prev_bpm, beats_elapsed, quant):
        messages = []

        # if we are on a slope
        bpm_diff = curr_bpm - prev_bpm
        slope = bpm_diff / beats_elapsed 

        beat_increment = 4 / quant  # .e.g .25 for ableton

        num_segments = beats_elapsed / beat_increment
        bpm_increment = bpm_diff / num_segments 

        bpm_accumulator = prev_bpm

        # FIXME: can't just cast to int - need to handle non aligned
        for i in range(int(num_segments)):
            # for every segment, we emit a horizontal line and a vertical
            # line.

            messages.append(SetTempo(bpm2tempo(bpm_accumulator), int(self._beats2ticks(beat_increment))))

            # currx = i*beat_increment +beat_increment 
            # ydiff = slope * currx
            new_bpm = bpm_accumulator + bpm_increment 
            messages.append(SetTempo(bpm2tempo(new_bpm), 0))
            bpm_accumulator = new_bpm
        
        return messages