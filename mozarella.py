import midi
import numpy as np
import os
import random
import fnmatch
from frypan import *

# DO NOT CHANGE
min_note_idx=24
max_note_idx=102

# stick len is number of notes in stick + milliseconds scalar
stick_len=max_note_idx-min_note_idx+1



def midi_event_generator(datadir="./data/"):
    files = find_files(datadir)
    for midifile in random.shuffle(files):
        yield generate_events(midifile)

def fry(datadir="./data/"):
    files = find_files(datadir)
    assert files is not None
    random.shuffle(files)
    for midifile in files:
        print("yielding file {}".format(midifile))
        yield generate_sticks(midifile)


def midi_emedding_generator(datadir="./data/"):
    files = find_files(datadir)
    assert files is not None 
    random.shuffle(files)
    for midifile in files:
        print("yielding file {}".format(midifile))
        yield generate_sticks(midifile)


def generate_events(midifile):
    midi_dump = midi.read_midifile(midifile)
    return midi_dump.resolution, midi_dump[1]


def generate_sticks(midifile):
    print("generating sticks for file {}".format(midifile))
    midi_dump = midi.read_midifile(midifile)
    midi_track = midi_dump[0]
    ppqn = midi_dump.resolution
    tempo = 500000
    ticks = int(0)
    # embeddigns for the midi
    # format is a one hot encoded vector of notes
    # last element is the duraiton of the note in milliseconds
    sticks = []

    # bookkeeping for which notes are being played currently
    note_state = []
    for event_idx in range(len(midi_track)):
        curr_event = midi_track[event_idx]
        delta_ticks = curr_event.tick
        event_name = curr_event.name
        event_data = curr_event.data
        ticks += delta_ticks
        if   event_name is midi.NoteOnEvent.name  and delta_ticks == 0:
            note_state.append(event_data[0])
        
        elif event_name is midi.NoteOnEvent.name  and delta_ticks != 0:
            sticks.append(generate_stick(note_state, delta_ticks, tempo, ppqn))            
            note_state.append(event_data[0])
            
        elif event_name is midi.NoteOffEvent.name and delta_ticks == 0:
            if event_data[0] in note_state:
                note_state.remove(event_data[0])
            
        elif event_name is midi.NoteOffEvent.name and delta_ticks != 0:
            sticks.append(generate_stick(note_state, delta_ticks, tempo, ppqn))
            if event_data[0] in note_state:
                note_state.remove(event_data[0])
        
        elif event_name is midi.SetTempoEvent.name and delta_ticks == 0:
            # mid-song tempo change
            # tempo is represented in microseconds per beat as tt tt tt - 24-bit (3-byte) hex
            # convert first to binary string and then to a decimal number (microsec/beat)
            tempo_binary = (format(curr_event.data[0], '08b')+
                            format(curr_event.data[1], '08b')+
                            format(curr_event.data[2], '08b'))
            tempo = int(tempo_binary, 2)
            
        elif event_name is midi.SetTempoEvent.name and delta_ticks != 0:
            sticks.append(generate_stick(note_state, delta_ticks, tempo, ppqn))
            tempo_binary = (format(curr_event.data[0], '08b')+
                            format(curr_event.data[1], '08b')+
                            format(curr_event.data[2], '08b'))
            tempo = int(tempo_binary, 2)

        elif event_name is midi.EndOfTrackEvent.name:
            break
        elif event_name is midi.TimeSignatureEvent.name:
            # lets not worry about non-4 time signatures
            if curr_event.numerator not in (2,4):
                break
        else:
            continue
    return sticks

def generate_stick(note_state, delta_ticks, tempo, ppqn):
    ms = tick_delta_to_ms(delta_ticks, tempo, ppqn)
    stick = [0 for x in range(stick_len)]
    
    # if there are any notes playing, add the top note to the list
    if len(note_state) != 0:
        if (max(note_state) < max_note_idx):
            stick[-min_note_idx] = 1
    stick[-1] = ms
    return stick
