"""
Mostly integration type tests.

These long arrays of results are created by calling

    print(proj.tempo_automation_events)
    print(proj.markers)

in the test, running it, copy-pasting what pytest prints to stdout
into the file, and removing the print.
"""

from dawtool import extract_markers, format_time, load_project
from dawtool.daw.ableton import TempoAutomationFloatEvent, AbletonSetVersion, AbletonProject
from dawtool.marker import Marker
from dawtool.project import UnknownExtension

import pytest

import os
from io import BytesIO

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR_ALS = os.path.join(TESTS_DIR, 'als')

#
# Ableton 10 integration tests
#

def test_als120():
    fname = f'{TESTS_DIR_ALS}/example-120.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=True)
        proj.parse()
        markers = proj.markers

    assert proj.version == AbletonSetVersion(major='5', minor='10.0_377', minorA=10, minorB=0, minorC=377, schema_change_count='3', creator='Ableton Live 10.1.7', revision='f7eb4c8e0a49802359f4e078b341fdfb9d547a77')

    assert [m.time for m in markers] == [0.0, 200.0000133333342, 216.00001440000096, 324.00002160000145, 464.0000309333354, 604.0000402666693, 716.0000477333365, 840.0000560000037, 1000.000066666671, 1189.053707412938, 1392.000092800006, 1512.0001008000067, 1656.0001104000073, 1792.0001194666745, 3904.0002602666837]
    assert [m.text for m in markers] == ['mirvs - his track你好', 'comfort - other track', 'comfort - yo', 'sh1n - track', 'stm - ggr', 'heart - ID', 'ID - ID', '', '', 'track - this track', 'another track', 'another track', 'another track', 'tids track', 'sd']
    assert [format_time(m.time) for m in markers] == ['00:00', '03:20', '03:36', '05:24', '07:44', '10:04', '11:56', '14:00', '16:40', '19:49', '23:12', '25:12', '27:36', '29:52', '01:05:04']

def test_als140():
    fname = f'{TESTS_DIR_ALS}/example-140.als'
    with open(fname, 'rb') as f:
        markers = extract_markers(fname, f, theoretical=True)

    times = ['00:00', '02:51', '03:05', '04:37', '06:37', '01:00:20']
    assert [format_time(m.time) for m in markers] == times

    assert [m.time for m in markers] == [0.0, 171.42857142857142, 185.14285714285714, 277.7142857142857, 397.71428571428567, 3620.5714285714284]
    assert [m.text for m in markers] == ['mirvs - his track你好', 'comfort - other track', 'comfort - yo', 'sh1n - track', 'stm - ggr',  'sd']

def test_als_empty():
    fname = f'{TESTS_DIR_ALS}/empty.als'
    with pytest.raises(ValueError):
        with open(fname, 'rb') as f:
            markers = extract_markers(fname, f)

def test_als_junk():
    fname = f'{TESTS_DIR_ALS}/junk.als'
    with pytest.raises(ValueError):
        with open(fname, 'rb') as f:
            markers = extract_markers(fname, f)

def test_als_automation_theo():
    fname = f'{TESTS_DIR_ALS}/automation.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=True)

    proj.parse()

    auto = [TempoAutomationFloatEvent(id='92', time=-63072000.0, real_time=0.0, value=60.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='290', time=4.0, real_time=4.0, value=60.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='291', time=8.0, real_time=6.772588722239782, value=120.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='596', time=12.0, real_time=8.305065593537753, value=200.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None)]
    marks = [Marker(time=0.0, text='A'), Marker(time=4.0, text='B'), Marker(time=5.6218604324326575, text='D'), Marker(time=6.772588722239782, text='C'), Marker(time=7.635634939595124, text='Z'), Marker(time=8.905065593537753, text='E')]

    assert proj.tempo_automation_events == auto
    assert proj.markers == marks

def test_als_auto_unaligned_daw():
    'als with many points, fairly steep slopes, and points unaligned on 16th notes'
    fname = f'{TESTS_DIR_ALS}/automation-intense-unaligned.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=False)

    proj.parse()
    print(proj.tempo_automation_events)
    auto = [TempoAutomationFloatEvent(id='598', time=-63072000.0, real_time=0.0, value=120.760574, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='649', time=1.8125, real_time=0.9005422581048679, value=120.760574, curve_control1=None, curve_control2=None, prev_aligned_bpm=120.760574), TempoAutomationFloatEvent(id='667', time=4.0625, real_time=2.3966117557062345, value=60.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=61.687793722222224), TempoAutomationFloatEvent(id='669', time=4.093925345487846, real_time=2.427177295750691, value=80.6271286, curve_control1=None, curve_control2=None, prev_aligned_bpm=61.687793722222224), TempoAutomationFloatEvent(id='670', time=4.1484021187146185, real_time=2.480163570609616, value=34.5163536, curve_control1=None, curve_control2=None, prev_aligned_bpm=61.687793722222224), TempoAutomationFloatEvent(id='671', time=4.178364343989344, real_time=2.5093060217820256, value=95.9973831, curve_control1=None, curve_control2=None, prev_aligned_bpm=61.687793722222224), TempoAutomationFloatEvent(id='668', time=4.25, real_time=2.578981708028704, value=58.0627136, curve_control1=None, curve_control2=None, prev_aligned_bpm=61.687793722222224), TempoAutomationFloatEvent(id='672', time=4.457870775058275, real_time=2.7937881772788167, value=55.9149513, curve_control1=None, curve_control2=None, prev_aligned_bpm=58.0627136), TempoAutomationFloatEvent(id='712', time=4.548306901431902, real_time=2.8828996005984946, value=72.4000015, curve_control1=None, curve_control2=None, prev_aligned_bpm=63.594430905110116), TempoAutomationFloatEvent(id='700', time=4.80127970987346, real_time=3.113221253516874, value=78.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=76.86483333864655), TempoAutomationFloatEvent(id='600', time=5.0, real_time=3.268340530951092, value=50.3135643, curve_control1=None, curve_control2=None, prev_aligned_bpm=76.86483333864655), TempoAutomationFloatEvent(id='599', time=6.5, real_time=4.455212285145871, value=125.883995, curve_control1=None, curve_control2=None, prev_aligned_bpm=50.3135643), TempoAutomationFloatEvent(id='601', time=7.25, real_time=4.946994580622144, value=40.0667267, curve_control1=None, curve_control2=None, prev_aligned_bpm=125.883995), TempoAutomationFloatEvent(id='291', time=8.0, real_time=5.706896019728953, value=120.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=40.0667267), TempoAutomationFloatEvent(id='602', time=8.5, real_time=5.9305966531965275, value=183.949417, curve_control1=None, curve_control2=None, prev_aligned_bpm=120.0), TempoAutomationFloatEvent(id='603', time=9.5, real_time=6.410345802117857, value=54.1561279, curve_control1=None, curve_control2=None, prev_aligned_bpm=183.949417), TempoAutomationFloatEvent(id='596', time=12.0, real_time=7.860727189077446, value=200.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=54.1561279), TempoAutomationFloatEvent(id='604', time=13.0, real_time=8.27541854608016, value=74.6498032, curve_control1=None, curve_control2=None, prev_aligned_bpm=200.0), TempoAutomationFloatEvent(id='605', time=15.25, real_time=9.587704231552863, value=147.658524, curve_control1=None, curve_control2=None, prev_aligned_bpm=74.6498032)]
    assert proj.tempo_automation_events == auto
    assert proj.markers == [Marker(time=0.0, text='A'), Marker(time=0.7452763515350631, text='X'), Marker(time=2.335821771598745, text='B'), Marker(time=4.173841066076857, text='D'), Marker(time=5.706896019728953, text='C'), Marker(time=6.905534691333889, text='Z'), Marker(time=7.692021891450212, text='1'), Marker(time=8.974199935476374, text='E'), Marker(time=10.705147339679828, text='YY')]

def test_als_auto_pathological3_daw():
    """
    25505 automation points,no slopes, just horizontal and vertical lines
    stress testing alignment
    """

    fname = f'{TESTS_DIR_ALS}/automation-pathological-end3.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=False)

    proj.parse()
    assert proj.markers == [Marker(time=447.53153265863915, text='A'), Marker(time=466.60806196643625, text='X'), Marker(time=486.1465317732963, text='B'), Marker(time=495.56805602397407, text='D'), Marker(time=505.2425003381325, text='C'), Marker(time=517.7672955377825, text='Z'), Marker(time=525.4196287976511, text='1'), Marker(time=539.046232416382, text='E'), Marker(time=549.6099694804802, text='YY')]


def test_als_automation_intense_theo():
    fname = f'{TESTS_DIR_ALS}/automation-intense.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=True)

    proj.parse()

    # auto = [TempoAutomationFloatEvent(id='598', time=-63072000.0, real_time=0.0, value=120.760574, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='597', time=2.0, real_time=0.9937018020467507, value=120.760574, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='290', time=4.0, real_time=2.4905527030701258, value=60.0, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='600', time=5.0, real_time=3.5868133818231116, value=50.3135643, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='599', time=6.5, real_time=4.838676372461883, value=125.883995, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='601', time=7.25, real_time=5.57897557720625, value=40.0667267, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='291', time=8.0, real_time=6.32803879569597, value=120.0, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='602', time=8.5, real_time=6.534582951935399, value=183.949417, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='603', time=9.5, real_time=7.251625196560135, value=54.1561279, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='596', time=12.0, real_time=9.011510026924826, value=200.0, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='604', time=13.0, real_time=9.563386505013117, value=74.6498032, curve_control1=None, curve_control2=None), TempoAutomationFloatEvent(id='605', time=15.25, real_time=10.924744397672802, value=147.658524, curve_control1=None, curve_control2=None)]
    # marks = [Marker(time=0.0, text='A'), Marker(time=0.7452763515350631, text='X'), Marker(time=2.4905527030701258, text='B'), Marker(time=4.481006849648747, text='D'), Marker(time=6.32803879569597, text='C'), Marker(time=7.708620375464505, text='Z'), Marker(time=8.710756906470802, text='1'), Marker(time=10.245379935705511, text='E'),Marker(time=12.042187505799767, text='YY')]

    auto = [TempoAutomationFloatEvent(id='598', time=-63072000.0, real_time=0.0, value=120.760574, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='597', time=2.0, real_time=0.9937018020467507, value=120.760574, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='290', time=4.0, real_time=2.3751211991079835, value=60.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='600', time=5.0, real_time=3.4657381748335556, value=50.3135643, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='599', time=6.5, real_time=4.557934529843792, value=125.883995, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='601', time=7.25, real_time=5.158240936269706, value=40.0667267, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='291', time=8.0, real_time=5.775787872079139, value=120.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='602', time=8.5, real_time=5.976181756557032, value=183.949417, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='603', time=9.5, real_time=6.541445040210277, value=54.1561279, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='596', time=12.0, real_time=7.885121207824302, value=200.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='604', time=13.0, real_time=8.356844190648877, value=74.6498032, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id='605', time=15.25, real_time=9.618101061558722, value=147.658524, curve_control1=None, curve_control2=None, prev_aligned_bpm=None)]
    marks = [Marker(time=0.0, text='A'), Marker(time=0.7452763515350631, text='X'), Marker(time=2.3751211991079835, text='B'), Marker(time=4.292025681716721, text='D'), Marker(time=5.775787872079139, text='C'), Marker(time=6.984600086821905, text='Z'), Marker(time=7.722987605556904, text='1'), Marker(time=9.024251745511293, text='E'), Marker(time=10.735544169685687, text='YY')]

    assert proj.markers == marks
    assert proj.tempo_automation_events == auto


#
# Ableton 8 integration tests
#

def test_als8_noauto():
    fname = f'{TESTS_DIR_ALS}/live8/live8-patch-markers-noauto.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f)

    proj.parse()

    print(proj.markers)
    print(proj.tempo_automation_events)

    marks = [Marker(time=125.91815320041972, text='b'), Marker(time=200.20986358866736, text='c')]
    auto = [TempoAutomationFloatEvent(id=None, time=-63072000.0, real_time=None, value=95.3, curve_control1=None, curve_control2=None, prev_aligned_bpm=None)]

    assert proj.markers == marks
    assert proj.tempo_automation_events == auto

def test_als8_auto():
    fname = f'{TESTS_DIR_ALS}/live8/live8-patch-markers-auto.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f)

    proj.parse()

    print(proj.markers)
    print(proj.tempo_automation_events)

    marks = [Marker(time=81.09683000726724, text='b'), Marker(time=125.34683000726724, text='c')]
    auto = [TempoAutomationFloatEvent(id=None, time=-63072000.0, real_time=0.0, value=95.3, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id=None, time=0.0, real_time=0.0, value=95.3, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id=None, time=4.0, real_time=2.103149251721395, value=138.3, curve_control1=None, curve_control2=None, prev_aligned_bpm=95.3), TempoAutomationFloatEvent(id=None, time=200.0, real_time=81.09683000726724, value=160.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=138.3)]

    assert proj.markers == marks
    assert proj.tempo_automation_events == auto

#
# Ableton 9 integration tests
#

def test_als9_noauto():
    fname = f'{TESTS_DIR_ALS}/live9/live9-patch-markers-noauto.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f)

    proj.parse()

    print(proj.markers)
    print(proj.tempo_automation_events)

    marks = [Marker(time=14.222222222222221, text='Live9Marker'), Marker(time=28.444444444444443, text='Live9Marker2'), Marker(time=56.888888888888886, text='Live9Marker3')]
    auto = [TempoAutomationFloatEvent(id=None, time=-63072000.0, real_time=None, value=135.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None)]

    assert proj.markers == marks
    assert proj.tempo_automation_events == auto

def test_als9_auto():
    fname = f'{TESTS_DIR_ALS}/live9/live9-patch-2-0point.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f)

    proj.parse()

    print(proj.markers)
    print(proj.tempo_automation_events)

    marks = [Marker(time=11.169835008759637, text='Live9Marker'), Marker(time=22.141263580188213, text='Live9Marker2'), Marker(time=44.08412072304535, text='Live9Marker3')]
    auto = [TempoAutomationFloatEvent(id=None, time=-63072000.0, real_time=0.0, value=135.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id=None, time=0.0, real_time=0.0, value=135.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=None), TempoAutomationFloatEvent(id=None, time=4.0, real_time=1.5698350087596382, value=175.0, curve_control1=None, curve_control2=None, prev_aligned_bpm=135.0)]

    assert proj.markers == marks
    assert proj.tempo_automation_events == auto


#
# Unit tests
#

def test_als_malformed_master():
    p = AbletonProject('f', BytesIO())
    p.version = AbletonSetVersion(None, None, 10, None, None, None, None, None)

    with pytest.raises(ValueError):
        contents = ''
        p._parse_automation(contents.encode())

    with pytest.raises(ValueError):
        contents = '<MasterTrack>'
        p._parse_automation(contents.encode())

    # no automation envelopes tag
    contents = '<MasterTrack></MasterTrack>'
    p._parse_automation(contents.encode())

    # no envelopes tag
    contents = '<MasterTrack><AutomationEnvelopes></AutomationEnvelopes></MasterTrack>'
    p._parse_automation(contents.encode())

def test_bad_ext():
    with pytest.raises(UnknownExtension):
        load_project('f.mp3', BytesIO())

    with pytest.raises(UnknownExtension):
        load_project('f', BytesIO())

def test_als_malform_no_ae():
    fname = f'{TESTS_DIR_ALS}/markers-malformed-no-master-ae.als'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=True)

    proj.parse()
