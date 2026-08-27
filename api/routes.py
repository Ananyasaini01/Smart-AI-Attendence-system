# api/routes.py
import sys
import os
from datetime import date
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

TEMPLATE_DIR = os.path.join(BASE_DIR, 'dashboard', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'dashboard', 'static')

from database.db_manager import DatabaseManager
from database.models import Attendance, Student

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
db = DatabaseManager()

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/attendance/today')
def today_attendance():
    try:
        today_str = str(date.today())
        with db.get_session() as session:
            # 1. Sirf wahi bache lo jo database mein exist karte hain
            active_students = session.query(Student).all()
            total_registered = len(active_students)
            valid_student_ids = {s.id for s in active_students}
            student_map = {s.id: s for s in active_students}

            # 2. Aaj ke saare logs fetch karo
            all_logs = session.query(Attendance).all()
            
            # 3. Unique Students Filter (Jinka ID valid hai aur date aaj ki hai)
            unique_present_ids = set()
            display_records = {}

            for log in all_logs:
                # SQLite date handling fix
                log_date = str(log.date)
                if log_date == today_str and log.student_id in valid_student_ids:
                    unique_present_ids.add(log.student_id)
                    # Latest record update for table
                    display_records[log.student_id] = log

            present_count = len(unique_present_ids)
            
            # ⚠️ FINAL SAFETY CHECK: Present registered se zyada nahi ho sakte
            if present_count > total_registered:
                present_count = total_registered

            absent_count = max(0, total_registered - present_count)

            # 4. Table ke liye data prepare karo
            table_data = []
            for s_id in unique_present_ids:
                s = student_map[s_id]
                a = display_records[s_id]
                table_data.append({
                    'roll': s.roll_number,
                    'name': s.name,
                    'time': a.entry_time.strftime('%H:%M:%S') if a.entry_time else 'N/A',
                    'status': 'PRESENT',
                    'confidence': round(a.confidence_score or 0, 2)
                })

            return jsonify({
                'total': total_registered,
                'present': present_count,
                'absent': absent_count,
                'records': table_data
            })
    except Exception as e:
        return jsonify({'error': str(e), 'total': 0, 'present': 0, 'absent': 0, 'records': []})

if __name__ == '__main__':
    print("\n🌐 Dashboard Server started! Press Refresh in Browser.")
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
