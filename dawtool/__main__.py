import dawtool
from dawtool import extract_markers, format_time, load_project
from dawtool.project import UnknownExtension

import sys
from argparse import ArgumentParser
import logging

SEC_PER_HOUR = 60 * 60

def main():
    fname = args.file
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

    if args.v:
        proj.dump()

    if args.markers:
        # There was no error, but no markers
        if not markers:
            print('Could not find markers in', fname)
            return

        # print(markers)

        # client chooses to make the formatting consistent if it detects the
        # markers go an hour or more
        hours_fmt = markers[-1].time >= SEC_PER_HOUR

        # client chooses the presentation, also chooses to throw away precision
        for m in markers:
            # print(format_time(int(m.time), hours_fmt), m.text)
            print(format_time(m.time,hours_fmt, precise=1), m.text)

    if args.emit:
        print(proj.emit(), end='')



ap = ArgumentParser(prog='dawtool')
ap.add_argument('file')
ap.add_argument('-v', action='store_true')
ap.add_argument('-d', '--debug', action='store_true')
ap.add_argument('-e', '--emit', help='re-emit to stdout. only for cue files', action='store_true')
ap.add_argument('-m', '--markers', action='store_true')
ap.add_argument('-t', '--theoretical', help='use theoretical time calculations', action='store_true')
args = ap.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    main()
