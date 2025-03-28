from django.shortcuts import render, get_object_or_404 , redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic.edit import UpdateView, DeleteView
from .models import Post , Comment, Attachment  , Reaction
from django.http import JsonResponse
from .forms import PostForm, CommentForm ,AttachmentForm 
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin , LoginRequiredMixin
from django.db import IntegrityError  # Add this import

class PostListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.prefetch_related('reaction_set', 'comments__reaction_set').order_by('-created_on')
        
        for post in posts:
            post.reaction_counts = {
                'Like': post.reaction_set.filter(reaction_type='Like').count(),
                'Heart': post.reaction_set.filter(reaction_type='Heart').count(),
                'Celebrate': post.reaction_set.filter(reaction_type='Celebrate').count(),
                'Laugh': post.reaction_set.filter(reaction_type='Laugh').count(),
                'Insightful': post.reaction_set.filter(reaction_type='Insightful').count(),
                'Support': post.reaction_set.filter(reaction_type='Support').count(),
            }
            
            for comment in post.comments.all():
                comment.reaction_counts = {
                    'Like': comment.reaction_set.filter(reaction_type='Like').count(),
                    'Heart': comment.reaction_set.filter(reaction_type='Heart').count(),
                    'Celebrate': comment.reaction_set.filter(reaction_type='Celebrate').count(),
                    'Laugh': comment.reaction_set.filter(reaction_type='Laugh').count(),
                    'Insightful': comment.reaction_set.filter(reaction_type='Insightful').count(),
                    'Support': comment.reaction_set.filter(reaction_type='Support').count(),
                }
        
        context = {
            'post_list': posts,
            'post_form': PostForm(),
            'comment_form': CommentForm(),
            'attachment_form': AttachmentForm(),
        }
        return render(request, 'post_list.html', context)
    
    def post(self, request, *args, **kwargs):
        # views.py (PostListView's post method)
        if 'post_submit' in request.POST:
            post_form = PostForm(request.POST)
            if post_form.is_valid():
                new_post = post_form.save(commit=False)
                new_post.author = request.user
                new_post.save()

                # Handle single image upload
                image_file = request.FILES.get('image')  # Use 'get()' for single file
                if image_file:
                    attachment = Attachment.objects.create(image=image_file)
                    new_post.attachments.add(attachment)  # Link via ManyToMany

                return redirect('post-list')
        # if 'post_submit' in request.POST:
        #     post_form = PostForm(request.POST)
        #     if post_form.is_valid():
        #         new_post = post_form.save(commit=False)
        #         new_post.author = request.user
        #         new_post.save()
        #         for file in request.FILES.getlist('image'):
        #             Attachment.objects.create(image=file, post=new_post)
        #         return redirect('post-list')

        elif 'comment_submit' in request.POST:
            comment_form = CommentForm(request.POST)
            post_id = request.POST.get('post_id')  # Get post ID from hidden field
            post = get_object_or_404(Post, id=post_id)

            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.author = request.user
                new_comment.post = post
                new_comment.save()

                # Save attachments if provided
                for file in request.FILES.getlist('image'):
                    attachment = Attachment.objects.create(image=file)
                    new_comment.attachments.add(attachment)

                return redirect('post-list')  # Redirect back to the home page

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
    def post(self, request, *args, **kwargs):
        reaction_type = kwargs.get('reaction_type')  # Get from URL parameter
        post_id = kwargs.get('post_id', None)
        comment_id = kwargs.get('comment_id', None)

        try:
            if post_id:
                # Handle post reaction
                post = get_object_or_404(Post, id=post_id)
                reaction, created = Reaction.objects.update_or_create(
                    user=request.user,
                    post=post,
                    comment=None,
                    defaults={'reaction_type': reaction_type}
                )
            elif comment_id:
                # Handle comment reaction
                comment = get_object_or_404(Comment, id=comment_id)
                reaction, created = Reaction.objects.update_or_create(
                    user=request.user,
                    comment=comment,
                    post=None,
                    defaults={'reaction_type': reaction_type}
                )
            return redirect(request.META.get('HTTP_REFERER', 'post-list'))
            
        except IntegrityError as e:
            # Handle any remaining constraints
            return redirect(request.META.get('HTTP_REFERER', 'post-list'))
    
class ViewCommentReactions(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs.get('comment_id'))
        reactions = Reaction.objects.filter(comment=comment).select_related('user')
        return render(request, 'viewReactions-comment.html', {
            'comment': comment,
            'reactions': reactions
        })
    ##############################
class RemoveReaction(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id', None)
        comment_id = kwargs.get('comment_id', None)

        if post_id:
            post = get_object_or_404(Post, id=post_id)
            Reaction.objects.filter(user=request.user, post=post).delete()
        elif comment_id:
            comment = get_object_or_404(Comment, id=comment_id)
            Reaction.objects.filter(user=request.user, comment=comment).delete()

        return JsonResponse({'success': True})  # Return JSON response


# class RemoveReaction(LoginRequiredMixin, View):
#     def post(self, request, *args, **kwargs):
#         post_id = kwargs.get('post_id', None)
#         comment_id = kwargs.get('comment_id', None)

#         if post_id:
#             post = get_object_or_404(Post, id=post_id)
#             Reaction.objects.filter(user=request.user, post=post).delete()
#         elif comment_id:
#             comment = get_object_or_404(Comment, id=comment_id)
#             Reaction.objects.filter(user=request.user, comment=comment).delete()

#         return redirect(request.META.get('HTTP_REFERER', 'post-list'))

class ViewReactionsView(LoginRequiredMixin, View):
    def get(self, request, post_id, *args, **kwargs):
        post = get_object_or_404(Post, id=post_id)
        reactions = post.reaction_set.all().select_related('user')  # Optimize query

        context = {
            'post': post,
            'reactions': reactions
        }
        return render(request, 'viewReactions.html', context)
