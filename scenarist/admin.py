from django.contrib import admin

# Register your models here.
from scenarist.models.story import Story, StoryAdmin
from scenarist.models.event import Event, EventAdmin

admin.site.register(Story, StoryAdmin)
admin.site.register(Event, EventAdmin)