from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets, status
from .models import Blog,Like,Comment,Tag
from .serializers import BlogSerializer,CommentSerializer,LikeSerializer
from rest_framework.decorators import action


   #BlogViewSet, 
  #  CommentViewSet, 
 #   TagViewSet,
#  LikeViewSet,


class BlogViewSet(viewsets.ModelViewSet):
    queryset=Blog.objects.all()
    serializer_class=BlogSerializer
    
    lookup_field='id'
    

    

    def update(self, request, *args, **kwargs):
        if request.user.id != self.get_object().user_id:
            return Response({"error": "You are not authorized to update this blog"}, status=403)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.id != self.get_object().user_id:
            return Response({"error": "You are not authorized to delete this blog"}, status=403)
        return super().destroy(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.id != self.get_object().user_id:
            return Response({"error": "You are not authorized to update this blog"}, status=403)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True,methods=['get'],name='blog-comments')
    def get_comments(self,request,pk=None):
        blog=self.get_object()
        comments=Comment.objects.filter(blog_id=blog.id)
        serializer=CommentSerializer(comments,many=True)
        return Response(serializer.data)
        
    @action(detail=True,methods=['get'],name='blog-likes')
    def get_likes(self,request,pk=None):
        blog=self.get_object()
        likes=Like.objects.filter(blog_id=blog.id)
        serializer=LikeSerializer(likes,many=True)
        return Response(serializer.data)
        
    @action(detail=True,methods=['post'],name='blog-like')
    def like(self,request,pk=None):
        blog=self.get_object()
        if Like.objects.filter(blog=blog, user=request.user).exists():
            return Response(
                {"error": "You already liked this blog"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        like=Like.objects.create(blog=blog,user=request.user)
        serializer=LikeSerializer(like)
        return Response(serializer.data)

    @action(detail=True,methods=['delete'],name='blog-unlike')
    def unlike(self,request,pk=None):
        blog=self.get_object()
        if not Like.objects.filter(blog=blog, user=request.user).exists():
            return Response(
                {"error": "You have not liked this blog"},
                status=status.HTTP_400_BAD_REQUEST
            )
        like=Like.objects.get(blog=blog,user=request.user)
        like.delete()
        return Response({"message":"Unliked"})

    @action(detail=True,methods=['post'],name='blog-comment')
    def post_comment(self,request,pk=None):
        blog=self.get_object()
        content=request.data['content'].strip() # Could throw KeyError if 'content' missing
        parent=request.data['parent']
        if not content or not content.strip():
            return Response(
                {
                    "error": "Content is required and cannot be empty",
                    "field": "content"
                },
            status=status.HTTP_400_BAD_REQUEST
        )
        parentcomment = Comment.objects.get(id=parent, blog=blog)


        if parentcomment and parentcomment.parent:
            return Response(
                {
                    "error": "Cannot reply to a reply (max nesting level reached)",
                    "field": "parent"
                },
            status=status.HTTP_400_BAD_REQUEST
        )
        Comment.objects.create(blog=blog,user=request.user,content=content,parent=parentcomment) 
        return Response({"message":"Commented"})



    @action(detail=False,methods=['get'],name='blog-search')
    def search(self,request,pk=None):
        blogs=Blog.objects.filter(title__icontains=request.query_params.get('q', ''))
        serializer=BlogSerializer(blogs,many=True)
        return Response(serializer.data)

    @action(detail=False,methods=['get'],name='blog-filter-tag')
    def filter_tag(self,request,pk=None):
        blogs=Blog.objects.filter(tags__name=request.query_params.get('tag', ''))
        serializer=BlogSerializer(blogs,many=True)
        return Response(serializer.data)

    @action(detail=False,methods=['get'],name='blog-filter-author')
    def filter_author(self,request,pk=None):
        blogs=Blog.objects.filter(user_id=request.query_params.get('author', ''))
        serializer=BlogSerializer(blogs,many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_blogs(self, request):
        blogs = Blog.objects.filter(user=request.user)
        serializer = BlogSerializer(blogs, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

