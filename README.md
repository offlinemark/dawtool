# dawtool

![](https://github.com/offlinemark/dawtool/workflows/CI/badge.svg)

dawtool parses and extracts data from Digital Audio Workstation (DAW) file
formats.

It provides a high accuracy implementation of **time marker extraction**,
including support for projects with tempo automation. 

Supported formats:
- Ableton Live set (.als) [v8-12]
- FL Studio project (.flp) [v10-11, 20]
- Cue sheet (.cue)

> Just browsing? Here are a few [points of interest](https://gist.github.com/offlinemark/96ddd2c323ced8c70e2b24c1536b7b5f) in the codebase.



## About

Time markers allow users to annotate the DAW timeline with text.  Certain use
cases benefit from the ability to export these annotations, such as
timestamping a DJ mix, podcast, or film.

dawtool implements time marker export for DAWs that do not implement it
natively, showcasing how DAWs can be extended through project file
manipulation.

![](https://timestamps.me/static/img/ableton%20screenshot.png)

For more on how dawtool works, see the [talk](https://youtu.be/AtLlPQHaxzg)
about it at the 2020 Audio Developer Conference.

[![](http://img.youtube.com/vi/AtLlPQHaxzg/0.jpg)](http://www.youtube.com/watch?v=AtLlPQHaxzg "Reverse Engineering DAWs to Build Custom Workflow Tools - Mark Mossberg - ADC20")

## Usage

> Time markers are the only officially supported output. However much more
> of the formats are available through internal APIs, such as tempo automation
> data.

### Python API

Simple API (Markers Only)

```python
import sys
import dawtool

filename = sys.argv[1]
with open(filename, 'rb') as f:
    markers = dawtool.extract_markers(filename, f)
    for marker in markers:
        print(marker.time, marker.text)
```

Advanced API (Markers & Other Data)

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

### Command line tool

```
$ dawtool -m my-dj-mix.als
00:00.000 nciku - peaceofmind
02:15.115 comfort - a n g e l _ w i n g s
05:18.654 rose bride rings - femme fatale
06:52.654 ranov - butterfly
08:47.077 scalade - tempura VIP
10:57.423 mirvs - defrosted
```

## Installation

dawtool requires Python 3.7 or greater.

```
pip install git+https://github.com/offlinemark/dawtool
```

## Status

dawtool is production ready. A [hosted version](https://timestamps.me)
has processed 10,000+ project files since March 2020.

Both the API and CLI should be considered unstable and
subject to change.

Tempo automation is supported for linear automation only. Nonlinear
automation may cause inaccuracies.

## Credits

dawtool's .flp parser is based on work from the
[LMMS](https://github.com/LMMS/lmms),
[PyDaw](https://github.com/andrewrk/PyDaw), and
[FLParser](https://github.com/monadgroup/FLParser) projects.
