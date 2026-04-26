from django.urls import path
from . import views

urlpatterns = [
    path('roadmaps/', views.roadmap_list, name='roadmap_list'),
    path('roadmaps/<uuid:pk>/', views.roadmap_detail, name='roadmap_detail'),
    path('roadmaps/generate/', views.generate_roadmap, name='generate_roadmap'),
    path('tasks/<uuid:pk>/', views.update_task, name='update_task'),
    path('interview/question/', views.get_interview_question, name='get_interview_question'),
]