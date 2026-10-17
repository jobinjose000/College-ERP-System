
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Allow access only to authenticated users
    whose ERP role is explicitly permitted.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied(
                    "You do not have permission to access this page."
                )

            return view_func(request, *args, **kwargs)

        return login_required(wrapped_view)

    return decorator


def is_same_college_or_super_admin(user, college):
    """
    Check whether a user belongs to the requested college,
    or has the SUPER_ADMIN ERP role.

    This checks college access only, not permission
    to perform a particular action.
    """

    if not user.is_authenticated:
        return False

    if user.role == user.Role.SUPER_ADMIN:
        return True

    return (
        user.college_id is not None
        and user.college_id == college.pk
    )
