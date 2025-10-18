from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Appointment, User,Payment
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .emails import send_rejection_email
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests

User = get_user_model()


# Home page
def home(request):
    return render(request, "new_login_home.html")

# Registration page
def registration_detail(request):
    return render(request,"register_form.html")

#  registration data
def registration_store(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        name=request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        age = request.POST.get("age")
        gender = request.POST.get("gender")

        if password != confirm_password:
            error = "Passwords do not match!"
            return render(request, 'register_form.html', {"error": error})


        if User.objects.filter(username=username).exists():
            error = "Username already taken!"
            return render(request, 'register_form.html', {"error": error})

        user = User.objects.create_user(
            username=username,
            name=name,
            email=email,
            password=password,
            phone=phone,
            age=age,
            gender=gender,
            role='patient'
        )
        return render(request, "new_login_home.html", {"message": "You has been registered login here!"})

    else:
        return render(request, 'register_form.html',{"error": "Invalid username or password!"})
    
# Verify login
def login_verify(request):
    error=None
    if request.method=='POST':
       # role=request.POST.get("role")
        username=request.POST.get("username")
        password=request.POST.get("password")
        try:
            user = User.objects.filter(username=username).first()
            if user and check_password(password,user.password):
                request.session['user_id']=user.id
                request.session['role']=user.role

                if user.role=='patient':
                    return redirect('patient_home')
                if user.role=='doctor':
                    return redirect('doctor_home')
                if user.role=='admin':
                    return redirect('admin_home')
            else:
                error="invalid username or password"
        except User.DoesNotExist:
            error=f"no {user.role} found with this username"
    return render(request,"new_login_home.html",{"error":error})


# Patient book appointment
def book_appointment(request):
    user_id =request.session.get("user_id")
    doctors = User.objects.filter(role="doctor")

    time_slots = [
      "06:00" ,"09:00", "12:00", "15:00"
    ]
    if user_id:
        patient=get_object_or_404(User,id=user_id,role="patient")

    return render(request, "book_appointment.html", {
        "doctors": doctors,
        "time_slots": time_slots,
        "patient":patient
    })



# Doctor home
def doctor_home(request):
    user_id=request.session.get("user_id")
    if not user_id:
        return redirect('home',{"message":"no user found"})
    
    doctor=get_object_or_404(User, id=user_id, role="doctor")
    appointments=Appointment.objects.filter(doctor=doctor).order_by('-date','-time')
    return render(request,"doctor_home.html",{"appointments":appointments,"doctor":doctor})

# Doctor updates appointment status
def update_status_doctor(request, appointment_id, status):
    appt = get_object_or_404(Appointment, id=appointment_id)
    appt.status = status
    appt.save()
    if status=="rejected":
        try:
            send_rejection_email(
                patient_email=appt.patient.email,
                doctor_name =appt.doctor.name,
                date=appt.date,
                time=appt.time
            )
        except Exception as e:
              print("email sending failed:",e)
    return redirect('doctor_home')
  

# Admin home
def admin_home(request):
    user_id=request.session.get("user_id")
    if not user_id:
        return redirect('home',{"message":"user not found"})
    return render(request, "admin_home.html")

def adminpage_logout(request):
    request.session.flush()
    return redirect("home")


# Admin dashboard
def admin_dashboard(request):
    appointments = Appointment.objects.all().order_by('-id')
    return render(request, "admin_dashboard.html", {"appointments": appointments})


def update_status(request, appointment_id, status):
    appointments= get_object_or_404(Appointment, id=appointment_id)
    appointments.status = status
    appointments.save()

    if status == "rejected":
        try:
          
            send_rejection_email(
                patient_email=appointments.patient.email,
                doctor_name=appointments.doctor.name,
                date=appointments.date,
                time=appointments.time
            )

            
            try:
                payment = Payment.objects.get(appointments=appointments)
                process_refund(payment.payment_id)
            except Payment.DoesNotExist:
                print("No payment found for this appointment.")

        except Exception as e:
            print("Error in refund/email:", e)

    return redirect("admin_dashboard")  

   
    

# Manage doctors
def doctor_add_page(request):
    doctors=User.objects.filter(role="doctor")
    return render(request,"doctor_add_page.html",{"doctors":doctors})


def delete_doctor(request, doctor_id):
    doctors=User.objects.get(id=doctor_id)
    doctors.delete()
    return redirect('doctor_add_page')


def add_doctor(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        name = request.POST.get("name")
        email = request.POST.get("email")
        speciality = request.POST.get("speciality")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        gender = request.POST.get("gender")

        try:
            doctor = User.objects.create(
                username=username,
                name=name,
                email=email,
                phone=phone,
                speciality=speciality,
                gender=gender,
                role='doctor'   
            )
            doctor.set_password(password)  
            doctor.save()
            return redirect('doctor_add_page')

        except Exception as K:
            error = f"Something went wrong: {str(K)}"
            return render(request, "doctor_add_page.html", {"error": error})
        
    return render(request, "doctor_add_page.html")


# Doctor logout
def doctor_logout(request):
    request.session.flush()
    return redirect('home')


#admin-manage patient
def patient_add_page(request):
    patients=User.objects.filter(role="patient")
    return render(request,"patient_add_page.html",{"patients":patients})


#admin-delete patient
def delete_patient(request,patient_id):
    patients=User.objects.get(id=patient_id)
    patients.delete()
    return redirect('patient_add_page')


#admin-add patient
def add_patient(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        gender = request.POST.get("gender")

        try:
            patient = User.objects.create(
                username=username,
                name=name,
                email=email,
                phone=phone,
                gender=gender
            )
            patient.set_password(password)  
            patient.save()
            return redirect('patient_add_page')

        except Exception as k:
            error = f"Something went wrong: {str(k)}"
            return render(request, "patient_add_page.html", {"error": error})

    return render(request, "patient_add_page.html")


#add new page in which patient have option of cheak status and book appointment

def patient_home(request):
  user_id=request.session.get("user_id")
  patient=get_object_or_404(User,id=user_id,role="patient")
  return render(request,"patient_home.html", {"patient":patient})


def patient_status(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('home') 
    appointments = Appointment.objects.filter(patient_id=user_id).order_by('-id')
    return render(request, "status_page.html", {"appointments": appointments})


# here is the backend of bookappointment

@csrf_exempt
def appointment_store_paypal(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            user_id = request.session.get('user_id')
            if not user_id:
                return JsonResponse({'success': False, 'error': 'User not logged in'})

            patient = get_object_or_404(User, id=user_id, role='patient')
            doctor = get_object_or_404(User, id=data['doctor_id'], role='doctor')

            # check if slot already booked
            exists = Appointment.objects.filter(
                doctor=doctor,
                date=data['date'],
                time=data['time']
            ).exists()

            if exists:
                return JsonResponse({'success': False, 'error': 'This slot is already booked!'})

            # create appointment
            appt = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=data['date'],
                time=data['time'],
                status='approved'
            )

            # create payment record
            Payment.objects.create(
                appointments=appt,
                payment_id=data['payment_id'],
                payer_name=data['payer_name'],
                payer_email=data['payer_email'],
                amount=data['payment_amount'],
                currency=data['payment_currency']
            )

            # send confirmation emails
            subject_patient = "Appointment confirmed"
            message_patient = f"Dear {patient.name},\n\nYour appointment with Dr. {doctor.name} has been booked on {data['date']} at {data['time']}.\n\nPayment ID: {data['payment_id']}"
            send_mail(subject_patient, message_patient, settings.EMAIL_HOST_USER, [patient.email], fail_silently=True)

            subject_doctor = "New Appointment Alert"
            message_doctor = f"Dear Dr. {doctor.name},\n\nYou have a new appointment booked by {patient.name} ({patient.email}) on {data['date']} at {data['time']}.\n\nPayment ID: {data['payment_id']}"
            send_mail(subject_doctor, message_doctor, settings.EMAIL_HOST_USER, [doctor.email], fail_silently=True)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# showing payment details for admin

def admin_payment_details(request):
    payments = Payment.objects.all().order_by("-created_at")
    return render(request, "payment_details.html", {"payments": payments})




def process_refund(payment_id):
    payment = Payment.objects.get(payment_id=payment_id)
    if not payment:
       raise Exception("Payment record not found")

    auth_response = requests.post(
        "https://api-m.sandbox.paypal.com/v1/oauth2/token",
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET)
    )

    token = auth_response.json().get("access_token")
    if not token:
        raise Exception("Failed to retrieve PayPal token")

    refund_response = requests.post(
        f"https://api-m.sandbox.paypal.com/v2/payments/captures/{payment_id}/refund",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        json={
            "amount": {
                "value": str(payment.amount),
                "currency_code": payment.currency
            }
        }
    )

    if refund_response.status_code in [200,201]:
        payment.status = "refunded"
        payment.save()
        return True
    else:
        raise Exception(refund_response.text)


        



###############################   END     ################################