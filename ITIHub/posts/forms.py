from django import forms
from .models import Post ,Comment, Attachment

class PostForm(forms.ModelForm):
    body = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'rows': '3',
            'placeholder': 'Say something...'
        })
    )

    class Meta:  
        model = Post
        fields = ['body']



class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        label='',
        widget = forms.Textarea(attrs={
            'rows':'3',
            'placeholder':'say something....'
        })
    )
       
    class Meta:
        model = Comment
        fields = ['comment']

 
 
class PostForm(forms.ModelForm):
    image = forms.ImageField(required=False)
    video = forms.FileField(required=False)

    class Meta:
        model = Post
        fields = ['body', 'image', 'video']

class CommentForm(forms.ModelForm):
    image = forms.ImageField(required=False)
    video = forms.FileField(required=False)

    class Meta:
        model = Comment
        fields = ['comment', 'image', 'video']
