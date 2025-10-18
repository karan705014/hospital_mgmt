from django.contrib import admin
from .models import User, Appointment,Payment
from django.contrib.auth.hashers import make_password

# ----------------- User Admin -----------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username','name','role', 'email', 'phone')
    list_filter = ('role', 'gender')
    search_fields = ('username', 'email', 'phone','role')

    # this code is used in to changed password and also hashed in admin pannel
    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get("password"):
            obj.password = make_password(form.cleaned_data["password"])
        super().save_model(request, obj, form, change)

# ----------------- Appointment Admin -----------------
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('date','time', 'patient', 'doctor', 'status')  
    list_filter = ('status', 'date','time')  
    search_fields = ('patient__username', 'doctor__username')
    ordering = ('-date',)  
    

    # this code is used in to changed password and also hashed in admin pannel
    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get("password"):
            obj.password = make_password(form.cleaned_data["password"])
        super().save_model(request, obj, form, change)


# this code is for payment 
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id','payer_name', 'amount', 'currency')  
    list_filter = ('payment_id', 'payer_name','created_at')  
    search_fields = ('payer_name', 'payment_id')
    ordering = ('-created_at',)  
    