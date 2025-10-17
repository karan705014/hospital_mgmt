from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Appointment, User
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .emails import send_rejection_email


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


def appointment_store(request):
    doctors=User.objects.filter(role="doctor")
    user_id = request.session.get("user_id")
    if not user_id:
        return render(request, "book_appointment.html", {
            "doctors": doctors,
            "message": "Please login first"
        })

    user = get_object_or_404(User, role="patient", id=user_id)

    if request.method=='POST':
        doctor_id=request.POST.get("doctors")
        time=request.POST.get("time")
        date=request.POST.get("date")
        doctor=User.objects.get(id=doctor_id, role="doctor")

        exists = Appointment.objects.filter(
            doctor_id=doctor_id,
            date=date,
            time=time
        ).exists()

        if exists:
            messages.error(request, "this slot has been already booked !")
            return redirect("book_appointment")

        if user.role=="patient":
            Appointment.objects.create(
                patient=user,
                doctor=doctor,
                date=date,
                time=time
            )
            subject_patient = "appointment confirmation"
            message_patient = f"Dear {user.name},\n\nYour appointment with Dr. {doctor.name} has been booked on {date} at {time}.\n\nThank you!"
            send_mail(subject_patient,message_patient,settings.EMAIL_HOST_USER,[user.email],fail_silently=True)


            subject_doctor = "New Appointment Alert"
            message_doctor = f"Dear Dr. {doctor.name},\n\nYou have a new appointment booked by {user.name} ({user.email}) on {date} at {time}.\n\nPlease check your dashboard for details."
            send_mail(subject_doctor, message_doctor, settings.EMAIL_HOST_USER, [doctor.email], fail_silently=True)



            messages.success(request, "Your appointment has been booked! Once approved, your status will be updated.")
            return redirect('patient_home') 
        else:
            return render(request,"book_appointment.html",{
                "doctors":doctors,
                "message":"only patient can login here"
            })
    return render(request,"book_appointment.html")


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
    appointments=get_object_or_404(Appointment, id=appointment_id)
    appointments.status=status
    appointments.save()

    if status=="rejected":
        try:
            send_rejection_email(
                patient_email=appointments.patient.email,
                doctor_name =appointments.doctor.name,
                date=appointments.date,
                time=appointments.time
            )
        except Exception as e:
            print("email sending failed:",e)
    return redirect('admin_dashboard')


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
    return render(request,"patient_home.html")

def patient_status(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('home') 
    appointments = Appointment.objects.filter(patient_id=user_id).order_by('-id')
    return render(request, "status_page.html", {"appointments": appointments})




###############################   END     ################################