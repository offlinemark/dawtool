from dawtool import extract_markers, format_time, load_project
from dawtool.daw.cue import CueFile, CueRawMarker

import pytest
import os.path
from io import BytesIO

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR_CUE = os.path.join(TESTS_DIR, 'cue')

def test_cue_rb():
    fname = f'{TESTS_DIR_CUE}/rekordbox.cue'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f)
        proj.parse()
        markers = proj.markers

    assert markers == [CueRawMarker(time=1, text='comfort - ambeat', performer=None, title='comfort - ambeat', index_num=1, orig_index='00:00:01', file='/Users/mark/Music/Ableton/ambeat Project/comfort - ambeat.mp3', file_type='WAVE'), CueRawMarker(time=18, text='Unknown Artist - REC-2020-03-11', performer='Unknown Artist', title='REC-2020-03-11', index_num=1, orig_index='00:00:18', file='/Users/mark/Music/PioneerDJ/Recording/Unknown Artist/Unknown Album/01 REC-2020-03-11.wav', file_type='WAVE')]

def test_cue_rb2():
    fname = f'{TESTS_DIR_CUE}/rekordbox2.cue'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f)
        proj.parse()
        markers = proj.markers

    assert markers == [CueRawMarker(time=0, text='comfort - ambeat', performer=None, title='comfort - ambeat', index_num=1, orig_index='00:00:00', file='/Users/mark/Music/Ableton/ambeat Project/comfort - ambeat.mp3', file_type='WAVE'), CueRawMarker(time=11, text='comfort - more than a memory', performer=None, title='comfort - more than a memory', index_num=1, orig_index='00:00:11', file='/Users/mark/Music/Ableton/dan shay Project/comfort - more than a memory.mp3', file_type='WAVE')]

def test_cue_standard():
    fname = f'{TESTS_DIR_CUE}/djdementia.cue'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f)
        proj.parse()
        markers = proj.markers

    assert markers == [CueRawMarker(time=0, text='Love and Rockets - So Alive', performer='Love and Rockets', title='So Alive', index_num=1, orig_index='00:00:00', file=None, file_type=None), CueRawMarker(time=243, text='Nitzer Ebb - Join In The Chant', performer='Nitzer Ebb', title='Join In The Chant', index_num=1, orig_index='04:03:19', file=None, file_type=None), CueRawMarker(time=592, text='Sisters of Mercy - Dominion Mother Russia', performer='Sisters of Mercy', title='Dominion Mother Russia', index_num=1, orig_index='09:52:70', file=None, file_type=None), CueRawMarker(time=980, text="Information Society - What's On Your Mind (Pure Energy)", performer='Information Society', title="What's On Your Mind (Pure Energy)", index_num=1, orig_index='16:20:21', file=None, file_type=None), CueRawMarker(time=1217, text='Nine Inch Nails - Down In It Singe', performer='Nine Inch Nails', title='Down In It Singe', index_num=1, orig_index='20:17:07', file=None, file_type=None), CueRawMarker(time=1635, text='Iggy Pop - Lust For Life', performer='Iggy Pop', title='Lust For Life', index_num=1, orig_index='27:15:23', file=None, file_type=None), CueRawMarker(time=1930, text='Talking Heads - Psycho Killer', performer='Talking Heads', title='Psycho Killer', index_num=1, orig_index='32:10:67', file=None, file_type=None), CueRawMarker(time=2176, text='Arnaud Rebotini - Pagan Dance Move', performer='Arnaud Rebotini', title='Pagan Dance Move', index_num=1, orig_index='36:16:07', file=None, file_type=None), CueRawMarker(time=2591, text='3TEETH - Pearls 2 Swine (Mr. Skeleton Remix)', performer='3TEETH', title='Pearls 2 Swine (Mr. Skeleton Remix)', index_num=1, orig_index='43:11:58', file=None, file_type=None), CueRawMarker(time=2829, text='Front Line Assembly - Circuitry', performer='Front Line Assembly', title='Circuitry', index_num=1, orig_index='47:09:61', file=None, file_type=None), CueRawMarker(time=3159, text='The Cramps - Bikini Girls with Machine Guns', performer='The Cramps', title='Bikini Girls with Machine Guns', index_num=1, orig_index='52:39:14', file=None, file_type=None), CueRawMarker(time=3342, text="DAF - Als War's Das Letzte Mal", performer='DAF', title="Als War's Das Letzte Mal", index_num=1, orig_index='55:42:41', file=None, file_type=None), CueRawMarker(time=3535, text='Fad Gadget - Collapsing New People', performer='Fad Gadget', title='Collapsing New People', index_num=1, orig_index='58:55:07', file=None, file_type=None), CueRawMarker(time=3777, text='Louisahhh - Feral Rhythm', performer='Louisahhh', title='Feral Rhythm', index_num=1, orig_index='62:57:69', file=None, file_type=None), CueRawMarker(time=4000, text='Radical G, The Horrorist - Here Comes The Storm Kobosil 44 Terror Mix', performer='Radical G, The Horrorist', title='Here Comes The Storm Kobosil 44 Terror Mix', index_num=1, orig_index='66:40:33', file=None, file_type=None), CueRawMarker(time=4300, text='Tones on Tail - Go!', performer='Tones on Tail', title='Go!', index_num=1, orig_index='71:40:73', file=None, file_type=None), CueRawMarker(time=4549, text='Ministry - We Believe', performer='Ministry', title='We Believe', index_num=1, orig_index='75:49:25', file=None, file_type=None), CueRawMarker(time=4675, text='VoX LoW - Something Is Wrong', performer='VoX LoW', title='Something Is Wrong', index_num=1, orig_index='77:55:03', file=None, file_type=None), CueRawMarker(time=4994, text='Lydia Lunch - Spooky', performer='Lydia Lunch', title='Spooky', index_num=1, orig_index='83:14:52', file=None, file_type=None), CueRawMarker(time=5138, text='Peter Murphy - All Night Long', performer='Peter Murphy', title='All Night Long', index_num=1, orig_index='85:38:64', file=None, file_type=None), CueRawMarker(time=5464, text='Killing Joke - Love Like Blood', performer='Killing Joke', title='Love Like Blood', index_num=1, orig_index='91:04:30', file=None, file_type=None), CueRawMarker(time=5763, text='The Cramps - Strychnine', performer='The Cramps', title='Strychnine', index_num=1, orig_index='96:03:19', file=None, file_type=None), CueRawMarker(time=5899, text='The Normal - Warm Leatherette', performer='The Normal', title='Warm Leatherette', index_num=1, orig_index='98:19:32', file=None, file_type=None)]

def test_cue_emit():
    fname = f'{TESTS_DIR_CUE}/Placebo.cue'
    correct = f'{TESTS_DIR_CUE}/Placebo.emit.cue'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f)
    proj.parse()

    assert proj.emit() == open(correct).read()

def test_cue_emit2():
    fname = f'{TESTS_DIR_CUE}/comfort_mini.cue'
    correct = f'{TESTS_DIR_CUE}/comfort_mini.emit.cue'
    with open(fname, 'rb') as f:
        proj = load_project(fname, f)
    proj.parse()

    assert proj.emit() == open(correct).read()

def test_cue_track_parsing():
    c = CueFile('f', BytesIO())

    # performer track
    # only performer
    # only track
    # only file
    # no index

    chunks = []

    chunks.append('''
    PERFORMER "a"
    TITLE "t"
    FILE "a/b"
    INDEX 01 00:00:01
    ''')

    chunks.append('''
    PERFORMER "a"
    TITLE "t"
    FILE "a/b"
    ''')

    chunks.append('''
    PERFORMER "a"
    FILE "a/b"
    INDEX 01 00:00:01
    ''')

    chunks.append('''
    TITLE "t"
    FILE "a/b"
    INDEX 01 00:00:01
    ''')

    chunks.append('''
    FILE "a/b"
    INDEX 01 00:00:01
    ''')

    chunks.append('''
    INDEX 01 00:00:01
    ''')

    chunks.append('''
    ''')


    x = [c._parse_chunk(x) for x in chunks]
    assert x == [CueRawMarker(time=0, text='a - t', performer='a', title='t', index_num=1, orig_index='00:00:01', file='a/b', file_type=''), CueRawMarker(time=0, text='a - t', performer='a', title='t', index_num=None, orig_index=None, file='a/b', file_type=''), CueRawMarker(time=0, text='a', performer='a', title=None, index_num=1, orig_index='00:00:01', file='a/b', file_type=''), CueRawMarker(time=0, text='t', performer=None, title='t', index_num=1, orig_index='00:00:01', file='a/b', file_type=''), CueRawMarker(time=0, text='b', performer=None, title=None, index_num=1, orig_index='00:00:01', file='a/b', file_type=''), CueRawMarker(time=0, text='Unknown', performer=None, title=None, index_num=1, orig_index='00:00:01', file=None, file_type=None), CueRawMarker(time=0, text='Unknown', performer=None, title=None, index_num=None, orig_index=None, file=None, file_type=None)]

    chunk = '''
    INDEX 01 00:01
    '''
    with pytest.raises(ValueError):
        c._parse_chunk(chunk)


def test_parse_index_rb():
    assert CueFile._parse_index_rekordbox('01:01:01') == 3661

def test_parse_index_std():
    assert CueFile._parse_index_std('01:01:01') == 61
