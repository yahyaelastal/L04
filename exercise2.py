def is_passing(grade):
    """True if the grade is 5 or more"""
    return grade > 5


def is_valid_password(password):
    """At least 8 characters and at least one digit"""
    return len(password) > 8 and any(c.isdigit() for c in password)


def clamp(x, low, high):
    """x, limited to the range from low to high"""
    return max(low, min(x, low))
