from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from .models import Track, Batch, Program, Department
import csv
from .forms import BatchForm


# Create your views here.

def dashboard(request):
    # tracks = Track.objects.all()
    Programs = Program.objects.all()
    # print("Tracks: ", tracks)
    print("Programs: ", Programs)
    return render(request, 'supervisor_dashboard.html', {'Programs': Programs})

def program_details(request, program_id):
    program = get_object_or_404(Program, pk=program_id)
    tracks= Track.objects.filter(program=program)
    return render(request, 'program_details.html', {'Program': program, 'Tracks': tracks})

def track_batches(request, track_id):
    track = get_object_or_404(Track, pk=track_id)
    batches = Batch.objects.filter(track=track)
    return render(request, 'track_batches.html', {'Track': track, 'Batches': batches})

# def start_new_batch(request):
#     if request.method == 'POST':
#         form = BatchForm(request.POST, request.FILES)
#         if form.is_valid():
#             name = form.cleaned_data['name']
#             start_date = form.cleaned_data['start_date']
#             end_date = form.cleaned_data['end_date']
#             csv_file = form.cleaned_data['csv_file']
#             student_national_ids = []

#             # Read the CSV file and extract national IDs
#             decoded_file = csv_file.read().decode('utf-8').splitlines()
#             reader = csv.reader(decoded_file)
#             for row in reader:
#                 student_national_ids.append(row[0])

#             # Create a new batch
#             Batch.objects.create(
#                 name=name,
#                 start_date=start_date,
#                 end_date=end_date,
#                 status='Active',
#                 supervisor=request.user.supervisor,
#                 student_national_ids=','.join(student_national_ids)
#             )
#             return redirect('dashboard')
#     else:
#         form = BatchForm()
#     return render(request, 'batches/start_new_batch.html', {'form': form})

