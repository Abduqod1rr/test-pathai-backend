import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Roadmap, Phase, Task
from groq import Groq

client = Groq(api_key=os.getenv('PATHI_GROQ_API_KEY'))

INTERVIEW_QUESTIONS = [
    {"category": "TIME & RESOURCES", "question": "How many hours per week can you realistically dedicate to this goal?"},
    {"category": "TIME & RESOURCES", "question": "Do you have a budget for this? (None / Small / Flexible)"},
    {"category": "TIME & RESOURCES", "question": "What's your current skill or knowledge level on this? (Beginner / Some experience / Intermediate)"},
    {"category": "EXTERNAL FACTORS", "question": "Are there people in your life who support this goal or might get in the way?"},
    {"category": "EXTERNAL FACTORS", "question": "Any big life commitments coming up? (job, family, moving, etc.)"},
    {"category": "EXTERNAL FACTORS", "question": "What's your biggest real-world obstacle right now?"},
    {"category": "PAST & MINDSET", "question": "Have you tried to achieve this goal before? What stopped you?"},
    {"category": "PAST & MINDSET", "question": "What does success look like to you in 3 months? In 1 year?"},
]

@api_view(['GET', 'POST'])
def roadmap_list(request):
    if request.method == 'GET':
        roadmaps = Roadmap.objects.all().order_by('-created_at')
        data = [{"id": str(r.id), "goal": r.goal, "why": r.why, "created_at": r.created_at.isoformat()} for r in roadmaps]
        return Response(data)
    elif request.method == 'POST':
        data = request.data
        roadmap = Roadmap.objects.create(
            goal=data.get('goal', ''),
            why=data.get('why', ''),
        )
        return Response({"id": str(roadmap.id), "goal": roadmap.goal})

@api_view(['GET', 'POST'])
def roadmap_detail(request, pk):
    try:
        roadmap = Roadmap.objects.get(id=pk)
    except Roadmap.DoesNotExist:
        return Response({"error": "Roadmap not found"}, status=404)
    
    if request.method == 'GET':
        phases_data = []
        for phase in roadmap.phases.order_by('order'):
            tasks = phase.tasks.order_by('order')
            phases_data.append({
                "id": str(phase.id),
                "title": phase.title,
                "description": phase.description,
                "order": phase.order,
                "tasks": [{
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "why": t.why,
                    "estimated_time": t.estimated_time,
                    "tag": t.tag,
                    "status": t.status,
                    "blocker_note": t.blocker_note,
                    "order": t.order,
                } for t in tasks]
            })
        return Response({
            "id": str(roadmap.id),
            "goal": roadmap.goal,
            "why": roadmap.why,
            "time_per_week": roadmap.time_per_week,
            "budget": roadmap.budget,
            "skill_level": roadmap.skill_level,
            "phases": phases_data,
        })

@api_view(['POST'])
def generate_roadmap(request):
    data = request.data
    roadmap_id = data.get('roadmap_id')
    
    try:
        roadmap = Roadmap.objects.get(id=roadmap_id)
    except Roadmap.DoesNotExist:
        return Response({"error": "Roadmap not found"}, status=404)
    
    context = {
        "goal": roadmap.goal,
        "why": roadmap.why,
        "time_per_week": data.get('time_per_week', roadmap.time_per_week),
        "budget": data.get('budget', roadmap.budget),
        "skill_level": data.get('skill_level', roadmap.skill_level),
        "support_obstacles": data.get('support_obstacles', roadmap.support_obstacles),
        "life_commitments": data.get('life_commitments', roadmap.life_commitments),
        "biggest_obstacle": data.get('biggest_obstacle', roadmap.biggest_obstacle),
        "past_experience": data.get('past_experience', roadmap.past_experience),
        "success_3_months": data.get('success_3_months', roadmap.success_3_months),
        "success_1_year": data.get('success_1_year', roadmap.success_1_year),
    }
    
    system_prompt = """You are a life strategy coach. Given a user's goal and their personal context, generate a realistic, personalized roadmap.
Account for their time, resources, obstacles, and external factors.
Return ONLY valid JSON in this format:
{
  "phases": [
    {
      "title": "Phase title",
      "description": "Why this phase matters",
      "tasks": [
        { "title": "Task title", "description": "Task description", "why": "Why this matters", "estimated_time": "e.g., 2 hours", "tag": "skill|habit|resource|social|mindset" }
      ]
    }
  ]
}
Generate 3-5 phases with 3-6 tasks each. Adapt complexity based on available time."""
    
    user_prompt = f"""Goal: {context['goal']}
Why: {context['why']}
Hours per week: {context['time_per_week']}
Budget: {context['budget']}
Skill level: {context['skill_level']}
Support/Obstacles: {context['support_obstacles']}
Life commitments: {context['life_commitments']}
Biggest obstacle: {context['biggest_obstacle']}
Past experience: {context['past_experience']}
Success in 3 months: {context['success_3_months']}
Success in 1 year: {context['success_1_year']}"""
    
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.7,
        max_tokens=4000,
    )
    
    response_text = completion.choices[0].message.content
    
    try:
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        roadmap_json = json.loads(response_text[json_start:json_end])
    except json.JSONDecodeError:
        return Response({"error": "Failed to parse AI response", "raw": response_text}, status=500)
    
    roadmap.phases.all().delete()
    
    for i, phase_data in enumerate(roadmap_json.get('phases', [])):
        phase = Phase.objects.create(
            roadmap=roadmap,
            title=phase_data['title'],
            description=phase_data.get('description', ''),
            order=i
        )
        for j, task_data in enumerate(phase_data.get('tasks', [])):
            Task.objects.create(
                phase=phase,
                title=task_data['title'],
                description=task_data.get('description', ''),
                why=task_data.get('why', ''),
                estimated_time=task_data.get('estimated_time', ''),
                tag=task_data.get('tag', 'skill'),
                status='todo',
                order=j
            )
    
    Roadmap.objects.filter(id=roadmap_id).update(
        time_per_week=context['time_per_week'],
        budget=context['budget'],
        skill_level=context['skill_level'],
        support_obstacles=context['support_obstacles'],
        life_commitments=context['life_commitments'],
        biggest_obstacle=context['biggest_obstacle'],
        past_experience=context['past_experience'],
        success_3_months=context['success_3_months'],
        success_1_year=context['success_1_year'],
    )
    
    return Response({"id": str(roadmap.id), "message": "Roadmap generated successfully", "phases": roadmap_json['phases']})

@api_view(['PATCH'])
def update_task(request, pk):
    try:
        task = Task.objects.get(id=pk)
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=404)
    
    if 'status' in request.data:
        task.status = request.data['status']
    if 'blocker_note' in request.data:
        task.blocker_note = request.data['blocker_note']
    
    task.save()
    return Response({"id": str(task.id), "status": task.status, "blocker_note": task.blocker_note})

@api_view(['POST'])
def get_interview_question(request):
    answered = request.data.get('answered_questions', [])
    answered_text = ", ".join([INTERVIEW_QUESTIONS[i]['question'] for i in answered if i < len(INTERVIEW_QUESTIONS)])
    
    next_idx = len(answered)
    if next_idx >= len(INTERVIEW_QUESTIONS):
        return Response({"done": True, "message": "All questions completed"})
    
    current = INTERVIEW_QUESTIONS[next_idx]
    
    if next_idx < len(INTERVIEW_QUESTIONS) - 1:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "system",
                "content": "You are a friendly life coach conducting a goal-setting interview. Ask ONE follow-up question based on the user's previous answers to learn more about their context."
            }, {
                "role": "user",
                "content": f"Previous questions asked: {answered_text}. Current category: {current['category']}. Current question: {current['question']}. Ask a brief contextual follow-up if needed, otherwise repeat the current question."
            }],
            temperature=0.7,
            max_tokens=200,
        )
        follow_up = completion.choices[0].message.content
        return Response({
            "index": next_idx,
            "category": current['category'],
            "question": current['question'],
            "follow_up": follow_up if follow_up != current['question'] else None
        })
    
    return Response({
        "index": next_idx,
        "category": current['category'],
        "question": current['question']
    })