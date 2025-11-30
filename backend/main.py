from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from services.audio_processor import AudioProcessor
from services.smart_mixer import SmartMixer
import os

app = FastAPI(title="Vocalize Backend", version="0.1.0")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio playback
os.makedirs("temp_audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="temp_audio"), name="audio")

processor = AudioProcessor(output_dir="temp_audio")
mixer = SmartMixer()

class ProcessRequest(BaseModel):
    youtube_url: str = None
    audio_url: str = None

class MixRequest(BaseModel):
    input_path: str # Relative path like "temp_audio/recording.wav"
    reference_path: str # Relative path like "temp_audio/htdemucs/song/vocals.wav"
    strength: float

class AutotuneRequest(BaseModel):
    input_path: str
    key: str
    semitones: float

@app.post("/process")
async def process_audio(request: ProcessRequest):
    try:
        # Check for Cloud Flag
        if os.environ.get("USE_CLOUD_PROCESSING") == "true":
            print("Using Cloud Processing (Modal)...")
            try:
                import modal
                f = modal.Function.lookup("vocalize-cloud", "process_audio_cloud")
                result = f.remote(request.youtube_url, request.audio_url)
                return result
            except ImportError:
                print("Modal not installed. Falling back to local.")
            except Exception as e:
                print(f"Cloud processing failed: {e}. Falling back to local.")

        # 1. Download
        if request.youtube_url:
            print(f"Downloading {request.youtube_url}...")
            file_path = processor.download_youtube(request.youtube_url)
        elif request.audio_url:
            print(f"Downloading from URL {request.audio_url}...")
            # We need a method to download from URL. 
            # For now, let's assume processor has it or we add it.
            # Actually, let's just use requests/urllib here or add to processor.
            import requests
            response = requests.get(request.audio_url)
            file_path = os.path.join("temp_audio", "uploaded_file.wav") # simplified
            with open(file_path, "wb") as f:
                f.write(response.content)
        else:
            raise HTTPException(status_code=400, detail="No URL provided")
        
        # 2. Detect Key
        print("Detecting key...")
        key = processor.detect_key(file_path)
        
        # 3. Separate Stems
        print("Separating stems...")
        stems = processor.separate_stems(file_path)
        
        # Convert absolute paths to relative URLs
        base_url = "http://localhost:8000/audio"
        stems_urls = {k: f"{base_url}/{os.path.relpath(v, 'temp_audio')}" for k, v in stems.items()}
        
        return {
            "status": "success",
            "key": key,
            "stems": stems_urls,
            "original_file": f"{base_url}/{os.path.basename(file_path)}"
        }
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mix")
async def mix_audio(request: MixRequest):
    try:
        # Resolve paths
        input_full = os.path.abspath(request.input_path)
        ref_full = os.path.abspath(request.reference_path)
        output_filename = f"mixed_{os.path.basename(input_full)}"
        output_full = os.path.join("temp_audio", output_filename)
        
        # Analyze
        print("Analyzing reference...")
        params = mixer.analyze_reference(ref_full)
        
        # Apply
        print("Applying mix...")
        mixer.apply_mix(input_full, output_full, params, request.strength)
        
        return {
            "status": "success",
            "output_url": f"http://localhost:8000/audio/{output_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autotune")
async def autotune_audio(request: AutotuneRequest):
    try:
        input_full = os.path.abspath(request.input_path)
        output_filename = f"tuned_{os.path.basename(input_full)}"
        output_full = os.path.join("temp_audio", output_filename)
        
        print(f"Shifting pitch by {request.semitones} semitones...")
        mixer.apply_autotune(input_full, output_full, request.key, request.semitones)
        
        return {
            "status": "success",
            "output_url": f"http://localhost:8000/audio/{output_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PitchShiftRequest(BaseModel):
    stems: dict[str, str] # dict of stem name -> relative url
    semitones: int

@app.post("/pitch_shift_stems")
async def pitch_shift_stems(request: PitchShiftRequest):
    try:
        shifted_stems = {}
        print(f"Shifting stems by {request.semitones} semitones...")
        
        for name, url in request.stems.items():
            # Extract relative path from URL (e.g., http://localhost:8000/audio/...)
            # We assume the URL structure matches what we serve
            if "/audio/" in url:
                rel_path = url.split("/audio/")[1]
                input_path = os.path.join("temp_audio", rel_path)
            else:
                # Fallback or error if URL is weird
                continue
                
            if not os.path.exists(input_path):
                print(f"File not found: {input_path}")
                continue
                
            # Create output filename
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_shifted_{request.semitones}{ext}"
            
            # Apply pitch shift
            # We use apply_autotune which wraps Pedalboard's PitchShift
            mixer.apply_autotune(input_path, output_path, key="C", strength=request.semitones)
            
            # Construct new URL
            new_rel_path = os.path.relpath(output_path, "temp_audio")
            shifted_stems[name] = f"http://localhost:8000/audio/{new_rel_path}"
            
        return {
            "status": "success",
            "stems": shifted_stems
        }
    except Exception as e:
        print(f"Pitch shift error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File, Form
import shutil

@app.post("/align_recording")
async def align_recording(
    file: UploadFile = File(...),
    start_time: float = Form(...)
):
    try:
        # Save uploaded file temporarily
        temp_input = os.path.join("temp_audio", f"temp_{file.filename}")
        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Output path
        output_filename = f"aligned_{file.filename}"
        output_path = os.path.join("temp_audio", output_filename)
        
        print(f"Aligning recording: start_time={start_time}s")
        
        # Use SmartMixer (or new method) to pad with silence
        # We'll add a helper in SmartMixer for this
        mixer.align_audio(temp_input, output_path, start_time)
        
        return {
            "status": "success",
            "url": f"http://localhost:8000/audio/{output_filename}"
        }
    except Exception as e:
        print(f"Alignment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Vocalize Audio Engine is Running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

class TranscribeRequest(BaseModel):
    audio_url: str

# Project Management Endpoints
from services.project_manager import ProjectManager
project_manager = ProjectManager()

@app.post("/projects/save")
async def save_project(request: Request):
    data = await request.json()
    return project_manager.save_project(data)

@app.get("/projects/list")
async def list_projects():
    return project_manager.list_projects()

@app.get("/projects/load/{project_id}")
async def load_project(project_id: str):
    return project_manager.load_project(project_id)

# Export Endpoint
from services.export_service import ExportService
export_service = ExportService()

class ExportRequest(BaseModel):
    stems: dict
    volumes: dict
    pitch_shift: float
    format: str = "mp3"

@app.post("/export")
async def export_audio(request: ExportRequest):
    try:
        # Convert URLs to local paths
        local_stems = {}
        for name, url in request.stems.items():
            if "/audio/" in url:
                rel_path = url.split("/audio/")[1]
                # Decode URL encoding if needed (simple replacement for spaces)
                rel_path = rel_path.replace("%20", " ")
                local_stems[name] = os.path.join("temp_audio", rel_path)
            else:
                # Assume it's already a path or invalid
                local_stems[name] = url

        output_path = export_service.mix_and_export(
            local_stems,
            request.volumes,
            request.pitch_shift,
            request.format
        )
        if output_path and os.path.exists(output_path):
            return FileResponse(output_path, filename=os.path.basename(output_path), media_type=f"audio/{request.format}")
        else:
            raise HTTPException(status_code=500, detail="Export failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_audio(request: TranscribeRequest):
    try:
        # Extract relative path from URL
        if "/audio/" in request.audio_url:
            rel_path = request.audio_url.split("/audio/")[1]
            input_path = os.path.join("temp_audio", rel_path)
        else:
            raise HTTPException(status_code=400, detail="Invalid audio URL")
            
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
            
        print(f"Transcribing {input_path}...")
        lyrics = processor.transcribe_audio(input_path)
        
        return {
            "status": "success",
            "lyrics": lyrics
        }
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

