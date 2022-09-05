from django.contrib import admin

from .models import Follower, User


class UserAdmin(admin.ModelAdmin):
    list_filter = ("email",)


admin.site.register(User, UserAdmin)
admin.site.register(Follower)
