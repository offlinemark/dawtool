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
