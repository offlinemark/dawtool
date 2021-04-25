import os.path

from .project import load_project

from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo

def extract_markers(filename, stream, *args, **kwargs):
    """
    Try to analyze a filename as one of the accepted project file types
    and extract marker information. This is just a convenience helper.
    
    raises FileNotFoundError
    raises ValueError

    return: list of Marker sorted based on the Marker.time
    """
    proj = load_project(filename, stream, *args, **kwargs)
    proj.parse()
    # print(proj)
    from pprint import pprint 
    # print(pprint(proj.tempo_automation_events))
    # proj.dump()
    return proj.markers


def emit_midi_tempo_map(filename, tempo_automation_events, quant):
    data = [(100, 1), (60, 2), (80, 3.5)]
    data = [(60, 0), (60, 1), (70, 1), (70, 1.5), (60, 2)]

    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(Message('note_on', note=64, velocity=64, time=0))

    if tempo_automation_events[0].beat < 0:
        tempo_automation_events[0].beat = 0

    for i, event in enumerate(tempo_automation_events):
        curr_bpm = event.bpm
        curr_beat = event.beat
        if i == 0:
            beats_elapsed = curr_beat 
            time_elapsed_tick = beats_elapsed * mid.ticks_per_beat
            print(232, int(time_elapsed_tick))
            track.append(MetaMessage('set_tempo', tempo=bpm2tempo(curr_bpm), time=int(time_elapsed_tick)))
            continue

        prev = tempo_automation_events[i-1]

        beats_elapsed = curr_beat - prev.beat
        time_elapsed_tick = beats_elapsed * mid.ticks_per_beat
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
                track.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm_accumulator), time=int(beat_increment*mid.ticks_per_beat)))

                # currx = i*beat_increment +beat_increment 
                # ydiff = slope * currx
                new_bpm = bpm_accumulator + bpm_increment 
                track.append(MetaMessage('set_tempo', tempo=bpm2tempo(new_bpm), time=0))
                bpm_accumulator = new_bpm
        else:
            # if we are on a horizontal line or vertical line
            track.append(MetaMessage('set_tempo', tempo=bpm2tempo(curr_bpm), time=int(time_elapsed_tick)))

    track.append(Message('note_off', note=64, velocity=127, time=32))
    mid.save(filename)