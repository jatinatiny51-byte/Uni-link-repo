def determine_role_by_id(user_id):
    """
    Identifies the user type strictly by their ID prefix before
    their class object is even fully built.
    """
    user_id = str(user_id).upper()
    if user_id.startswith("F"):
        return "Teacher"
    elif user_id.startswith("S"):
        return "Student"
    return "Unknown"


class AccessManager:
    def __init__(self):
        """
        Defines the absolute privilege ceilings for your class models.
        This dictates what they can do in both the SQL layer and the UI layer.
        """
        self.role_blueprints = {
            "Teacher": {
                "sql_role": "Teacher",  # Maps directly to your prop.py AccessValidator
                "db_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                "ui_permissions": ["create_material", "approve_request", "manage_students"],
                "max_concurrent_queries": 5  # Teachers get higher priority bandwidth
            },
            "Student": {
                "sql_role": "Student",
                "db_operations": ["SELECT"],  # Strict read-only for core tables
                "ui_permissions": ["view_material", "submit_request"],
                "max_concurrent_queries": 2  # Prevents student accounts from spamming the DB
            }
        }

    def issue_access_profile(self, user_model):
        """
        Takes an instantiated pro_struct object (Teacher or Student) and
        binds it to an immutable access profile.
        """
        entity_type = user_model.__class__.__name__

        if entity_type not in self.role_blueprints:
            raise PermissionError(f"[!] Security Alert: Unrecognized entity model '{entity_type}'. Access denied.")

        # Create a fresh copy of the blueprint for this specific user session
        profile = self.role_blueprints[entity_type].copy()

        # Agnostically extract the ID whether they are a Teacher or Student
        user_id = None
        if hasattr(user_model, 'get_faculty_id'):
            user_id = user_model.get_faculty_id()
        elif hasattr(user_model, 'get_student_id'):
            user_id = user_model.get_student_id()

        profile["session_id"] = user_id
        profile["is_authenticated"] = True  # Placeholder until PIN logic is built

        return profile