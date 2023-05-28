import multiprocessing
from flask_mail import Message
from app import mail
from app.config import Config


class EmailProcess(multiprocessing.Process):
    def __init__(self, email_address, email_subject, html_body):
        super(EmailProcess, self).__init__()
        self.email = email_address
        self.email_subject = email_subject
        self.html_body = html_body

    def run(self):
        print("sending email: %s" % self.email)
        sender = Config.MAIL_USERNAME
        recipients = [self.email]
        send_email(self.email_subject, sender, recipients, self.html_body)
        print("done sending")


def send_email(subject, sender, recipients, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.html = html_body
    mail.send(msg)
