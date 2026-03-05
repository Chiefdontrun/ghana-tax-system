"""
Registration validators — phone normalisation and business-type whitelist.
"""

import re

from rest_framework.exceptions import ValidationError

# Ghana phone regex patterns (raw digits after stripping spaces/dashes)
_GHANA_PHONE_PATTERNS = [
    re.compile(r"^\+233([0-9]{9})$"),   # +233XXXXXXXXX
    re.compile(r"^233([0-9]{9})$"),     # 233XXXXXXXXX
    re.compile(r"^0([0-9]{9})$"),       # 0XXXXXXXXX
]

VALID_BUSINESS_TYPES = [
    "food_vendor",
    "clothing",
    "electronics",
    "services",
    "agriculture",
    "wholesale",
    "retail",
    "artisan",
    "other",
]


def validate_ghana_phone(phone: str) -> str:
    """
    Accept +233XXXXXXXXX, 0XXXXXXXXX, 233XXXXXXXXX formats.
    Normalise to +233XXXXXXXXX.
    Raises rest_framework.exceptions.ValidationError if invalid.
    """
    cleaned = phone.strip().replace(" ", "").replace("-", "")

    for pattern in _GHANA_PHONE_PATTERNS:
        match = pattern.match(cleaned)
        if match:
            return f"+233{match.group(1)}"

    raise ValidationError(
        f"'{phone}' is not a valid Ghana phone number. "
        "Expected formats: +233XXXXXXXXX, 0XXXXXXXXX, 233XXXXXXXXX."
    )


def validate_business_type(business_type: str) -> str:
    """Ensure business_type is in the allowed whitelist."""
    if business_type not in VALID_BUSINESS_TYPES:
        raise ValidationError(
            f"'{business_type}' is not a valid business type. "
            f"Allowed values: {', '.join(VALID_BUSINESS_TYPES)}."
        )
    return business_type
