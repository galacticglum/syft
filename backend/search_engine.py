import argparse
from pathlib import Path
from datetime import timedelta
import api.hash_util as hash_util

from google.cloud import speech, storage
from google.cloud.speech import enums
from google.cloud.speech import types

parser = argparse.ArgumentParser(description='The core search engine.')
parser.add_argument('input', type=str, help='The path to the input audio file.')
parser.add_argument('--auth', dest='auth_json_filepath', type=str, help='The path to the service account credentials file.')
args = parser.parse_args()

speech_client = speech.SpeechClient.from_service_account_json(args.auth_json_filepath)
storage_client = storage.Client.from_service_account_json(args.auth_json_filepath)

BUCKET_NAME = 'syft-audio-bucket'
BUCKET_AUDIO_ROOT = '/'
bucket = storage_client.get_bucket(BUCKET_NAME)

with open(Path(args.input), 'rb') as audio_file:
    # Upload the file to GCS if it doesn't already exists
    blob_filename = str(Path(BUCKET_AUDIO_ROOT) / hash_util.get_crc32_str(audio_file))
    blob = bucket.blob(blob_filename)
    if not blob.exists():
        blob.upload_from_file(audio_file, rewind=True)

    # blob URI is valid for one hour
    # expiration = timedelta(hours=1)
    # blob_uri = blob.generate_signed_url(expiration)
    blob_uri = 'gs://{}/{}'.format(BUCKET_NAME, blob_filename)
    
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
        sample_rate_hertz=16000,
        language_code='en-US')

    operation = speech_client.long_running_recognize(config, {'uri': blob_uri})
    op_result = operation.result()
    for result in op_result.results:
        for alternative in result.alternatives:
            print('=' * 20)
            print(alternative.transcript)
            print(alternative.confidence)