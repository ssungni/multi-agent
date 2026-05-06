import pygame
import sounddevice as sd
from scipy.io.wavfile import write
from openai import OpenAI
from pathlib import Path



client = OpenAI()

# 1. 녹음 함수
def record_audio(filename="input.wav", duration=5, fs=44100):
    print("🎤 말하세요...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, recording)
    print("녹음 완료!")

# 2. STT
def speech_to_text(filename):
    with open(filename, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file
        )
    return transcript.text

# 3. GPT 응답
def get_ai_response(user_text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role":"system",
                "content":"You are a friendly English conversation tutor. Reply only in English."
            },
            {
                "role":"user",
                "content":user_text
            }
        ]
    )
    return response.choices[0].message.content

# 4. TTS
def text_to_speech(text):
    output = Path("reply.mp3")

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=text,
        instructions="Speak clearly and warmly."
    ) as response:
        response.stream_to_file(output)

    pygame.mixer.init()
    pygame.mixer.music.load(str(output))
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pass

# 실행 루프
while True:
    record_audio()
    user_text = speech_to_text("input.wav")

    print("🙋 내가 말한 것:", user_text)

    if user_text.lower() in ["bye", "quit", "exit"]:
        break

    ai_reply = get_ai_response(user_text)

    print("🤖 AI:", ai_reply)

    text_to_speech(ai_reply)