from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_username(username):
    if username.lower() == "me":
        raise ValidationError(
            _("%(username)s не валидный юзернейм"),
            params={"username": username},
        )
