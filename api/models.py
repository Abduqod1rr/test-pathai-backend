from django.db import models
import uuid

class Roadmap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.CharField(max_length=500)
    why = models.TextField(blank=True)
    time_per_week = models.CharField(max_length=50, blank=True)
    budget = models.CharField(max_length=50, blank=True)
    skill_level = models.CharField(max_length=50, blank=True)
    support_obstacles = models.TextField(blank=True)
    life_commitments = models.TextField(blank=True)
    biggest_obstacle = models.TextField(blank=True)
    past_experience = models.TextField(blank=True)
    success_3_months = models.TextField(blank=True)
    success_1_year = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.goal

class Phase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roadmap = models.ForeignKey(Roadmap, related_name='phases', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.roadmap.goal} - {self.title}"

class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]
    
    TAG_CHOICES = [
        ('skill', 'Skill'),
        ('habit', 'Habit'),
        ('resource', 'Resource'),
        ('social', 'Social'),
        ('mindset', 'Mindset'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phase = models.ForeignKey(Phase, related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    why = models.TextField(blank=True)
    estimated_time = models.CharField(max_length=100, blank=True)
    tag = models.CharField(max_length=20, choices=TAG_CHOICES, default='skill')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    blocker_note = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title