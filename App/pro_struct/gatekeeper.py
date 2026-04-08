from App.data.connect import DatabaseConnectionPool
from App.data.fetch import QueryExecutor
from App.data.prop import AccessValidator


class BusinessGatekeeper:
    def __init__(self):
        # Safely initializes the full Data Module pipeline
        self.pool = DatabaseConnectionPool()
        self.validator = AccessValidator()
        self.executor = QueryExecutor(self.pool, self.validator)

    def register_user(self, uid, name, dept, role, pin):
        """Pre-Authentication route to register new users with strict validation."""
        conn = None
        cursor = None
        try:
            # Enforce uppercase department names
            dept = str(dept).upper().strip()

            # Strict validation for Student IDs
            if role == 'student':
                if not uid.startswith("RA2411"):
                    return (False, "Registration Error: Student ID must begin with 'RA2411'.")
                if len(uid) != 15:
                    return (False, "Registration Error: Student ID must be exactly 15 characters.")

            conn = self.pool.get_connection()
            if not conn.is_connected():
                conn.ping(reconnect=True, attempts=3, delay=2)

            cursor = conn.cursor()
            if role == 'teacher':
                cursor.execute(
                    "INSERT INTO teachers (faculty_id, name, dept, pin) VALUES (%s, %s, %s, %s)",
                    (uid, name, dept, pin)
                )
            else:
                cursor.execute(
                    "INSERT INTO students (student_id, name, dept) VALUES (%s, %s, %s)",
                    (uid, name, dept)
                )

            conn.commit()
            return (True, "Account created successfully.")

        except Exception as e:
            if "Duplicate entry" in str(e):
                return (False, f"Account with ID '{uid}' already exists.")
            return (False, f"Registration Error: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def authenticate_user(self, uid, cred):
        try:
            if uid.startswith("F"):
                res = self.executor.execute_read(
                    "Teacher", "teachers",
                    "SELECT * FROM teachers WHERE faculty_id = %s AND pin = %s",
                    (uid, cred)
                )
                if res: return (True, {"name": res[0]['name'], "role": "teacher"})
                return (False, "Invalid Faculty ID or PIN.")
            else:
                res = self.executor.execute_read(
                    "Student", "students",
                    "SELECT * FROM students WHERE student_id = %s AND name = %s",
                    (uid, cred)
                )
                if res: return (True, {"name": res[0]['name'], "role": "student"})
                return (False, "Invalid Student ID or Name.")
        except Exception as e:
            return (False, f"Data Module Error: {str(e)}")

    def fetch_dashboard(self, role, user_id):
        try:
            sql_role = "Teacher" if role == 'teacher' else "Student"

            if role == 'teacher':
                query = """
                        SELECT s.subject_code, s.subject_name, s.dept, t.name AS faculty_name
                        FROM subjects s
                                 LEFT JOIN teachers t ON s.faculty_id = t.faculty_id
                        WHERE s.faculty_id = %s \
                        """
                subjects = self.executor.execute_read(sql_role, "subjects", query, (user_id,))
            else:
                query = """
                        SELECT s.subject_code, s.subject_name, s.dept, t.name AS faculty_name
                        FROM subjects s
                                 LEFT JOIN teachers t ON s.faculty_id = t.faculty_id \
                        """
                subjects = self.executor.execute_read(sql_role, "subjects", query)

            for sub in subjects: sub['icon'] = "📚"
            return (True, subjects)
        except Exception as e:
            return (False, f"Data Module Error: {str(e)}")

    def submit_request(self, stu_id, sub_code, req_type, title, url):
        try:
            self.executor.execute_write(
                "Student", "requests", "INSERT",
                "INSERT INTO requests (requester_id, subject_code, query_type, link_title, link_url, status) VALUES (%s, %s, %s, %s, %s, 'PENDING')",
                (stu_id, sub_code, req_type, title, url)
            )
            return (True, "Request submitted successfully.")
        except Exception as e:
            return (False, f"Data Module Error: {str(e)}")

    def view_requests(self, fac_id):
        try:
            requests = self.executor.execute_read(
                "Teacher", "requests",
                "SELECT r.* FROM requests r JOIN subjects s ON r.subject_code = s.subject_code WHERE s.faculty_id = %s AND r.status = 'PENDING'",
                (fac_id,)
            )
            return (True, requests)
        except Exception as e:
            return (False, f"Data Module Error: {str(e)}")

    def fetch_subject_details(self, sub_code):
        try:
            subject_data = self.executor.execute_read(
                "Student", "subjects",
                "SELECT s.subject_code, s.subject_name, t.name AS faculty_name FROM subjects s LEFT JOIN teachers t ON s.faculty_id = t.faculty_id WHERE s.subject_code = %s",
                (sub_code,)
            )

            if not subject_data: return (False, "Subject not found.")

            component_rows = self.executor.execute_read(
                "Student", "components",
                "SELECT category, title, link_url FROM components WHERE subject_code = %s",
                (sub_code,)
            )

            grouped = {}
            for row in component_rows:
                cat = row['category']
                if cat not in grouped: grouped[cat] = []
                grouped[cat].append({"title": row['title'], "url": row['link_url']})

            return (True, {
                "name": subject_data[0].get('subject_name', 'Unknown Subject'),
                "code": subject_data[0].get('subject_code', sub_code),
                "faculty": subject_data[0].get('faculty_name', 'Unknown Faculty'),
                "icon": "📚",
                "components": [{"category": k, "links": v} for k, v in grouped.items()]
            })
        except Exception as e:
            return (False, f"Data Module Error: {str(e)}")
