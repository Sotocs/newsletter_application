from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.views import View
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from .forms import RegistrationForm
from .tokens import account_activation_token
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .mixins import ManagerRequiredMixin
from .models import User


class LoginView(auth_views.LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True
    next_page = reverse_lazy("recipient_list")


class RegistrationView(View):
    template_name = "users/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("recipient_list")

        form = RegistrationForm()

        return render(
            request,
            self.template_name,
            {"form": form},
        )

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("recipient_list")

        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            user.set_password(form.cleaned_data["password"])
            user.is_active = False
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))

            token = account_activation_token.make_token(user)

            activation_url = request.build_absolute_uri(
                reverse(
                    "activate",
                    kwargs={
                        "uidb64": uid,
                        "token": token,
                    },
                )
            )

            send_mail(
                subject="Подтверждение регистрации",
                message=(
                    "Для подтверждения регистрации перейдите "
                    f"по ссылке:\n\n{activation_url}"
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(
                request,
                "Письмо с подтверждением отправлено на ваш email.",
            )

            return redirect("login")

        return render(
            request,
            self.template_name,
            {"form": form},
        )


class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        User = get_user_model()

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
        ):
            user = None

        if user is not None and account_activation_token.check_token(
            user,
            token,
        ):
            user.is_active = True
            user.save(update_fields=["is_active"])

            messages.success(
                request,
                "Email успешно подтверждён. Теперь вы можете войти.",
            )

            return redirect("login")

        return render(
            request,
            "users/activation_invalid.html",
        )


class UserListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"


class UserBlockView(LoginRequiredMixin, ManagerRequiredMixin, View):
    def post(self, request, pk):
        user = User.objects.get(pk=pk)

        if user == request.user:
            return redirect("manager_user_list")

        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

        return redirect("manager_user_list")
