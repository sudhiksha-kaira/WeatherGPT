import os

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# SPEECH TO TEXT
# ============================================================

def transcribe_audio(audio_file):

    if audio_file is None:
        return None, None

    try:

        # Send audio to Groq Whisper
        transcription = client.audio.transcriptions.create(
            file=(
                "weather_voice.wav",
                audio_file.getvalue()
            ),
            model="whisper-large-v3",
            response_format="json",
            temperature=0
        )

        text = transcription.text.strip()

        return text, None

    except Exception as e:

        return None, str(e)