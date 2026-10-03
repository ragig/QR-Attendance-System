from django.urls import path

from .views import (
    AttendanceHistoryView,
    AttendanceSessionListCreateView,
    CourseListCreateView,
    DepartmentListCreateView,
    MarkAttendanceView,
    CloseAttendanceSessionView,
    CheckOutView,
    dashboard_view,
    export_report_view,
    login_view,
    qr_login_view,
    me_view,
    register_view,
    NoticeListCreateView,
    NoticeDetailView,
)

urlpatterns = [
    path('auth/register/', register_view, name='register'),
    path('auth/login/', login_view, name='login'),
    path('auth/qr-login/', qr_login_view, name='qr-login'),
    path('auth/me/', me_view, name='me'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('departments/', DepartmentListCreateView.as_view(), name='departments'),
    path('courses/', CourseListCreateView.as_view(), name='courses'),
    path('sessions/', AttendanceSessionListCreateView.as_view(), name='sessions'),
    path('sessions/<int:pk>/close/', CloseAttendanceSessionView.as_view(), name='close-session'),
    path('attendance/mark/', MarkAttendanceView.as_view(), name='mark-attendance'),
    path('attendance/checkout/', CheckOutView.as_view(), name='attendance-checkout'),
    path('attendance/history/', AttendanceHistoryView.as_view(), name='history'),
    path('notices/', NoticeListCreateView.as_view(), name='notices'),
    path('notices/<int:pk>/', NoticeDetailView.as_view(), name='notice-detail'),
    path('reports/export/', export_report_view, name='export-report'),
]
