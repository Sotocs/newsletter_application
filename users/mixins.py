from django.contrib.auth.mixins import UserPassesTestMixin
from users.models import User


class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == User.Role.MANAGER
        )

    def handle_no_permission(self):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied
