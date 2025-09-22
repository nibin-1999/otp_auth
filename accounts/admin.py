from django.contrib import admin
from .models import User, OTPCode

# -----------------------------
# User Admin
# -----------------------------


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'full_name', 'phone',
                    'email', 'role', 'loyalty_points', 'is_staff', 'is_active')
    search_fields = ('id', 'username', 'full_name', 'phone', 'email', 'role')
    list_filter = ('is_staff', 'is_active', 'role')
    ordering = ('-id',)


admin.site.register(User, UserAdmin)


# -----------------------------
# OTPCode Admin
# -----------------------------
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'code', 'type',
                    'is_used', 'expires_at', 'created_at')
    search_fields = ('id', 'user__phone', 'code')
    list_filter = ('type', 'is_used', 'expires_at')
    readonly_fields = ('created_at',)
    ordering = ('-id',)


admin.site.register(OTPCode, OTPCodeAdmin)
