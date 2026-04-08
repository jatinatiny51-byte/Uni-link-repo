import os
import sys
import importlib.util


def dynamic_class_binder(class_name):
    project_root = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(project_root):
        if any(x in root for x in [".venv", "__pycache__", ".git", ".idea"]): continue
        for file in files:
            if file.endswith(".py") and file != os.path.basename(__file__):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        if f"class {class_name}" in f.read():
                            module_name = f"dynamic_{class_name.lower()}"
                            spec = importlib.util.spec_from_file_location(module_name, full_path)
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)
                            return getattr(module, class_name)
                except Exception:
                    continue
    raise ImportError(f"Logic '{class_name}' not found.")


class BusinessGatekeeper:
    def __init__(self, query_executor, access_manager, watchdog):
        self.executor = query_executor
        self.access_manager = access_manager
        self.watchdog = watchdog

        self.Teacher = dynamic_class_binder("Teacher")
        self.Student = dynamic_class_binder("Student")
        self.Request = dynamic_class_binder("Request")

    def authenticate_user(self, user_id, pin=None):
        if not self.watchdog.check_connection_health():
            return False, "Database unavailable. Connection closed abruptly."

        user_id = str(user_id).upper().strip()
        role = self.access_manager.determine_role_by_id(user_id)

        try:
            if role == "Teacher":
                if not pin: return False, "PIN required for Faculty."
                query = "SELECT faculty_id, name, dept FROM teachers WHERE faculty_id = %s AND pin = %s"
                res = self.executor.execute_read("Teacher", "teachers", query, (user_id, pin))
                if not res: return False, "Invalid ID or PIN."
                obj = self.Teacher(res[0]['faculty_id'], res[0]['name'], res[0]['dept'])

            elif role == "Student":
                query = "SELECT student_id, name, dept FROM students WHERE student_id = %s"
                res = self.executor.execute_read("Student", "students", query, (user_id,))
                if not res: return False, "Student ID not found."
                obj = self.Student(res[0]['student_id'], res[0]['name'], res[0]['dept'])
            else:
                return False, "Unrecognized format."

            profile = self.access_manager.issue_access_profile(obj)
            return True, {"user_object": obj, "profile": profile}
        except Exception as e:
            return False, str(e)

    def fetch_secure_subject_view(self, user_profile, subject_code):
        query = """
                SELECT s.subject_code, \
                       s.subject_name, \
                       t.name AS teacher_name, \
                       c.component_id, \
                       c.category, \
                       c.title, \
                       c.link_url
                FROM subjects s
                         JOIN teachers t ON s.faculty_id = t.faculty_id
                         LEFT JOIN components c ON s.subject_code = c.subject_code
                WHERE s.subject_code = %s \
                """
        result = self.executor.execute_read(
            role=user_profile["sql_role"],
            table="subjects",
            query=query,
            params=(subject_code,)
        )
        return result

    def execute_or_route_mutation(self, user_profile, subject_owner_id, subject_code, mutation_payload):
        clean_payload = self.watchdog.sanitize_payload(mutation_payload)
        session_id = user_profile["session_id"]

        if user_profile["sql_role"] == "Teacher" and session_id == subject_owner_id:
            query = "INSERT INTO components (subject_code, category, title, link_url) VALUES (%s, %s, %s, %s)"
            self.executor.execute_write(
                role="Teacher", table="components", action="INSERT", query=query,
                params=(subject_code, clean_payload['category'], clean_payload['title'], clean_payload['link_url'])
            )
            return True, "Component added directly."

        else:
            query = """
                    INSERT INTO requests (requester_id, requester_role, subject_code, query_type, link_title, link_url, \
                                          status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Pending') \
                    """
            self.executor.execute_write(
                role=user_profile["sql_role"],
                table="requests",
                action="INSERT",
                query=query,
                params=(
                    session_id,
                    user_profile["sql_role"],
                    subject_code,
                    "Cross-Faculty/Student Add",
                    clean_payload['title'],
                    clean_payload['link_url']
                )
            )
            return True, "Unauthorized direct edit. Modification request successfully generated and routed to the owner."

