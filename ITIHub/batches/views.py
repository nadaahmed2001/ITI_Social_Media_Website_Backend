from django.shortcuts import render, get_object_or_404, redirect
from .models import Track, Batch, Program, Department
import csv
# from .forms import BatchForm
from .models import UnverifiedNationalID, Batch
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
import csv
from users.decorators import supervisor_required
from django.contrib import messages
from .forms import BatchForm
from django.http import HttpResponse




# Create your views here.

@supervisor_required
def dashboard(request):
    print("I'm now inside the supervisor dashboard")
    # tracks = Track.objects.all()
    Programs = Program.objects.all()
    # print("Tracks: ", tracks)
    print("Programs: ", Programs)
    user=request.user
    return render(request, 'supervisor_dashboard.html', {'Programs': Programs, 'User': user})

def program_details(request, program_id):
    print("I'm now inside the program details")
    program = get_object_or_404(Program, pk=program_id)
    tracks= Track.objects.filter(program=program)
    return render(request, 'program_details.html', {'Program': program, 'Tracks': tracks})

def track_batches(request, track_id):
    track = get_object_or_404(Track, pk=track_id)
    batches = Batch.objects.filter(track=track)
    return render(request, 'track_batches.html', {'Track': track, 'Batches': batches})





@supervisor_required
def create_batch(request):
    if request.method == "POST":
        form = BatchForm(request.POST, request.FILES)
        if form.is_valid():
            batch = form.save(commit=False)
            # batch.supervisor = request.user  # Assign logged-in supervisor
            batch.status = "Active"
            batch.save()

            # Process CSV file if uploaded
            csv_file = request.FILES.get("csv_file")
            if csv_file:
                decoded_file = csv_file.read().decode("utf-8").splitlines()
                reader = csv.reader(decoded_file)
                for row in reader:
                    national_id = row[0].strip()
                    UnverifiedNationalID.objects.create(national_id=national_id, batch=batch)

            messages.success(request, "Batch created successfully!")
            return redirect("supervisor_dashboard")  # Redirect to dashboard

    else:
        form = BatchForm()

    tracks = Track.objects.all()
    return render(request, "create_batch.html", {"form": form, "tracks": tracks})
