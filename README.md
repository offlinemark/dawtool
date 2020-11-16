# dawtool

dawtool parses and extracts data from Digital Audio Workstation (DAW) file
formats.

Its primary feature is high accuracy **time marker extraction**.

Supported formats:
- Ableton Live set (.als)
- FL Studio project (.flp)
- Cue sheet (.cue)

## About

Time markers allow users to annotate the DAW timeline with text.  Certain use
cases benefit from the ability to export these annotations, such as
timestamping a DJ mix, podcast, or film.

dawtool implements time marker export for DAWs that do not implement it
natively, showcasing how DAWs can be extended through project file
manipulation.

![](https://timestamps.me/static/img/ableton%20screenshot.png)

## Usage

Python API:

```python
import sys
import dawtool

filename = sys.argv[1]
with open(filename, 'rb') as f:
    # Load project based on file extension
    proj = dawtool.load_project(filename, f)
    # Parse project, recompute time markers
    proj.parse()
    # Access project data
    for marker in proj.markers:
        print(marker.time, marker.text)
```

Command line tool:

```
$ dawtool -m my-dj-mix.als
```

## Installation

```
git clone https://github.com/offlinemark/dawtool
pip install dawtool
```

## Status

dawtool's core functionality is stable, although the APIs are not.
A [hosted version](https://timestamps.me) has processed 600+ project files
since March 2020.

## Credits

dawtool's .flp parser is based on work from the
[LMMS](https://github.com/LMMS/lmms),
[PyDaw](https://github.com/andrewrk/PyDaw), and
[FLParser](https://github.com/monadgroup/FLParser) projects.

## License

GPL v3
