from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket
from app.utils.file_utils import save_upload_file
from app.services.preprocessing import extract_audio, transcribe_audio, parse_pdf
from app.models.request_models import preprocessResponse
import os
import asyncio

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


@router.websocket("/ws")
async def preprocess_ws(websocket: WebSocket):
    """
    WebSocket endpoint: streams progress updates while preprocessing.
    Frontend (Streamlit) can listen and update progress bar.
    """
    await websocket.accept()

    try:
        # Step 1: Wait for client to send metadata
        data = await websocket.receive_json()
        filename = data.get("filename")
        filetype = data.get("content_type")
        filepath = data.get("file_path")  # path must exist on server

        # Simulate steps with progress
        steps = []
        if filetype == "application/pdf":
            steps = ["Parsing PDF", "Cleaning text", "Finalizing"]
        elif filetype.startswith("audio/"):
            steps = ["Extracting audio", "Transcribing", "Finalizing"]
        elif filetype.startswith("video/"):
            steps = ["Extracting audio", "Transcribing video", "Finalizing"]
        else:
            await websocket.send_json({"error": f"Unsupported file type: {filetype}"})
            await websocket.close()
            return

        for i, step in enumerate(steps, start=1):
            await asyncio.sleep(1)  # simulate delay (replace with real processing chunks)
            progress = int((i / len(steps)) * 100)
            await websocket.send_json({"progress": progress, "status": step})

        # Actually process file
        if filetype == "application/pdf":
            text = parse_pdf(filepath)
        elif filetype.startswith("audio/"):
            text = transcribe_audio(filepath)
        elif filetype.startswith("video/"):
            audio_path = extract_audio(filepath)
            text = transcribe_audio(audio_path)
            os.remove(audio_path)

        # Final result
        await websocket.send_json({
            "progress": 100,
            "status": "Done",
            "result": {"source": filename, "text": text}
        })

    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()
        if os.path.exists(filepath):
            os.remove(filepath)

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
