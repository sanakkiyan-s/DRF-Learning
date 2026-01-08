from django.contrib import admin

# Register your models here.
from .models import User,Comment,Like,Tag,Blog

admin.site.register(User)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Tag)
admin.site.register(Blog)


