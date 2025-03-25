from django.shortcuts import render, get_object_or_404 , redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic.edit import UpdateView, DeleteView
from .models import Post , Comment, Attachment  , Reaction
from django.http import JsonResponse
from .forms import PostForm, CommentForm ,AttachmentForm
from django.contrib.auth.models import User
from .forms import PostForm, CommentForm 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin , LoginRequiredMixin

class PostListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.all().order_by('-created_on')
        for post in posts:
            post.reaction_counts = {
                'Like': post.reaction_set.filter(reaction_type='Like').count(),
                'Heart': post.reaction_set.filter(reaction_type='Heart').count(),
                'Celebrate': post.reaction_set.filter(reaction_type='Celebrate').count(),
                'Laugh': post.reaction_set.filter(reaction_type='Laugh').count(),
                'Insightful': post.reaction_set.filter(reaction_type='Insightful').count(),
                'Support': post.reaction_set.filter(reaction_type='Support').count(),
            }
        
        context = {
            'post_list': posts,
            'post_form': PostForm(),
            'comment_form': CommentForm(),
            'attachment_form': AttachmentForm(),
        }
        return render(request, 'post_list.html', context)
    
    def post(self, request, *args, **kwargs):
        if 'post_submit' in request.POST:
            post_form = PostForm(request.POST)
            if post_form.is_valid():
                new_post = post_form.save(commit=False)
                new_post.author = request.user
                new_post.save()
                for file in request.FILES.getlist('image'):
                    Attachment.objects.create(image=file, post=new_post)
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

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            # Handle multiple attachments
            for file in request.FILES.getlist('image'):
                attachment = Attachment.objects.create(image=file)
                comment.attachments.add(attachment)

            for file in request.FILES.getlist('image'):
                 attachment = Attachment.objects.create(image=file, comment=comment)


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

class AddReaction(LoginRequiredMixin, View):
    def post(self, request, post_id, reaction_type, *args, **kwargs):
        post = get_object_or_404(Post, id=post_id)

        # Check if the user has already reacted to this post
        existing_reaction = Reaction.objects.filter(user=request.user, post=post).first()

        if existing_reaction:
            # If the reaction is the same, remove it (toggle behavior)
            if existing_reaction.reaction_type == reaction_type:
                existing_reaction.delete()
                return redirect(request.POST.get('next', '/'))
            else:
                # Update reaction if it's different
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
        else:
            # Create new reaction
            Reaction.objects.create(user=request.user, post=post, reaction_type=reaction_type)

        return redirect(request.POST.get('next', '/'))

class RemoveReaction(LoginRequiredMixin, View):
    def post(self, request, post_id, *args, **kwargs):
        post = get_object_or_404(Post, id=post_id)
        Reaction.objects.filter(user=request.user, post=post).delete()
        return redirect(request.POST.get('next', '/'))
    
# class AddLike(LoginRequiredMixin, View):
#     def post(self, request, pk, *args, **kwargs):
#         post = Post.objects.get(pk=pk)
    
#         is_dislike = False
#         for dislike in post.dislikes.all():  # ✅ Fix here (post.dislike → post.dislikes)
#             if dislike == request.user:
#                 is_dislike = True
#                 break
#         if is_dislike:
#             post.dislikes.remove(request.user)  # ✅ Fix here too

#         is_like = False
#         for like in post.likes.all():
#             if like == request.user:
#                 is_like = True
#                 break

#         if not is_like:
#             post.likes.add(request.user)

#         if is_like:
#             post.likes.remove(request.user)
        
#         next_url = request.POST.get('next', '/')
#         return HttpResponseRedirect(next_url)

# class Dislike(LoginRequiredMixin, View):
#     def post(self, request, pk, *args, **kwargs):
#         post = Post.objects.get(pk=pk)

#         is_like = False
#         for like in post.likes.all():
#             if like == request.user:
#                 is_like = True
#                 break
#         if is_like:
#             post.likes.remove(request.user)

#         is_dislike = False
#         for dislike in post.dislikes.all():  # ✅ Fix here (post.dislike → post.dislikes)
#             if dislike == request.user:
#                 is_dislike = True
#                 break

#         if not is_dislike:
#             post.dislikes.add(request.user)  # ✅ Fix here too

#         if is_dislike:
#             post.dislikes.remove(request.user)  # ✅ Fix here too

#         next_url = request.POST.get('next', '/')
#         return HttpResponseRedirect(next_url)
