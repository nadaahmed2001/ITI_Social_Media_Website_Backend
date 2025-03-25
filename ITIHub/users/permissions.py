from rest_framework.permissions import BasePermission

class IsSupervisor(BasePermission):
    """
    Custom permission to allow only supervisors to access certain views.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_supervisor
