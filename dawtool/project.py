"""
Generic stuff for DAW project files

method with "daw" in name take into account daw tempo quantization (more accurate)
when doing time calculations.
"theoretical" methods do not do this, just simple math.
"""

from .marker import Marker
from .util import calc_time_elapsed_theoretical, spb, format_time
from .util import linspace, power_of_two

from dataclasses import dataclass

@dataclass
class GenericTempoAutomationEvent:
    beat: float
    real_time: float
    bpm: float


from os.path import splitext

# Map file extension to class responsible for parsing
# filled by _register_project_subclasses at the bottom
ProjectsMap = {}


class UnknownExtension(Exception):
    pass

def load_project(filename, stream, *args, **kwargs):
    """
    Resets the stream
    """
    try:
        fname, ext = splitext(filename)
        proj = ProjectsMap[ext](filename, stream, *args, **kwargs)
        stream.seek(0)
        return proj
    except KeyError:
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(0)
        # TODO: dont pass so much info, let client do that
        raise UnknownExtension(ext, size, stream.read(100))


class Project:
    # When implementing a subclass make sure to implement the EXT class
    # attribute and add the subclass to `_register_project_subclasses`.

    EXT = ''
    TEMPO_QUANT = None

    # TODO: make filename optional
    def __init__(self, filename, stream, theoretical=False):
        self.filename = filename
        self.stream = stream
        self.markers = []
        self.version = None

        # Use theoretical time calculations, or use the real daw
        # implementation based ones
        self.theoretical = theoretical

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        ProjectsMap[cls.EXT] = cls

    @property
    def sec_per_beat(self):
        return spb(self.beats_per_min)

    def parse(self):
        raise NotImplementedError

    def dump(self):
        pass

    @property
    def has_tempo_automation(self):
        """
        Returns None if unknown.
        """
        return None 

    #
    # tempo automation stuff
    #

    def dump(self):
        """
        dump the automation timeline including automation events and markers
        and the distances between each timeline event
        """

        # If the proj has no markers, we need to force compute real times
        self._calc_tempo_automation_event_real_times()

        # TODO: just use real_time now that Marker has it
        def gettime(x):
            return x.real_time
            # if isinstance(x, TempoAutomationFloatEvent):
            #     return x.real_time
            # else:
            #     assert 0, type(x)
            #     return x.time

        timeline_events = self.markers + self.tempo_automation_events
        # timeline_events = self.raw_markers + self.tempo_automation_events
        sorted_timeline_events = sorted(timeline_events, key=lambda x: gettime(x))

        print('>>> Full Timeline Dump <<<')

        for i, ev in enumerate(sorted_timeline_events):
            print(format_time(gettime(ev), precise=True), ev)
            try:
                dist = gettime(sorted_timeline_events[i+1]) - gettime(ev)
                if dist:
                    print('\t +', dist)
            except IndexError:
                break

        print('>>> End Timeline Dump <<<')
        print('\n\n\n')
        # print('>>> Automation Events Dump <<<')

        # for i, ev in enumerate(self.tempo_automation_events):
        #     print(format_time(gettime(ev), precise=True), ev)
        #     try:
        #         dist = self.tempo_automation_events[i+1].real_time - ev.real_time
        #         if dist:
        #             print('\t +', dist)
        #     except IndexError:
        #         break

        # print('>>> End Automation Events Dump <<<')

    def _calc_tempo_automation_event_real_times(self):
        """
        Go through all the automation events and compute the real time each
        is at. Iterate, and simply accumulate the distances to the next point.
        """
        for i, event in enumerate(self.tempo_automation_events):
            beat = event.beat

            if beat <= 0:
                # There seems to always be an event at time -63072000 to start for Ableton
                event.real_time = 0.0
                # logging.debug(self.tempo_automation_events[i])
                continue

            prev_event = self.tempo_automation_events[i-1]
            time_elapsed = self._time_between_events(prev_event, event)
            # print('time elapsed', time_elapsed)
            self.tempo_automation_events[i].real_time = prev_event.real_time + time_elapsed
            # logging.debug(self.tempo_automation_events[i])
        
    def _calc_beat_real_time(self, beat):
        # TODO: handle if beat was somehow negative?

        if self._calc_beat_real_time_fast_path():
            return beat * self.sec_per_beat
        
        # check if the cache is full, otherwise, fill it
        # TODO: it is not actually necessary to completely fill the cache/
        # compute all the real time of all the events. technically it's
        # only necessary to compute the times of events until the first event
        # past the last marker. this might optimize things if there are lots
        # of events, but the markers are all close to the start
        if self.tempo_automation_events[0].real_time is None:
            self._calc_tempo_automation_event_real_times()

        # Binary search the cache. This won't make a difference if there's a
        # small amount of automation events, but it will if there's a lot of
        # them. This might be the case if the dj used the
        # record automation feature on their tempo, which can add
        # hundreds (thousands?) of points.
        total_len = len(self.tempo_automation_events)
        min_idx = 0
        max_idx = total_len - 1

        # This loop should always exit via one of the returns, should never
        # break out
        while True:
            curr_idx = (min_idx + max_idx) // 2
            event = self.tempo_automation_events[curr_idx]
        
            # Got candidate, now do our suite of tests

            # the Ableton special case
            if beat == 0 and event.beat < 0:
                return event.real_time

            if beat == event.beat:
                return event.real_time

            at_last_event = curr_idx >= total_len - 1
            if at_last_event:
                next_event = None
                return self._calc_beat_real_time_from_events(beat, event, next_event)

            between_curr_and_next = event.beat < beat < self.tempo_automation_events[curr_idx+1].beat
            if between_curr_and_next:
                next_event = self.tempo_automation_events[curr_idx+1]
                return self._calc_beat_real_time_from_events(beat, event, next_event)

            # Not it, keep moving
            if beat > event.beat:
                min_idx = curr_idx + 1
            if beat < event.beat:
                max_idx = curr_idx - 1

        # should never get here because the at_last_event condition above
        # should catch all beats past the last automation event, and the 
        # between_curr_and_next any very early ones that are after 0
        raise ValueError('No automation events smaller than requested time')

        # # might keep this around for perf testing later
        # # (TODO: binary) search the cache to find the nearest earliest event
        # for i, event in enumerate(self.tempo_automation_events):

        #     # beat was exactly on an automation event, use cached result
        #     if beat == event.beat:
        #         return event.real_time

        #     at_last_event = i >= len(self.tempo_automation_events) - 1
        #     if at_last_event:
        #         next_event = None
        #         return self._calc_beat_real_time_from_events(beat, event, next_event)

        #     in_between_events = event.beat < beat < self.tempo_automation_events[i+1].beat
        #     if in_between_events:
        #         next_event = self.tempo_automation_events[i+1]
        #         return self._calc_beat_real_time_from_events(beat, event, next_event)

        # raise ValueError('No automation events smaller than requested time')

    def _calc_beat_real_time_from_events(self, beat, first, second):
        bpm = self._calc_bpm_at_beat(beat, first, second)
        fake_event = GenericTempoAutomationEvent(beat, None, bpm)
        final_real_time_diff = self._time_between_events(first, fake_event)
        # print('final real time diff', final_real_time_diff)
        return first.real_time + final_real_time_diff

    def _calc_bpm_at_beat(self, beat, first, second):
        # After last event there are no more changes, so just use it's bpm
        if second is None:
            return first.bpm

        # If surrounding events are equal, we are equal to them
        if first.bpm == second.bpm:
            return first.bpm


        # Ok, we are in between two points with a slope between them, algebra time ig
        slope = (second.bpm - first.bpm) / (second.beat - first.beat)
        # print('slope', slope)
        time_diff = beat - first.beat
        # print('time_diff', time_diff)
        bpm_diff = slope * time_diff
        # print('bpm_diff', bpm_diff)
        ret = first.bpm + bpm_diff
        # print ('ret', ret)
        return ret

    def _time_between_events(self, first, second):
        if self.theoretical:
            return self._time_between_events_theoretical(first, second)
        else:
            return self._time_between_events_daw(first, second)

    #
    # theoretical time calculations
    #

    def _time_between_events_theoretical(self, first, second):
        # TODO: only handling linear changes for now, ignoring curves

        # get the horizontal beat distance between them (remember, the
        # prev one is negative for some reason for Ableton)
        if first.beat <= 0:
            beat_distance = second.beat
        else:
            beat_distance = second.beat - first.beat

        # integrate that line from first_spb to second_spb over the
        # beat_distance
        theoretical_time_elapsed = calc_time_elapsed_theoretical(first.bpm, second.bpm, beat_distance)

        real_time_elapsed = theoretical_time_elapsed

        return real_time_elapsed

    #
    # daw time calculations (tempo quantization)
    #

    def _time_between_events_daw(self, first, second):
        """
        Compute time between events taking into account DAW tempo
        quantization.

        second.prev_aligned_bpm must be set in the process of this
        function executing.
        """
        # TODO: only handling linear changes for now, ignoring curves

        # Explanation of prev_aligned_bpm:
        #
        # If the first event in the pair is unaligned, then the bpm to use
        # during the calculation of its interval is actually the bpm of the
        # closest previous aligned point (not necessarily the immediate prevous
        # point), stored in its prev_aligned_bpm field.  That prev_aligned_bpm
        # information requires more context than is available from just first
        # and second, so it is set for us by a previous iteration of this
        # function running.  This function is responsible for setting the
        # second.prev_aligned_bpm, which results in a chain-like propagation.
        # Technically it does not need to set second.prev_aligned_bpm if second
        # is aligned, as second will never need that value but for consistency
        # we unconditionally forward prev_aligned_bpm.
        #
        # An alternative might simply store some state on the project for the
        # most recent aligned bpm, instead of tracking them for all points. We
        # opted to store this in case it's useful later if doing further
        # analysis of the points.
        #
        # Note that if a point is aligned, its prev_aligned_bpm should not be
        # set to its own bpm.

        ret = None

        vertical = first.beat == second.beat
        horizontal = first.bpm == second.bpm

        if vertical:
            ret = self._time_between_events_daw_vertical(first, second)
        elif horizontal:
            ret = self._time_between_events_daw_horizontal(first, second, self.TEMPO_QUANT)
        else:
            # slope
            ret = self._time_between_events_daw_slope(first, second, self.TEMPO_QUANT)

        assert second.prev_aligned_bpm is not None, 'prev_aligned_bpm must be forwarded'
        return ret

    def _time_between_events_daw_horizontal(self, first, second, quant):
        """
        Time elapsed between points on a horizontal line, taking into
        account quantization and alignment.

        Responsible for setting second.prev_aligned_bpm
        """
        assert first.bpm == second.bpm, "Must be horizontal line"

        # next, get the horizontal beat distance between them (remember, the
        # prev one is negative for some reason for Ableton)
        start_beat = 0. if first.beat <= 0 else first.beat
        end_beat = second.beat
        interval = end_beat - start_beat
        beat_align = 4/quant # e.g. .25 for 16 notes

        # they are both aligned 
        if start_beat % beat_align == 0 and end_beat % beat_align == 0:
            # technically not necessary, but for consistency we forward
            second.prev_aligned_bpm = first.bpm
            return spb(first.bpm) * interval

        window_start, window_end = self._alignment_window(start_beat, beat_align)

        # is there any possibility they are within the same alignment window
        # including aligned on the ends?
        if start_beat == window_start:
            # since start_beat is aligned, we use first.bpm and forward it
            # doesn't matter where end_beat is
            elapsed = spb(first.bpm) * interval
            second.prev_aligned_bpm = first.bpm
            return elapsed
        else:
            # otherwise, it's not aligned. what about end_beat?
            # is end_beat within the windows, including aligned on the end?
            if end_beat <= window_end:
                # since start_beat is not aligned, we use prev_aligned_bpm
                # and forward that
                elapsed = spb(first.prev_aligned_bpm) * interval
                second.prev_aligned_bpm = first.prev_aligned_bpm
                return elapsed
            else:
                # since we start unaligned and we span into another window, the
                # bpm that should be used for the starting chunk is
                # potentially different than the bpm for the rest of the span
                first_interval = window_end - start_beat
                second_interval = end_beat - window_end
                first_elapsed = spb(first.prev_aligned_bpm) * first_interval
                second_elapsed  = spb(first.bpm) * second_interval

                second.prev_aligned_bpm = first.bpm
                elapsed = first_elapsed + second_elapsed
                return elapsed

        # should not be possible to get here
        raise ValueError('Error in handling straight line points, should not have gotten here')

    def _time_between_events_daw_vertical(self, first, second):
        """
        Responsible for setting second.prev_aligned_bpm
        """
        assert first.beat == second.beat, "Must be vertical line"
        # always need to forward the prev_aligned_bpm in case of a pathological
        # situation with a lot of small segments all within an alignment window.
        # technically, we don't if beat is aligned
        second.prev_aligned_bpm = first.prev_aligned_bpm
        return 0.0
    
    def _time_elapsed_bpm_range_daw(self, start_bpm, end_bpm, interval, beat_align):
        """
        Calculate time elapsed to go from start_bpm to end_bpm across interval
        beats given a DAW tempo quantization ever beat_align beats
        """
        steps = int(interval // beat_align)
        bpm_steps = linspace(start_bpm, end_bpm, steps+1)[:-1]
        sec_per_beat = map(spb, bpm_steps)
        elapsed = sum(map(lambda x: x * beat_align, sec_per_beat))
        return elapsed

    def _time_between_events_daw_slope(self, first, second, quant):
        """
        Time elapsed between points on a sloped line, taking into
        account quantization and alignment.

        Responsible for setting second.prev_aligned_bpm.
        """
        assert power_of_two(quant)
        assert first.beat != second.beat, "Not meant to handle vertical lines"
        
        start_beat = 0. if first.beat <= 0 else first.beat
        end_beat = second.beat
        start_bpm = first.bpm
        end_bpm = second.bpm

        interval = end_beat - start_beat
        beat_align = 4/ (quant) # e.g. .25 for 16 notes

        # handle if they're both aligned
        if start_beat % beat_align == 0 and end_beat % beat_align == 0:
            # not forwarding persay, nothing to fwd here since they're both
            # aligned. just initializing.
            second.prev_aligned_bpm = first.bpm
            return self._time_elapsed_bpm_range_daw(start_bpm, end_bpm, interval, beat_align)

        # ok, at least one of them is unaligned. we need to handle every possible
        # permutation of their state of alignment

        window_start, window_end = self._alignment_window(start_beat, beat_align)

        # here we handle if they are within the same alignment window

        if start_beat == window_start:
            # if start_beat is aligned 
            if end_beat < window_end:
                # since start_beat is aligned, we use first.bpm and forward it
                elapsed = spb(first.bpm) * interval
                second.prev_aligned_bpm = first.bpm
                return elapsed
            else:
                # end_beat must be in a following window, due to the above
                # check if they are both aligned. we fall through
                pass
        else:
            # otherwise, it's not aligned. what about end_beat?
            # is end_beat within the windows, including aligned on the end?
            if end_beat <= window_end:
                # since start_beat is not aligned, we use prev_aligned_bpm
                # and forward that
                elapsed = spb(first.prev_aligned_bpm) * interval
                # pass forward for consistency
                second.prev_aligned_bpm = first.prev_aligned_bpm
                return elapsed
            else:
                # end_beat must be in a following window, due to the above
                # check if they are both aligned. we fall through
                pass

        # ok.. they are in separate alignment windows

        end_diff = (end_beat % beat_align)
        end_aligned = end_beat - end_diff
        start_diff = window_end - start_beat
        start_aligned = window_end

        # bpm to use in calculation
        calc_bpm = start_bpm
        if start_beat % beat_align:
            # if start_beat is not aligned, start_bpm should actually be the value
            # of the bpm at the previous alignment (which we should have saved
            # for ourselves when we computed it in the last segment)
            assert first.prev_aligned_bpm is not None
            calc_bpm = first.prev_aligned_bpm
            
        start_aligned_bpm = self._calc_bpm_at_beat(start_aligned, first, second)
        end_aligned_bpm = self._calc_bpm_at_beat(end_aligned, first, second)
        second.prev_aligned_bpm = end_aligned_bpm  # store this for the next segment where we'll need it again
        
        alignlen = end_aligned - start_aligned
        assert alignlen % beat_align == 0
        
        middle = self._time_elapsed_bpm_range_daw(start_aligned_bpm, end_aligned_bpm, alignlen, beat_align)
        front = spb(calc_bpm) * start_diff
        back = spb(end_aligned_bpm) * end_diff
        return float(front + middle + back)

    #
    # helpers
    #

    @staticmethod
    def _alignment_window(beat, align):
        start = beat - (beat % align)
        end = start + align
        return start, end


def _register_project_subclasses():
    """
    Triggers __init_subclass__ and fills ProjectsMap
    """
    from .daw.ableton import AbletonProject
    from .daw.flstudio import FlStudioProject
    from .daw.cue import CueFile

_register_project_subclasses()
