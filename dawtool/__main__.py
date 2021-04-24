import dawtool
from dawtool import extract_markers, format_time, load_project
from dawtool.project import UnknownExtension

import sys
from argparse import ArgumentParser
import logging

SEC_PER_HOUR = 60 * 60

def main():
    fname = args.file
    from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo
    import mido

    data = [(100, 1), (60, 2), (80, 3.5)]
    data = [(60, 0), (60, 1), (70, 1), (70, 1.5), (60, 2)]

    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(Message('note_on', note=64, velocity=64, time=0))

    for i, pair in enumerate(data):
        bpm = pair[0]
        curr_beat = pair[1]
        if i == 0:
            time_elapsed =curr_beat 
            time_elapsed_tick = time_elapsed * mid.ticks_per_beat
            t = mido.bpm2tempo(bpm)
            track.append(MetaMessage('set_tempo', tempo=t, time=int(time_elapsed_tick)))
            continue

        time_elapsed = max(curr_beat - data[i-1][1], 0)
        time_elapsed_tick = time_elapsed * mid.ticks_per_beat
        print(bpm, time_elapsed_tick)
        print('\t' , bpm, int(time_elapsed_tick))

        prev = data[i-1]
        prev_bpm = prev[0]
        prev_beat = prev[1]

        if prev_bpm != bpm and time_elapsed:
            bpmdiff = bpm - prev_bpm
            slope = bpmdiff / time_elapsed

            xunit = .25

            # if we are on a slope
            segs = time_elapsed / xunit # .25 for live 16

            ybump = bpmdiff / segs

            xbpm = prev_bpm

            
            print(11, segs)
            # FIXME: can't just cast to int - need to handle non aligned
            for i in range(int(segs)):
                track.append(MetaMessage('set_tempo', tempo=bpm2tempo(xbpm), time=int(xunit*mid.ticks_per_beat)))

                # currx = i*xunit + xunit
                # ydiff = slope * currx
                newbpm = xbpm + ybump

                track.append(MetaMessage('set_tempo', tempo=bpm2tempo(newbpm), time=0))

                xbpm = newbpm

        else:
            # if we are on a horizontal line or vertical line
            t = mido.bpm2tempo(bpm)
            track.append(MetaMessage('set_tempo', tempo=t, time=int(time_elapsed_tick)))



    # track.append(Message('program_change', program=12, time=0))
    # track.append(Message('note_on', note=64, velocity=64, time=32))
    track.append(Message('note_off', note=64, velocity=127, time=32))
    # track.append(Message('note_on', note=65, velocity=64, time=0))
    # track.append(Message('note_off', note=65, velocity=127, time=32))

    mid.save(fname)

    return
    try:
        # markers are raw time data. it's up to the client to determine how to
        # present it
        with open(fname, 'rb') as f:
            # markers = dawtool.extract_markers(fname, f)
            proj = load_project(fname, f, theoretical=args.theoretical)
            proj.parse()
            # print(len(proj.tempo_automation_events))
            markers = proj.markers
    except FileNotFoundError:
        print(fname, 'not found')
        return
    except UnknownExtension as e:
        print('unknown ext', e)
        return
    except ValueError as e:
        print('Could not extract markers from', fname, ':', e)
        raise


    if args.verbose:
        proj.dump()

    if args.markers:
        # There was no error, but no markers
        if not markers:
            print('Could not find markers in', fname)
            return

        for m in markers:
            print(format_time(m.time, args.hours, precise=args.imprecise), m.text)

    if args.emit:
        print(proj.emit(), end='')



ap = ArgumentParser(prog='dawtool')
ap.add_argument('file')
ap.add_argument('-v', '--verbose', help='Enable verbose logging', action='store_true')
ap.add_argument('-d', '--debug', help='Enable debug logging', action='store_true')
ap.add_argument('-e', '--emit', help='Re-emit to stdout. Only for cue files', action='store_true')
ap.add_argument('-m', '--markers', help='Output time markers', action='store_true')
ap.add_argument('-x', '--hours', help='Output time markers in hours', action='store_true')
ap.add_argument('-t', '--theoretical', help='Use theoretical time calculations', action='store_true')
ap.add_argument('-i', '--imprecise', help='Use imprecise formatting', action='store_false')
args = ap.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    main()
