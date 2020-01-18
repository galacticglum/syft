import zlib

'''
The default chunk size in bytes (128 kB).
'''
DEFAULT_CHUNK_SIZE = 131072

def get_crc32(file, chunk_size=DEFAULT_CHUNK_SIZE):
    # Hash the file by reading chunks sequentially
    # This prevents memory overflows
    file_hash = 0
    for chunk in iter(lambda: file.read(chunk_size), b''):
        file_hash = zlib.crc32(chunk, file_hash)

    return file_hash & 0xFFFFFFFF

def get_crc32_str(file, chunk_size=DEFAULT_CHUNK_SIZE):
    return "%X" % get_crc32(file, chunk_size=chunk_size)