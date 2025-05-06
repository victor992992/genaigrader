from chat.models import Evaluation, QuestionEvaluation
from chat.services.evaluation_service import generate_prompt
from django.utils import timezone
import json
import time


def stream_responses(questions, user_prompt, llm, total_questions, exam):
    """
    Streams evaluation results for each question, yielding JSON-encoded progress updates.

    Parameters:
    - questions: List of Question objects to be evaluated.
    - user_prompt: Custom instruction provided by the user.
    - llm: An instance of LlmApi, encapsulating model configuration and interaction.
    - total_questions: Total number of questions to evaluate.
    - exam: The Exam object associated with this evaluation.

    Yields:
    - str: Server-sent event JSON containing progress and evaluation details.
    """
    correct_count = 0
    total_evaluation_time = 0.0

    evaluation = Evaluation.objects.create(
        prompt=(
            user_prompt +
            " Te voy a pasar una pregunta de test y tienes que responderme con qué opción es la correcta. "
            "Sólo debes decirme la opción, por ejemplo 'a', absolutamente nada más.\n"
        ),
        ev_date=timezone.now(),
        grade=0,
        model=llm.model_obj,  # Store original model object
        exam=exam,
        time=0.0
    )

    for index, question in enumerate(questions):
        start_time = time.monotonic()

        progress = process_question(
            correct_count,
            index,
            question,
            user_prompt,
            llm,
            total_questions,
            evaluation
        )

        end_time = time.monotonic()
        question_time = end_time - start_time
        total_evaluation_time += question_time

        correct_count = progress['correct_count']
        progress['time'] = round(question_time, 2)

        if index == len(questions) - 1:
            progress['total_time'] = round(total_evaluation_time, 2)

        yield f"data: {json.dumps(progress)}\n\n"

    evaluation.grade = round((correct_count / total_questions * 10), 2) if total_questions > 0 else 0.0
    evaluation.time = round(total_evaluation_time, 2)
    evaluation.save()


def process_question(correct_count, index, question, user_prompt, llm, total_questions, evaluation):
    """
    Processes a single question using the provided LlmApi instance and updates evaluation state.

    Parameters:
    - correct_count: Number of correct answers so far.
    - index: Index of the current question.
    - question: The Question object to be evaluated.
    - user_prompt: Instructional prefix to influence model behavior.
    - llm: An instance of LlmApi to generate the model response.
    - total_questions: Total number of questions in the session.
    - evaluation: The Evaluation database object to associate with results.

    Returns:
    - dict: A dictionary containing processed question data and result.
    """
    prompt_data = generate_prompt(question, user_prompt)
    response = list(llm.generate_response(prompt_data['prompt']))[0].strip().lower()

    is_correct = (response[0] == question.correct_option.content.strip().lower()[0])

    QuestionEvaluation.objects.create(
        evaluation=evaluation,
        question=question,
        question_option=question.correct_option
    )

    if is_correct:
        correct_count += 1

    return {
        "processed_questions": index + 1,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "response": {
            "question_prompt": prompt_data['question_prompt'],
            "user_prompt": prompt_data['user_prompt'],
            "prompt": prompt_data['prompt'],
            "response": response,
            "correct_option": question.correct_option.content,
            "is_correct": is_correct,
        }
    }
