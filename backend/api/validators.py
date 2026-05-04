from django.core.exceptions import ValidationError
import re

class ComplexPasswordValidator:
    def validate(self, password, user=None):
        if not re.findall(r'[A-Z]', password):
            raise ValidationError("Hasło musi zawierać przynajmniej jedną wielką literę.")
        if not re.findall(r'\d', password):
            raise ValidationError("Hasło musi zawierać przynajmniej jedną cyfrę.")
        if not re.findall(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Hasło musi zawierać znak specjalny.")

    def get_help_text(self):
        return "Twoje hasło musi zawierać wielką literę, cyfrę i znak specjalny."

