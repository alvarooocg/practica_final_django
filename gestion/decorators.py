"""
Decorators for role-based access control in the cultural center management system.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Decorator to restrict view access based on user roles.

    Ensures the user is authenticated and has one of the specified roles.
    Raises PermissionDenied if the user's role is not in the allowed roles.

    Args:
        *roles: Variable number of role strings (e.g., 'admin', 'monitor').
                Valid roles are defined in CustomUser.ROL_CHOICES.

    Returns:
        Decorator function that wraps the view.

    Raises:
        PermissionDenied: If the authenticated user does not have an allowed role.

    Example:
        @role_required('admin', 'monitor')
        def my_view(request):
            return HttpResponse('Only admin and monitor can see this')
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.user.rol not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
