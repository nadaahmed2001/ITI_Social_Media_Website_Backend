from django import forms
from django.contrib.auth.forms import UserCreationForm, ModelForm 
from .models import User, Profile, Skill
from batches.models import UnverifiedNationalID, VerifiedNationalID
from django.contrib.auth.forms import AuthenticationForm


class StudentRegistrationForm(UserCreationForm):
    national_id = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "national_id"]

    def clean_national_id(self):
        national_id = self.cleaned_data["national_id"]

        # Ensure the student hasn’t already registered
        if VerifiedNationalID.objects.filter(national_id=national_id).exists():
            raise forms.ValidationError("This National ID is already registered.")
        
        # Check if the national ID is in Unverified list
        if not UnverifiedNationalID.objects.filter(national_id=national_id).exists():
            raise forms.ValidationError("This National ID is not allowed to register.")



        return national_id




class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )




class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'
        exclude = ['user', 'username', 'id', 'created', 'updated']
        
        
class SkillForm(ModelForm):
    class Meta:
        model = Skill
        fields = '__all__'
        exclude = ['owner', 'id', 'created', 'modified']
        
    def __init__(self, *args, **kwargs):
        super(SkillForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input input--text'})
            
