# import json  # Add this import at the top
# import logging
from django.shortcuts import render, get_object_or_404 , redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic.edit import UpdateView, DeleteView
from .models import Post , Comment, Attachment  
from django.http import JsonResponse
from .forms import PostForm, CommentForm ,AttachmentForm
from django.contrib.auth.models import User
from .forms import PostForm, CommentForm 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin , LoginRequiredMixin


class PostListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.all().order_by('-created_on')
        post_form = PostForm()
        comment_form = CommentForm()
        attachment_form = AttachmentForm()

        context = {
            'post_list': posts,
            'post_form': post_form,
            'comment_form': comment_form,
            'attachment_form': attachment_form,
        }
        return render(request, 'post_list.html', context)

    def post(self, request, *args, **kwargs):
        if 'post_submit' in request.POST:
            post_form = PostForm(request.POST)
            attachment_form = AttachmentForm(request.POST, request.FILES)

            if post_form.is_valid():
                new_post = post_form.save(commit=False)
                new_post.author = request.user
                new_post.save()

                # Handle multiple attachments in one efficient loop
                for file in request.FILES.getlist('image') + request.FILES.getlist('video'):
                    attachment = Attachment.objects.create(image=file if file.content_type.startswith('image') else None, video=file if file.content_type.startswith('video') else None)
                    new_post.attachments.add(attachment)

                return redirect('post-list')

        return redirect('post-list')


class PostDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        form = CommentForm()
        comments = post.comments.all().order_by('-created_on')

        context = {'post': post, 'form': form, 'comments': comments}
        return render(request, 'post_detail.html', context)

    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        form = CommentForm(request.POST)
        attachment_form = AttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            # Handle multiple attachments
            for file in request.FILES.getlist('image') + request.FILES.getlist('video'):
                attachment = Attachment.objects.create(image=file if file.content_type.startswith('image') else None,
                                                       video=file if file.content_type.startswith('video') else None)
                comment.attachments.add(attachment)

            return redirect('post-detail', pk=post.pk)

        return render(request, 'post_detail.html', {'post': post, 'form': form})


class PostEditView(LoginRequiredMixin,UserPassesTestMixin,UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'post_edit.html'

    def get_success_url(self):
        return reverse_lazy('post-detail', kwargs={'pk': self.object.pk})


    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    
class PostDeleteView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = Post
    template_name = 'post-delete.html' 
    success_url = reverse_lazy('post-list')  
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    
class CommentEditView(LoginRequiredMixin,UserPassesTestMixin,UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'comment_edit.html'

    def get_success_url(self):
        return reverse_lazy('post-detail', kwargs={'pk': self.object.post.pk})

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    
class CommentDeleteView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = Comment
    template_name = 'comment_delete.html'

    def get_success_url(self):
        return reverse_lazy('post-detail', kwargs={'pk': self.object.post.pk})
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class AddLike(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        post.toggle_like(request.user)  # Now using model method
        return HttpResponseRedirect(request.POST.get('next', '/'))


class Dislike(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        post.toggle_dislike(request.user)  # Now using model method
        return HttpResponseRedirect(request.POST.get('next', '/'))

