# delete_student.py
from database.db_manager import DatabaseManager
from database.models import Student, Attendance, Alert


def delete_student(roll_number):
    db = DatabaseManager()

    with db.get_session() as session:
        # Roll number se student find karo
        student = session.query(Student).filter(
            Student.roll_number == str(roll_number)
        ).first()

        if student is None:
            print(f"\n❌ Student with Roll Number '{roll_number}' not found.\n")
            return

        student_id = student.id
        student_name = student.name

        print("\nStudent Found:")
        print(f"Name: {student_name}")
        print(f"Roll Number: {roll_number}")

        confirm = input("\nType YES to permanently delete this student: ")

        if confirm.strip().upper() != "YES":
            print("❌ Delete cancelled. No data was removed.")
            return

        # Pehle attendance records delete karo
        session.query(Attendance).filter(
            Attendance.student_id == student_id
        ).delete(synchronize_session=False)

        # Student-related alerts delete karo
        session.query(Alert).filter(
            Alert.student_id == student_id
        ).delete(synchronize_session=False)

        # Finally student + face embedding delete karo
        session.delete(student)

        print(f"\n✅ Student '{student_name}' deleted successfully.")
        print("✅ Face embeddings, attendance records and alerts removed from database.\n")


if __name__ == "__main__":
    roll = input("Enter Roll Number to delete: ").strip()

    if not roll:
        print("❌ Roll number cannot be empty.")
    else:
        delete_student(roll)