from django.contrib import admin

from .models import ManagedNavigationItem


@admin.register(ManagedNavigationItem)
class ManagedNavigationItemAdmin(admin.ModelAdmin):
    list_display = ['label', 'location', 'route', 'parent', 'display_order', 'is_active']
    list_filter = ['location', 'is_active']
    list_editable = ['display_order', 'is_active']
    search_fields = ['label', 'route', 'description']
    ordering = ['location', 'display_order']