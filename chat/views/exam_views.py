from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction
from chat.models import Course, Model, Question, QuestionOption
from chat.services.file_service import save_uploaded_file
from chat.services.exam_service import process_exam_file, create_exam
from chat.services.course_service import get_or_create_course
from chat.services.model_service import get_or_create_model
from chat.services.stream_service import stream_responses
from chat.llm_api import LlmApi
from chat.services.upload_file_service import handle_file_upload

@login_required
def exam_view(request):
    """Renderiza la página del examen con modelos y asignaturas"""
    models = Model.objects.all()
    local_models = [m for m in models if not m.is_external]
    external_models = [m for m in models if m.is_external]
    courses = Course.objects.all()
    return render(request, "exam.html", {
        "courses": courses,
        "local_models": local_models,
        "external_models": external_models
    })

@csrf_exempt
def upload_file(request):
    """Handle exam upload and processing with full validation"""
    return handle_file_upload(request)