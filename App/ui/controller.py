
from App.secure.engine import SecureEngine


class UIController:
    def __init__(self):
        self.engine = SecureEngine()

    def boot(self):
        self.engine.start()

    def shutdown(self):
        self.engine.stop()

    def dispatch(self, feature, *args):
        """Standardizes the IPC response for the Web Server."""
        try:
            # 1. Fire request through the Secure Module IPC Queue
            response = self.engine.execute(feature, *args)

            if response.get("status") == "SUCCESS":
                # 2. Unpack logic results (True/False, ResultData)
                is_ok, result = response.get("data")

                if is_ok:
                    return {"status": "success", "payload": result, "message": "OK"}
                else:
                    return {"status": "error", "payload": None, "message": result}

            return {"status": "error", "message": "IPC Engine Timeout"}

        except Exception as e:
            return {"status": "error", "message": f"UI Bridge Fault: {str(e)}"}

    # OOPS Wrappers
    def login(self, u, c):
        return self.dispatch("authenticate_user", u, c)

    def get_dashboard(self, r, i):
        return self.dispatch("fetch_dashboard", r, i)

    def get_subject(self, code):
        return self.dispatch("fetch_subject_details", code)
