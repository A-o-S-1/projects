from django.contrib import admin

from .models import AcademicsPage, Department, Subject


@admin.register(AcademicsPage)
class AcademicsPageAdmin(admin.ModelAdmin):
    fieldsets = (("Content", {"fields": ("intro", "junior_secondary_overview", "senior_secondary_overview")}),)

    def has_add_permission(self, request):
        return not AcademicsPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 1
    fields = ("name", "level", "track", "description")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    list_editable = ("order",)
    inlines = [SubjectInline]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "level", "track")
    list_filter = ("level", "track", "department")
    search_fields = ("name",)
