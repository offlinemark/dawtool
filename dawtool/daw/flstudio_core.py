#
# This file alone is licensed under the GPL v3.
#

"""
FL Studio project core parser.
"""

from ..project import Project
from ..marker import Marker
from ..util import spb

from io import BytesIO
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


class FlStudioProjectCore(Project):
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
        self.raw_markers = []
        self.stream = BytesIO(stream.read())  # prevent dangling file

    @property
    def sec_per_pulse(self):
        return spb(self.beats_per_min) / self.pulses_per_beat

    def __repr__(self):
        return '<FlStudioProjectCore version={} ppb={} bpm={} channels={}>'.format(self.version, self.pulses_per_beat,
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
