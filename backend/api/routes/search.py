'''
Defines the search-related API routes.

'''

import re
import uuid
import time
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
from api.extensions import cache, get_context_search_model
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
    is_context_search = fields.BooleanField(default_value=False)

class MatchCacheKey:
    def __init__(self, blob_uri, query_text, is_context_search):
        self.blob_uri = blob_uri
        self.query_text = query_text
        self.is_context_search = is_context_search

    @property
    def key(self):
        return (self.blob_uri, self.query_text, self.is_context_search)

    def __hash__(self):
        return self.key.__hash__()

def string_query(query_text, blob_uri, op_result, search_output_mode=SearchOutputMode.EXACT_MATCH):
    match_result_cache = cache.get('match_result_cache') or dict()
    match_cache_key = MatchCacheKey(blob_uri, query_text, False)
    if match_cache_key in match_result_cache: return match_result_cache[match_cache_key]
    
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
                    'matched_query': transcript,
                    'start_time': get_word_time_seconds(start_word.start_time),
                    'end_time': get_word_time_seconds(end_word.end_time),
                    'confidence': confidence,
                    'transcript': sentence[match.start():match.end()] 
                })

    match_result_cache[match_cache_key] = match_results
    cache.set('match_result_cache', match_result_cache)

    return match_results

def context_query(query_text, blob_uri, op_result, search_output_mode=SearchOutputMode.EXACT_MATCH):
    match_result_cache = cache.get('match_result_cache') or dict()
    match_cache_key = MatchCacheKey(blob_uri, query_text, True)
    if match_cache_key in match_result_cache: return match_result_cache[match_cache_key]
    
    match_results = []
    for result in op_result.results:
        # Check if the response is valid, which happens if and only if the result alternatives
        # is at least of length 1 AND the transcript is non-empty.
        if len(result.alternatives) == 0 or not result.alternatives[0].transcript: continue    
        tokens = [word.strip().lower() for word in result.alternatives[0].transcript.split(' ') if word != '']
        puncutation_translator = str.maketrans('', '', string.punctuation)
        sanitized_tokens = [token.translate(puncutation_translator) for token in tokens]

        predictions = get_context_search_model().predict((result.alternatives[0].transcript, query_text))
        for prediction in predictions:
            answer = prediction[0].strip()
            answer_tokens = answer.lower().translate(puncutation_translator).split(' ')

            if not answer: continue
            sublist = find_sub_list(sanitized_tokens, answer_tokens)

            if len(sublist) == 0: continue
            sublist_bounds = sublist[0]

            if search_output_mode == SearchOutputMode.EXACT_MATCH:
                start_word_index = sublist_bounds[0]
                end_word_index = sublist_bounds[1]
                transcript = answer
            elif search_output_mode == SearchOutputMode.SENTENCE:
                pass
        
            start_word = result.alternatives[0].words[start_word_index]
            end_word = result.alternatives[0].words[end_word_index]
            match_results.append({
                'matched_query': query_text,
                'start_time': get_word_time_seconds(start_word.start_time),
                'end_time': get_word_time_seconds(end_word.end_time),
                'confidence': prediction[2],
                'transcript': transcript 
            })

    match_result_cache[match_cache_key] = match_results
    cache.set('match_result_cache', match_result_cache)

    return match_results

@bp.route('/', methods=['POST'])
@validate_route(QuerySchema)
def query():
    route_start_time = start_time = time.time()
    print('='*20)

    data = get_validator_data()
    query_text = data['query'].strip().lower()
    search_output_mode = data['search_output_mode']
    
    auth_filepath = Path(current_app.instance_path) / Path(current_app.config['GOOGLE_CLOUD_AUTH_FILENAME'])
    speech_client = speech.SpeechClient.from_service_account_json(auth_filepath)
    storage_client = storage.Client.from_service_account_json(auth_filepath)

    bucket = storage_client.get_bucket(current_app.config['GOOGLE_CLOUD_STORAGE_BUCKET_NAME'])

    with open(get_tmp_filepath(), 'w+b') as input_file:
        data['file_input'] = data['file_input'][data['file_input'].find(',')+1:]
        file_input = data['file_input'] + '=' * ((4 - len(data['file_input']) % 4) % 4)
        input_file.write(base64.b64decode(file_input))
        input_hash = hash_util.get_md5_str(file_input)

        print('Decoding and writing input file took {:.3f} seconds'.format(time.time() - start_time)) 
        start_time = time.time()

    input_hash_to_blob_uri = cache.get('input_hash_to_blob_uri') or dict()
    if input_hash in input_hash_to_blob_uri:
        blob_uri = input_hash_to_blob_uri[input_hash]
        blob = bucket.blob(blob_uri.replace('gs://{}/'.format(current_app.config['GOOGLE_CLOUD_STORAGE_BUCKET_NAME']), ''))
    else:
        try:
            audio, sample_rate = librosa.load(input_file.name)
        except Exception as exception:
            raise exceptions.AudioFileLoadError('file_input', exception)

        print('Libroa audio file loading took {:.3f} seconds'.format(time.time() - start_time))
        start_time = time.time()

        tmp_filepath = get_tmp_filepath()

        # Preprocess the audio data by converting it to a mono WAVE
        audio_mono = librosa.to_mono(audio)
        soundfile.write(tmp_filepath, audio_mono, sample_rate, subtype='PCM_16', format='wav')

        print('Audio processing and exporting took {:.3f} seconds'.format(time.time() - start_time))
        start_time = time.time()

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
            input_hash_to_blob_uri[input_hash] = blob_uri
            cache.set('input_hash_to_blob_uri', input_hash_to_blob_uri)

        # Remove audio file now that we are done with it
        tmp_filepath.unlink()

        print('Uploading to GCS took {:.3f} seconds'.format(time.time() - start_time))
        start_time = time.time()

    Path(input_file.name).unlink()

    transcription_cache = cache.get('transcription_cache') or dict()
    if blob_uri in transcription_cache:
        op_result = transcription_cache[blob_uri]
        print('Loaded {} from cache'.format(blob_uri))
    else:
        # This configuration is predetermined...All audio files are converted 
        # a WAVE format with 16-bit PCM encoding. Sample rate is determined using librosa.
        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            enable_speaker_diarization=True,
            enable_automatic_punctuation=True,
            language_code='en-US')

        operation = speech_client.long_running_recognize(config, types.RecognitionAudio(uri=blob_uri))
        op_result = operation.result()
        transcription_cache[blob_uri] = op_result
        cache.set('transcription_cache', transcription_cache)

    print('Transcription took {:.3f} seconds'.format(time.time() - start_time))
    start_time = time.time()

    if not data['is_context_search']:
        match_results = string_query(query_text, blob_uri, op_result, search_output_mode)
    else:
        match_results = context_query(query_text, blob_uri, op_result, search_output_mode)

    print('Search took {:.3f} seconds'.format(time.time() - start_time))

    end_time = time.time()

    access_link = blob.generate_signed_url(timedelta(hours=1))
    return jsonify(status_code=201, message='Query was successful!', matches=match_results, 
        access_link=access_link, elapsed_time=end_time - route_start_time, success=True)