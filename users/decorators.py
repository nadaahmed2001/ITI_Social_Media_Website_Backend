from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

def student_or_supervisor_required(view_func):
    def wrapper(request, *args, **kwargs):
        print("I'm now inside the student or supervisor required decorator")
        print("User:", request.user)
        print("Authenticated:", request.user.is_authenticated)
        # Ensure authentication is applied before checking permissions
        if not request.user or not request.user.is_authenticated:
            raise PermissionDenied  # 403 Forbidden

        # Debugging prints
        print("User:", request.user)
        print("Authenticated:", request.user.is_authenticated)
        print("Is Student:", getattr(request.user, "is_student", False))
        print("Is Supervisor:", getattr(request.user, "is_supervisor", False))

        if not getattr(request.user, "is_student", False) and not getattr(request.user, "is_supervisor", False):
            raise PermissionDenied  # 403 Forbidden
        
        return view_func(request, *args, **kwargs)

    return wrapper




def student_required(view_func):
    """
    Decorator to allow only students to access the view.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_student:
            print("Not a student")
            raise PermissionDenied  # Return a 403 Forbidden response
        return view_func(request, *args, **kwargs)
    return wrapper



def supervisor_required(view_func):
    """
    Decorator to allow only supervisors to access the view.
    """
    print("I'm now inside the supervisor required decorator")
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_supervisor:
            print("Not a supervisor")
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
