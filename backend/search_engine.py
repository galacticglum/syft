import re
import uuid
import string
import argparse
import tempfile
from enum import Enum
from pathlib import Path
from datetime import timedelta

import librosa
import soundfile

import nltk
import nltk.tokenize
import api.hash_util as hash_util
from google.cloud import speech_v1p1beta1 as speech, storage
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types

class SearchOutputMode(Enum):
    EXACT_MATCH = 'exact_match'
    SENTENCE = 'sentence'

parser = argparse.ArgumentParser(description='The core search engine.')
parser.add_argument('input', type=str, help='The path to the input audio file.')
parser.add_argument('query', type=str, help='The search query.')
parser.add_argument('--search-output-mode', help='The mode in which the search matches should be outputted.', type=SearchOutputMode, choices=list(SearchOutputMode), default=SearchOutputMode.EXACT_MATCH)
parser.add_argument('--auth', dest='auth_json_filepath', type=str, help='The path to the service account credentials file.')

args = parser.parse_args()
args.query = args.query.strip().lower()

speech_client = speech.SpeechClient.from_service_account_json(args.auth_json_filepath)
storage_client = storage.Client.from_service_account_json(args.auth_json_filepath)

BUCKET_NAME = 'syft-audio-bucket'
BUCKET_AUDIO_ROOT = ''
# empty, directory, directory/
bucket = storage_client.get_bucket(BUCKET_NAME)

# Download the NLTK model (which should probably only do this once, on startup)
nltk.download('punkt')

def normalize_text(text):
    '''
    Normalizes text to make it searchable. Removes any leading/trailing whitespace,
    converts to lowercase, and removes any punctuation.
    '''
    return text.translate(str.maketrans('', '', string.punctuation)).strip().lower()

def find_sub_list(source, sublist):
    results = []
    len_sublist = len(sublist)
    for index in (i for i, e in enumerate(source) if e == sublist[0]):
        if source[index:index + len_sublist] == sublist:
            results.append((index, index + len_sublist - 1))

    return results

try:
    audio, sample_rate = librosa.load(args.input)
except Exception as exception:
    print('Failed to load audio file ({})'.format(args.input), exception)
    exit(1)

tmp_filepath = Path(tempfile.gettempdir()) / str(uuid.uuid4())

# Preprocess the audio data by converting it to a mono WAVE
audio_mono = librosa.to_mono(audio)
soundfile.write(tmp_filepath, audio_mono, sample_rate, subtype='PCM_16', format='wav')

# Upload the file to GCS if it doesn't already exists
blob_root = BUCKET_AUDIO_ROOT
if blob_root and not BUCKET_AUDIO_ROOT.endswith('/'):
    blob_root = BUCKET_AUDIO_ROOT + '/'

with open(tmp_filepath, 'rb') as audio_file:
    blob_filename = '{}{}'.format(blob_root, hash_util.get_crc32_str(audio_file)) 
    blob = bucket.blob(blob_filename)
    if not blob.exists():
        blob.upload_from_file(audio_file, rewind=True)

    blob_uri = 'gs://{}/{}'.format(BUCKET_NAME, blob_filename)

# Remove audio file now that we are done with it
tmp_filepath.unlink()

config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=sample_rate,
    enable_speaker_diarization=True,
    enable_automatic_punctuation=True,
    language_code='en-US')

operation = speech_client.long_running_recognize(config, types.RecognitionAudio(uri=blob_uri))
op_result = operation.result()
for result in op_result.results:
    # Check if the response is valid, which happens if and only if the result alternatives
    # is at least of length 1 AND the transcript is non-empty.
    if len(result.alternatives) == 0 or not result.alternatives[0].transcript: continue    
    sentences = [sentence.strip().lower() for sentence in nltk.tokenize.sent_tokenize(result.alternatives[0].transcript)]
    tokens = [word.strip().lower() for word in result.alternatives[0].transcript.split(' ') if word != '']

    for sentence in sentences:
        sublist_bounds = find_sub_list(tokens, sentence.split(' '))[0]
        sentence_word_infos = result.alternatives[0].words[sublist_bounds[0]:sublist_bounds[1]+1]

        matches = re.finditer(args.query, sentence)      
        match_results = set()
        for match in matches:
            if args.search_output_mode == SearchOutputMode.EXACT_MATCH:
                start_boundary = i = match.start()
                
                # Check if the match starts inside a word
                if i != 0 and sentence[i - 1] != ' ':
                    start_boundary = sentence.rfind(' ', 0, i) + 1

                end_boundary = j = match.end() - 1

                # Check if the match ends inside a word
                if j != len(sentence) - 1 and sentence[j + 1] != ' ':
                    end_boundary = sentence.find(' ', j)
                    if end_boundary == -1:
                        end_boundary = len(sentence) - 1
                    else:
                        end_boundary -= 1

                # Add boundary
                boundary = (start_boundary, end_boundary)
                if boundary in match_results: continue
                match_results.add(boundary)

                start_word = sentence_word_infos[sentence.count(' ', 0, start_boundary)]
                end_word = sentence_word_infos[sentence.count(' ', 0, end_boundary)]
            elif args.search_output_mode == SearchOutputMode.SENTENCE:
                start_word = sentence_word_infos[0]
                end_word = sentence_word_infos[-1]

            print('Found match (query=\'{}\') at {}:{} to {}:{}.'.format(args.query,
                start_word.start_time.seconds, start_word.start_time.nanos, \
                end_word.end_time.seconds, end_word.end_time.nanos))