from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from chat.models import Course, Model
from chat.services.exam_service import process_exam_file #TODO no se puede quitar no se por que
from chat.services.upload_file_service import handle_file_upload

@login_required
def exam_view(request):
    """Render the exam page with models and courses"""
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
