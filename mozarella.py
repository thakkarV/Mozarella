import midi
import numpy as np
import os
import random
import fnmatch
from fryer import find_files, tick_delta_to_ms, ms_to_tick_delta

# DO NOT CHANGE
MIN_NOTE_IDX = 21
MAX_NOTE_IDX = 108
DEFAULT_VELOCITY = 100
# embd len is number of notes in embd + milliseconds scalar
EMBEDDING_LENGTH = MAX_NOTE_IDX-MIN_NOTE_IDX+1

# this is what the students will be using
def midi_embedding_generator(datadir="./data/"):
    '''Yields a list of embedding lists each time it is called from the
        input path to the midi corpus'''
    files = find_files(datadir)
    if files is None:
        raise RuntimeError("Invalid path to midi corpus.")
    random.shuffle(files)
    for midifile in files:
        yield generate_embeddings_from_midi(midifile)


def midi_event_generator(datadir="./data/"):
    '''Yields a touple of midi resolution and raw list of midi events
        each time it is called instead of embeddings'''
    files = find_files(datadir)
    random.shuffle(files)
    for midifile in files:
        yield generate_events(midifile)


def generate_events(midifile):
    '''Retruns a touple of midi resolution and raw list of midi events
        for the input midi file'''
    midi_dump = midi.read_midifile(midifile)
    return midi_dump.resolution, midi_dump[0]


def generate_embeddings_from_midi(midifile):
    '''Returns a list of all embedding lists for the input path to a
        format 0 midi file. Other midi formats not supported'''
    midi_dump = midi.read_midifile(midifile)

    # only format 0 supported
    if len(midi_dump) != 1:
        raise RuntimeError("Only format 0 midi files are supported.")

    midi_track = midi_dump[0]
    ppqn = midi_dump.resolution
    tempo = 500000
    ticks = int(0)
    # embeddigns for the midi
    # format is a one hot encoded vector of notes
    # last element is the duraiton of the note in milliseconds
    embeddings = []

    # bookkeeping for which notes are being played currently
    note_state = []
    for event_idx in range(len(midi_track)):
        curr_event = midi_track[event_idx]
        delta_ticks = curr_event.tick
        event_name = curr_event.name
        event_data = curr_event.data
        ticks += delta_ticks
        if event_name is midi.NoteOnEvent.name and delta_ticks == 0:
            note_state.append(event_data[0])

        elif event_name is midi.NoteOnEvent.name and delta_ticks != 0:
            embeddings.append(embed_note(note_state, delta_ticks, tempo, ppqn))
            note_state.append(event_data[0])

        elif event_name is midi.NoteOffEvent.name and delta_ticks == 0:
            if event_data[0] in note_state:
                note_state.remove(event_data[0])

        elif event_name is midi.NoteOffEvent.name and delta_ticks != 0:
            embeddings.append(embed_note(note_state, delta_ticks, tempo, ppqn))
            if event_data[0] in note_state:
                note_state.remove(event_data[0])

        elif event_name is midi.SetTempoEvent.name and delta_ticks == 0:
            # mid-song tempo change
            # tempo is represented in microseconds per beat as tt tt tt - 24-bit (3-byte) hex
            # convert first to binary string and then to a decimal number (microsec/beat)
            tempo_binary = (format(curr_event.data[0], '08b') +
                            format(curr_event.data[1], '08b') +
                            format(curr_event.data[2], '08b'))
            tempo = int(tempo_binary, 2)

        elif event_name is midi.SetTempoEvent.name and delta_ticks != 0:
            embeddings.append(embed_note(note_state, delta_ticks, tempo, ppqn))
            tempo_binary = (format(curr_event.data[0], '08b') +
                            format(curr_event.data[1], '08b') +
                            format(curr_event.data[2], '08b'))
            tempo = int(tempo_binary, 2)

        elif event_name is midi.EndOfTrackEvent.name:
            break
        elif event_name is midi.TimeSignatureEvent.name:
            # lets not worry about non-4 time signatures
            if curr_event.numerator not in (2, 4):
                break
        else:
            continue
    return embeddings


def embed_note(note_state, delta_ticks, tempo, ppqn):
    '''Returns a single embedding list for one input note.'''
    ms = tick_delta_to_ms(delta_ticks, tempo, ppqn)
    embd = [0 for x in range(EMBEDDING_LENGTH)]

    # if there are any notes playing, add the top note to the list
    if len(note_state) != 0:
        top_note = max(note_state)
        if (top_note >= MIN_NOTE_IDX) and (top_note < MAX_NOTE_IDX):
            embd[top_note-MIN_NOTE_IDX] = 1
    embd[-1] = ms
    return embd


def generate_midi_from_embeddings(embeddings, tempo=1000000, ppqn=960, path="./out.mid"):
    '''Writes a midi file to disk based on input embeddings'''
    track = midi.Track()

    default_tempo_event = midi.SetTempoEvent()
    default_tempo_event.set_mpqn(tempo)
    track.append(default_tempo_event)

    # each embedding is a note
    carry_ticks = 0
    for embd in embeddings:
        # each note has a start and an end
        note_on = midi.NoteOnEvent()
        note_off = midi.NoteOffEvent()

        if len(embd) == MAX_NOTE_IDX-MIN_NOTE_IDX:
            # no note duration info in embedding
            ticks = int(ppqn/2)
        elif len(embd) == MAX_NOTE_IDX-MIN_NOTE_IDX+1:
            # duration of note availble so we set ticks accordingly
            ticks = int(ms_to_tick_delta(embd[-1], tempo, ppqn))
            del embd[-1]
        else:
            raise RuntimeError(
                "Invalid length of embedding for midi generation.")

        note_idx = [i for i, elem in enumerate(embd) if elem != 0]
        print(note_idx)

        # at most one note playing at a time
        # if one, then within range
        assert len(note_idx) == 1 or len(note_idx) == 0
        if len(note_idx) == 1:
            assert note_idx[0] < MAX_NOTE_IDX-MIN_NOTE_IDX
            actual_note = note_idx[0]+MIN_NOTE_IDX

            # set beginning of note
            note_on.set_pitch(actual_note)
            note_on.set_velocity(DEFAULT_VELOCITY)
            note_on.tick = 0+carry_ticks

            # set end of note
            note_off.set_pitch(actual_note)
            note_off.set_velocity(DEFAULT_VELOCITY)
            note_off.tick = ticks

            # add the start and end of the note to the track
            track.append(note_on)
            track.append(note_off)
            carry_ticks = 0

        # silence for this iteration; take care of it by carrying ticks forward
        else:
            carry_ticks = ticks

    # end of track
    end_event = midi.EndOfTrackEvent()
    end_event.tick = carry_ticks
    track.append(end_event)

    # write pattern to file
    pattern = midi.Pattern(resolution=ppqn, tick_relative=True)
    pattern.append(track)
    midi.write_midifile(path, pattern)
    print("Wrote midi file at the path {} with {} notes.".format(path, len(track)))
    print("You can use either GarageBand on MacOS or timidity on linux to convert it to a .wav file.")
