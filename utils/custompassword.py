from django.contrib.auth.password_validation import (CommonPasswordValidator,
                                                     MinimumLengthValidator,
                                                     NumericPasswordValidator)
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible
from rest_framework.serializers import CharField

from validator.validators import (PasswordRegexValidation,
                                  PasswordSpecialCharacterValidation)


@deconstructible
class PasswordValidator(BaseValidator):
    def __init__(self, validators: tuple = (PasswordRegexValidation, PasswordSpecialCharacterValidation, CommonPasswordValidator, MinimumLengthValidator, NumericPasswordValidator)) -> None:
        self.errors = []
        self.validators = validators

    def __call__(self, value):
        cleaned = self.clean(value)
        validators = self.validators
        errors = self.errors
        for validator in validators:
            try:
                validator().validate(cleaned)
            except Exception as e:
                print(type(e))
                errors.append(e)
        if errors:
            raise ValidationError(errors)


class PasswordField(CharField):
    def __init__(self, **kwargs):
        self.validators.append(PasswordValidator())
        super().__init__(**kwargs)
