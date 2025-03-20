from django import forms

class BatchForm(forms.Form):
    name = forms.CharField(max_length=100)
    start_date = forms.DateField(widget=forms.SelectDateWidget)
    end_date = forms.DateField(widget=forms.SelectDateWidget, required=False)
    csv_file = forms.FileField()