'''
Defines the search-related API routes.

'''

import re
import uuid
import string
import base64
import argparse
import tempfile
from enum import Enum
from pathlib import Path
from datetime import timedelta

import librosa
import soundfile

import nltk.tokenize
import api.hash_util as hash_util
from google.cloud import speech_v1p1beta1 as speech, storage
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types

import api.http_errors as exceptions
from flask import Blueprint, jsonify, request, current_app
from api.validator import get_validator_data, validate_route, Schema, validators, fields

bp = Blueprint('search', __name__, url_prefix='/api/search')

class SearchOutputMode(Enum):
    '''
    The match mode of the search query.

    '''
    
    EXACT_MATCH = 'exact_match'
    SENTENCE = 'sentence'

def get_tmp_filepath(): return Path(tempfile.gettempdir()) / str(uuid.uuid4())
def get_word_time_seconds(time): return time.seconds + time.nanos / 1e9

def normalize_text(text):
    '''
    Normalizes text to make it searchable. Removes any leading/trailing whitespace,
    converts to lowercase, and removes any punctuation.
    '''
    return text.translate(str.maketrans('', '', string.punctuation)).strip().lower()

def find_sub_list(source, sublist):
    '''
    Determines the bounding indices of a sublist.

    '''
    
    results = []
    len_sublist = len(sublist)
    for index in (i for i, e in enumerate(source) if e == sublist[0]):
        if source[index:index + len_sublist] == sublist:
            results.append((index, index + len_sublist - 1))

    return results

class QuerySchema(Schema):
    file_input = fields.StringField(validators=[validators.DataRequired()])
    query = fields.StringField(validators=[validators.DataRequired()])
    search_output_mode = fields.EnumField(SearchOutputMode, default_value=SearchOutputMode.EXACT_MATCH)

@bp.route('/', methods=['POST'])
@validate_route(QuerySchema)
def query():
    data = get_validator_data()
    query_text = data['query'].strip().lower()
    search_output_mode = data['search_output_mode']
    
    auth_filepath = Path(current_app.instance_path) / Path(current_app.config['GOOGLE_CLOUD_AUTH_FILENAME'])
    speech_client = speech.SpeechClient.from_service_account_json(auth_filepath)
    storage_client = storage.Client.from_service_account_json(auth_filepath)

    bucket = storage_client.get_bucket(current_app.config['GOOGLE_CLOUD_STORAGE_BUCKET_NAME'])

    with open(get_tmp_filepath(), 'w+b') as input_file:
        data['file_input'] = data['file_input'][data['file_input'].find(',')+1:]
        file_input = data['file_input'] + '=' * ((4 - len(data['file_input']) % 4) % 4) #ugh
        input_file.write(base64.b64decode(file_input))
    
    try:
        audio, sample_rate = librosa.load(input_file.name)
    except Exception as exception:
        raise exceptions.AudioFileLoadError('file_input', exception)

    tmp_filepath = get_tmp_filepath()

    # Preprocess the audio data by converting it to a mono WAVE
    audio_mono = librosa.to_mono(audio)
    soundfile.write(tmp_filepath, audio_mono, sample_rate, subtype='PCM_16', format='wav')

    # Upload the file to GCS if it doesn't already exists
    bucket_audio_root = current_app.config['GOOGLE_CLOUD_STORAGE_BUCKET_AUDIO_ROOT']
    blob_root = bucket_audio_root
    if blob_root and not bucket_audio_root.endswith('/'):
        blob_root = bucket_audio_root + '/'

    with open(tmp_filepath, 'rb') as audio_file:
        blob_filename = '{}{}'.format(blob_root, hash_util.get_crc32_str(audio_file)) 
        blob = bucket.blob(blob_filename)
        if not blob.exists():
            blob.upload_from_file(audio_file, rewind=True)

        blob_uri = 'gs://{}/{}'.format(current_app.config['GOOGLE_CLOUD_STORAGE_BUCKET_NAME'], blob_filename)

    # Remove audio file now that we are done with it
    tmp_filepath.unlink()
    Path(input_file.name).unlink()

    # This configuration is predetermined...All audio files are converted 
    # a WAVE format with 16-bit PCM encoding. Sample rate is determined using librosa.
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        # sample_rate_hertz=sample_rate,
        enable_speaker_diarization=True,
        enable_automatic_punctuation=True,
        language_code='en-US')

    operation = speech_client.long_running_recognize(config, types.RecognitionAudio(uri=blob_uri))
    op_result = operation.result()
    match_results = []
    for result in op_result.results:
        # Check if the response is valid, which happens if and only if the result alternatives
        # is at least of length 1 AND the transcript is non-empty.
        if len(result.alternatives) == 0 or not result.alternatives[0].transcript: continue    
        sentences = [sentence.strip().lower() for sentence in nltk.tokenize.sent_tokenize(result.alternatives[0].transcript)]
        tokens = [word.strip().lower() for word in result.alternatives[0].transcript.split(' ') if word != '']
        for sentence in sentences:
            sublist_bounds = find_sub_list(tokens, sentence.split(' '))[0]
            sentence_word_infos = result.alternatives[0].words[sublist_bounds[0]:sublist_bounds[1]+1]

            matches = re.finditer(query_text, sentence)      
            match_cache = set()
            for match in matches:
                if search_output_mode == SearchOutputMode.EXACT_MATCH:
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
                    if boundary in match_cache: continue
                    match_cache.add(boundary)

                    start_word_index = sentence.count(' ', 0, start_boundary)
                    end_word_index = sentence.count(' ', 0, end_boundary)
                elif search_output_mode == SearchOutputMode.SENTENCE:
                    start_word_index = 0
                    end_word_index = len(sentence_word_infos) - 1

                confidence = result.alternatives[0].confidence
                start_word = sentence_word_infos[start_word_index]
                end_word = sentence_word_infos[end_word_index]
                match_results.append({
                    'start_time': get_word_time_seconds(start_word.start_time),
                    'end_time': get_word_time_seconds(end_word.end_time),
                    'confidence': confidence
                })

    access_link = blob.generate_signed_url(timedelta(hours=1))
    return jsonify(status_code=201, message='Query was successful!', matches=match_results, access_link=access_link, success=True)