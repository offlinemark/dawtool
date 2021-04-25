from .project import BasicGenericTempoAutomationEvent

from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo

from io import BytesIO

from dataclasses import dataclass


@dataclass
class AlignedGenericTempoAutomationEvent(BasicGenericTempoAutomationEvent):
    pass

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

def aligned(beat, tempo_quant):
    return beat - (beat % tempo_quant)

def is_aligned(beat, tempo_quant):
    return beat % tempo_quant == 0

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
        aligned_tempo_automation_events = self._compute_aligned_points(tempo_automation_events, tempo_quant)
        track += [x.to_mido() for x in self._render_map(aligned_tempo_automation_events, tempo_quant)]
        track.append(Message('note_off', note=64, velocity=127, time=32))
        return track
    
    
    @staticmethod
    def _compute_aligned_points(tempo_automation_events, tempo_quant):
        """
        Transform the points into one that easier to generate the tempo map from.
        Replace any unaligned points with aligned points on previous and next
        alignment, based on the tempo quantization.

        algo:
        iter each point, if aligned append to ret
        if unaligned,
        first check the last appended point. if we're still in the same quant
        boundary, do nothing. this quant boundary has already been covered

        check next point.
        is it in this quant boundary. then do nothing and contiue to it, it will take care of the trailing point
        if not, is it in the next quant boundary? do nothing also.
        is it not in this or the next quant bounday? we need to compute the trailing point now.



         unconditionally append prev aligned point to ret
        check if next point 
        edge cases: multiple points in same quant boundary
        points in adjacent quant boundaries
        """

        ret = []

        for i, event in enumerate(tempo_automation_events):
            if is_aligned(event.beat, tempo_quant):
                ret.append(event)
                continue

            aligned_beat = aligned(event.beat, tempo_quant)
            next_aligned_beat = aligned_beat + tempo_quant

            quant_before_already_handled = ret and ret[-1].beat == aligned_beat
            print(123, ret[-1].beat, aligned_beat)
            if not quant_before_already_handled:
                # this branch is usually taken. it won't be taken if
                # many points are grouped in same quant.
                # append "before" aligned beat
                ret.append(AlignedGenericTempoAutomationEvent(beat=aligned_beat, bpm=event.prev_aligned_bpm))

            # do we need to append the "after" one too?
            at_last_event = i == len(tempo_automation_events) - 1
            if not at_last_event:
                # ok so we are not at last event. we need to check if the next one will do it for us.
                # it will if it is aligned on precisely the next quant or is after the next quant
                # but is less than the quant after that.
                # if it is not, we need to add an "after" event.
                # if we were at the last event, we don't need to do anything, since that "before"
                # event we just added is the final event, period.

                next_event = tempo_automation_events[i+1]
                next_event_is_in_this_quant = next_event.beat < next_aligned_beat
                next_event_is_in_next_quant = next_aligned_beat <= next_event.beat < next_aligned_beat+tempo_quant
                if next_event_is_in_this_quant or next_event_is_in_next_quant:
                    # we don't need to append an after.
                    continue
                else:
                    # there is another event, but it's not next. so we do math.
                    slope = (next_event.bpm - event.bpm) / (next_event.beat - event.beat)
                    bpm_diff = slope * (next_aligned_beat - event.beat)
                    next_aligned_beat_bpm = event.bpm + bpm_diff

                    ret.append(AlignedGenericTempoAutomationEvent(beat=next_aligned_beat, bpm=next_aligned_beat_bpm))


            # if ret and ret[:-1].beat == aligned_beat:
                # the current quant has already been processed.


        return ret
    
    def _render_map(self, tempo_automation_events, quant):
        """
        tempo_automation_events must be aligned
        """
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