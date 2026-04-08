class AccessValidator:
    def __init__(self):
        self.role_permissions = {
            "Teacher": {
                "teachers": ["SELECT", "UPDATE"],
                "students": ["SELECT"],
                "subjects": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                "components": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                "requests": ["SELECT", "UPDATE"]
            },
            "Student": {
                "teachers": ["SELECT"],
                "students": ["SELECT", "UPDATE"],
                "subjects": ["SELECT"],
                "components": ["SELECT"],
                "requests": ["SELECT", "INSERT"]
            }
        }

    def can_access(self, role, table, action):
        if role not in self.role_permissions:
            return False
        if table not in self.role_permissions[role]:
            return False
        return action.upper() in self.role_permissions[role][table]

    def sanitize_input(self, data):
        if not isinstance(data, (tuple, list, dict)):
            raise ValueError("Parameters must be passed as a tuple, list, or dictionary for parameterized execution.")
        return data

