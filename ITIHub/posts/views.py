from django.shortcuts import render, get_object_or_404 , redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import UpdateView, DeleteView
from .models import Post , Comment, Attachment 
from django.http import JsonResponse
from .forms import PostForm, CommentForm
from django.contrib.auth.models import User
from .forms import PostForm, CommentForm 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin , LoginRequiredMixin


class PostListView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.all().order_by('-created_on')
        post_form = PostForm()
        comment_form = CommentForm()
        context = {
            'post_list': posts,
            'post_form': post_form,
            'comment_form': comment_form,
        }
        return render(request, 'post_list.html', context)

    def post(self, request, *args, **kwargs):
        if 'post_submit' in request.POST:  # Handle post submission
            post_form = PostForm(request.POST)
            if post_form.is_valid():
                new_post = post_form.save(commit=False)
                new_post.author = request.user if request.user.is_authenticated else None
                new_post.save()

        elif 'comment_submit' in request.POST:  # Handle comment submission
            post_id = request.POST.get('post_id')
            post = get_object_or_404(Post, id=post_id)
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.author = request.user if request.user.is_authenticated else None
                new_comment.post = post
                new_comment.save()

        return redirect('post-list')  # Redirect to the same page to display updates
    
class PostDetailView(LoginRequiredMixin,View):
    def get(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        form = CommentForm()
        comments = post.comments.all().order_by('-created_on')

        context = {'post': post, 'form': form, 'comments': comments}
        return render(request, 'post_detail.html', context)

    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        form = CommentForm(request.POST)
        if request.method == "POST":
          if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            if request.user.is_authenticated:
                comment.author = request.user  
            else:
                comment.author = None  
            comment.save()
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
  

class AddLike(LoginRequiredMixin , View):
    def post(self , request , pk , *args , **kwargs):
        post = Post.objects.get(pk=pk)
        
        is_like = False
    
        for like in post.likes.all():
            if like == request.user:
                is_like = True
                break

        if not is_like :
            post.likes.add(request.user)

        if is_like:
            post.likes.remove(request.user)

# class Dislike(LoginRequiredMixin , View):
#     def post(self , request , pk , *args , **kwargs):
#         post = Post.objects.get(pk=pk)

#         is_dislike = False

#         for dislike in post.dislike.all():
#             if dislike == request.user:
#                 is_dislike = True
#                 break

#         if not
