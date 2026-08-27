from openai import OpenAI

client = OpenAI()
audio_file= open(r"C:\Users\User\Desktop\multi-agent\tts-stt_test\speech.mp3", "rb")

transcription = client.audio.transcriptions.create(
    model="gpt-4o-transcribe", 
    file=audio_file
)

print(transcription.text)