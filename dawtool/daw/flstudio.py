"""
Largely based off of LMMS/PyDaw, but with some new events they didn't have.

TODO: where is the flp format version? check against it?
"""

from ..project import Project
from ..marker import Marker
from ..util import spb

from io import BytesIO
from collections import Counter
from enum import IntEnum, auto
import struct
from binascii import hexlify as hx
from dataclasses import dataclass, field
from typing import List
import logging

# for debugging
from hexdump import hexdump

logger = logging.getLogger(__name__)

# can raise error if doesn't match magic

class Event:
    # BYTE Events
    BYTE = 0
    TIME_SIG_NUMERATOR = 33  # there are unused, but I found them when reversing. relevant to markers
    TIME_SIG_DENOMINATOR = 34

    # WORD Events
    WORD = 64
    CHANNEL_NEW = 0x40
    TEMPO_OLD = 66  # this was in pydaw/lmms but was not in my flps

    # DWORD Events
    DWORD = 128

    # Marker time. MSB=marker action. 3 LSB=time.
    class MarkerAction(IntEnum):
        NONE = 0
        MARKER_LOOP = auto()  # loop to next marker
        SKIP = auto()  # skip to next marker
        PAUSE = auto() # pause here
        LOOP = auto() # not sure
        START = auto()
        PATTERN_LENGTH = auto()
        BAR_OVERRIDE = auto()
        TIME_SIGNATURE = auto()
        PUNCH_IN = auto()
        PUNCH_OUT = auto() # all above are interp as punch out
    MARKER_TIME = DWORD + 20  # 0x94
    TEMPO = DWORD + 28

    # TEXT Events
    TEXT = 192
    VERSION = TEXT + 7
    MARKER_TEXT = TEXT + 13

    CHANNEL_NAME = 0xcb   # 203 TODO: order these nicely
    CHANNEL_SAMPLE_PATH = 0xc4

    # DATA Events

    BASIC_CHAN_PARAMS = 0xdb

    AUTOMATION_DATA = 0xea
    AUTOMATION_CHANNELS = 0xe3

    # 223 - 0xdf == automation?

    # Unknown Events



    # text event with , "Automation" "Unsorted" text
    # channel group name
    UNKNOWN_E7 = 0xe7  # +39

    # Appears right before 0xe9. byte event. only ever observed as 0
    UNKNOWN_24 = 0x24

    # something related to automation. array of 8 byte structs maybe
    PLAYLIST_ITEMS = 0xe9

    # 0xf1 event is something interesting. occurs once and has data
    # "Arrangement". right before some automation stuff
    UNKNOWN_F1 = 0xf1


    # it's a signed int
    UNKNOWN_92 = 0x92
    UNKNOWN_93 = 0x92

    # also signed
    UNKNOWN_9A = 0x9a



@dataclass
class FlStudioRawMarker(Marker):
    time: int
    action: int

    @property
    def pulse(self):
        return self.time

    @pulse.setter
    def pulse(self, val):
        self.time = val


# some other unknown fields
@dataclass
class AutomationChannel:
    # (not mixer track master)
    PARAM_MASTER_VOLUME = 0
    PARAM_MASTER_PITCH = 2
    PARAM_MASTER_TEMPO = 5

    DEST_MASTER = 0x4000


    channel_id: int
    param_id: int
    dest_id: int

    def __repr__(self):
        return 'AutomationChannel(channel_id={}, param_id={}, dest_id={}, mixer_track_num={})'.format(self.channel_id,
                hex(self.param_id),
                hex(self.dest_id),
                self.mixer_track_num)

    @property
    def is_master(self):
        return self.dest_id == AutomationChannel.DEST_MASTER

    @property
    def is_mixer_track(self):
        # unsure exactly if it goes all the way up to 0x4000
        # in practice, you can't add that many tracks
        return 0x2000 <= self.dest_id < 0x4000

    @property
    def mixer_track_num(self):
        # e.g. 0x2000 -> 0
        # e.g. 0x2080 -> 2
        # e.g. 0x3000 -> 64
        if not self.is_mixer_track:
            return None
        # stored in high 3 nibbles
        # hi byte counts normally, lowest nibble of the 3 only cycles through
        # (0, 4, 8, 0xc) which basically just acts like an extra 2 low bits..
        start = 0x20 << 2
        low = (self.dest_id & 0xf0) >> 4
        if low not in (0, 4, 8, 0xc):
            raise ValueError('Malformed dest_id', self.dest_id)
        hi = self.dest_id >> 8
        track_num = (hi << 2) | (low // 4)
        normalized = track_num - start
        return normalized

    @property
    def fx_insert_num(self):
        # stored in low nibble
        return self.dest_id & 0xf


@dataclass
class GlobalTempoAutomationPoint:
    beat: float
    real_time: float  # computed
    bpm: float
    track_id: int  # for debugging

    prev_aligned_bpm: float = None # computed


# Artificial automation points are those we inject into the final rendered
# automation points in order to implement gap and overlap semantics
# They are exactly the same as GlobalTempoAutomationPoint, this is just to
# help debugging + express intent
@dataclass
class ArtificialGlobalTempoAutomationPoint(GlobalTempoAutomationPoint):
    track_id: int = None


@dataclass
class ChannelAutomationPoint:
    beat_increment: float = None  # num beats since last point
    value: float = None
    tension: float = None
    unknown3: bytes = None # these might be part of direction
    direction: int = None


# Channels have a lot more to them, but this is all I know
@dataclass
class Channel:
    id: int = None
    name: str = None
    sample_path: str = None
    automation_points: List[ChannelAutomationPoint] = field(default_factory=list)


# commented out = unsure/not needed
@dataclass
class PlaylistItem:
    start_pulse: int
    # pattern_base: int
    channel_id: int
    len_pulses: int
    track_id: int
    # unknown: int
    flags: int
    # unknown2: int
    # start_offset: float
    # end_offset: float

    @property
    def end_pulse(self):
        return self.start_pulse + self.len_pulses

    @property
    def muted(self):
        return bool(self.flags & (0x2000))

@dataclass
class RenderedPlaylistItem:
    """
    Light wrapper over a list of GlobalTempoAutomationPoint. start/end times
    resolved to beat
    """
    channel_id: int
    track_id: int
    start_beat: float
    # end_beat: float
    len: float  # (beats) prob don't need all these beats. prob don't need end beat
    # TODO: is this specific to tempo automation points, or just general?
    points: List[GlobalTempoAutomationPoint]


class FlStudioProject(Project):
    EXT = '.flp'
    TEMPO_QUANT = 512  # tempo quantization looks about 512th notes

    MAGIC = b'FLhd'

    def __init__(self, filename, stream, *args, **kwargs):
        super().__init__(filename, stream, *args, **kwargs)
        self.pulses_per_beat = 0  # aka ppq
        self.beats_per_min = 0
        # TODO: use a tuple so can more easily do version checks
        self.version = None
        self.num_channels = 0
        self.channels = []
        self.automation_channels = []
        self.playlist_items = []
        self.tempo_automation_events = []
        self.raw_markers = []
        self.stream = BytesIO(stream.read())  # prevent dangling file

    @property
    def sec_per_pulse(self):
        return spb(self.beats_per_min) / self.pulses_per_beat

    def __repr__(self):
        return '<FlStudioProject version={} ppb={} bpm={} channels={}>'.format(self.version, self.pulses_per_beat,
                self.beats_per_min, self.num_channels)

    def parse(self):
        if self._read(4) != self.MAGIC:
            raise ValueError('flp bad magic')

        header_len = self._read32LE()
        if header_len != 6:
            raise ValueError('flp unexpected header len')

        proj_format_type = self._read16LE()
        if proj_format_type != 0:
            raise ValueError('flp unexpected song format')

        self.num_channels = self._read16LE()
        self.pulses_per_beat = self._read16LE()

        self._parse_events_chunk()
        self._compute_tempo_automations()
        self._calc_markers()

    @property
    def has_tempo_automation(self):
        return bool(self.tempo_automation_events)

    def _parse_events_chunk(self):
        if self._read(4) != b'FLdt':
            raise ValueError('flp bad data chunk header')

        data_chunk_len = self._read32LE()

        while True:
            try:
                event_id = self._read8LE()
                # print('getting event id', hex(event_id), end=' ')
                # print()
            except struct.error:
                # print('exiting')
                break
            
            if Event.BYTE <= event_id < Event.WORD:
                data = self._read8LE()
                # print(data, hex(data))
            elif Event.WORD <= event_id < Event.DWORD:
                data = self._read16LE()
                # print(data, hex(data))
            elif Event.DWORD <= event_id < Event.TEXT:
                if event_id in [Event.UNKNOWN_92, Event.UNKNOWN_9A, Event.UNKNOWN_93]:
                    data = self._read32LE(True)
                else:
                    data = self._read32LE()
                # print(data, hex(data))
            elif event_id >= Event.TEXT:
                text_data_len = self._parse_text_data_len()
                data = self._read(text_data_len)
                # print(text_data_len, end=' ')
                # print(data[:20])
            else:
                raise ValueError('flp invalid event id', event_id)

            self._handle_event(event_id, data)

    def _handle_event(self, event_id, data):
        # TODO: eventually refactor to event handler functions
        if event_id == Event.TEMPO:
            # convert from milliseconds
            self.beats_per_min = data / 1000.0
        elif event_id == Event.CHANNEL_NEW:
            self.channels.append(Channel(id=data))
        elif event_id == Event.CHANNEL_NAME:
            if not self.channels:
                # This means flp is malformed. This event shoudl only be after
                # a CHANNEL_NEW. Ignore it i guess..
                # TODO: it would be cool to have some testing infrastructure
                # to allow replaying events against the parser without requiring
                # crafting a malformed flp
                logger.warning('CHANNEL_NAME before CHANNEL_NEW')
                return

            self.channels[-1].name = self._decode_str(data)
        elif event_id == Event.CHANNEL_SAMPLE_PATH:
            if not self.channels:
                # This means flp is malformed. see above
                logger.warning('CHANNEL_NAME before CHANNEL_NEW')
                return

            self.channels[-1].sample_path = self._decode_str(data)
        elif event_id == Event.AUTOMATION_CHANNELS:
            orig_seek = self.stream.tell()
            self._reset_stream(data)

            unk = self._read16LE()
            track_id = self._read32LE()
            unk2 = self._read16LE()
            param_id = self._read16LE()
            dest_id = self._read16LE()
            unk3 = self._read32LE()
            unk4 = self._read32LE()

            assert self.stream.tell() == orig_seek

            achan = AutomationChannel(track_id, param_id, dest_id)
            self.automation_channels.append(achan)
        elif event_id == Event.AUTOMATION_DATA:
            curr_chan = self.channels[-1]

            # TODO: these are useful for debugging, and should be logging
            # but at some level beyond debug
            # print(hexdump(data))

            # seek back before the data
            start_seek = self.stream.tell()
            self.stream.seek(self.stream.tell() - len(data))

            # Structure: header (unknown) + array size + arrays of point structs
            # point struct is 24 bytes

            unknowns = (
                self._read32LE(),  # always 1?
                self._read32LE(),  # always 64?
                self._read8LE(),
                self._read32LE(),
                self._read32LE(),
            )
            # print('unk', unknowns)
            num_points = self._read32LE()
            # curr_beat = 0

            for i in range(num_points):
                # ii = self.stream.tell() - start_seek
                # print(hexdump(data[ii:ii+24]))

                beat_increment = self._readDouble()
                value = self._readDouble()
                tension = self._readFloat()
                unknown3 = self._read(3)  # unsure if these 3 bytes are part of the direction
                direction = self._read8LE()

                point = ChannelAutomationPoint(beat_increment, value, tension, unknown3, direction)
                curr_chan.automation_points.append(point)

                # curr_beat += dist_from_last

                # print('beat_increment', beat_increment)
                # print('curr_beat', curr_beat)
                # print(self.sec_per_beat)
                # print('curr_time', curr_beat * self.sec_per_beat)
                # # print('pos * ppq', pos * self.pulses_per_beat)
                # print('value', value)
                # print('tension', tension)
                # print('direction', hex(direction))

            # print(curr_chan)
            # next 4 bytes is int -> number of structures that follow (?)
            # each structure seems 108 bytes in len
            # structure is unknown

            # ii = self.stream.tell() - start_seek
            # print(hexdump(data[ii:]))

            self.stream.seek(start_seek)
        elif event_id == Event.PLAYLIST_ITEMS:
            if len(self.channels) != self.num_channels:
                logger.warning("Number of channels doesn't match header during PLAYLIST_ITEMS")

            # from pprint import pprint
            # print(pprint(self.channels))

            # array of structs of size 32. add automation added 1 struct to this

            from hexdump import hexdump

            start_seek = self.stream.tell()
            self.stream.seek(self.stream.tell() - len(data))

            # left these in bc they're useful for debugging
            # hexdump(data)

            for i in range(0, len(data), 32):
                # hexdump(data[i:i+32])

                start_pulse = self._read32LE(True)
                maybe_patbase = self._read16LE()
                channel_id = self._read16LE()

                len_pulses = self._read32LE()
                track_id = self._read32LE()
                if self.version[0] == 20:
                    track_id = 500 - track_id
                else:
                    # TODO: sort of guessing at this, seems right for fl 11
                    # but that's the only non-20 i've tried
                    track_id = 199 - track_id

                unk = self._read16LE()
                flags = self._read16LE()
                uunk = self._read32LE()

                # not totally sure about these, but don't think I rly need them
                startoff = self._readFloat()
                endoff = self._readFloat()

                item = PlaylistItem(start_pulse, channel_id, len_pulses, track_id, flags)
                self.playlist_items.append(item)

                # print('start_pulse', hex(start_pulse), start_pulse)  # steps/pulses?
                # print('start_time', hex(start_pulse), start_pulse * self.sec_per_pulse)  # steps/pulses?
                # print('maybe_patbase', hex(maybe_patbase))
                # print('channel_id', hex(channel_id))
                # print('len_pulses', hex(len_pulses), len_pulses)
                # print('len time',  len_pulses * self.sec_per_pulse)
                # print('end time', start_pulse * self.sec_per_pulse + len_pulses * self.sec_per_pulse)
                # print('track_id', track_id)
                # print('unk', hex(unk))
                # print('flags', hex(flags))
                # print('uunk', hex(uunk))
                # print('startoff', startoff)
                # print('endoff', endoff)
        elif event_id == Event.VERSION:
            # i think it's probably ascii, but we can use utf-8 to be safe
            # TODO: port to _decode_str
            verstr = data.decode('utf-8').replace('\x00', '')
            self.version = tuple(map(int, verstr.split('.')))
        elif event_id == Event.MARKER_TIME:
            marker_action = data >> (8*3)
            pulse = data & 0xffffff
            self.raw_markers.append(FlStudioRawMarker(pulse, '', marker_action))
        elif event_id == Event.MARKER_TEXT:
            # now we patch up the previously added marker
            # TODO: port to self._decode_str
            try:
                marker_text = data.decode('utf-16').replace('\x00', '')
            except UnicodeDecodeError:
                # TODO actually check the version number
                # FL 11 seems to store it in ascii
                marker_text = data.decode('ascii').replace('\x00', '')

            if not self.raw_markers:
                # this would be weird. self.raw_markers should always contain at
                # least one element because a MARKER_TIME should always 
                # come before a MARKER_TEXT. I guess we can just add a marker
                # with the text at time 0?
                self.raw_markers.append(Marker(0, marker_text))
                return

            if self.raw_markers[-1].text:
                # this would also be weird. The last marker (which should
                # exist already) should not have text in it, since it is
                # initialized blank (because it expects this MARKER_TEXT to
                # come later and fill it in). Nothing exactly to do here
                # though..
                # TODO: log warning/error
                pass

            self.raw_markers[-1].text = marker_text
        ##### Unknown/experimentation/unused below here
        elif event_id == Event.TEMPO_OLD:
            # TODO: I have never seen this in real life so this is completely
            # untested; i have no idea what the data actually is for this
            # event
            raise Exception('FLP contains TEMPO_OLD event! Please file a bug report and send us this flp!')
        elif event_id == Event.UNKNOWN_24:
            # the random weird one that's always 0, right before the e9
            # print('got 0x24', data)
            pass
        elif event_id == Event.BASIC_CHAN_PARAMS:
            # print(self.channels[-1].name)
            # hexdump(data)
            self.stream.seek(self.stream.tell() - len(data))
            a = self._read32LE()
            b = self._read32LE()
            c = self._read64LE()
            d = self._read64LE()
            # print('a', hex(a), a)
            # print('b', hex(b), b)
            # print('c', hex(c), c)
            # print('d', hex(d), d)
            pass
        else:
            # unhandled event
            # print('unhandled event')
            pass

    def _parse_text_data_len(self):
        # text len encoded in the low 7 bits of the following bytes.
        # the last byte with length data in it has 0 high bit.
        ret = 0
        shift = 0

        while True:
            byt = self._read8LE()
            ret |= ((byt & 0x7f) << shift)
            shift += 7
            if not (byt & 0x80):
                break
        
        return ret
    

    #
    # Tempo automation
    #

    def _calc_markers(self):
        # Filter out the time signature, loop, punch in, etc markers
        filtered_markers = [m for m in self.raw_markers if m.action == Event.MarkerAction.NONE]
        markers = [Marker(self._calc_beat_real_time(self._convert_pulse_to_beat(m.pulse)), m.text) for m in filtered_markers]
        self.markers = markers

    def _calc_beat_real_time_fast_path(self):
        return not self.tempo_automation_events
    
    @property
    def tempo_automation_channels(self):
        def is_master_tempo_auto(x):
            return x.is_master and x.param_id == AutomationChannel.PARAM_MASTER_TEMPO
        tempo_auto_chans = filter(is_master_tempo_auto, self.automation_channels)
        return tempo_auto_chans

    def _compute_tempo_automations(self):
        """
        Using the automation channels, playlist items, channel automation
        points, construct a complete view of all tempo automations with
        globally resolved times.
        """

        if not self.tempo_automation_channels:
            return
        
        # at a high level, the below code needs to convert the various
        # playlist items with automation points into a global list of
        # automation points with fully resolved global times (vs the
        # offset based representation in the file). we also need to honor
        # the proper semantics if there is gap/overlap/perfect alignment/same start time between
        # clips
        # gap semantics: if there is a gap between two clips, it is as if
        # the last point of the prev clip is continued in a horizontal line
        # until the first point of the next clip where it sharply transitions
        # overlap semantics: if there is an overlap between two clips,
        # the clip that starts later completely takes precedence starting from
        # the start point of that clip. the rest of the previous clip is
        # ignored. (this is what FL shows when dragging cursor across multiple
        # overlapping clips, not what it does during playback, which is different
        # and hard to characterize)
        # perfect alignment: if the next clip start at exactly the same time
        # as the last clip, nothing special really happens, all points from
        # both are rendered
        # same start time: for clips that start at exactly the same time, the
        # longest clip (determined by item length, not points) takes precedence
        # and all others are ignored


        # first, basic render of all playlist items in all tempo automation
        # channels
        # "rendering" a playlist item is resolving all of its automation points
        # (which are stored as offsets from each other in the channel) against
        # the known start point of the playlist item
        tempo_auto_clips = []
        for auto_chan in self.tempo_automation_channels:
            # TODO: validate channel_id? would be weird. how do we even handle?
            # any of these situations where we parse some object that has a track_id or id, to be indexed into something else
            # is potentially a bug
            try:
                chan = self.channels[auto_chan.channel_id]
            except IndexError:
                raise ValueError('Malformed auto chan channel id', auto_chan.channel_id)
            clips = self._get_chan_clips(chan)
            tempo_auto_clips.extend(clips)

        # next, sort by the start of the clip. the start_beat and the time
        # of the first point are equal, so either can be used
        sorted_clips = sorted(tempo_auto_clips, key=lambda x: x.start_beat)
        self._dedup_clips(sorted_clips)

        deduped_clips = sorted_clips
        self.tempo_automation_events = self._render_dedup_clips(deduped_clips)

    def _dedup_clips(self, sorted_clips):
        # TODO: cleaner non-mutation based approach? index walking seemed
        # bit messy, as did keeping a list of times that had been deduped
        # already

        # find all items that start at the same time. find the longest
        # item (as determined by end-start, not points) and remove all others
        counter = Counter(c.start_beat for c in sorted_clips)
        need_deduping = (time for time, count in counter.items() if count > 1)

        # now, rm the ones that need deduping
        for time in need_deduping:
            dups = filter(lambda x: x.start_beat == time, sorted_clips)
            sorted_dups = sorted(dups, key=lambda x: x.len)
            for dup in sorted_dups[:-1]:
                # safe; clips must be unique in some way
                sorted_clips.remove(dup)

    def _render_dedup_clips(self, deduped_clips):
        # now, we're ready to render out all the clips into a final
        # list of automation points, while respecting gap/overlap semantics
        final_render = []

        if not deduped_clips:
            return []

        first_point = deduped_clips[0].points[0]
        if first_point.beat != 0.0:
            first = ArtificialGlobalTempoAutomationPoint(0.0, None, first_point.bpm)
            final_render.append(first)

        for i, curr in enumerate(deduped_clips):
            if curr is deduped_clips[-1]:
                # last clip, just render them all
                final_render += curr.points
                break

            next = deduped_clips[i+1]
            curr_last_point = curr.points[-1]
            curr_last_point_beat = curr_last_point.beat

            if next.start_beat == curr_last_point_beat:
                # perfect alignment semantics
                # TODO: hard to literally create an flp that has this
                # just render precisely all points in curr
                final_render += curr.points
            elif next.start_beat > curr_last_point_beat:
                # gap semantics

                # render all points in curr
                final_render += curr.points
                # then add 1 fake point to implement gap semantics
                fake = ArtificialGlobalTempoAutomationPoint(next.start_beat, None, curr_last_point.bpm)
                final_render.append(fake)
            elif next.start_beat < curr_last_point_beat:
                # overlap semantics. these don't actually represent what 
                # FL does during playback (they represent what happens if you
                # drag the cursor along multiple overlapping clips). the 
                # real behavior is weird and hard to characterize, so hopefully
                # this will do, since ppl shouldn't be using overlapping
                # tempo automations anyway...

                overlap_beat = next.start_beat

                # render all points less than the overlap point
                for point in filter(lambda x: x.beat < overlap_beat, curr.points):
                    final_render.append(point)

                # do we happen to have any points at exactly the same as the
                # overlap point? then this is easy, we render those and we're
                # done
                # TODO: try to make an flp that actually has this scenario
                at_overlap = [p for p in curr.points if p.beat == overlap_beat]
                if at_overlap:
                    final_render += at_overlap
                    continue

                # ok this might be hard now. we need to inject an artifical
                # point at the overlap point, however if there is a slope
                # to the line, we don't actually know the bpm that this
                # point needs to be at- we need to compute it based on
                # the slope, and the distance between the prev point
                # and the overlap

                # now we need to consider the two points on either side
                # of the overlap point

                # we are guaranteed that the overlap point is less than
                # the last point

                prev_overlap = None
                post_overlap = None
                # TODO: technically, we could binary search. only useful if
                # there were a /lot/ of points in this clip (unlikely)
                for i, point in enumerate(curr.points):
                    next_point = curr.points[i+1]
                    if point.beat < overlap_beat < next_point.beat:
                        prev_overlap = point
                        post_overlap = next_point
                        break

                # we should be guaranteed to have found prev_overlap
                # and post_overlap
                assert prev_overlap is not None
                assert post_overlap is not None

                if prev_overlap.bpm == post_overlap.bpm:
                    # If there was no slope, great, just use their bpm
                    fake = ArtificialGlobalTempoAutomationPoint(overlap_beat, None, prev_overlap.bpm)
                    final_render.append(fake)
                    continue

                # ok, calculate the slope of the line to figure out what the
                # bpm of the fake point should be
                fake_point_bpm = self._calc_bpm_at_beat(overlap_beat, prev_overlap, post_overlap)
                fake = ArtificialGlobalTempoAutomationPoint(overlap_beat, None, fake_point_bpm)
                final_render.append(fake)

        return final_render
    
    def _get_chan_clips(self, channel):
        # return a list of RenderedPlaylistItem
        #lists of global automation points
        # each playlist item in the channel is rendered into an array
        # of GlobalTempoAutomationPoint. we make of list of those lists and return
        # it
        ret = []

        def item_filter(x):
            return x.channel_id == channel.id and not x.muted
        playlist_items = filter(item_filter, self.playlist_items)

        for item in playlist_items:
            points = self._resolve_playlist_item_auto_points(channel, item)
            start = self._convert_pulse_to_beat(item.start_pulse)
            len = self._convert_pulse_to_beat(item.len_pulses)
            # rendered = RenderedPlaylistItem(channel.id, item.track_id, start, end, points)
            rendered = RenderedPlaylistItem(channel.id, item.track_id, start, len, points)
            ret.append(rendered)

        return ret

    def _resolve_playlist_item_auto_points(self, channel, playlist_item):
        # compute the start beat offset from the item.
        # then resolve all the channel automation points against it

        # returns a list of resolved global tempo automation points
        ret = []

        start_beat = playlist_item.start_pulse / self.pulses_per_beat
        curr_beat = start_beat
        for point in channel.automation_points:
            # first point's beat_increment is always 0
            point_beat = curr_beat + point.beat_increment 
            curr_beat = point_beat
            bpm = self._convert_point_value_to_bpm(point.value)
            point = GlobalTempoAutomationPoint(point_beat, None, bpm, playlist_item.track_id)
            ret.append(point)

        return ret

    def _convert_pulse_to_beat(self, pulse):
        return pulse / self.pulses_per_beat
    
    def _convert_point_value_to_bpm(self, value):
        # for some reason, they use this linear equation...
        # value = (1/120)*bpm - .5
        return (value + .5)*120

    #
    # Stream helpers
    #
    def _read(self, num_bytes):
        return self.stream.read(num_bytes)

    def _read32LE(self, signed=False):
        if signed:
            return struct.unpack('<i', self.stream.read(4))[0]
        return struct.unpack('<I', self.stream.read(4))[0]

    def _read64LE(self):
        return struct.unpack('<Q', self.stream.read(8))[0]

    def _readFloat(self):
        return struct.unpack('<f', self.stream.read(4))[0]

    def _readDouble(self):
        return struct.unpack('<d', self.stream.read(8))[0]

    def _read16LE(self):
        return struct.unpack('<H', self.stream.read(2))[0]

    def _read8LE(self):
        # print('rn at', hex(self.stream.tell()))
        return struct.unpack('<B', self.stream.read(1))[0]
    
    def _decode_str(self, data):
        if self.version[0] > 11:
            # FL 12, 20
            return data.decode('utf-16').replace('\x00', '')
        else:
            # FL 11 seems to store it in ascii
            return data.decode('ascii').replace('\x00', '')

    def _reset_stream(self, data):
        self.stream.seek(self.stream.tell() - len(data))
