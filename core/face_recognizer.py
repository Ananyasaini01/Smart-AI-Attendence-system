# core/face_recognizer.py
import numpy as np
from scipy.spatial.distance import cosine
import logging

logger = logging.getLogger(__name__)

class FaceRecognizer:
    def __init__(self, config, db_manager):
        self.config = config
        self.db = db_manager
        self.known_embeddings = {}
        self.reload_embeddings()

    def reload_embeddings(self):
        self.known_embeddings = self.db.get_all_face_encodings()
        logger.info(f"✅ Total {len(self.known_embeddings)} students ke encodings load ho gaye.")

    def recognize(self, embedding):
        if embedding is None or len(self.known_embeddings) == 0:
            return None, "Unknown", 0.0

        best_student_id = None
        best_name = "Unknown"
        best_similarity = 0.0

        for student_id, data in self.known_embeddings.items():
            for known_emb in data['encodings']:
                sim = 1.0 - cosine(embedding, known_emb)
                if sim > best_similarity:
                    best_similarity = sim
                    best_student_id = student_id
                    best_name = f"{data['name']} ({data['roll']})"

        if best_similarity >= self.config.RECOGNITION_THRESHOLD:
            return best_student_id, best_name, best_similarity

        return None, "Unknown", best_similarity