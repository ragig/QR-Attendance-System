from django.contrib import admin

from .models import AttendanceRecord, AttendanceSession, Course, Department, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'employee_id', 'role', 'department', 'user')
    list_filter = ('role', 'department')
    search_fields = ('display_name', 'employee_id', 'user__username', 'user__email')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')
    list_filter = ('department',)
    search_fields = ('name', 'department__name')


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'faculty', 'active', 'expires_at', 'created_at')
    list_filter = ('active', 'course')
    search_fields = ('title', 'qr_code', 'faculty__username')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'session', 'check_in', 'check_out', 'status')
    list_filter = ('status', 'session')
    search_fields = ('employee__username', 'session__title')
