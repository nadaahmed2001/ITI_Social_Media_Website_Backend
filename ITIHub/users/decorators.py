from django.core.exceptions import PermissionDenied

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
