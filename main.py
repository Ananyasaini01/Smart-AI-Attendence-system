import cv2
import numpy as np
import sqlite3
import json
import tkinter as tk
from tkinter import messagebox
from insightface.app import FaceAnalysis
from PIL import Image, ImageTk

DB_PATH = "attendance.db"

# ==================== COLORS (Light Professional Theme) ====================
BG_MAIN     = "#f4f6f9"
BG_CARD     = "#ffffff"
BG_HEADER   = "#ffffff"
SHADOW      = "#d1d9e6"
BORDER      = "#e1e5eb"
TEXT_DARK   = "#1a202c"
TEXT_MUTED  = "#64748b"
TEXT_LIGHT  = "#94a3b8"
PRIMARY     = "#4f46e5"
PRIMARY_HOV = "#4338ca"
SUCCESS     = "#10b981"
SUCCESS_HOV = "#059669"
DANGER      = "#ef4444"
DANGER_HOV  = "#dc2626"
INFO        = "#3b82f6"
INFO_HOV    = "#2563eb"

# Camera display size (chhota kiya)
CAM_W, CAM_H = 520, 390

# ==================== DATABASE ====================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number VARCHAR(20) UNIQUE,
            name VARCHAR(100),
            department VARCHAR(50),
            semester INTEGER,
            face_encodings JSON,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

def load_students():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT roll_number, name, department, face_encodings FROM students")
    rows = cur.fetchall()
    conn.close()
    students = []
    for roll, name, dept, enc_json in rows:
        if enc_json:
            try:
                enc = np.array(json.loads(enc_json), dtype=np.float32)
                students.append({"roll": roll, "name": name, "dept": dept, "enc": enc})
            except Exception:
                pass
    return students

def save_to_db(roll, name, dept, sem, emb_list):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO students (roll_number, name, department, semester, face_encodings, is_active) VALUES (?,?,?,?,?,1)",
            (roll, name, dept, sem, json.dumps(emb_list))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# ==================== FACE MATCH ====================

def find_match(emb, students, threshold=0.35):
    if not students:
        return None, 0.0
    emb_n = emb / (np.linalg.norm(emb) + 1e-8)
    best, best_sim = None, 0.0
    for s in students:
        e = s["enc"]
        if e.ndim == 2:
            norms = np.linalg.norm(e, axis=1, keepdims=True) + 1e-8
            sim = float(np.max((e / norms) @ emb_n))
        else:
            sim = float(np.dot(e / (np.linalg.norm(e) + 1e-8), emb_n))
        if sim > best_sim:
            best_sim = sim
            best = s
    return (best, best_sim) if best_sim >= threshold else (None, best_sim)


def make_shadow_button(parent, text, bg, hover_bg, command):
    shadow = tk.Frame(parent, bg=SHADOW)
    btn = tk.Button(
        shadow, text=text, font=("Segoe UI", 11, "bold"),
        bg=bg, fg="white",
        activebackground=hover_bg, activeforeground="white",
        relief="flat", bd=0, cursor="hand2",
        padx=18, pady=9, command=command
    )
    btn.pack(padx=(0, 2), pady=(0, 2))
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return shadow


# ==================== MAIN APP ====================

class FaceAttendanceApp:
    def __init__(self):
        init_db()

        print("[..] InsightFace model load ho raha hai...")
        self.face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        print("[OK] Model ready")

        self.students = load_students()
        print(f"[OK] {len(self.students)} students loaded")

        self.cap = None
        self.mode = None
        self.register_info = {}
        self.after_id = None

        # ================== MAIN WINDOW ==================
        self.root = tk.Tk()
        self.root.title("Smart Attendance System")
        self.root.geometry("820x680")
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(False, False)

        # --- Top Header Bar ---
        header_wrap = tk.Frame(self.root, bg=SHADOW, height=72)
        header_wrap.pack(fill="x")
        header_wrap.pack_propagate(False)

        header = tk.Frame(header_wrap, bg=BG_HEADER, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        left_frame = tk.Frame(header, bg=BG_HEADER)
        left_frame.pack(side="left", padx=20, pady=8)

        tk.Label(left_frame, text="🎓", font=("Segoe UI Emoji", 26),
                 bg=BG_HEADER).pack(side="left", padx=(0, 10))

        title_frame = tk.Frame(left_frame, bg=BG_HEADER)
        title_frame.pack(side="left")
        tk.Label(title_frame, text="Smart Attendance",
                 font=("Segoe UI", 16, "bold"), fg=TEXT_DARK, bg=BG_HEADER).pack(anchor="w")
        tk.Label(title_frame, text="Face Recognition System",
                 font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_HEADER).pack(anchor="w")

        # Stats Badge
        badge_wrap = tk.Frame(header, bg=SHADOW)
        badge_wrap.pack(side="right", padx=20, pady=16)
        badge = tk.Frame(badge_wrap, bg="#eef2ff", padx=12, pady=6)
        badge.pack(padx=(0, 2), pady=(0, 2))
        tk.Label(badge, text="👥", font=("Segoe UI Emoji", 12),
                 bg="#eef2ff").pack(side="left", padx=(0, 5))
        self.count_lbl = tk.Label(badge, text=f"{len(self.students)} Registered",
                                  font=("Segoe UI", 10, "bold"),
                                  fg=PRIMARY, bg="#eef2ff")
        self.count_lbl.pack(side="left")

        # --- Camera Feed Card ---
        cam_shadow = tk.Frame(self.root, bg=SHADOW)
        cam_shadow.pack(pady=(15, 10))

        cam_card = tk.Frame(cam_shadow, bg=BG_CARD)
        cam_card.pack(padx=(0, 3), pady=(0, 3))

        self.vid_lbl = tk.Label(cam_card, bg="#1a1a1a",
                                text="📷\n\nCamera Off\nClick a button below",
                                fg="#666", font=("Segoe UI", 13),
                                width=CAM_W, height=CAM_H)
        # Fixed size using pixel dimensions
        self.vid_lbl.config(width=CAM_W, height=CAM_H)
        self.vid_lbl.pack(padx=8, pady=8)
        # Force pixel size (width/height in tk.Label is in chars for text, so use frame)
        cam_card.config(width=CAM_W + 16, height=CAM_H + 16)
        cam_card.pack_propagate(False)
        self.vid_lbl.place(x=8, y=8, width=CAM_W, height=CAM_H)

        # --- Button Row ---
        bf = tk.Frame(self.root, bg=BG_MAIN)
        bf.pack(pady=(5, 10))

        s1 = make_shadow_button(bf, "  ➕   Register Student  ",
                                 SUCCESS, SUCCESS_HOV, self.open_register_dialog)
        s1.grid(row=0, column=0, padx=8)

        s2 = make_shadow_button(bf, "  ▶   Start Attendance  ",
                                 INFO, INFO_HOV, self.start_attendance)
        s2.grid(row=0, column=1, padx=8)

        s3 = make_shadow_button(bf, "  ⏹   Stop Camera  ",
                                 DANGER, DANGER_HOV, self.stop_camera)
        s3.grid(row=0, column=2, padx=8)

        # --- Status Bar (Bottom) ---
        status_frame = tk.Frame(self.root, bg=BG_CARD, height=36)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        tk.Frame(status_frame, bg=BORDER, height=1).pack(fill="x", side="top")

        self.status_var = tk.StringVar(value="⚡  Ready — Choose an option to begin")
        tk.Label(status_frame, textvariable=self.status_var,
                 font=("Segoe UI", 9, "bold"), fg=SUCCESS, bg=BG_CARD,
                 anchor="w", padx=20).pack(fill="both", expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ================== REGISTER DIALOG ==================
    def open_register_dialog(self):
        self.stop_camera()

        dlg = tk.Toplevel(self.root)
        dlg.title("Register New Student")
        dlg.geometry("460x600")
        dlg.configure(bg=BG_MAIN)
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - 230
        y = (dlg.winfo_screenheight() // 2) - 300
        dlg.geometry(f"460x600+{x}+{y}")

        card_shadow = tk.Frame(dlg, bg=SHADOW)
        card_shadow.pack(padx=18, pady=18, fill="both", expand=True)

        card = tk.Frame(card_shadow, bg=BG_CARD)
        card.pack(padx=(0, 4), pady=(0, 4), fill="both", expand=True)

        header_area = tk.Frame(card, bg=BG_CARD, pady=15)
        header_area.pack(fill="x")

        icon_wrap = tk.Frame(header_area, bg=BG_CARD)
        icon_wrap.pack()
        tk.Label(icon_wrap, text="👤", font=("Segoe UI Emoji", 32),
                 bg="#eef2ff", fg=PRIMARY, padx=14, pady=6).pack()

        tk.Label(header_area, text="Student Registration",
                 font=("Segoe UI", 16, "bold"),
                 fg=TEXT_DARK, bg=BG_CARD).pack(pady=(10, 2))
        tk.Label(header_area, text="Fill in the details to enroll a new student",
                 font=("Segoe UI", 8),
                 fg=TEXT_MUTED, bg=BG_CARD).pack()

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=25, pady=6)

        form_frame = tk.Frame(card, bg=BG_CARD)
        form_frame.pack(pady=(8, 5), padx=30, fill="x")

        entries = {}
        fields = [
            ("👤  Full Name", "Name", "Enter student's full name"),
            ("🆔  Roll Number", "Roll Number", "e.g. 2024CS101"),
            ("🏛  Department", "Department", "e.g. Computer Science"),
            ("📚  Semester", "Semester", "e.g. 4"),
        ]

        for icon_label, key, placeholder in fields:
            tk.Label(form_frame, text=icon_label,
                     font=("Segoe UI", 9, "bold"),
                     fg=TEXT_DARK, bg=BG_CARD, anchor="w").pack(fill="x", pady=(8, 3))

            entry_wrap = tk.Frame(form_frame, bg=BORDER)
            entry_wrap.pack(fill="x")

            entry = tk.Entry(
                entry_wrap, font=("Segoe UI", 10),
                bg=BG_CARD, fg=TEXT_LIGHT,
                insertbackground=PRIMARY,
                relief="flat", bd=0,
                highlightthickness=0
            )
            entry.pack(fill="x", ipady=7, ipadx=9, padx=1, pady=1)
            entry.insert(0, placeholder)

            def on_focus_in(e, wrap=entry_wrap, ph=placeholder):
                wrap.config(bg=PRIMARY)
                if e.widget.get() == ph:
                    e.widget.delete(0, "end")
                    e.widget.config(fg=TEXT_DARK)

            def on_focus_out(e, wrap=entry_wrap, ph=placeholder):
                wrap.config(bg=BORDER)
                if not e.widget.get().strip():
                    e.widget.insert(0, ph)
                    e.widget.config(fg=TEXT_LIGHT)

            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)
            entries[key] = entry

        def submit():
            name = entries["Name"].get().strip()
            roll = entries["Roll Number"].get().strip()
            dept = entries["Department"].get().strip()
            sem  = entries["Semester"].get().strip()

            placeholders = ["Enter student's full name", "e.g. 2024CS101",
                            "e.g. Computer Science", "e.g. 4"]

            if name in placeholders or not name:
                messagebox.showwarning("Missing Info", "Please enter a valid Name!", parent=dlg); return
            if roll in placeholders or not roll:
                messagebox.showwarning("Missing Info", "Please enter a valid Roll Number!", parent=dlg); return
            if dept in placeholders or not dept:
                messagebox.showwarning("Missing Info", "Please enter a valid Department!", parent=dlg); return
            if sem in placeholders or not sem:
                messagebox.showwarning("Missing Info", "Please enter a valid Semester!", parent=dlg); return
            try:
                sem = int(sem)
            except ValueError:
                messagebox.showwarning("Invalid", "Semester must be a number!", parent=dlg); return

            self.register_info = {"name": name, "roll": roll, "dept": dept, "sem": sem}
            dlg.destroy()
            self.begin_capture()

        btn_wrap = tk.Frame(card, bg=BG_CARD)
        btn_wrap.pack(pady=(15, 12), padx=30, fill="x")

        sub_shadow = tk.Frame(btn_wrap, bg=SHADOW)
        sub_shadow.pack(fill="x")

        submit_btn = tk.Button(
            sub_shadow, text="📸  Capture Face & Register",
            font=("Segoe UI", 11, "bold"),
            bg=PRIMARY, fg="white",
            activebackground=PRIMARY_HOV, activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            pady=10, command=submit
        )
        submit_btn.pack(fill="x", padx=(0, 3), pady=(0, 3))
        submit_btn.bind("<Enter>", lambda e: submit_btn.config(bg=PRIMARY_HOV))
        submit_btn.bind("<Leave>", lambda e: submit_btn.config(bg=PRIMARY))

        tk.Label(card, text="🔒  Face data stored securely",
                 font=("Segoe UI", 7),
                 fg=TEXT_LIGHT, bg=BG_CARD).pack(pady=(0, 10))

    # ================== CAPTURE & ATTENDANCE ==================
    def begin_capture(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Camera start nahi ho paya!")
            return
        self.mode = "register"
        self.status_var.set(f"📸  Registering: {self.register_info['name']} — Look at the camera...")
        self.loop()

    def start_attendance(self):
        self.stop_camera()
        self.students = load_students()
        self.count_lbl.config(text=f"{len(self.students)} Registered")
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Camera start nahi ho paya!")
            return
        self.mode = "attendance"
        self.status_var.set("▶  Attendance Mode Active — Detecting faces...")
        self.loop()

    # ================== CAMERA LOOP ==================
    def loop(self):
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            self.after_id = self.root.after(30, self.loop)
            return

        faces = self.face_app.get(frame)

        if self.mode == "register":
            if faces:
                f = faces[0]
                b = f.bbox.astype(int)
                cv2.rectangle(frame, (b[0], b[1]), (b[2], b[3]), (16, 185, 129), 2)
                cv2.putText(frame, "Face Detected! Saving...", (b[0], b[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (16, 185, 129), 2)
                self.display(frame)

                info = self.register_info
                ok = save_to_db(info["roll"], info["name"], info["dept"],
                                info["sem"], f.embedding.tolist())
                if ok:
                    self.students = load_students()
                    self.count_lbl.config(text=f"{len(self.students)} Registered")
                    self.status_var.set(f"✅  {info['name']} registered successfully!")
                    messagebox.showinfo("Success", f"🎉  {info['name']} successfully registered!")
                else:
                    self.status_var.set("❌  Roll Number already exists!")
                    messagebox.showwarning("Duplicate", f"Roll Number '{info['roll']}' already registered!")

                self.stop_camera()
                return
            else:
                cv2.putText(frame, "No face detected", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (239, 68, 68), 2)

        elif self.mode == "attendance":
            for f in faces:
                b = f.bbox.astype(int)
                match, sim = find_match(f.embedding, self.students)

                if match:
                    match_percent = int(sim * 100)
                    label = f"{match['name']} | {match['dept']} ({match_percent}%)"
                    color = (16, 185, 129)
                else:
                    label = "Unknown"
                    color = (239, 68, 68)

                cv2.rectangle(frame, (b[0], b[1]), (b[2], b[3]), color, 2)
                cv2.putText(frame, label, (b[0], b[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        self.display(frame)
        self.after_id = self.root.after(30, self.loop)

    def display(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (CAM_W, CAM_H))
        img = ImageTk.PhotoImage(Image.fromarray(frame))
        self.vid_lbl.imgtk = img
        self.vid_lbl.configure(image=img, text="")

    # ================== STOP & CLOSE ==================
    def stop_camera(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.cap:
            self.cap.release()
            self.cap = None
        self.mode = None
        self.status_var.set("⏹  Camera Stopped")
        self.vid_lbl.configure(image="",
                               text="📷\n\nCamera Off\nClick a button below",
                               fg="#666", font=("Segoe UI", 13))

    def on_close(self):
        self.stop_camera()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    FaceAttendanceApp().run()