from rest_framework import serializers

from .models import User,Blog,Comment,Tag,Like


class TagSerializer(serializers.ModelSerializer):
    class Meta:
      model=Tag
      fields = ['id','name']  




class BlogSerializer(serializers.ModelSerializer):

    user = serializers.ReadOnlyField(source='user.id')
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    user_full_name = serializers.SerializerMethodField()
  

    class Meta:
      model = Blog
      fields = ['id', 'user', 'title', 'content', 'created_at', 'updated_at', 'edited', 'tags', 'tag_names', 'likes_count', 'comments_count', 'user_full_name']
      read_only_fields = ['created_at', 'updated_at', 'edited']

        
    def validate(self, data):
        if 'title' in data and not data['title'].strip():
            raise serializers.ValidationError({"title": "Title cannot be empty."})
        if 'content' in data and not data['content'].strip():
            raise serializers.ValidationError({"content": "Content cannot be empty."})
        return data
    
    def validate_tag_names(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("Cannot add more than 5 tags.")
        return value

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        blog = Blog.objects.create(**validated_data)
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            blog.tags.add(tag)
        return blog

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tag_names is not None:
            instance.tags.clear()
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                instance.tags.add(tag)
        return instance
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_user_full_name(self, obj):
        return obj.user.get_full_name()

class CommentSerializer(serializers.ModelSerializer):

    user=serializers.ReadOnlyField(source='user.id')
    class Meta:

      model=Comment
      fields = ['id', 'blog', 'user', 'content', 'created_at', 'updated_at', 'parent']
      read_only_fields = ['created_at', 'updated_at']

class LikeSerializer(serializers.ModelSerializer):
   
    user=serializers.ReadOnlyField(source='user.id')
    blog=serializers.ReadOnlyField(source='blog.id')

    class Meta:
      model=Like
      fields = ['id','blog','user','created_at']
      read_only_fields = ['created_at']

    def validate(self, attrs):
        user = self.context['request'].user
        blog = self.context['blog']
        if Like.objects.filter(user=user, blog=blog).exists():
            raise serializers.ValidationError("You already liked this post.")
        return attrs


