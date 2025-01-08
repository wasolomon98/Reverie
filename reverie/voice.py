import pyaudio
import webrtcvad
import signal
import sys
import wave
import time  # to timestamp filenames
import os
import openai
import pyttsx3
from reverie.gpt_utils import query_gpt

from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

tts_engine = pyttsx3.init()

conversation_state = "IDLE"
last_interaction_time = None
CONVERSATION_TIMEOUT = 30

def speak(text: str):
    """
    Speaks the provided text out loud using the pyttsx3 engine.
    """
    if not text:
        return  # skip empty strings
    tts_engine.say(text)
    tts_engine.runAndWait()

def save_wav(filepath, audio_frames, sample_rate=16000, channels=1):
    """
    Save raw audio frames as a WAV file.
    """
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(audio_frames))

def transcribe_audio(file_path: str) -> str:
    try:
        with open(file_path, "rb") as audio_file:
            response = openai.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                # Optionally specify language="en" or other args if desired
            )
        # The response is a dict with a "text" key
        return response.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""

def handle_speech_segment(speech_frames, sample_rate=16000, channels=1):
    """
    Handles the entire pipeline for a finalized speech segment:
    1. Save the WAV file
    2. Transcribe via Whisper
    3. Query GPT
    4. Speak the response
    """
    global conversation_state, last_interaction_time

    # 1. Save WAV
    filename = f"recordings/speech_{int(time.time())}.wav"
    save_wav(filename, speech_frames, sample_rate=sample_rate, channels=channels)
    print(f"Saved WAV file: {filename}")

    text = transcribe_audio(filename)
    print("Transcription:", text)

    # 2. Decide logic based on state
    if conversation_state == "IDLE":
        # Only respond if the user explicitly said "hello reverie" at the start
        if text.lower().startswith("hello reverie"):
            speak("How may I assist you?")
            # Now we wait for the next speech to pass to GPT
            conversation_state = "CONVERSING"
        else:
            # In IDLE mode, we ignore everything else
            print("No action taken; ignoring.")
            # stay in IDLE
            return

    elif conversation_state == "CONVERSING":
        if "bye reverie" in text.lower():
            speak("Okay, goodbye!")
            conversation_state = "IDLE"
            return

        if not text:
            speak("I didn't catch that.")
            return

        # This utterance is what we send to GPT
        gpt_response = query_gpt(text)
        print("GPT-4o mini Response:", gpt_response)
        speak(gpt_response)

        # After responding, revert to IDLE
        last_interaction_time = time.time()

def record_audio_with_vad():
    """
    Continuously listens via PyAudio + WebRTC VAD.
    When a speech segment ends, we call handle_speech_segment() to process it.
    """
    vad = webrtcvad.Vad()
    vad.set_mode(3)  # More aggressive

    RATE = 16000
    CHUNK_DURATION_MS = 10
    CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)
    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )

    speech_frames = []
    is_speaking = False
    # Adjust min frames to your environment—these are just example values
    min_speech_frames = 30   # frames of speech to confirm "speech start"
    min_silence_frames = 60  # frames of silence to confirm "speech end"

    speech_counter = 0
    silence_counter = 0

    print("Listening for speech. Press Ctrl+C to stop.")

    try:
        while True:
            audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            is_speech = vad.is_speech(audio_data, sample_rate=RATE)

            if is_speech:
                speech_counter += 1
                silence_counter = 0
                speech_frames.append(audio_data)

                if not is_speaking and speech_counter >= min_speech_frames:
                    is_speaking = True
                    print("Speech started...")
            else:
                if is_speaking:
                    silence_counter += 1
                    speech_frames.append(audio_data)

                    if silence_counter >= min_silence_frames:
                        is_speaking = False
                        print("Speech ended.")

                        # Delegate the heavy lifting to another function
                        handle_speech_segment(speech_frames, RATE, CHANNELS)

                        # Reset counters and clear frames
                        speech_frames = []
                        speech_counter = 0
                        silence_counter = 0

            if conversation_state == "CONVERSING":
                now = time.time()
                if (now - last_interaction_time) > CONVERSATION_TIMEOUT:
                    print("No query for 30 seconds, returning to IDLE.")
                    conversation_state = "IDLE"

    finally:
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()

def main():
    """
    The main entry point for Reverie.
    """
    print("DEBUG: TTS, openai, and environment loaded. Now starting VAD loop.")
    record_audio_with_vad()

def signal_handler(sig, frame):
    print("Exiting on Ctrl+C")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    main()
