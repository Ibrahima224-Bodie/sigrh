from django.urls import path
from .views import (
    ProfileView,
    UserListView,
    UserDetailView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
    UserToggleActiveView,
    RoleListView,
    PermissionListView,
    RolePermissionUpdateView,
)

urlpatterns = [
    path('profil/', ProfileView.as_view(), name='profile'),
    path('', UserListView.as_view(), name='user-list'),
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('roles/<slug:role_code>/permissions/', RolePermissionUpdateView.as_view(), name='role-permission-update'),
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    path('create/', UserCreateView.as_view(), name='user-create'),
    path('<uid:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<uid:pk>/edit/', UserUpdateView.as_view(), name='user-update'),
    path('<uid:pk>/toggle-active/', UserToggleActiveView.as_view(), name='user-toggle-active'),
    path('<uid:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),
]
