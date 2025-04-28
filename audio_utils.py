# audio_utils.py

import asyncio
import subprocess

async def stream_pcm_chunks(mp4_file_path, sample_rate=16000, chunk_size=32000):
    """
    Streams PCM audio chunks from a local MP4 file using ffmpeg.

    Args:
        mp4_file_path (str): Path to the MP4 file.
        sample_rate (int): Audio sampling rate. Default 16kHz.
        chunk_size (int): Size of audio chunks to yield (in bytes).

    Yields:
        Bytes: PCM audio chunk.
    """

    process = await asyncio.create_subprocess_exec(
        'ffmpeg',
        '-i', mp4_file_path,
        '-f', 's16le',            # raw PCM format
        '-acodec', 'pcm_s16le',    # 16-bit PCM
        '-ar', '16000',   # Sampling rate
        '-ac', '1',                # Mono channel
        '-loglevel', 'quiet',      # Suppress ffmpeg logs
        '-',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        while True:
            chunk = await process.stdout.read(chunk_size)
            if not chunk:
                break
            yield chunk
    finally:
        process.terminate()
        await process.wait()
