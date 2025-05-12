from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from chat.models import Exam, Model, Evaluation
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse
from django.utils import timezone
from chat.services.stream_service import stream_responses
from chat.llm_api import LlmApi
import logging
import json

def batch_stream(exams_to_eval, models_to_eval, repetitions):
    total_exams = len(exams_to_eval)
    total_models = len(models_to_eval)
    total_reps = repetitions
    eval_count = 0
    for exam in exams_to_eval:
        questions = exam.question_set.prefetch_related('questionoption_set').all()
        if not questions.exists():
            logging.warning(f"Exam {exam} has no questions.")
            yield f"data: {json.dumps({'error': f'Exam {exam} has no questions.'})}\n\n"
            continue
        subject_name = exam.course.name if hasattr(exam, 'course') and exam.course else ''
        exam_name = exam.description
        for model in models_to_eval:
            try:
                llm = LlmApi(model)
                llm.validate()
            except ValueError as e:
                logging.warning(f"Model {model}: {str(e)}")
                yield f"data: {json.dumps({'error': f'Model {model}: {str(e)}'})}\n\n"
                continue
            for rep in range(1, repetitions+1):
                eval_count += 1
                progress_msg = (
                    f"Eval {eval_count}/{total_exams*total_models*total_reps} - "
                    f"Model: {model.description} Subject: {subject_name} Exam: {exam_name} Repetition: {rep}/{total_reps}"
                )
                logging.warning(f"Progress: {progress_msg}")
                yield f"data: {json.dumps({'progress': progress_msg})}\n\n"
                user_prompt = ''
                # Collect responses and stats
                responses = list(stream_responses(questions, user_prompt, llm, len(questions), exam))
                # Try to extract grade and time from the last response if present
                last_grade = None
                last_time = None
                last_correct = None
                last_total = len(questions)
                for r in reversed(responses):
                    try:
                        data = json.loads(r.replace('data: ', '').strip())
                        if 'total_time' in data and 'correct_count' in data and 'total_questions' in data:
                            last_grade = data['correct_count']
                            last_time = data['total_time']
                            last_total = data['total_questions']
                            break
                    except Exception:
                        continue
                # Stream all responses as before
                for chunk in responses:
                    logging.warning(f"Yielding chunk: {chunk[:100]}")
                    yield chunk
                # After all responses, send a summary for this eval
                if last_grade is not None and last_time is not None:
                    summary = {
                        'eval_result': {
                            'grade': f"{last_grade}/{last_total}",
                            'time': last_time
                        }
                    }
                    yield f"data: {json.dumps(summary)}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"

@login_required
@csrf_exempt
def batch_evaluations_view(request):
    user = request.user
    exams = Exam.objects.filter(creator_username=user)
    models = Model.objects.all()

    if request.method == 'POST':
        logging.warning('Batch evaluation POST received')
        if request.content_type == 'application/json':
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

        return StreamingHttpResponse(
            batch_stream(exams_to_eval, models_to_eval, repetitions),
            content_type="text/event-stream"
        )

    return render(request, 'batch_evaluations.html', {
        'exams': exams,
        'models': models,
    })
