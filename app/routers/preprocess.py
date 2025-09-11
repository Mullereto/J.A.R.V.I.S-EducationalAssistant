from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.file_utils import save_upload_file
from app.services.preprocessing import extract_audio, transcribe_audio, parse_pdf
from app.models.request_models import preprocessResponse
import os

router = APIRouter(prefix='/preprocess', tags=["Preprocessing"])


from fastapi import APIRouter, UploadFile, File, HTTPException
import os

router = APIRouter()

@router.post("/Preprocess", response_model=preprocessResponse)
async def preprocess_input(file: UploadFile = File(...)):
    file_path = save_upload_file(file)

    try:
        if file.content_type == "application/pdf":
            text = parse_pdf(file_path)
        elif file.content_type.startswith("audio/"):
            text = transcribe_audio(file_path)
        elif file.content_type.startswith("video/"):
            audio_path = extract_audio(file_path)
            text = transcribe_audio(audio_path)
            os.remove(audio_path)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )
    finally:
        os.remove(file_path)

    return preprocessResponse(source=file.filename, text=text)

# @router.post("/audio", response_model=preprocessResponse)
# async def process_audio(file: UploadFile = File(...)):
#     """Processes audio file: extracts audio, transcribes, and returns text."""
#     file_path = save_upload_file(file)
#     text = transcribe_audio(file_path)
#     os.remove(file_path)
#     return preprocessResponse(source=file.filename, text=text)

# @router.post("/pdf", response_model=preprocessResponse)
# async def process_pdf(file: UploadFile = File(...)):
#     """Processes PDF file: parses text, and returns text."""
#     file_path = save_upload_file(file)
#     text = parse_pdf(file_path)
#     os.remove(file_path)
#     return preprocessResponse(source=file.filename, text=text)

# @router.post("/video", response_model=preprocessResponse)
# async def process_video(file: UploadFile = File(...)):
#     """Processes video file: extracts audio, transcribes, and returns text."""
#     file_path = save_upload_file(file)
#     audio_path = extract_audio(file_path)
#     os.remove(file_path)
#     text = transcribe_audio(audio_path)
#     os.remove(audio_path)
#     return preprocessResponse(source=file.filename, text=text)
