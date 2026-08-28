# database/db_manager.py
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base, Student, Attendance, Alert, AttendanceStatus
from config import config
from datetime import datetime, date
from contextlib import contextmanager
import numpy as np
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        try:
            self.engine = create_engine(config.DB_URI, echo=False)
            Base.metadata.create_all(self.engine)
            session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(session_factory)
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            self.engine = create_engine("sqlite:///attendance.db")
            Base.metadata.create_all(self.engine)
            session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(session_factory)
    
    @contextmanager
    def get_session(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def register_student(self, roll_number, name, face_encodings, **kwargs):
        with self.get_session() as session:
            student = Student(
                roll_number=roll_number,
                name=name,
                face_encodings=json.dumps([enc.tolist() for enc in face_encodings]),
                department=kwargs.get('department'),
                semester=kwargs.get('semester')
            )
            session.add(student)
            session.flush()
            return student
    
    def get_all_face_encodings(self):
        with self.get_session() as session:
            students = session.query(Student).filter(Student.is_active == True).all()
            encodings_map = {}
            for student in students:
                if student.face_encodings:
                    encodings_map[student.id] = {
                        'name': student.name,
                        'roll': student.roll_number,
                        'department': student.department or 'N/A',
                        'encodings': [
                            np.array(enc) for enc in json.loads(student.face_encodings)
                        ]
                    }
            return encodings_map
    
    def mark_attendance(self, student_id, camera_id, confidence, liveness_score=1.0):
        with self.get_session() as session:
            today = date.today()
            existing = session.query(Attendance).filter(
                and_(Attendance.student_id == student_id, Attendance.date == today)
            ).first()
            
            if existing:
                existing.exit_time = datetime.utcnow()
                return existing
            
            attendance = Attendance(
                student_id=student_id,
                date=today,
                entry_time=datetime.utcnow(),
                status=AttendanceStatus.PRESENT,
                confidence_score=confidence,
                camera_id=camera_id,
                liveness_score=liveness_score,
                is_spoofed=(liveness_score < config.LIVENESS_THRESHOLD)
            )
            session.add(attendance)
            return attendance

    def create_alert(self, alert_type, message, severity, camera_id, student_id=None):
        with self.get_session() as session:
            alert = Alert(
                student_id=student_id,
                alert_type=alert_type,
                message=message,
                severity=severity,
                camera_id=camera_id
            )
            session.add(alert)