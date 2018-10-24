# Mozarella:

A midi corpus reader and embedding generator for EC500 Deep Learnign Class Homeworks

## Usage
### Installing
You will need `python-midi` python module for reading and writing midi files.

The module is publically available here: https://github.com/vishnubob/python-midi

Make sure to install the python3 version by switching to the feature/python3 branch. You can also follow the following instructions for installation.

```bash
git clone https://github.com/vishnubob/python-midi.git
cd python-midi
git checkout feature/python3
python setup.py install
```

### Training
To generate embeddings to use as training data for LSTM
```python
# import embedding generator
from mozarella import midi_emedding_generator

# call the generator to get list of embeddings
for epoch_i in range(epoch_n):
    for embeddings in midi_emedding_generator("./path/to/corpus"):
        # now use the list to train
        train_on(embeddings)
```

`embeddings` is a list of lists. Each element list contains a one hot encoded representaion of the note being played as well as the duration of the note as the last element of the list. That way, only two elements of each embedding should be non-zero. You are free to turn this into a numpy ndarry however you deem fit for your training usage and batch sizes. Read section `Format of Embeddings` for the format of these embeddings.

Each `embeddings` list has all the embeddings for an entire song, which is on average on the order of 1000 for the songs in the given dataset. You may only want to use 32 or 64 of them at a time for each training iterations for example. The last element in each embedding vector is the duration of that note in milliseconds. You can choose to ignore this as well and only include it for the bonus assignment. In this case, you can treat all the notes as having the same duration during playback.

### Inference
To generate a .mid file for testing our the output of inference from your trianed network you can do the following:

```python
from mozarella import generate_midi_from_embeddings

# assuming you have a list of embeddings in the same format as the training embeddings
embeddings = sample_notes_from_lstm()
generate_midi_from_embeddings(embeddings, "/path/to/output/file.mid")
```

Here the embeddings must have the same format as the training data embeddings, but you can choose to omit the duration of the notes (i.e. each element of the `embeddings` list should be a list of length 88 or 89).

You can play the generated midi file by using GarageBand on MacOS or [timidity](https://www.systutorials.com/docs/linux/man/1-timidity/) on linux. You can also you an online midi visualizer and player such as https://onlinesequencer.net/ for convenience.


## Format of Embeddings
Each call to midi_emedding_generator yields a list of lists of embeddings.

Say we do the follwoing
```for embeddings in midi_emedding_generator("./path/to/corpus"):```
then `len(embeddings)` is the total number of embeddings for this song. All the embeddings are in chronological order of the notes in the song. 

Each element in this list is also a list that contains the embedding of the current note being played in one-hot format with the last element representing the duration of that note in milliseconds. Since we are assuming all notes are piano notes the length of each individual embedding is therefore 89. First 88 elments one-hot encode the note and the last 89th element contains duration.
