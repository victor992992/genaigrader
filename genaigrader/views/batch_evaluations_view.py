from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from chat.models import Exam, Model
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse
import logging

@login_required
@csrf_exempt
def batch_evaluations_view(request):
    user = request.user
    exams = Exam.objects.filter(creator_username=user)
    models = Model.objects.all()
    if request.method == 'POST':
        logging.warning('Batch evaluation POST received')
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            selected_exam_ids = data.get('exams[]', [])
            selected_model_ids = data.get('models[]', [])
            repetitions = int(data.get('repetitions', 1))
            logging.warning('Parsed as JSON')
        else:
            selected_exam_ids = request.POST.getlist('exams[]')
            selected_model_ids = request.POST.getlist('models[]')
            repetitions = int(request.POST.get('repetitions', 1))
            logging.warning('Parsed as form POST')
        logging.warning(f'selected_exam_ids: {selected_exam_ids}, selected_model_ids: {selected_model_ids}, repetitions: {repetitions}')

        exams_to_eval = Exam.objects.filter(id__in=selected_exam_ids, creator_username=user)
        models_to_eval = Model.objects.filter(id__in=selected_model_ids)
        logging.warning(f'exams_to_eval: {[e.id for e in exams_to_eval]}, models_to_eval: {[m.id for m in models_to_eval]}')

        from chat.services.stream_service import stream_responses
        from chat.llm_api import LlmApi
        import json
        from chat.models import Evaluation
        from django.utils import timezone

        def batch_stream():
            total_exams = len(exams_to_eval)
            total_models = len(models_to_eval)
            total_reps = repetitions
            eval_count = 0
            for exam_idx, exam in enumerate(exams_to_eval, start=1):
                questions = exam.question_set.prefetch_related('questionoption_set').all()
                if not questions.exists():
                    logging.warning(f"Exam {exam} has no questions.")
                    yield f"data: {json.dumps({'error': f'Exam {exam} has no questions.'})}\n\n"
                    continue
                subject_name = exam.course.name if hasattr(exam, 'course') and exam.course else ''
                exam_name = exam.description
                for model_idx, model in enumerate(models_to_eval, start=1):
                    try:
                        llm = LlmApi(model)
                        llm.validate()
                    except ValueError as e:
                        logging.warning(f"Model {model}: {str(e)}")
                        yield f"data: {json.dumps({'error': f'Model {model}: {str(e)}'})}\n\n"
                        continue
                    for rep in range(1, repetitions+1):
                        eval_count += 1
                        progress_msg = f"Eval {eval_count}/{total_exams*total_models*total_reps} - Model: {model.description} Subject: {subject_name} Exam: {exam_name} Repetition: {rep}/{total_reps}"
                        logging.warning(f"Progress: {progress_msg}")
                        yield f"data: {json.dumps({'progress': progress_msg})}\n\n"
                        user_prompt = ''
                        for chunk in stream_responses(exam.question_set.all(), user_prompt, llm, len(exam.question_set.all()), exam):
                            logging.warning(f"Yielding chunk: {chunk[:100]}")
                            yield chunk
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingHttpResponse(batch_stream(), content_type="text/event-stream")
    return render(request, 'batch_evaluations.html', {
        'exams': exams,
        'models': models,
    })
