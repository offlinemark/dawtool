"""
Ableton parsing and basic timeline engine reimplementation.

Supports extracting locators and tempo automation data, and computing
real time corresponding to arbitrary beats in the als project, while respecting
tempo automation.

Doesn't parse the whole xml, uses string searching to find just the tags we
need, which is faster.

Random Automation Note:
It is not generally possibly to create an Ableton project like this without
hand editing the xml, but if a project is created like so:

- first event is the myterious one with negative beat time
- second one has a beat time > 0 and whose bpm is != to the first event's bpm

this can creates errors in the time calculations.
This is impossible to create in the UI because when a user places the first
automation point, the negative point's bpm is set to the bpm of the
user placed point.
"""

from ..project import Project
from ..marker import Marker

import gzip
from collections import namedtuple
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# TODO: raise an error if doesn't match the ableton magic or something
# validate project file version

AbletonSetVersion = namedtuple('AbletonSetVersion', 'major minor minorA minorB minorC schema_change_count creator revision')

#
# Markers
#

class AbletonRawMarker(Marker):
    """
    time for an Ableton raw marker is beat number (float) (not seconds time)
    """
    @classmethod
    def fromxml(cls, locator):
        """
        locator is the xml element that corresponds to the locator
        """
        beat = float(locator.find('Time').get('Value'))
        # TODO: what if not found?
        text = locator.find('Name').get('Value').strip()
        return cls(beat, text)

    @property
    def beat(self):
        return self.time

    @beat.setter
    def beat(self, val):
        self.time = val

#
# Automation
#

CurveControl = namedtuple('CurveControl', 'x y')

@dataclass
class AutomationFloatEvent:
    """
    For tempo automation, time is beat num, not seconds time.
    real_time is seconds time. (only present here, not in the xml)
    """
    id: str
    time: float
    real_time: float  # computed
    value: float
    curve_control1: CurveControl
    curve_control2: CurveControl

    # this one is an to optimization, and also serves to simplify the code.
    # if this event is not aligned on a 16th note boundary, this is going to
    # cause extra work when we compute times. the effective bpm, as used for
    # time calculations will actually be the bpm at the closest previous
    # 16th note. that is what this field stores
    prev_aligned_bpm: float = None # computed

    @classmethod
    def fromxml(cls, float_event):
        """
        float_event is xml element
        """
        id = float_event.get('Id')
        time = float(float_event.get('Time'))
        value = float(float_event.get('Value'))

        curve1x = float_event.get('CurveControl1X')
        if curve1x is None:
            # Should either have all the curve controls, or none of them
            return cls(id, time, None, value, None, None, None)

        curve1y = float_event.get('CurveControl1Y')
        curve2x = float_event.get('CurveControl2X')
        curve2y = float_event.get('CurveControl2Y')

        curve_control1 = CurveControl(float(curve1x), float(curve1y))
        curve_control2 = CurveControl(float(curve2x), float(curve2y))

        return cls(id, time, None, value, curve_control1, curve_control2, None)


# It's really confusing to use .time and .value above, so here's an alias
# with more semantic meaning.
class TempoAutomationFloatEvent(AutomationFloatEvent):
    @property
    def bpm(self):
        return self.value

    @bpm.setter
    def bpm(self, val):
        self.value = val

    @property
    def beat(self):
        return self.time

    @beat.setter
    def beat(self, val):
        self.time = val


#
# Ableton Project
#

class AbletonProject(Project):
    EXT = '.als'
    TEMPO_QUANT = 16  # tempo automation quantized to 16th notes

    LOCATORS_TAG = 'Locators'
    TEMPO_TAG = 'Tempo'

    def __init__(self, filename, stream, *args, **kwargs):
        super().__init__(filename, stream, *args, **kwargs)
        # TODO: add underscores for priv
        self.beats_per_min = None
        self.raw_markers = []
        self.tempo_automation_target_id = None
        self.tempo_automation_events = None  # sorted by beat num
        self.raw_contents = stream.read()
        self.contents = b''

    @property
    def has_tempo_automation(self):
        if self.tempo_automation_events is None:
            return False

        # projs with no automation will have 1 event still
        return len(self.tempo_automation_events) > 1

    def __repr__(self):
        return '<AbletonProject {}>'.format(self.filename)

    @staticmethod
    def _find_tag(contents, tag, start=None):
        start_tag = f"<{tag}>".encode()
        end_tag = f"</{tag}>".encode()

        start_idx = contents.find(start_tag, start)
        # TODO: what if not found?
        end_idx = contents.find(end_tag, start_idx)

        return contents[start_idx:end_idx+len(end_tag)]

    def _parse_locators(self, contents):
        """
        returns empty bytes if no locators
        """
        # For some reason inside the first Locators tag, there is another
        # identical Locators tag. However, if there are no locators, inside
        # the first Locators tags there is simple another *closing* Locators
        # tag.
        outer_chunk = self._find_tag(contents, self.LOCATORS_TAG)
        inner_chunk = self._find_tag(outer_chunk[1:], self.LOCATORS_TAG)
        return inner_chunk

    def parse(self):
        try:
            self.contents = gzip.decompress(self.raw_contents)
        except OSError as e:
            raise ValueError('Not gzip', len(self.raw_contents), self.raw_contents[:30]) from None

        if not self.contents:
            raise ValueError('Empty contents')

        self._parse_version()

        # Gather all raw info needed to compute marker times
        self._parse_tempo(self.contents)
        self._parse_markers(self.contents)
        self._parse_automation(self.contents)

        self._calc_markers()

    def _parse_version(self):
        start_idx = self.contents.find(b'<Ableton')
        # TODO: what if not found
        end_idx = self.contents.find(b'>', start_idx)
        ableton_tag_chunk = self.contents[start_idx:end_idx+1].decode()

        try:
            # fake end tag
            ableton_tag = ET.fromstring(ableton_tag_chunk + '</Ableton>')
        except ParseError:
            raise ValueError('Cannot parse version')

        minor = ableton_tag.get('MinorVersion')
        minorA = None
        minorB = None
        minorC = None
        if minor is not None:
            big, little = minor.split('.')
            minorA = int(big)
            minorB, minorC = map(int, little.split('_'))

        self.version = AbletonSetVersion(
            ableton_tag.get('MajorVersion'),
            minor, minorA, minorB, minorC,
            ableton_tag.get('SchemaChangeCount'),
            ableton_tag.get('Creator'),
            ableton_tag.get('Revision')
        )

    def _calc_markers(self):
        markers = [Marker(self._calc_beat_real_time(m.beat), m.text) for m in self.raw_markers]
        # Ableton's raw markers are not sorted in the file
        sorted_markers = sorted(markers, key=lambda x: x.time)
        self.markers = sorted_markers

    def _calc_beat_real_time_fast_path(self):
        "If there are no tempo auto events basically"
        # TODO: refactor to use use self.has_tempo_automation instead basically
        # may require defaulting self.tempo_automation_events to [] instead of
        # None

        # There seems to always be 1 tempo auto event (even if there is no
        # tempo automation). That event has time -63072000 and the value
        # of the manual bpm of the project.
        return self.tempo_automation_events is None or \
                len(self.tempo_automation_events) == 1

    def _parse_arranger_automation_events(self, contents):
        """
        Only for Ableton 8 and 9.
        """
        tempo_chunk = self._find_tag(contents, 'Tempo')
        try:
            tempo = ET.fromstring(tempo_chunk)
        except ParseError:
            raise ValueError('Cannot parse tempo')

        arranger_auto = tempo.find('ArrangerAutomation')
        if arranger_auto is None:
            logger.warning('%s: No ArrangerAutomation found in Tempo', self.filename)
            return

        events = arranger_auto.find('Events')
        return events

    def _parse_automation(self, contents):
        """
        Needs to be called after _parse_tempo
        """

        events = None

        # Ableton 8, 9 store tempo auto differently
        if self.version.minorA < 10:
            events = self._parse_arranger_automation_events(contents)
        else:
            # TODO: need better code structure to manage diff Ableton version
            # This only applies to Ableton 10
            master_track_chunk = self._find_tag(contents, 'MasterTrack')
            try:
                master_track = ET.fromstring(master_track_chunk)
            except ParseError:
                raise ValueError('Cannot parse automation')

            auto_envelopes = master_track.find('AutomationEnvelopes')
            if auto_envelopes is None:
                logger.warning('%s: No AutomationEnvelopes found in MasterTrack', self.filename)
                return

            envelopes = auto_envelopes.find('Envelopes')
            if envelopes is None:
                logger.warning('%s: No found in MasterTrack', self.filename)
                return

            # events = None
            for env in envelopes:
                pointee_id = env.find('EnvelopeTarget').find('PointeeId').get('Value')
                if pointee_id == self.tempo_automation_target_id:
                    events = env.find('Automation').find('Events')
                    break

        if events is None:
            return

        self.tempo_automation_events = [TempoAutomationFloatEvent.fromxml(ev) for ev in events]

    def _parse_tempo(self, contents):
        if self.version.minorA == 8:
            events = self._parse_arranger_automation_events(contents)
            if not events:
                # there should always be at least 1 event in general, and especially
                # for Ableton 8.
                raise ValueError('Ableton 8 project had no automation events')
            self.beats_per_min = float(events[0].get('Value'))
            # There is no automation target id for Ableton 8
            return

        # Ableton 9, 10
        tempo_chunk = self._find_tag(contents, self.TEMPO_TAG)
        try:
            tempo = ET.fromstring(tempo_chunk)
        except ParseError:
            raise ValueError('Cannot parse tempo')

        # TODO: Ableton 8 doesn't have Manual. we crash.
        self.beats_per_min = float(tempo.find('Manual').get('Value'))
        self.tempo_automation_target_id = tempo.find('AutomationTarget').get('Id')

    def _parse_markers(self, contents):
        locators_chunk = self._parse_locators(contents)
        if not locators_chunk:
            self.raw_markers = []
            return

        try:
            locators = ET.fromstring(locators_chunk)
        except ParseError:
            raise ValueError('Cannot parse locators')

        self.raw_markers = [AbletonRawMarker.fromxml(loc) for loc in locators]
