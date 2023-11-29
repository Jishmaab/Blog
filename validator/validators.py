from django.core.exceptions import ValidationError
import re

class PasswordRegexValidation:
    def validate(self, password, user=None):
        if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z0-9\s]).{8,}$', password):
            raise ValidationError("The password must contain at least one uppercase letter, one lowercase letter, one digit, one special character, and be at least 8 characters long.")

class PasswordSpecialCharacterValidation:
    def validate(self, password, user=None):
        if not re.match(r'^[\w\d\W]*$', password):
            raise ValidationError("The password must contain special characters.")




    
