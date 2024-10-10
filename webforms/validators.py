import re
from wtforms import ValidationError


def strong_password(form, field):
    password = field.data

    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')

    errors = []

    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter.')
    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one digit.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character.')

    if errors:
        raise ValidationError(' '.join(errors))


def contact_num_length(form, field):
    number_length = len(str(field.data))
    if number_length < 10 or number_length > 11:
        raise ValidationError('Contact Number must be between 10 and 11 digits.')


def totp_length(form, field):
    if field.data is None:
        raise ValidationError('TOTP cannot be empty.')

    totp_str = str(field.data)

    # Check if the TOTP has leading zeros, ensure its length is exactly 6, and contains only digits
    if len(totp_str) != 6 or not totp_str.isdigit():
        raise ValidationError('TOTP must be exactly 6 digits.')
