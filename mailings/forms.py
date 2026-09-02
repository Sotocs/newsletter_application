from django import forms
from django.utils import timezone

from .models import Recipient, Message, Mailing


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ("email", "full_name", "comment")
        labels = {
            "email": "Email",
            "full_name": "Ф. И. О.",
            "comment": "Комментарий",
        }

        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "example@mail.com",
                }
            ),
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Иван Иванов",
                }
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Комментарий",
                }
            ),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("subject", "body")
        labels = {
            "subject": "Тема письма",
            "body": "Тело письма",
        }
        widgets = {
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Тема письма",
                }
            ),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "placeholder": "Введите текст письма",
                }
            ),
        }

class MailingForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label="Дата и время начала",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
                "class": "form-control",
            },
        ),
    )

    end_time = forms.DateTimeField(
        label="Дата и время окончания",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
                "class": "form-control",
            },
        ),
    )

    class Meta:
        model = Mailing
        fields = (
            "start_time",
            "end_time",
            "message",
            "recipients",
        )

        labels = {
            "message": "Сообщение",
            "recipients": "Получатели",
        }

        widgets = {
            "message": forms.Select(
                attrs={
                    "class": "form-select",
                },
            ),
            "recipients": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": 8,
                },
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["message"].queryset = Message.objects.filter(
            owner=user
        )

        self.fields["recipients"].queryset = Recipient.objects.filter(
            owner=user
        )

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and start_time < timezone.now():
            self.add_error(
                "start_time",
                "Время начала не может быть в прошлом.",
            )

        if start_time and end_time and start_time >= end_time:
            self.add_error(
                "end_time",
                "Время окончания должно быть позже времени начала.",
            )

        return cleaned_data