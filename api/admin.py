from django.contrib import admin
from .models import Roadmap, Phase, Task

@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ('goal', 'created_at', 'updated_at')
    search_fields = ('goal',)

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'roadmap', 'order')
    list_filter = ('roadmap',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'phase', 'status', 'tag', 'order')
    list_filter = ('status', 'tag', 'phase__roadmap')
    search_fields = ('title',)