from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.contrib.postgres.search import SearchVector
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count

from .models import Post, Comment
from .forms import EmailPostForm, CommentForm, SearchForm


class PostListView(ListView):
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        slug = self.get_slug()

        if slug:
            context['tag'] = self.get_tag(slug)

        return context

    def get_queryset(self):
        object_list = Post.published.all()

        tag_slug = self.get_slug()

        if tag_slug:
            tag = self.get_tag(tag_slug)
            object_list = object_list.filter(tags__in=[tag])

        return object_list

    def get_tag(self, slug):
        return get_object_or_404(Tag, slug=slug)

    def get_slug(self):
        if 'tag_slug' in self.kwargs:
            return self.kwargs['tag_slug']
        else:
            return None


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status='published', publish__year=year,
                             publish__month=month, publish__day=day)
    comments = post.comments.filter(active=True)
    new_comment = None
    comment_form = CommentForm()

    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
        else:
            comment_form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids) \
        .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')) \
                        .order_by('-same_tags', '-publish')[:4]

    return render(request, 'blog/post/detail.html', {
        'post': post,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'similar_posts': similar_posts
    })


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    form = EmailPostForm()

    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'.format(
                cd['name'], cd['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments:{}'.format(
                post.title, post_url, cd['name'], cd['comments'])

            send_mail(subject, message, 'admin@myblog.com', [cd['to']])
            sent = True
        else:
            form = EmailPostForm()

    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data['query']
        results = Post.objects.annotate(
            search=SearchVector('title', 'body'),
        ).filter(search=query)

    return render(request, 'blog/post/search.html', {
        'form': form,
        'query': query,
        'results': results})
