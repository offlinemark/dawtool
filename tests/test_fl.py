from dawtool import extract_markers, format_time, load_project
from dawtool.daw.flstudio import Channel, ChannelAutomationPoint, PlaylistItem, GlobalTempoAutomationPoint, ArtificialGlobalTempoAutomationPoint, FlStudioProject, AutomationChannel, FlStudioRawMarker
from dawtool.marker import Marker

from io import BytesIO
import pytest

import os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))



def test_flp_theo():
    fname = f'{TESTS_DIR}/fl/fl test.flp'
    with open(fname, 'rb') as f:
        markers = extract_markers(fname, f, theoretical=True)
    assert markers == [Marker(time=0.0, text='yoyo'), Marker(time=3.9006710621563982, text='magic'), Marker(time=9.068958321105523, text='sdaf'), Marker(time=25.042552775223523, text='sdf'), Marker(time=114.55011445229198, text='yoy'), Marker(time=172.16755032966174, text='new son - yo'), Marker(time=275.46808052745877, text='yoxxxxxxxGGGG'), Marker(time=392.855046661319, text='bleh33'), Marker(time=571.870170015456, text='IN'), Marker(time=669.8882867372292, text='QWER'), Marker(time=967.2686009430086, text='WOW'), Marker(time=3259.962403563346, text='out here'), Marker(time=3626.980089866244, text='end')]

def test_flp_auto_basic_theo():
    fname = f'{TESTS_DIR}/fl/auto-basic.flp'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=True)
        proj.parse()
    print(proj.channels)
    assert proj.channels == [Channel(id=0, name='Kick', sample_path='%FLStudioFactoryData%/Data/Patches/Packs/Legacy/Drums/Dance/Kick Basic.wav', automation_points=[]), Channel(id=1, name='Clap', sample_path='%FLStudioFactoryData%/Data/Patches/Packs/Legacy/Drums/Dance/Clap Basic.wav', automation_points=[]), Channel(id=2, name='Hat', sample_path='%FLStudioFactoryData%/Data/Patches/Packs/Legacy/Drums/Dance/Hat Basic.wav', automation_points=[]), Channel(id=3, name='Snare', sample_path='%FLStudioFactoryData%/Data/Patches/Packs/Legacy/Drums/Dance/Snare Basic.wav', automation_points=[]), Channel(id=4, name='coin 4', sample_path='/Users/mark/Music/recording/samples/_drumkits/ａｌｕｃａｒｄ＇ｓ\u3000ｉｃｅ\u3000ｃａｓｔｌｅ\u3000ｄｒｕｍ\u3000ｋｉｔ/_ｓｆｘ_/random fx I mostly use/coin.wav', automation_points=[]), Channel(id=5, name='Tempo 5', sample_path=None, automation_points=[ChannelAutomationPoint(beat_increment=0.0, value=0.5, tension=0.0, unknown3=b'\x00\x00\x00', direction=0), ChannelAutomationPoint(beat_increment=1.2499998807907104, value=0.5, tension=0.0, unknown3=b'\x00\x00\x00', direction=2)]), Channel(id=6, name='Tempo 6', sample_path=None, automation_points=[ChannelAutomationPoint(beat_increment=0.0, value=0.5833333134651184, tension=0.0, unknown3=b'\x00\x00\x00', direction=0), ChannelAutomationPoint(beat_increment=4.75, value=0.3076923191547394, tension=0.0, unknown3=b'\x00\x00\x00', direction=2)])]

    print(proj.playlist_items)
    assert proj.playlist_items == [PlaylistItem(start_pulse=0, channel_id=5, len_pulses=456, track_id=1, flags=64), PlaylistItem(start_pulse=0, channel_id=4, len_pulses=192, track_id=3, flags=64), PlaylistItem(start_pulse=752, channel_id=6, len_pulses=456, track_id=2, flags=64), PlaylistItem(start_pulse=1376, channel_id=5, len_pulses=456, track_id=1, flags=64)]

def test_flp_auto_basic2_theo():
    fname = f'{TESTS_DIR}/fl/auto-basic2.flp'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=True)
        proj.parse()

    print(proj.tempo_automation_events)
    print(proj.markers)
    auto = [ArtificialGlobalTempoAutomationPoint(beat=0.0, real_time=0.0, bpm=106.48648738861084, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=0.9270833333333334, real_time=0.5223667468436876, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=4.984892686208089, real_time=2.398727645463972, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=7.145833333333333, real_time=3.2288451006413315, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=7.145833333333333, real_time=3.2288451006413315, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=11.203642686208088, real_time=5.1052059992616154, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=14.458333333333334, real_time=6.355483521217345, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=14.458333333333334, real_time=6.355483521217345, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=18.51614268620809, real_time=8.23184441983763, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=20.052083333333332, real_time=8.821870408284491, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=20.052083333333332, real_time=8.821870408284491, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=24.109892686208088, real_time=10.698231306904775, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=25.28125, real_time=11.148203939758847, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=25.28125, real_time=11.148203939758847, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=29.339059352874756, real_time=13.024564838379131, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=30.583333333333332, real_time=13.502548142351761, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=30.583333333333332, real_time=13.502548142351761, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=34.641142686208084, real_time=15.378909040972044, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=43.666666666666664, real_time=18.846031105739364, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=43.666666666666664, real_time=18.846031105739364, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=47.72447601954142, real_time=20.722392004359648, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=None)]
    markers = [Marker(time=14.464036142744112, text='Auto'), Marker(time=16.46912558510744, text='ASDF'), Marker(time=20.980291463829325, text='MM')]

    assert proj.tempo_automation_events == auto
    assert proj.markers == markers

def test_flp_auto_basic2_daw():
    fname = f'{TESTS_DIR}/fl/auto-basic2.flp'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=False)
        proj.parse()

    print(proj.tempo_automation_events)
    print(proj.markers)
    events = [ArtificialGlobalTempoAutomationPoint(beat=0.0, real_time=0.0, bpm=106.48648738861084, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=0.9270833333333334, real_time=0.5223667468436876, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=106.48648738861084), GlobalTempoAutomationPoint(beat=4.984892686208089, real_time=2.3994277372238053, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=156.1841329103173), ArtificialGlobalTempoAutomationPoint(beat=7.145833333333333, real_time=3.229545306174421, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=7.145833333333333, real_time=3.229545306174421, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=11.203642686208088, real_time=5.106139355343321, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=156.18413291031732), ArtificialGlobalTempoAutomationPoint(beat=14.458333333333334, real_time=6.356416991072306, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=14.458333333333334, real_time=6.356416991072306, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=18.51614268620809, real_time=8.233011040241207, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=156.18413291031726), ArtificialGlobalTempoAutomationPoint(beat=20.052083333333332, real_time=8.823037142461324, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=20.052083333333332, real_time=8.823037142461324, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=24.109892686208088, real_time=10.699631191630225, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=156.18413291031732), ArtificialGlobalTempoAutomationPoint(beat=25.28125, real_time=11.149603938257552, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=25.28125, real_time=11.149603938257552, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=29.339059352874756, real_time=13.026665204429104, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=156.15223454990542), ArtificialGlobalTempoAutomationPoint(beat=30.583333333333332, real_time=13.504648949660437, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=30.583333333333332, real_time=13.504648949660437, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=34.641142686208084, real_time=15.381242998829336, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=156.18413291031735), ArtificialGlobalTempoAutomationPoint(beat=43.666666666666664, real_time=18.848365177369914, bpm=156.1904740333557, track_id=None, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=43.666666666666664, real_time=18.848365177369914, bpm=106.48648738861084, track_id=1, prev_aligned_bpm=156.1904740333557), GlobalTempoAutomationPoint(beat=47.72447601954142, real_time=20.7244921622086, bpm=156.1904740333557, track_id=1, prev_aligned_bpm=156.12033618949357)]
    marks = [Marker(time=14.466061944142794, text='Auto'), Marker(time=16.47145965673799, text='ASDF'), Marker(time=20.98239198176239, text='MM')]

    assert proj.tempo_automation_events == events
    assert proj.markers == marks

def test_flp_auto_complex_theo():
    fname = f'{TESTS_DIR}/fl/complex.flp'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=True)
    proj.parse()

    print(proj.tempo_automation_events)
    print(proj.markers)

    auto = [GlobalTempoAutomationPoint(beat=0.0, real_time=0.0, bpm=127.88732528686523, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=1.6458414793014526, real_time=0.9123849810850921, bpm=90.70422649383545, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=2.959980010986328, real_time=1.7283322853130831, bpm=102.81690001487732, track_id=1, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=6.625, real_time=3.8670974037809733, bpm=102.81690001487732, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=6.625, real_time=3.8670974037809733, bpm=120.0, track_id=2, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=11.841332912445068, real_time=6.01160364583677, bpm=175.38461208343506, track_id=2, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=13.041666666666666, real_time=6.422244148431342, bpm=175.38461208343506, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=13.041666666666666, real_time=6.422244148431342, bpm=124.72440719604492, track_id=4, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=14.454412619272867, real_time=7.101860584876991, bpm=124.72440719604492, track_id=4, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=16.589843908945717, real_time=8.129132473842393, bpm=124.72440719604492, track_id=4, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=17.115885535875954, real_time=8.450819383229293, bpm=75.59055089950562, track_id=4, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=17.810966531435646, real_time=8.852371580604116, bpm=138.42519521713257, track_id=4, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=22.072916666666668, real_time=10.699701524497247, bpm=138.42519521713257, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=22.072916666666668, real_time=10.699701524497247, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=23.48566261927287, real_time=11.379317960942895, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=25.62109390894572, real_time=12.406589849908297, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=26.147135535875957, real_time=12.728276759295197, bpm=75.59055089950562, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=26.84221653143565, real_time=13.12982895667002, bpm=138.42519521713257, track_id=3, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=33.541666666666664, real_time=16.033686216783245, bpm=138.42519521713257, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=33.541666666666664, real_time=16.033686216783245, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=34.954412619272865, real_time=16.713302653228894, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=37.08984390894572, real_time=17.740574542194295, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=37.615885535875954, real_time=18.062261451581197, bpm=75.59055089950562, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=38.310966531435646, real_time=18.46381364895602, bpm=138.42519521713257, track_id=3, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=39.833333333333336, real_time=19.12367913060178, bpm=138.42519521713257, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=39.833333333333336, real_time=19.12367913060178, bpm=127.88732528686523, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=41.47917481263479, real_time=20.036064111686873, bpm=90.70422649383545, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=42.793313344319664, real_time=20.852011415914863, bpm=102.81690001487732, track_id=1, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=50.541666666666664, real_time=25.37365327900887, bpm=102.81690001487732, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=50.541666666666664, real_time=25.37365327900887, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=51.954412619272865, real_time=26.05326971545452, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=54.08984390894572, real_time=27.08054160441992, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=54.615885535875954, real_time=27.402228513806822, bpm=75.59055089950562, track_id=3, prev_aligned_bpm=None), ArtificialGlobalTempoAutomationPoint(beat=54.895833333333336, real_time=27.5938950362706, bpm=100.89755884981437, track_id=None, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=54.895833333333336, real_time=27.5938950362706, bpm=127.88732528686523, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=56.54167481263479, real_time=28.506280017355692, bpm=90.70422649383545, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=57.855813344319664, real_time=29.322227321583682, bpm=102.81690001487732, track_id=1, prev_aligned_bpm=None)]
    markers = [Marker(time=29.04176593744516, text='Auto'), Marker(time=32.31201984884661, text='ASDF'), Marker(time=35.223749340366794, text='MM')]

    assert proj.tempo_automation_events == auto
    assert proj.markers == markers

def test_flp_auto_complex_daw():
    fname = f'{TESTS_DIR}/fl/complex.flp'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=False)
    proj.parse()

    print(proj.tempo_automation_events)
    print(proj.markers)
    assert proj.tempo_automation_events == [GlobalTempoAutomationPoint(beat=0.0, real_time=0.0, bpm=127.88732528686523, track_id=1, prev_aligned_bpm=None), GlobalTempoAutomationPoint(beat=1.6458414793014526, real_time=0.911635230481727, bpm=90.70422649383545, track_id=1, prev_aligned_bpm=90.82207798054122), GlobalTempoAutomationPoint(beat=2.959980010986328, real_time=1.7278841654056063, bpm=102.81690001487732, track_id=1, prev_aligned_bpm=102.75371602927872), ArtificialGlobalTempoAutomationPoint(beat=6.625, real_time=3.866649627455197, bpm=102.81690001487732, track_id=None, prev_aligned_bpm=102.81690001487732), GlobalTempoAutomationPoint(beat=6.625, real_time=3.866649627455197, bpm=120.0, track_id=2, prev_aligned_bpm=102.81690001487732), GlobalTempoAutomationPoint(beat=11.841332912445068, real_time=6.011772630351835, bpm=175.38461208343506, track_id=2, prev_aligned_bpm=175.32732608763763), ArtificialGlobalTempoAutomationPoint(beat=13.041666666666666, real_time=6.422413403125042, bpm=175.38461208343506, track_id=None, prev_aligned_bpm=175.38461208343506), GlobalTempoAutomationPoint(beat=13.041666666666666, real_time=6.422413403125042, bpm=124.72440719604492, track_id=4, prev_aligned_bpm=175.38461208343506), GlobalTempoAutomationPoint(beat=14.454412619272867, real_time=7.101306113814689, bpm=124.72440719604492, track_id=4, prev_aligned_bpm=124.72440719604492), GlobalTempoAutomationPoint(beat=16.589843908945717, real_time=8.128578002780092, bpm=124.72440719604492, track_id=4, prev_aligned_bpm=124.72440719604492), GlobalTempoAutomationPoint(beat=17.115885535875954, real_time=8.449053473364255, bpm=75.59055089950562, track_id=4, prev_aligned_bpm=76.19865436084064), GlobalTempoAutomationPoint(beat=17.810966531435646, real_time=8.852002840907348, bpm=138.42519521713257, track_id=4, prev_aligned_bpm=137.85757689719802), ArtificialGlobalTempoAutomationPoint(beat=22.072916666666668, real_time=10.699335521560686, bpm=138.42519521713257, track_id=None, prev_aligned_bpm=138.42519521713257), GlobalTempoAutomationPoint(beat=22.072916666666668, real_time=10.699335521560686, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=138.42519521713257), GlobalTempoAutomationPoint(beat=23.48566261927287, real_time=11.378703970971651, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=124.72440719604492), GlobalTempoAutomationPoint(beat=25.62109390894572, real_time=12.405975859937055, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=124.72440719604492), GlobalTempoAutomationPoint(beat=26.147135535875957, real_time=12.726451330521218, bpm=75.59055089950562, track_id=3, prev_aligned_bpm=76.19865436084096), GlobalTempoAutomationPoint(beat=26.84221653143565, real_time=13.12940069806431, bpm=138.42519521713257, track_id=3, prev_aligned_bpm=137.8575768971977), ArtificialGlobalTempoAutomationPoint(beat=33.541666666666664, real_time=16.03326069493774, bpm=138.42519521713257, track_id=None, prev_aligned_bpm=138.42519521713257), GlobalTempoAutomationPoint(beat=33.541666666666664, real_time=16.03326069493774, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=138.42519521713257), GlobalTempoAutomationPoint(beat=34.954412619272865, real_time=16.712629144348707, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=124.72440719604492), GlobalTempoAutomationPoint(beat=37.08984390894572, real_time=17.73990103331411, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=124.72440719604492), GlobalTempoAutomationPoint(beat=37.615885535875954, real_time=18.060376503898272, bpm=75.59055089950562, track_id=3, prev_aligned_bpm=76.19865436084064), GlobalTempoAutomationPoint(beat=38.310966531435646, real_time=18.463325871441363, bpm=138.42519521713257, track_id=3, prev_aligned_bpm=137.85757689719802), ArtificialGlobalTempoAutomationPoint(beat=39.833333333333336, real_time=19.123194089847328, bpm=138.42519521713257, track_id=None, prev_aligned_bpm=138.42519521713257), GlobalTempoAutomationPoint(beat=39.833333333333336, real_time=19.123194089847328, bpm=127.88732528686523, track_id=1, prev_aligned_bpm=138.42519521713257), GlobalTempoAutomationPoint(beat=41.47917481263479, real_time=20.034736876644555, bpm=90.70422649383545, track_id=1, prev_aligned_bpm=90.76324425465822), GlobalTempoAutomationPoint(beat=42.793313344319664, real_time=20.850985577344076, bpm=102.81690001487732, track_id=1, prev_aligned_bpm=102.77771914604848), ArtificialGlobalTempoAutomationPoint(beat=50.541666666666664, real_time=25.372628232782063, bpm=102.81690001487732, track_id=None, prev_aligned_bpm=102.81690001487732), GlobalTempoAutomationPoint(beat=50.541666666666664, real_time=25.372628232782063, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=102.81690001487732), GlobalTempoAutomationPoint(beat=51.954412619272865, real_time=26.052778528795397, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=124.72440719604492), GlobalTempoAutomationPoint(beat=54.08984390894572, real_time=27.0800504177608, bpm=124.72440719604492, track_id=3, prev_aligned_bpm=124.72440719604492), GlobalTempoAutomationPoint(beat=54.615885535875954, real_time=27.400525888344962, bpm=75.59055089950562, track_id=3, prev_aligned_bpm=76.19865436084064), ArtificialGlobalTempoAutomationPoint(beat=54.895833333333336, real_time=27.592956291283517, bpm=100.89755884981437, track_id=None, prev_aligned_bpm=100.42673059443348), GlobalTempoAutomationPoint(beat=54.895833333333336, real_time=27.592956291283517, bpm=127.88732528686523, track_id=1, prev_aligned_bpm=100.42673059443348), GlobalTempoAutomationPoint(beat=56.54167481263479, real_time=28.50492617024704, bpm=90.70422649383545, track_id=1, prev_aligned_bpm=90.76324425465822), GlobalTempoAutomationPoint(beat=57.855813344319664, real_time=29.32117487094656, bpm=102.81690001487732, track_id=1, prev_aligned_bpm=102.77771914604848)]
    marks = [Marker(time=29.040613113158678, text='Auto'), Marker(time=32.310968190553474, text='ASDF'), Marker(time=35.22269768207366, text='MM')]
    assert proj.markers == marks

def test_flp_markers():
    """
    Test that we parse and correctly id markers of various action types.
    Test that we only look at "None" markers when computing the marker times.
    """
    fname = f'{TESTS_DIR}/fl/fl-markers.flp'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f, theoretical=False)
    proj.parse()

    print(proj.raw_markers)
    raw = [FlStudioRawMarker(time=1220, text='Auto', action=0), FlStudioRawMarker(time=1356, text='start', action=5), FlStudioRawMarker(time=1932, text='time sig', action=8), FlStudioRawMarker(time=2624, text='loop', action=4), FlStudioRawMarker(time=3168, text='marker loop', action=1), FlStudioRawMarker(time=3988, text='marker skip', action=2), FlStudioRawMarker(time=4896, text='marker pause', action=3), FlStudioRawMarker(time=5640, text='punch in', action=9), FlStudioRawMarker(time=6516, text='punch out', action=10)]
    assert proj.raw_markers == raw

    print(proj.markers)
    m = [Marker(time=5.865384615384616, text='Auto')]
    assert proj.markers == m


def test_flp_noexist_theo():
    fname = f'{TESTS_DIR}/flp/fl test.als'
    with pytest.raises(FileNotFoundError):
        with open(fname, 'rb') as f:
            markers = extract_markers(fname, f)


def test_malformed_auto_chan():
    # 44 is out of bounds
    bad_auto_chan = AutomationChannel(44, AutomationChannel.PARAM_MASTER_TEMPO, AutomationChannel.DEST_MASTER)
    print(bad_auto_chan)
    p = FlStudioProject(None, BytesIO())
    p.automation_channels.append(bad_auto_chan)

    with pytest.raises(ValueError):
        p._compute_tempo_automations()

def test_FL20_str_decode():
    p = FlStudioProject(None, BytesIO())
    p.version = (20,)

    x = '你好'
    assert x == p._decode_str(x.encode('utf-16'))
    x = 'hi'
    assert x == p._decode_str(x.encode('utf-16'))

def test_FL12_str_decode():
    p = FlStudioProject(None, BytesIO())
    p.version = (12,)

    x = '你好'
    assert x == p._decode_str(x.encode('utf-16'))
    x = 'hi'
    assert x == p._decode_str(x.encode('utf-16'))

def test_FL11_str_decode():
    p = FlStudioProject(None, BytesIO())
    p.version = (11,)

    x = 'hi'
    assert x == p._decode_str(x.encode('ascii'))

    with pytest.raises(UnicodeDecodeError):
        x = 'hi'
        assert x == p._decode_str(x.encode('utf-16'))
