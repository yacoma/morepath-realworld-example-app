import re

from more.cerberus import CerberusValidator


class EmailValidator(CerberusValidator):
    def _check_with_verify_email(self, field, value):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", value):
            self._error(field, "Not valid email")
