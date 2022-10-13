from django.db import models
from django.contrib import admin
from datetime import datetime, timedelta
from scenarist.utils.helper import json_default
from scenarist.models.story import Story
import json
import logging

logger = logging.Logger(__name__)


class Event(models.Model):
    class Meta:
        ordering = ['timeline', 'time_offset_hours']

    name = models.CharField(max_length=128, default='')
    # story = models.ForeignKey(Story, on_delete=models.SET_NULL, null=True)
    # place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True)
    time_offset_hours = models.IntegerField(default=-1, blank=True)
    time_offset_custom = models.CharField(default='', max_length=32, blank=True)
    timeline = models.CharField(default='', max_length=32, blank=True)
    day = models.DateTimeField(default=datetime.now, blank=True, null=True)
    place_order = models.PositiveIntegerField(default=0, blank=True)
    tags = models.TextField(max_length=256, blank=True, default='')
    exact_place = models.CharField(max_length=256, blank=True, default='')
    preamble = models.TextField(max_length=2048, blank=True, default='')
    objectives = models.TextField(max_length=2048, blank=True, default='')
    fallback = models.TextField(max_length=2048, blank=True, default='')
    description = models.TextField(max_length=4096, blank=True, default='')
    side_treks = models.TextField(max_length=4096, blank=True, default='')
    rewards = models.TextField(max_length=1024, blank=True, default='')
    consequences = models.TextField(max_length=2048, blank=True, default='')
    special = models.TextField(max_length=2048, blank=True, default='')
    cast = models.TextField(max_length=1024, blank=True, default='')
    # era = models.CharField(max_length=16, blank=True, default='2019')
    is_event = models.BooleanField(default=False)
    is_downtime = models.BooleanField(default=False)
    is_briefing = models.BooleanField(default=False)
    is_debriefing = models.BooleanField(default=False)

    def fix(self):
        if self.time_offset_hours >= 0:
            self.time_offset_custom = f'{int(self.time_offset_hours / 24)} {self.time_offset_hours % 24}'
        else:
            words = self.time_offset_custom.split(' ')
            if len(words) == 2:
                self.time_offset_hours = int(words[0]) * 24 + int(words[1])
            else:
                self.time_offset_hours = -1
            if self.time_offset_hours < -1:
                self.time_offset_hours = -1
                self.time_offset_custom = ''
        # Update orders in and out of the scenes
        from_list = EventsLink.objects.filter(event_from=self)
        to_list = EventsLink.objects.filter(event_to=self)
        n = 0
        for l in from_list:
            l.order_out = n
            n += 1
            l.save()
        n = 0
        for l in to_list:
            l.order_in = n
            n += 1
            l.save()

    def as_json(self):
        jstr = json.dumps(self, default=json_default, sort_keys=True, indent=4)
        return jstr

    def __str__(self):
        st = ''
        if self.story is not None:
            st = self.story.acronym
        return f'{self.name}'

    @property
    def timeline_name(self):
        res = 'timeline'
        story = self.story
        for x in story.all_timelines:
            if x['label'] == self.timeline:
                res = x['name']
        return res

    @property
    def external_links(self):
        lst = []
        for e in ExternalLink.objects.filter(parent_scene=self):
            lst.append(f'<a href="{e.url}" target="_blank">{e.name}</a>')
        return "<BR/>".join(lst)

    @property
    def events_from(self):
        list = []
        from_list = EventsLink.objects.filter(scene_from=self)
        for l in from_list:
            list.append(f'H{l.scene_to.time_offset_hours}-{l.scene_to.name}/{l.scene_to.id}')
        return "|".join(list)

    @property
    def events_to(self):
        list = []
        to_list = EventsLink.objects.filter(scene_to=self)
        for l in to_list:
            list.append(f'H{l.scene_from.time_offset_hours}-{l.scene_from.name}/{l.scene_from.id}')
        return "|".join(list)

    @property
    def story_time(self):
        d = None
        if self.story:
            refdatetime = datetime.combine(self.story.dday, datetime.min.time())
            d = refdatetime + timedelta(hours=self.time_offset_hours)
        return d

    @property
    def story_day(self):
        d = None
        if self.story:
            refdatetime = datetime.combine(self.story.dday, datetime.min.time())
            # d = refdatetime #+ timedelta(hours=self.time_offset_hours)
        return refdatetime

    # @property
    # def verified_cast(self):
    #     if self.cast == '':
    #         return ""
    #     else:
    #         from collector.models.creatures import Creature
    #         cast = self.cast.split(', ')
    #         cast_list = Creature.objects.filter(rid__in=cast)
    #         list = []
    #         for c in cast_list:
    #             list.append(f'<a href="#{c.rid}">{c.name}</a>')
    #         strl = ", ".join(list)
    #         return f'Expected: {len(cast)}, found {len(list)}: {strl}'

    # @property
    # def ultimate_cast(self):
    #     if self.cast == '':
    #         return ""
    #     else:
    #         from collector.models.creatures import Creature
    #         cast = self.cast.split(', ')
    #         cast_list = Creature.objects.filter(rid__in=cast)
    #         list = []
    #         for c in cast_list:
    #             list.append(f'<a href="#{c.rid}">{c.name}</a>')
    #         strl = ", ".join(list)
    #         if len(cast) == len(list):
    #             return f'{strl}'
    #         else:
    #             return f'Expected: {len(cast)}, found {len(list)}: {strl} [{self.cast}]'

    @property
    def all_as_tags(self):
        list = self.tags.split(" ")
        list.append(f'Sc:{self.id:04}')
        if self.is_downtime:
            list.append("DOWNTIME")
        if self.is_event:
            list.append("EVENT")
        if self.is_briefing:
            list.append("INTRODUCTION")
        if self.is_debriefing:
            list.append("DEBRIEFING")
        return " ".join(list)


def refix(modeladmin, request, queryset):
    for event in queryset:
        event.fix()
        event.save()
    short_description = 'Fix scenes'


LINK_CATEGORIES = (
    ('FOE', 'Enemies actions'),
    ('FRIEND', 'Allies actions'),
    ('THIRD', 'Others actions'),
    ('TIME', '-'),
    ('FATE', 'Fate or ill luck'),
)


class EventsLink(models.Model):
    class Meta:
        ordering = ['category', 'event_from', 'event_to']

    category = models.CharField(default='TIME', max_length=10, choices=LINK_CATEGORIES)
    description = models.TextField(max_length=1024, default='', blank=True)
    event_from = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='event_from', null=True)
    event_to = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='event_to', null=True)
    valid = models.BooleanField(default=True)
    order_in = models.IntegerField(default=0, blank=True)
    order_out = models.IntegerField(default=0, blank=True)

    def __str__(self):
        return f'{self.scene_from.name} [{self.category}] {self.scene_to.name}'


class ExternalLink(models.Model):
    class Meta:
        ordering = ['name']

    url = models.CharField(default='', max_length=1024, blank=True)
    event_scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='event_scene', null=True)
    name = models.CharField(default='', max_length=256, blank=True)
    notes = models.TextField(default='', max_length=1024, blank=True)

    def __str__(self):
        return f'{self.name} ({self.url})';


class EventFromInline(admin.TabularInline):
    model = EventsLink
    extras = 1
    fk_name = 'event_from'
    ordering = ('event_to',)


class EventToInline(admin.TabularInline):
    model = EventsLink
    extras = 1
    fk_name = 'event_to'
    ordering = ('event_from',)


class ExternalLinkInline(admin.TabularInline):
    model = ExternalLink
    extras = 1
    fk_name = 'parent_event'
    ordering = ('name',)


class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'place', 'timeline', 'time_offset_hours', 'story_time', 'links_to', 'links_from',
                    'verified_cast']
    ordering = ['time_offset_hours', 'place', 'name']
    list_filter = ['story', 'place']
    search_fields = ['name', 'description', 'preamble', 'rewards', 'consequences']
    actions = [refix]
    inlines = [EventFromInline, EventToInline, ExternalLinkInline]
