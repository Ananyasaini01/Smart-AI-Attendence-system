# core/proxy_detector.py
from datetime import datetime
from collections import defaultdict

class ProxyDetector:
    def __init__(self, config, db_manager):
        self.config = config
        self.db = db_manager
        self.history = defaultdict(list)

    def check_proxy(self, student_id, camera_id, confidence):
        now = datetime.now()
        is_proxy = False
        reasons = []

        # Ek hi student 60 seconds mein doosre camera pe dikhe toh proxy
        for cam, ts in self.history[student_id]:
            if cam != camera_id and (now - ts).total_seconds() < 60:
                is_proxy = True
                reasons.append(f"Simultaneous presence in {cam} & {camera_id}")

        if confidence < 0.5:
            is_proxy = True
            reasons.append("Low face recognition confidence")

        self.history[student_id].append((camera_id, now))
        return {'is_proxy': is_proxy, 'reasons': reasons}