from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "get_full_name", "role", "phone", "region", "is_active", "is_online")
    list_filter = ("role", "region", "is_active")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {
            "fields": ("first_name", "last_name", "phone", "role", "region")
        }),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "is_online", "groups", "user_permissions")
        }),
        ("Dates", {"fields": ("date_joined", "updated_at")}),
    )
    readonly_fields = ("date_joined", "updated_at")
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone", "first_name", "last_name", "role", "region", "password1", "password2"),
        }),
    )
