from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .validators import validate_username


class User(AbstractUser):
    username = models.CharField(
        _("username"),
        max_length=30,
        unique=True,
        help_text=_(
            "Required. 30 characters or fewer. Letters, digits and "
            "@/./+/-/_ only."
        ),
        validators=[
            validators.RegexValidator(
                r"^[\w.@+-]+$",
                _(
                    "Enter a valid username. "
                    "This value may contain only letters, numbers "
                    "and @/./+/-/_ characters."
                ),
                "invalid",
            ),
            validate_username,
        ],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_("email address"), max_length=254, unique=True)
    password = models.CharField(_("password"), max_length=150)
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)


class Follower(models.Model):
    author = models.ForeignKey(
        "User", related_name="author", on_delete=models.CASCADE
    )
    follower = models.ForeignKey(
        "User", related_name="follower", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("author", "follower")
        constraints = [
            models.CheckConstraint(
                name="prevent_self_follow",
                check=~models.Q(author=models.F("follower")),
            ),
        ]
