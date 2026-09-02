from django.core.mail import send_mail
from django.utils import timezone

from .models import Mailing, MailingAttempt


def send_mailing(mailing: Mailing) -> None:
    now = timezone.now()

    if not mailing.start_time <= now <= mailing.end_time:
        raise ValueError(
            "Рассылку можно запустить только в разрешённый период."
        )

    attempts = []

    for recipient in mailing.recipients.all():
        try:
            result = send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=None,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            if result:
                attempts.append(
                    MailingAttempt(
                        mailing=mailing,
                        status=MailingAttempt.STATUS_SUCCESS,
                        server_response="Письмо успешно отправлено.",
                    )
                )
            else:
                attempts.append(
                    MailingAttempt(
                        mailing=mailing,
                        status=MailingAttempt.STATUS_FAILED,
                        server_response="Письмо не было отправлено.",
                    )
                )

        except Exception as exc:
            attempts.append(
                MailingAttempt(
                    mailing=mailing,
                    status=MailingAttempt.STATUS_FAILED,
                    server_response=str(exc),
                )
            )

    MailingAttempt.objects.bulk_create(attempts)