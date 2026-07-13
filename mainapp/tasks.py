import os
import smtplib
from email.utils import formatdate, make_msgid

from celery import shared_task

from django.contrib.auth.tokens import default_token_generator
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from email.message import EmailMessage
import logging

logger = logging.getLogger(__name__)


@shared_task
def email_activation_compte(domaine,user_email,new_password):
    from .models import User
    url_logo = f"http://{domaine}/static/mainapp/logo/logo_AFG_Bank.png"
    try:
        user = User.objects.get(email=user_email)
        corps = render_to_string(
            "activation_compte.html",
            {'user': user,'domaine':domaine,
             'url_logo': 'cid:logo_afg',
             "uid": urlsafe_base64_encode(force_bytes(user.id)),
             "token": default_token_generator.make_token(user),
             "password": new_password}
            )
        to = user_email
        msg = EmailMessage()
        msg['From'] = os.environ.get('SENDER_EMAIL')
        msg['To'] = to
        msg['Subject'] = 'Création de compte utilisateur'
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()
        msg.set_content(
            "Votre compte a été créé. Ouvrez cet e-mail dans un client compatible HTML "
            "pour activer votre compte."
        )
        msg.add_alternative(corps, subtype='html')

        logo_path = finders.find('mainapp/logo/logo_AFG_Bank.png')
        if logo_path:
            with open(logo_path, 'rb') as f:
                msg.get_payload()[1].add_related(
                    f.read(), maintype='image', subtype='png', cid='logo_afg'
                )

        with smtplib.SMTP(os.environ.get('SMTP_SERVER'), int(os.environ.get('SMTP_PORT'))) as server:
            server.starttls()
            server.login(os.environ.get('SENDER_EMAIL'), os.environ.get('EMAIL_PASSWORD'))
            server.send_message(msg)
            logger.info(f"Email envoyé avec succès.")
    except Exception as e:
        logger.error(f"Echec de l'envoi de l'email: {e}")