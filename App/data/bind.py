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
    raise ImportError(f"Target logic '{class_name}' not found.")


if __name__ == "__main__":
    # 1. Dynamically load your models and the new AccessManager
    Teacher = dynamic_class_binder("Teacher")
    Student = dynamic_class_binder("Student")
    AccessManager = dynamic_class_binder("AccessManager")

    # 2. Create raw user objects (simulating a login)
    admin_teacher = Teacher(faculty_id="F-101", name="Dr. Smith", dept="CS", pin="1234")
    new_student = Student(student_id="S-205", name="Alex", dept="CS")

    # 3. Issue their access profiles
    manager = AccessManager()

    teacher_profile = manager.issue_access_profile(admin_teacher)
    student_profile = manager.issue_access_profile(new_student)

    # 4. Prove the isolation
    print(f"--- Teacher Profile ({teacher_profile['session_id']}) ---")
    print(f"Allowed DB Ops: {teacher_profile['db_operations']}")

    print(f"\n--- Student Profile ({student_profile['session_id']}) ---")
    print(f"Allowed DB Ops: {student_profile['db_operations']}")