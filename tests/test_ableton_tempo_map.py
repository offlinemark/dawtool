from dawtool import load_project
from dawtool.project import BasicGenericTempoAutomationEvent
from dawtool.tempomap import MidiTempoMap, SetTempo 
from dawtool.tempomap import AlignedGenericTempoAutomationEvent as AlignedEvent

import pytest

import os
from dataclasses import dataclass
# from io import BytesIO

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR_ALS = os.path.join(TESTS_DIR, 'als')

ABL_TEMPO_QUANT = 16

@dataclass
class GenericTempoAutomationEventWithPrev(BasicGenericTempoAutomationEvent):
    prev_aligned_bpm: float = -1.0

Event = GenericTempoAutomationEventWithPrev

def test_no_tempo_auto():
    fname = f'{TESTS_DIR_ALS}/example-120.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=False)
        proj.parse()

    tempo_map = MidiTempoMap(proj)
    messages = tempo_map._render_map(proj.tempo_automation_events, proj.TEMPO_QUANT)
    expected = [SetTempo(tempo=500000, time=0)]
    assert messages == expected

def test_basic_tempo_auto():
    fname = f'{TESTS_DIR_ALS}/automation.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=False)
        proj.parse()

    tempo_map = MidiTempoMap(proj)
    messages = tempo_map._render_map(proj.tempo_automation_events, proj.TEMPO_QUANT)

    expected = [SetTempo(tempo=1000000, time=0), SetTempo(tempo=1000000, time=1920), SetTempo(tempo=1000000, time=120), SetTempo(tempo=941176, time=0), SetTempo(tempo=941176, time=120), SetTempo(tempo=888889, time=0), SetTempo(tempo=888889, time=120), SetTempo(tempo=842105, time=0), SetTempo(tempo=842105, time=120), SetTempo(tempo=800000, time=0), SetTempo(tempo=800000, time=120), SetTempo(tempo=761905, time=0), SetTempo(tempo=761905, time=120), SetTempo(tempo=727273, time=0), SetTempo(tempo=727273, time=120), SetTempo(tempo=695652, time=0), SetTempo(tempo=695652, time=120), SetTempo(tempo=666667, time=0), SetTempo(tempo=666667, time=120), SetTempo(tempo=640000, time=0), SetTempo(tempo=640000, time=120), SetTempo(tempo=615385, time=0), SetTempo(tempo=615385, time=120), SetTempo(tempo=592593, time=0), SetTempo(tempo=592593, time=120), SetTempo(tempo=571429, time=0), SetTempo(tempo=571429, time=120), SetTempo(tempo=551724, time=0), SetTempo(tempo=551724, time=120), SetTempo(tempo=533333, time=0), SetTempo(tempo=533333, time=120), SetTempo(tempo=516129, time=0), SetTempo(tempo=516129, time=120), SetTempo(tempo=500000, time=0), SetTempo(tempo=500000, time=120), SetTempo(tempo=480000, time=0), SetTempo(tempo=480000, time=120), SetTempo(tempo=461538, time=0), SetTempo(tempo=461538, time=120), SetTempo(tempo=444444, time=0), SetTempo(tempo=444444, time=120), SetTempo(tempo=428571, time=0), SetTempo(tempo=428571, time=120), SetTempo(tempo=413793, time=0), SetTempo(tempo=413793, time=120), SetTempo(tempo=400000, time=0), SetTempo(tempo=400000, time=120), SetTempo(tempo=387097, time=0), SetTempo(tempo=387097, time=120), SetTempo(tempo=375000, time=0), SetTempo(tempo=375000, time=120), SetTempo(tempo=363636, time=0), SetTempo(tempo=363636, time=120), SetTempo(tempo=352941, time=0), SetTempo(tempo=352941, time=120), SetTempo(tempo=342857, time=0), SetTempo(tempo=342857, time=120), SetTempo(tempo=333333, time=0), SetTempo(tempo=333333, time=120), SetTempo(tempo=324324, time=0), SetTempo(tempo=324324, time=120), SetTempo(tempo=315789, time=0), SetTempo(tempo=315789, time=120), SetTempo(tempo=307692, time=0), SetTempo(tempo=307692, time=120), SetTempo(tempo=300000, time=0)]

    assert messages == expected

def test_intense_aligned_tempo_auto():
    fname = f'{TESTS_DIR_ALS}/automation-intense.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=False)
        proj.parse()

    tempo_map = MidiTempoMap(proj)
    messages = tempo_map._render_map(proj.tempo_automation_events, proj.TEMPO_QUANT)

    expected = [SetTempo(tempo=496851, time=0), SetTempo(tempo=496851, time=960), SetTempo(tempo=496851, time=120), SetTempo(tempo=530197, time=0), SetTempo(tempo=530197, time=120), SetTempo(tempo=568341, time=0), SetTempo(tempo=568341, time=120), SetTempo(tempo=612399, time=0), SetTempo(tempo=612399, time=120), SetTempo(tempo=663862, time=0), SetTempo(tempo=663862, time=120), SetTempo(tempo=724767, time=0), SetTempo(tempo=724767, time=120), SetTempo(tempo=797977, time=0), SetTempo(tempo=797977, time=120), SetTempo(tempo=887639, time=0), SetTempo(tempo=887639, time=120), SetTempo(tempo=1000000, time=0), SetTempo(tempo=1000000, time=120), SetTempo(tempo=1042058, time=0), SetTempo(tempo=1042058, time=120), SetTempo(tempo=1087808, time=0), SetTempo(tempo=1087808, time=120), SetTempo(tempo=1137761, time=0), SetTempo(tempo=1137761, time=120), SetTempo(tempo=1192521, time=0), SetTempo(tempo=1192521, time=120), SetTempo(tempo=953764, time=0), SetTempo(tempo=953764, time=120), SetTempo(tempo=794663, time=0), SetTempo(tempo=794663, time=120), SetTempo(tempo=681054, time=0), SetTempo(tempo=681054, time=120), SetTempo(tempo=595866, time=0), SetTempo(tempo=595866, time=120), SetTempo(tempo=529619, time=0), SetTempo(tempo=529619, time=120), SetTempo(tempo=476629, time=0), SetTempo(tempo=476629, time=120), SetTempo(tempo=616787, time=0), SetTempo(tempo=616787, time=120), SetTempo(tempo=873712, time=0), SetTempo(tempo=873712, time=120), SetTempo(tempo=1497502, time=0), SetTempo(tempo=1497502, time=120), SetTempo(tempo=899400, time=0), SetTempo(tempo=899400, time=120), SetTempo(tempo=642704, time=0), SetTempo(tempo=642704, time=120), SetTempo(tempo=500000, time=0), SetTempo(tempo=500000, time=120), SetTempo(tempo=394803, time=0), SetTempo(tempo=394803, time=120), SetTempo(tempo=326177, time=0), SetTempo(tempo=326177, time=120), SetTempo(tempo=396037, time=0), SetTempo(tempo=396037, time=120), SetTempo(tempo=503978, time=0), SetTempo(tempo=503978, time=120), SetTempo(tempo=692805, time=0), SetTempo(tempo=692805, time=120), SetTempo(tempo=1107908, time=0), SetTempo(tempo=1107908, time=120), SetTempo(tempo=872848, time=0), SetTempo(tempo=872848, time=120), SetTempo(tempo=720073, time=0), SetTempo(tempo=720073, time=120), SetTempo(tempo=612812, time=0), SetTempo(tempo=612812, time=120), SetTempo(tempo=533363, time=0), SetTempo(tempo=533363, time=120), SetTempo(tempo=472151, time=0), SetTempo(tempo=472151, time=120), SetTempo(tempo=423542, time=0), SetTempo(tempo=423542, time=120), SetTempo(tempo=384008, time=0), SetTempo(tempo=384008, time=120), SetTempo(tempo=351224, time=0), SetTempo(tempo=351224, time=120), SetTempo(tempo=323597, time=0), SetTempo(tempo=323597, time=120), SetTempo(tempo=300000, time=0), SetTempo(tempo=300000, time=120), SetTempo(tempo=355740, time=0), SetTempo(tempo=355740, time=120), SetTempo(tempo=436920, time=0), SetTempo(tempo=436920, time=120), SetTempo(tempo=566105, time=0), SetTempo(tempo=566105, time=120), SetTempo(tempo=803753, time=0), SetTempo(tempo=803753, time=120), SetTempo(tempo=724971, time=0), SetTempo(tempo=724971, time=120), SetTempo(tempo=660255, time=0), SetTempo(tempo=660255, time=120), SetTempo(tempo=606146, time=0), SetTempo(tempo=606146, time=120), SetTempo(tempo=560234, time=0), SetTempo(tempo=560234, time=120), SetTempo(tempo=520787, time=0), SetTempo(tempo=520787, time=120), SetTempo(tempo=486530, time=0), SetTempo(tempo=486530, time=120), SetTempo(tempo=456502, time=0), SetTempo(tempo=456502, time=120), SetTempo(tempo=429964, time=0), SetTempo(tempo=429964, time=120), SetTempo(tempo=406343, time=0)]

    assert messages == expected

def test_unaligned_tempo_auto():
    pass






def test_transform_single_unaligned():
    events = [
        Event(beat=0, bpm=60),
        Event(beat=.3, bpm=54, prev_aligned_bpm=55),
        Event(beat=.75, bpm=70),
    ]

    expected = [
        Event(beat=0, bpm=60),
        AlignedEvent(beat=.25, bpm=55),
        AlignedEvent(beat=.5, bpm=61.111111111111114),
        Event(beat=.75, bpm=70),
    ]

    aligned = MidiTempoMap._compute_aligned_points(events, ABL_TEMPO_QUANT)
    assert expected == aligned

def test_transform_multiple_not_adjacent_unaligned_and_NOT_aligned_at_end():
    events = [
        Event(beat=0, bpm=60),
        Event(beat=.3, bpm=54, prev_aligned_bpm=55),
        Event(beat=.81, bpm=59.4, prev_aligned_bpm=57),
    ]

    expected = [
        Event(beat=0, bpm=60),
        AlignedEvent(beat=.25, bpm=55),
        AlignedEvent(beat=.5, bpm=56.11764705882353),
        AlignedEvent(beat=.75, bpm=57),
    ]

    aligned = MidiTempoMap._compute_aligned_points(events, ABL_TEMPO_QUANT)
    assert expected == aligned

def test_transform_multiple_not_adjacent_unaligned_and_aligned_at_end():
    events = [
        Event(beat=0, bpm=60),
        Event(beat=.3, bpm=54, prev_aligned_bpm=55),
        Event(beat=.81, bpm=59.4, prev_aligned_bpm=57),
        Event(beat=1, bpm=61),
    ]

    expected = [
        Event(beat=0, bpm=60),
        AlignedEvent(beat=.25, bpm=55),
        AlignedEvent(beat=.5, bpm=56.11764705882353),
        AlignedEvent(beat=.75, bpm=57),
        Event(beat=1, bpm=61),
    ]

    aligned = MidiTempoMap._compute_aligned_points(events, ABL_TEMPO_QUANT)
    assert expected == aligned

def test_transform_multiple_adjacent_unaligned():
    events = [
        Event(beat=0, bpm=60),
        Event(beat=.3, bpm=54, prev_aligned_bpm=55),
        Event(beat=.6, bpm=56, prev_aligned_bpm=55.333333333333336),
        Event(beat=.8, bpm=63, prev_aligned_bpm=61.25),
    ]

    expected = [
        Event(beat=0, bpm=60),
        AlignedEvent(beat=.25, bpm=55),
        AlignedEvent(beat=.5, bpm=55.333333333333336),
        AlignedEvent(beat=.75, bpm=61.25)
    ]

    aligned = MidiTempoMap._compute_aligned_points(events, ABL_TEMPO_QUANT)
    assert expected == aligned

def test_transform_multiple_unaligned_in_same_quant():
    """
    If multiple points in same quant, points after the first get ignored,
    except for the last, which is used in computing the tail end point.
    """
    events = [
        Event(beat=0, bpm=60),

        Event(beat=.3, bpm=54, prev_aligned_bpm=55),
        Event(beat=.33, bpm=58),
        Event(beat=.39, bpm=43),

        Event(beat=.75, bpm=61),
    ]

    expected = [
        Event(beat=0, bpm=60),

        AlignedEvent(beat=.25, bpm=55),
        AlignedEvent(beat=.5, bpm=48.5),

        Event(beat=.75, bpm=61),
    ]

    aligned = MidiTempoMap._compute_aligned_points(events, ABL_TEMPO_QUANT)
    assert expected == aligned