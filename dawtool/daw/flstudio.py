"""
FL Studio project module, including tempo automation code.
"""

from ..marker import Marker
from .flstudio_core import FlStudioProjectCore, Event, Channel, \
                           ChannelAutomationPoint, PlaylistItem, \
                           AutomationChannel, FlStudioRawMarker

from dataclasses import dataclass, field
from typing import List
from collections import Counter


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


class FlStudioProject(FlStudioProjectCore):
    def __init__(self, filename, stream, *args, **kwargs):
        super().__init__(filename, stream, *args, **kwargs)
        self.tempo_automation_events = []

    def __repr__(self):
        return '<FlStudioProject version={} ppb={} bpm={} channels={}>'.format(self.version, self.pulses_per_beat,
                self.beats_per_min, self.num_channels)

    def parse(self):
        super().parse()
        self._compute_tempo_automations()
        self._calc_markers()
        self._calc_tempo_automation_event_real_times() # TODO: remove this - for now we need this because compute_tempo_map needs its analysis even in projects w/o markers
        self._compute_tempo_map()

    @property
    def has_tempo_automation(self):
        return bool(self.tempo_automation_events)

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
