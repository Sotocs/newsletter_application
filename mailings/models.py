from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Recipient(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"


class Message(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "Письмо"
        verbose_name_plural = "Письма"


class Mailing(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="mailings",
    )
    recipients = models.ManyToManyField(
        Recipient,
        related_name="mailings",
    )
    is_active = models.BooleanField(default=True)

    def clean(self):
        errors = {}

        if self.start_time < timezone.now():
            errors["start_time"] = "Время начала не может быть в прошлом."

        if self.start_time >= self.end_time:
            errors["end_time"] = "Время окончания должно быть позже времени начала."

        if errors:
            raise ValidationError(errors)

    @property
    def status(self):
        now = timezone.now()

        if not self.is_active:
            return "Отключена"

        if now < self.start_time:
            return "Создана"

        if self.start_time <= now <= self.end_time:
            return "Запущена"

        return "Завершена"

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"


class MailingAttempt(models.Model):
    STATUS_SUCCESS = "Успешно"
    STATUS_FAILED = "Не успешно"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    attempt_time = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
    )

    server_response = models.TextField(blank=True)

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    def __str__(self):
        return f"{self.mailing} — {self.status}"

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
