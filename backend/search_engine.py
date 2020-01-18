import re
import string
import argparse
from enum import Enum
from pathlib import Path
from datetime import timedelta

import nltk
import nltk.tokenize
import api.hash_util as hash_util
from google.cloud import speech_v1p1beta1 as speech, storage
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types

class SearchMode(Enum):
    WORD = 'word'
    STRING = 'string'
    SENTENCE = 'sentence'
    FRAGMENT = 'fragment'

parser = argparse.ArgumentParser(description='The core search engine.')
parser.add_argument('input', type=str, help='The path to the input audio file.')
parser.add_argument('query', type=str, help='The search query.')
parser.add_argument('--search-mode', type=SearchMode, choices=list(SearchMode))
parser.add_argument('--regex', dest='regex', help='Enable regular expression pattern matching.', action='store_true')
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

with open(Path(args.input), 'rb') as audio_file:
    # Upload the file to GCS if it doesn't already exists
    blob_root = BUCKET_AUDIO_ROOT
    if blob_root and not BUCKET_AUDIO_ROOT.endswith('/'):
        blob_root = BUCKET_AUDIO_ROOT + '/'
    
    blob_filename = '{}{}'.format(blob_root, hash_util.get_crc32_str(audio_file)) 
    blob = bucket.blob(blob_filename)
    if not blob.exists():
        blob.upload_from_file(audio_file, rewind=True)

    blob_uri = 'gs://{}/{}'.format(BUCKET_NAME, blob_filename)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
        sample_rate_hertz=16000,
        enable_speaker_diarization=True,
        enable_automatic_punctuation=True,
        language_code='en-US')

    operation = speech_client.long_running_recognize(config, types.RecognitionAudio(uri=blob_uri))
    op_result = operation.result()
    for result in op_result.results:
        # Check if the response is valid, which happens if and only if the result alternatives
        # is at least of length 1 AND the transcript is non-empty.
        if len(result.alternatives) == 0 or not result.alternatives[0].transcript: continue
        print('='*20)
        # print(result.alternatives[0].transcript)
        
        if args.search_mode == SearchMode.WORD:
            for word_info in result.alternatives[0].words:
                # Remove punctuation from word
                raw_word = normalize_text(word_info.word)
                matched = re.search(args.query, raw_word) if args.regex else raw_word == args.query
                if matched:
                    print('Found match (query=\'{}\') at {}:{} to {}:{}.'.format(args.query, \
                        word_info.start_time.seconds, word_info.start_time.nanos, \
                        word_info.end_time.seconds, word_info.end_time.nanos))
        elif args.search_mode == SearchMode.STRING:
            sentences = [sentence.strip().lower() for sentence in nltk.tokenize.sent_tokenize(result.alternatives[0].transcript)]
            print(sentences)
            for sentence in sentences:
                matches = re.findall(args.query, sentence)
                for match in matches:
                    # print(sentence)
                    print('Found match (query=\'{}\').'.format(args.query))

        # print(result.alternatives[0].confidence)