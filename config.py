# config.py
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class SystemConfig:
    # Database: Default SQLite use karega (koi setup ki tension nahi)
    DB_URI: str = "sqlite:///attendance.db"
    
    # Camera settings: "0" ka matlab aapka laptop webcam hai
    CAMERAS: List[Dict] = field(default_factory=lambda: [
        {
            "id": "CAM_001",
            "rtsp_url": "0",  # CCTV ka URL baad mein yahan daal sakte ho
            "location": "Classroom 1",
            "type": "entry"
        }
    ])
    
    # AI Detection Thresholds
    DETECTION_CONFIDENCE: float = 0.6
    RECOGNITION_THRESHOLD: float = 0.55
    LIVENESS_THRESHOLD: float = 0.5
    
    # Features Toggles
    ANTI_SPOOF_ENABLED: bool = True
    EMOTION_ENABLED: bool = True
    ENGAGEMENT_ENABLED: bool = True
    PROXY_DETECTION_ENABLED: bool = True
    
    # Thresholds
    HEAD_POSE_THRESHOLD: float = 30.0
    EYE_ASPECT_RATIO_THRESHOLD: float = 0.22
    DROWSINESS_FRAMES: int = 20
    LATE_THRESHOLD_MINUTES: int = 10
    
    # Paths
    FACE_DB_PATH: str = "ml_models/face_embeddings/"
    LOG_PATH: str = "logs/"

config = SystemConfig()