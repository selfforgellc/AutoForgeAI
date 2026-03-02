from __future__ import annotations
import torch
from pathlib import Path
from ultralytics import YOLO
import cv2
import numpy as np

# Path to lightweight model (3 MB)
MODEL_PATH = Path(__file__).resolve().parent / "yolov8n.pt"

class VisualAnalyzer:
    def __init__(self):
        self.model = YOLO(str(MODEL_PATH))
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def analyze(self, image_path: Path) -> dict:
        """Run inference on a single image and return detections."""
        results = self.model(image_path)
        detections = []
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = r.names[cls]
                xyxy = box.xyxy[0].tolist()
                detections.append({
                    "label": label,
                    "confidence": round(conf, 3),
                    "box": xyxy
                })
        return {"detections": detections}

    def annotate_image(self, image_path: Path, detections: list[dict]) -> str:
        """Draw bounding boxes and save annotated copy."""
        img = cv2.imread(str(image_path))
        for det in detections:
            x1, y1, x2, y2 = map(int, det["box"])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                img,
                f"{det['label']} {det['confidence']:.2f}",
                (x1, max(y1 - 5, 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        out_path = str(image_path.with_name(image_path.stem + "_annotated.jpg"))
        cv2.imwrite(out_path, img)
        return out_path
