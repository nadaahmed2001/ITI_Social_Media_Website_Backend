from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import StudentRegistrationForm
from .models import User
from batches.models import Student, StudentBatch
from django.contrib.auth import authenticate
from batches.models import UnverifiedNationalID, VerifiedNationalID
from django.contrib import messages
from .forms import CustomLoginForm
from django.contrib.auth import authenticate
from .decorators import student_required



# Create your views here.
def supervisor_login_view(request):
    print("I'm now inside the supervisor login view")
    if request.method == "POST":
        print("I'm now inside the post method")
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            print("Form is valid")
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            print("Username: ", username)
            print("Password: ", password)
            user = authenticate(request, username=username, password=password)
            print("User is authenticated: ", user)

            if user is not None and user.is_supervisor:
                login(request, user)
                messages.success(request, "Login successful!")
                return redirect("supervisor_dashboard")  # Redirect to supervisor dashboard
            else:
                messages.error(request, "Invalid credentials or not a supervisor.")
        else:
            print("Form errors:", form.errors)  # Debugging: Print form errors
            messages.error(request, "Invalid form submission.")
    else:
        form = CustomLoginForm()

    return render(request, "users/supervisor_login.html", {"form": form})

def supervisor_logout(request):
    logout(request)
    return redirect("supervisor_login")



def student_register(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_student = True
            user.save()

            # Create a student profile
            student = Student.objects.create(user=user)

            # Get national ID and batch
            national_id = form.cleaned_data["national_id"]
            try:
                unverified_entry = UnverifiedNationalID.objects.get(national_id=national_id)
                batch = unverified_entry.batch  # Get batch from unverified entry
                
                if batch is None:
                    messages.error(request, "No batch assigned to this National ID. Contact admin.")
                    return render(request, "student/student_register.html", {"form": form})

                # Move the national ID to the verified list
                VerifiedNationalID.objects.create(national_id=national_id, batch=batch)

                # Assign student to the batch
                StudentBatch.objects.create(student=student, batch=batch)

                # Remove from the unverified list
                unverified_entry.delete()

                messages.success(request, "Account created successfully.")
                return redirect("student_login")

            except UnverifiedNationalID.DoesNotExist:
                messages.error(request, "This National ID is not allowed to register.")
                return render(request, "student/student_register.html", {"form": form})

    else:
        form = StudentRegistrationForm()

    return render(request, "student/student_register.html", {"form": form})



def student_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_student:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect("student_dashboard")  # Redirect to student dashboard
        else:
            messages.error(request, "Invalid credentials or not a student account.")

    return render(request, "student/student_login.html")


def student_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("student_login")

@student_required
def student_dashboard(request):
    user=request.user
    return render(request, "student/student_dashboard.html", {"user": user})