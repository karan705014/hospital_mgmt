from django.core.mail import send_mail
from django.conf import settings

def send_rejection_email(patient_email, doctor_name, date, time):
    subject = "Appointment Rejected"
    message = f"""
Hello,

Your appointment with Dr. {doctor_name} on {date} at {time} has been rejected.

“Your appointment has been rejected due to unavailability of doctor.”

"""
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [patient_email],
        fail_silently=False
    )
