import asyncio
import json
import os
import websockets
import boto3
import time

from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, UUID_TO_S3
from audio_utils import stream_pcm_chunks
from transcribe_utils import stream_audio_to_transcribe
from logger import setup_logger
from metric_logger import log_metric_to_cloudwatch

# Setup structured logger
logger = setup_logger()

# Setup AWS session
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

s3_client = session.client('s3')

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"

async def handle_connection(websocket):
    logger.info("⚡ New client connected")
    try:
        raw_message = await websocket.recv()
        logger.info(f"Received raw message: {raw_message}")

        data = json.loads(raw_message)
        uuid = data["uuid"]
        source_locale = data["source_locale"]
        target_locale = data["target_locale"]
        request_type = data["request_type"]
        subtitle_format = data.get("subtitle_format", "webvtt")

        logger.info(f"Connection details: UUID={uuid}, Source={source_locale}, Target={target_locale}, Type={request_type}, Format={subtitle_format}")

        # --- Download or Prepare File ---
        s3_entry = UUID_TO_S3.get(uuid)
        if not s3_entry:
            await websocket.send(json.dumps({"error": "Invalid UUID or asset not found."}))
            return

        bucket_name = s3_entry["bucket"]
        key = s3_entry["key"]

        local_file_path = f"/tmp/{uuid}.mp4"

        # Measure download time
        download_start = time.perf_counter()
        # For now, skipping real download for local testing
        download_end = time.perf_counter()
        download_time = download_end - download_start
        logger.info(f"(Simulated) Download complete: {local_file_path} in {download_time:.2f} seconds")
        log_metric_to_cloudwatch("DownloadTime", download_time)

        await websocket.send(json.dumps({"event": "download_complete"}))

        # --- Wait for "start_transcription" or "stop_transcription" ---
        while True:
            action_raw = await websocket.recv()
            action_data = json.loads(action_raw)

            if action_data.get("action") == "start_transcription":
                logger.info("🎬 Client requested to start transcription.")
                break
            elif action_data.get("action") == "stop_transcription":
                logger.info("Client requested to stop before starting transcription.")
                await websocket.send(json.dumps({"event": "transcription_stopped"}))
                return

        if request_type == "transcription":
            session_start = time.perf_counter()

            await websocket.send(json.dumps({"status": "Starting transcription..."}))

            subtitle_counter = 1

            stop_transcription = False

            async def listen_for_stop():
                nonlocal stop_transcription
                try:
                    while True:
                        action_raw = await websocket.recv()
                        action_data = json.loads(action_raw)
                        if action_data.get("action") == "stop_transcription":
                            logger.info("Stop requested during transcription.")
                            stop_transcription = True
                            break
                except websockets.exceptions.ConnectionClosedOK:
                    logger.info("🔌 Connection closed gracefully during listen_for_stop.")

            async def send_subtitle(subtitle_payload):
                nonlocal subtitle_counter

                if stop_transcription:
                    raise Exception("Transcription stopped by client.")

                text = subtitle_payload["text"]
                start_time = subtitle_payload["start_time"]
                end_time = subtitle_payload["end_time"]

                # Use corrected timestamp formatter
                start = format_timestamp(start_time)
                end = format_timestamp(end_time)

                if subtitle_format == "webvtt":
                    formatted = f"{start} --> {end}\n{text}\n\n"
                elif subtitle_format == "srt":
                    formatted = f"{subtitle_counter}\n{start.replace('.', ',')} --> {end.replace('.', ',')}\n{text}\n\n"
                elif subtitle_format == "ttmlv2":
                    formatted = f'<p begin="{start}" end="{end}">{text}</p>\n'
                else:
                    formatted = text  # fallback

                await websocket.send(json.dumps({"subtitle": formatted}))

                logger.info(f"Subtitle {subtitle_counter} sent: {text}")
                subtitle_counter += 1

            # For now: hardcoded local path for testing
            audio_chunk_generator = stream_pcm_chunks("/Users/aditya/PycharmProjects/broca-on-demand/videoplayback.mp4")

            await asyncio.gather(
                stream_audio_to_transcribe(audio_chunk_generator, send_subtitle, language_code=source_locale),
                listen_for_stop()
            )

            if stop_transcription:
                await websocket.send(json.dumps({"event": "transcription_stopped"}))

            session_end = time.perf_counter()
            total_session_time = session_end - session_start
            logger.info(f"Total transcription session time: {total_session_time:.2f} seconds")
            log_metric_to_cloudwatch("SessionDuration", total_session_time)

        else:
            await websocket.send(json.dumps({"error": "Unsupported request type."}))

    except Exception as e:
        logger.error(f"Error during connection handling: {e}")
        try:
            await websocket.send(json.dumps({"error": str(e)}))
        except:
            pass

async def main():
    async with websockets.serve(handle_connection, "localhost", 8765):
        logger.info("WebSocket Server started at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
