from rest_framework.permissions import BasePermission


class IsStudentOrSupervisor(BasePermission):
    """
    Custom permission to allow only students or supervisors to access a view.
    """

    def has_permission(self, request, view):
        # Ensure user is authenticated first
        if not request.user or not request.user.is_authenticated:
            return False  # Block unauthenticated users
        
        # Check if user is a student or a supervisor
        return getattr(request.user, "is_student", False) or getattr(request.user, "is_supervisor", False)
