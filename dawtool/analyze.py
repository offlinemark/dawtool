# TODO: rename this file. We are not exactly doing analysis here.

import os.path

from .project import load_project

def extract_markers(filename, stream, *args, **kwargs):
    """
    Try to analyze a filename as one of the accepted project file types
    and extract marker information. This is just a convenience helper.
    
    raises FileNotFoundError
    raises ValueError

    return: list of Marker sorted based on the Marker.time
    """
    proj = load_project(filename, stream, *args, **kwargs)
    proj.parse()
    # print(proj)
    from pprint import pprint 
    # print(pprint(proj.tempo_automation_events))
    # proj.dump()
    return proj.markers

def export_tempo_map(filename, stream, midi_filename, *args, **kwargs):
    """
    
    raises FileNotFoundError
    raises ValueError

    return: list of Marker sorted based on the Marker.time
    """
    proj = load_project(filename, stream, *args, **kwargs)
    proj.parse()
    return proj.tempo_map
