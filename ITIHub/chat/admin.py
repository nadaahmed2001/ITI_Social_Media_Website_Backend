from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(GroupChat)
admin.site.register(GroupMessage)
admin.site.register(ChatMessage)
from .models import ChatBotMessage

admin.site.register(ChatBotMessage)