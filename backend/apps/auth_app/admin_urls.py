"""
auth_app admin URL configuration — /api/admin/...
"""

from django.urls import path
from apps.auth_app.views import AdminUserListCreateView, AdminUserDetailView

urlpatterns = [
    path("users", AdminUserListCreateView.as_view(), name="admin-users"),
    path("users/<str:admin_id>", AdminUserDetailView.as_view(), name="admin-user-detail"),
]
