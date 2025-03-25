from django import forms
from .models import Post, Comment, Attachment

class PostForm(forms.ModelForm):
    body = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={'rows': '3', 'placeholder': 'Say something...'})
    )

    class Meta:  
        model = Post
        fields = ['body']

class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={'rows': '3', 'placeholder': 'Say something...'})
    )

    class Meta:
        model = Comment
        fields = ['comment']

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['image', 'video']

