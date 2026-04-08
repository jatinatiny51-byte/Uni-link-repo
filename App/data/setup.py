
import mysql.connector

# --- UPDATE YOUR CREDENTIALS HERE ---
db_config = {
    "localhost": "127.0.0.1",
    "user": "root",
    "password": "",  # Change if your local DB password differs
}


def setup_database():
    try:
        print("[*] Connecting to MySQL Server...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 1. Fresh Database Creation
        cursor.execute("DROP DATABASE IF EXISTS school_db")
        cursor.execute("CREATE DATABASE school_db")
        cursor.execute("USE school_db")
        print("[✔] Database 'school_db' created and selected.")

        # 2. Table Creation
        tables = [
            """CREATE TABLE teachers
               (
                   faculty_id VARCHAR(50) PRIMARY KEY,
                   name       VARCHAR(100),
                   dept       VARCHAR(100),
                   pin        VARCHAR(10)
               )""",
            """CREATE TABLE students
               (
                   student_id VARCHAR(50) PRIMARY KEY,
                   name       VARCHAR(100),
                   dept       VARCHAR(100)
               )""",
            """CREATE TABLE subjects
               (
                   subject_code VARCHAR(50) PRIMARY KEY,
                   subject_name VARCHAR(100),
                   faculty_id   VARCHAR(50),
                   dept         VARCHAR(100)
               )""",
            """CREATE TABLE components
               (
                   component_id INT AUTO_INCREMENT PRIMARY KEY,
                   subject_code VARCHAR(50),
                   category     VARCHAR(50),
                   title        VARCHAR(150),
                   link_url     VARCHAR(255)
               )""",
            """CREATE TABLE requests
               (
                   request_id     INT AUTO_INCREMENT PRIMARY KEY,
                   requester_id   VARCHAR(50),
                   requester_role VARCHAR(50),
                   subject_code   VARCHAR(50),
                   query_type     VARCHAR(50),
                   link_title     VARCHAR(150),
                   link_url       VARCHAR(255),
                   status         VARCHAR(50) DEFAULT 'Pending',
                   created_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
               )"""
        ]

        for table_sql in tables:
            cursor.execute(table_sql)
        print("[✔] Schema tables generated successfully.")

        # 3. Data Insertion (Based on provided sample data)
        # Teachers [cite: 14]
        cursor.executemany(
            "INSERT INTO teachers (faculty_id, name, dept, pin) VALUES (%s, %s, %s, %s)",
            [
                ("F1", "Dr. T Anusha", "CSE", "1209"),
                ("F2", "Ms. Charulatha RT", "CSE", "1654")
            ]
        )

        # Students [cite: 15]
        cursor.executemany(
            "INSERT INTO students (student_id, name, dept) VALUES (%s, %s, %s)",
            [
                ("RA2411003040038", "Jatin verma", "CSE(core)"),
                ("RA2411003040076", "Abhishek jatla", "CSE(core)")
            ]
        )

        # Subjects [cite: 14]
        cursor.executemany(
            "INSERT INTO subjects (subject_code, subject_name, faculty_id, dept) VALUES (%s, %s, %s, %s)",
            [
                ("21CSC204J", "DAA", "F1", "CSE"),
                ("21CSC253T", "IOT", "F2", "CSE")
            ]
        )

        # Components
        cursor.executemany(
            "INSERT INTO components (subject_code, category, title, link_url) VALUES (%s, %s, %s, %s)",
            [
                ("21CSC204J", "Lab", "Elab", "https://dld.srmist.edu.in/vdpetelab2024/#/"),
                ("21CSC204J", "Notes", "Unit 1",
                 "https://drive.google.com/file/d/1HirXE45jQf6P7W9HtE_3GNGcB01_KZqF/view?usp=sharing"),
                ("21CSC253T", "Notes", "Unit 1 to 5",
                 "https://drive.google.com/file/d/1IHat9StY1UUl_b_z948lS28802ip0E03/view?usp=sharing")
            ]
        )

        conn.commit()
        print("[✔] Sample data populated successfully.")

    except mysql.connector.Error as err:
        print(f"[✘] Error: {err}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()
        print("[*] Database connection closed.")


if __name__ == "__main__":
    setup_database()

