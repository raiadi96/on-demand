import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:
        print("🔗 Connected to server")

        # Send initial connection request
        connect_payload = {
            "uuid": "123765",
            "source_locale": "en-US",
            "target_locale": "en-IN",
            "request_type": "transcription",
            "subtitle_format": "webvtt"  # Options: "webvtt", "srt", "ttmlv2"
        }
        await websocket.send(json.dumps(connect_payload))
        print(f"📨 Sent connection request: {connect_payload}")

        # Listen for server messages
        while True:
            server_message = await websocket.recv()
            print(f"📝 Server: {server_message}")

            data = json.loads(server_message)

            # Handle different types of server events
            if data.get("event") == "download_complete":
                print("✅ Download complete! Sending start_transcription...")

                # Automatically send start transcription after download completes
                start_payload = {
                    "action": "start_transcription"
                }
                await websocket.send(json.dumps(start_payload))
                print("🎬 Sent start_transcription action.")

            elif data.get("event") == "transcription_stopped":
                print("🛑 Transcription stopped by server.")
                break  # Exit loop

            elif data.get("subtitle"):
                print(f"🗣️ Subtitle: {data['subtitle'].strip()}")

            # Optional: After receiving 10 subtitles, send stop_transcription
            # You can implement manual or auto stopping here
            # For example, after receiving N subtitles or after few seconds

async def main():
    await connect()

if __name__ == "__main__":
    asyncio.run(main())
