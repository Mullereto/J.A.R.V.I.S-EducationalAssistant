import subprocess
import fitz
import whisper
import os


whisper_model = whisper.load_model("base")

def extract_audio(video_path:str, output_path:str = "temp_audio.wav") -> str:
    """Extracts audio from video using ffmpeg."""
    command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", output_path]
    subprocess.run(command, check=True)
    return output_path

def transcribe_audio(audio_path:str) -> str:
    """Transcribes audio using Whisper model."""
    result = whisper_model.transcribe(audio_path)
    return result["text"]

def parse_pdf(pdf_path:str) -> str:
    """Parses text from PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text
