import asyncio
import time
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

from config import AWS_REGION

class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, transcript_result_stream, output_func):
        super().__init__(transcript_result_stream)
        self.output_func = output_func

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            if result.is_partial:
                continue  # Only finalized subtitles

            for alt in result.alternatives:
                transcript_text = alt.transcript.strip()

                if transcript_text and alt.items:
                    start_time = alt.items[0].start_time
                    end_time = alt.items[-1].end_time
                    subtitle_payload = {
                        "text": transcript_text,
                        "start_time": start_time,
                        "end_time": end_time
                    }
                    await self.output_func(subtitle_payload)

async def stream_audio_to_transcribe(audio_chunk_generator, output_func, language_code="en-US"):

    client = TranscribeStreamingClient(region=AWS_REGION)

    try:
        stream = await client.start_stream_transcription(
            language_code=language_code,
            media_sample_rate_hz=16000,
            media_encoding="pcm",
        )

        async def send_audio():
            chunk_counter = 1
            async for chunk in audio_chunk_generator:
                if chunk:
                    chunk_start = time.perf_counter()
                    await stream.input_stream.send_audio_event(audio_chunk=chunk)
                    chunk_end = time.perf_counter()

                    send_time = chunk_end - chunk_start

                    chunk_counter += 1

            await stream.input_stream.end_stream()

        handler = MyEventHandler(stream.output_stream, output_func)

        await asyncio.gather(send_audio(), handler.handle_events())

    except Exception as e:
        raise e
