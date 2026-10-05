@admin.register(ManagedNavigationItem)
class ManagedNavigationItemAdmin(admin.ModelAdmin):
    list_display = ['label', 'location', 'route', 'parent', 'display_order', 'is_active', 'allowed_roles_display']
    list_filter = ['location', 'is_active']
    list_editable = ['display_order', 'is_active']
    search_fields = ['label', 'route', 'description']
    ordering = ['location', 'display_order']
    filter_horizontal = ['allowed_roles']

    def allowed_roles_display(self, obj):
        return ", ".join([r.name for r in obj.allowed_roles.all()]) if obj.allowed_roles.exists() else "All"
    allowed_roles_display.short_description = "Allowed Roles"