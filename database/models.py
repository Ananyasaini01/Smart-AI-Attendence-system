# database/models.py
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, Enum, JSON, Date, Time
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class AttendanceStatus(enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    PROXY_DETECTED = "proxy_detected"

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    roll_number = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(50))
    semester = Column(Integer)
    face_encodings = Column(JSON)
    registered_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    attendances = relationship("Attendance", back_populates="student")

class Attendance(Base):
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    date = Column(Date, nullable=False)
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    confidence_score = Column(Float)
    camera_id = Column(String(20))
    liveness_score = Column(Float)
    is_spoofed = Column(Boolean, default=False)
    marked_at = Column(DateTime, default=datetime.utcnow)
    
    student = relationship("Student", back_populates="attendances")

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=True)
    alert_type = Column(String(50))
    message = Column(Text)
    severity = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow)
    camera_id = Column(String(20))