from datetime import datetime

class Teacher:
    def __init__(self, faculty_id, name, dept):
        self._faculty_id = faculty_id
        self._name = name
        self._dept = dept

    @property
    def faculty_id(self): return self._faculty_id

    @property
    def name(self): return self._name
    @name.setter
    def name(self, value):
        if not isinstance(value, str) or len(value) > 100:
            raise ValueError("Name must be a string under 100 characters.")
        self._name = value

    @property
    def dept(self): return self._dept
    @dept.setter
    def dept(self, value):
        if not isinstance(value, str) or len(value) > 100:
            raise ValueError("Department must be a string under 100 characters.")
        self._dept = value

    def __repr__(self):
        return f"Teacher(ID: {self._faculty_id}, Name: {self._name})"


class Request:
    def __init__(self, student_id, subject_code, query_type, link_title, link_url, status="Pending", request_id=None, created_at=None):
        self._request_id = request_id
        self._student_id = student_id
        self._subject_code = subject_code
        self._query_type = query_type
        self._link_title = link_title
        self._link_url = link_url
        self._status = status
        self._created_at = created_at  # New Timestamp Attribute

    # ... (Other immutable getters remain the same) ...

    @property
    def request_id(self): return self._request_id
    @request_id.setter
    def request_id(self, new_id):
        if self._request_id is not None:
            raise PermissionError("Cannot overwrite existing Request ID.")
        self._request_id = new_id

    # --- Write-Once Timestamp ---
    @property
    def created_at(self): return self._created_at
    @created_at.setter
    def created_at(self, timestamp):
        if self._created_at is not None:
            raise PermissionError("Cannot overwrite creation timestamp.")
        if not isinstance(timestamp, datetime):
            raise TypeError("Timestamp must be a valid datetime object.")
        self._created_at = timestamp

    @property
    def link_url(self): return self._link_url
    @link_url.setter
    def link_url(self, value):
        if not isinstance(value, str) or len(value) > 255:
            raise ValueError("URL exceeds database limits (255 chars).")
        self._link_url = value

    @property
    def status(self): return self._status
    @status.setter
    def status(self, value):
        valid_statuses = ["Pending", "Approved", "Rejected"]
        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        self._status = value

    def __repr__(self):
        return f"Request(ID: {self._request_id}, Status: {self._status}, Date: {self._created_at})"
