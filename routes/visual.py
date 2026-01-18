from __future__ import annotations
from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import tempfile
from visual.analyzer import VisualAnalyzer

router = APIRouter(prefix="/visual", tags=["visual"])
analyzer = VisualAnalyzer()

@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """Accepts a photo, runs YOLOv8n, and returns detections."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    result = analyzer.analyze(tmp_path)
    annotated = analyzer.annotate_image(tmp_path, result["detections"])
    return {
        "summary": f"{len(result['detections'])} objects detected",
        "detections": result["detections"],
        "annotated_image": annotated
    }
