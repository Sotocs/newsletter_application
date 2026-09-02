from users.models import User
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.core.cache import cache
from users.mixins import ManagerRequiredMixin
from .services import send_mailing
from django.utils import timezone
from .forms import MailingForm, MessageForm, RecipientForm
from .models import Mailing, MailingAttempt, Message, Recipient
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator

def clear_home_statistics_cache():
    cache.delete("home_statistics")


class RecipientListView(LoginRequiredMixin, View):
    def get(self, request):
        recipients = Recipient.objects.filter(
            owner=request.user
        )

        return render(
            request,
            "mailings/recipient_list.html",
            {"recipients": recipients},
        )


class RecipientCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = RecipientForm()

        return render(
            request,
            "mailings/recipient_form.html",
            {"form": form},
        )

    def post(self, request):
        form = RecipientForm(request.POST)

        if form.is_valid():
            recipient = form.save(commit=False)
            recipient.owner = request.user
            recipient.save()

            clear_home_statistics_cache()

            return redirect("recipient_list")

        return render(
            request,
            "mailings/recipient_form.html",
            {"form": form},
        )


class RecipientUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        recipient = get_object_or_404(
            Recipient,
            pk=pk,
            owner=request.user,
        )

        form = RecipientForm(instance=recipient)

        return render(
            request,
            "mailings/recipient_form.html",
            {
                "form": form,
                "recipient": recipient,
            },
        )

    def post(self, request, pk):
        recipient = get_object_or_404(
            Recipient,
            pk=pk,
            owner=request.user,
        )

        form = RecipientForm(
            request.POST,
            instance=recipient,
        )

        if form.is_valid():
            form.save()
            clear_home_statistics_cache()

            return redirect("recipient_list")

        return render(
            request,
            "mailings/recipient_form.html",
            {
                "form": form,
                "recipient": recipient,
            },
        )


class RecipientDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        recipient = get_object_or_404(
            Recipient,
            pk=pk,
            owner=request.user,
        )

        return render(
            request,
            "mailings/recipient_confirm_delete.html",
            {"recipient": recipient},
        )

    def post(self, request, pk):
        recipient = get_object_or_404(
            Recipient,
            pk=pk,
            owner=request.user,
        )

        recipient.delete()

        clear_home_statistics_cache()

        return redirect("recipient_list")


class MailingSendView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mailing = get_object_or_404(
            Mailing,
            pk=pk,
            owner=request.user,
        )

        if not mailing.is_active:
            messages.error(
                request,
                "Эта рассылка отключена менеджером.",
            )
            return redirect(
                "mailing_detail",
                pk=mailing.pk,
            )

        try:
            send_mailing(mailing)
            clear_home_statistics_cache()

            messages.success(
                request,
                "Рассылка успешно запущена.",
            )

        except ValueError as exc:
            messages.error(
                request,
                str(exc),
            )

        return redirect(
            "mailing_detail",
            pk=mailing.pk,
        )

class MessageListView(LoginRequiredMixin, View):
    def get(self, request):
        messages_list = Message.objects.filter(
            owner=request.user
        )

        return render(
            request,
            "mailings/message_list.html",
            {"messages_list": messages_list},
        )

class MessageCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = MessageForm()

        return render(
            request,
            "mailings/message_form.html",
            {"form": form},
        )

    def post(self, request):
        form = MessageForm(request.POST)

        if form.is_valid():
            message = form.save(commit=False)
            message.owner = request.user
            message.save()

            return redirect("message_list")

        return render(
            request,
            "mailings/message_form.html",
            {"form": form},
        )

class MessageUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        message = get_object_or_404(
            Message,
            pk=pk,
            owner=request.user,
        )

        form = MessageForm(instance=message)

        return render(
            request,
            "mailings/message_form.html",
            {
                "form": form,
                "message": message,
            },
        )

    def post(self, request, pk):
        message = get_object_or_404(
            Message,
            pk=pk,
            owner=request.user,
        )

        form = MessageForm(
            request.POST,
            instance=message,
        )

        if form.is_valid():
            form.save()

            return redirect("message_list")

        return render(
            request,
            "mailings/message_form.html",
            {
                "form": form,
                "message": message,
            },
        )

class MessageDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        message = get_object_or_404(
            Message,
            pk=pk,
            owner=request.user,
        )

        return render(
            request,
            "mailings/message_confirm_delete.html",
            {"message": message},
        )

    def post(self, request, pk):
        message = get_object_or_404(
            Message,
            pk=pk,
            owner=request.user,
        )

        message.delete()

        return redirect("message_list")

@method_decorator(
    cache_control(
        max_age=60,
        private=True,
    ),
    name="dispatch",
)
class HomeView(View):
    def get(self, request):
        cache_key = "home_statistics"

        statistics = cache.get(cache_key)

        if statistics is None:
            now = timezone.now()

            statistics = {
                "total_mailings": Mailing.objects.count(),
                "active_mailings": Mailing.objects.filter(
                    start_time__lte=now,
                    end_time__gte=now,
                    is_active=True,
                ).count(),
                "total_recipients": Recipient.objects.values(
                    "email"
                ).distinct().count(),
                "total_attempts": MailingAttempt.objects.count(),
                "successful_attempts": MailingAttempt.objects.filter(
                    status=MailingAttempt.STATUS_SUCCESS,
                ).count(),
                "failed_attempts": MailingAttempt.objects.filter(
                    status=MailingAttempt.STATUS_FAILED,
                ).count(),
            }

            cache.set(
                cache_key,
                statistics,
                timeout=60,
            )

        return render(
            request,
            "mailings/home.html",
            statistics,
        )

class MailingListView(LoginRequiredMixin, View):
    def get(self, request):
        mailings = (
            Mailing.objects
            .select_related("message", "owner")
            .prefetch_related("recipients")
        )

        if request.user.role != User.Role.MANAGER:
            mailings = mailings.filter(owner=request.user)

        return render(
            request,
            "mailings/mailing_list.html",
            {
                "mailings": mailings,
            },
        )

class MailingCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = MailingForm(user=request.user)

        return render(
            request,
            "mailings/mailing_form.html",
            {
                "form": form,
            },
        )

    def post(self, request):
        form = MailingForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            mailing = form.save(commit=False)
            mailing.owner = request.user
            mailing.save()
            form.save_m2m()

            clear_home_statistics_cache()

            return redirect(
                "mailing_detail",
                pk=mailing.pk,
            )

        return render(
            request,
            "mailings/mailing_form.html",
            {
                "form": form,
            },
        )

class MailingDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        mailing = get_object_or_404(
            Mailing.objects
            .select_related("message", "owner")
            .prefetch_related("recipients"),
            pk=pk,
        )

        if (
            mailing.owner != request.user
            and request.user.role != User.Role.MANAGER
        ):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied

        return render(
            request,
            "mailings/mailing_detail.html",
            {
                "mailing": mailing,
            },
        )

class MailingUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        mailing = get_object_or_404(
            Mailing,
            pk=pk,
            owner=request.user,
        )

        form = MailingForm(
            instance=mailing,
            user=request.user,
        )

        return render(
            request,
            "mailings/mailing_form.html",
            {
                "form": form,
                "mailing": mailing,
            },
        )

    def post(self, request, pk):
        mailing = get_object_or_404(
            Mailing,
            pk=pk,
            owner=request.user,
        )

        form = MailingForm(
            request.POST,
            instance=mailing,
            user=request.user,
        )

        if form.is_valid():
            form.save()

            clear_home_statistics_cache()

            return redirect(
                "mailing_detail",
                pk=mailing.pk,
            )

        return render(
            request,
            "mailings/mailing_form.html",
            {
                "form": form,
                "mailing": mailing,
            },
        )

class MailingDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        mailing = get_object_or_404(
            Mailing,
            pk=pk,
            owner=request.user,
        )

        return render(
            request,
            "mailings/mailing_confirm_delete.html",
            {
                "mailing": mailing,
            },
        )

    def post(self, request, pk):
        mailing = get_object_or_404(
            Mailing,
            pk=pk,
            owner=request.user,
        )

        mailing.delete()

        clear_home_statistics_cache()

        return redirect("mailing_list")

class MailingAttemptListView(LoginRequiredMixin, View):
    def get(self, request, pk):
        mailing = get_object_or_404(
            Mailing,
            pk=pk,
            owner=request.user,
        )

        attempts = mailing.attempts.all().order_by("-attempt_time")

        return render(
            request,
            "mailings/mailing_attempt_list.html",
            {
                "mailing": mailing,
                "attempts": attempts,
            },
        )

class MailingDisableView(
    LoginRequiredMixin,
    ManagerRequiredMixin,
    View,
):
    def post(self, request, pk):
        mailing = get_object_or_404(
            Mailing,
            pk=pk,
        )

        mailing.is_active = not mailing.is_active
        mailing.save(update_fields=["is_active"])

        clear_home_statistics_cache()

        if mailing.is_active:
            messages.success(
                request,
                "Рассылка включена.",
            )
        else:
            messages.success(
                request,
                "Рассылка отключена.",
            )

        return redirect(
            "mailing_detail",
            pk=mailing.pk,
        )