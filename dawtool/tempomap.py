from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo

from io import BytesIO

class MidiTempoMap:
    def __init__(self, project):
        self.project = project

    def generate(self):
        tempo_map_bytes = BytesIO()
        mid = MidiFile()
        track = self._generate_track(self.project.tempo_automation_events, self.project.TEMPO_QUANT, mid.ticks_per_beat)
        mid.tracks.append(track)
        mid.save(file=tempo_map_bytes)
        return tempo_map_bytes.getvalue()
    
    def _generate_track(self, tempo_automation_events, tempo_quant, ticks_per_beat):
        track = MidiTrack()
        track.append(Message('note_on', note=64, velocity=64, time=0))
        track += self._render_map(tempo_automation_events, tempo_quant, ticks_per_beat)
        track.append(Message('note_off', note=64, velocity=127, time=32))
        return track
    
    def _render_map(self, tempo_automation_events, quant, ticks_per_beat):
        messages = []
        
        # untested:
        if tempo_automation_events is None:
            # if no tempo auto, our map is a single point at the start. we may encounter
            # that issue with live where it revert back to the original bpm with 1
            # point you need to click away.
            messages.append(MetaMessage('set_tempo', tempo=bpm2tempo(self.project.beats_per_min), time=0))
            return messages

        for i, event in enumerate(tempo_automation_events):
            curr_bpm = event.bpm
            curr_beat = event.beat if event.beat >= 0 else 0

            if i == 0:
                beats_elapsed = curr_beat 
                time_elapsed_tick = beats_elapsed * ticks_per_beat
                messages.append(MetaMessage('set_tempo', tempo=bpm2tempo(curr_bpm), time=int(time_elapsed_tick)))
                continue

            prev = tempo_automation_events[i-1]

            beats_elapsed = curr_beat - prev.beat
            time_elapsed_tick = beats_elapsed * ticks_per_beat
            # print(curr_bpm, time_elapsed_tick)
            # print('\t' , curr_bpm, int(time_elapsed_tick))

            if prev.bpm != curr_bpm and beats_elapsed:
                # if we are on a slope
                bpm_diff = curr_bpm - prev.bpm
                slope = bpm_diff / beats_elapsed 

                beat_increment = 4 / quant  # .e.g .25 for ableton

                num_segments = beats_elapsed / beat_increment
                bpm_increment = bpm_diff / num_segments 

                bpm_accumulator = prev.bpm
                # print(11, num_segments)
                # FIXME: can't just cast to int - need to handle non aligned
                for i in range(int(num_segments)):
                    # for every segment, we emit a horizontal line and a vertical
                    # line.

                    # print(11, int(beat_increment*mid.ticks_per_beat))
                    messages.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm_accumulator), time=int(beat_increment*ticks_per_beat)))

                    # currx = i*beat_increment +beat_increment 
                    # ydiff = slope * currx
                    new_bpm = bpm_accumulator + bpm_increment 
                    messages.append(MetaMessage('set_tempo', tempo=bpm2tempo(new_bpm), time=0))
                    bpm_accumulator = new_bpm
            else:
                # if we are on a horizontal line or vertical line
                messages.append(MetaMessage('set_tempo', tempo=bpm2tempo(curr_bpm), time=int(time_elapsed_tick)))
        
        return messages