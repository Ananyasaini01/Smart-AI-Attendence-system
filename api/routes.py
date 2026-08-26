# api/routes.py
import sys
import os
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS

# Absolute Path Setup (Taaki TemplateNotFound error kabhi na aaye)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

TEMPLATE_DIR = os.path.join(BASE_DIR, 'dashboard', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'dashboard', 'static')

from database.db_manager import DatabaseManager
from database.models import Attendance, Student

app = Flask(__name__,
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
db = DatabaseManager()

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/attendance/today')
def today_attendance():
    try:
        with db.get_session() as session:
            total_students = session.query(Student).filter(Student.is_active == True).count()
            today_records = session.query(Attendance).all()
            present_count = len(today_records)
            
            records = []
            for rec in today_records:
                student = session.query(Student).get(rec.student_id)
                records.append({
                    'roll': student.roll_number if student else 'N/A',
                    'name': student.name if student else 'N/A',
                    'time': rec.entry_time.strftime('%H:%M:%S') if rec.entry_time else 'N/A',
                    'status': rec.status.value if hasattr(rec.status, 'value') else str(rec.status),
                    'confidence': round(rec.confidence_score or 0, 2)
                })
            
            return jsonify({
                'total': total_students,
                'present': present_count,
                'absent': max(0, total_students - present_count),
                'records': records
            })
    except Exception as e:
        return jsonify({'error': str(e), 'present': 0, 'absent': 0, 'total': 0, 'records': []})

if __name__ == '__main__':
    print("\n🌐 Starting Web Dashboard Server at http://localhost:5000\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)