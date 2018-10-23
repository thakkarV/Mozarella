import os
import random
import fnmatch
import midi

def find_files(datadir="./data/", pattern="*.mid"):
    '''Recursively finds all files matching the pattern.'''
    files = []
    for root, _, filenames in os.walk(datadir):
        for filename in fnmatch.filter(filenames, pattern):
            files.append(str(os.path.join(root, filename)))
    return files


def tick_delta_to_ms(delta_ticks, tempo, ppqn):
	'''converts a range of midi ticks into a range of milliseconds'''
	return (((tempo * delta_ticks) / ppqn)/1000)

def ms_to_tick_delta(ms, tempo, ppqn):
	'''converts a range of midi ticks into a range of milliseconds'''
	return ((ms*1000)*ppqn)/tempo

def ms_per_tick(tempo, ppqn):
	'''takes in the tempo and the resolution and outputs the number of microseconds per tick'''
	return ((tempo/ppqn)/1000)

def ticks_per_ms(tempo, ppqn):
    return 1/ms_per_tick(tempo,ppqn)

def ensure_format0(datadir="./data/"):
    files = find_files(datadir)
    for midifile in files:
        mididump = midi.read_midifile(midifile)
        if len(mididump) > 1:
            print(midifile)
