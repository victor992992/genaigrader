from ..models import Question
from chat.llm_api import LlmApi 

def generate_prompt(question, user_prompt):
    """
    Generates a structured prompt to be sent to the language model.

    Parameters:
    - question: Question instance containing the statement and options.
    - user_prompt: Optional user-defined instruction to prepend to the prompt.

    Returns:
    - dict with full prompt and separated components.
    """
    prompt = ""
    user_prompt_part = user_prompt or ""
    
    user_prompt_part += (
        "\n\nTe voy a pasar una pregunta de test y tienes que responderme con qué opción es la correcta. "
        "Sólo debes decirme la opción, por ejemplo 'a', absolutamente nada más.\n"
    )

    question_prompt_part = question.statement + "\n"

    for option in question.questionoption_set.all().order_by('content'):
        question_prompt_part += f"{option.content}\n"

    prompt = user_prompt_part + question_prompt_part

    return {
        'prompt': prompt,
        'user_prompt': user_prompt_part,
        'question_prompt': question_prompt_part
    }


def evaluate_questions(questions, llm, user_prompt):
    """
    Evaluates a list of questions using a language model API instance.

    Parameters:
    - questions: A list of Question instances to evaluate.
    - llm: An instance of LlmApi used to communicate with the model.
    - user_prompt: Additional instructions to influence model behavior.

    Returns:
    - Tuple: (list of responses, number of correct answers, total questions)
    """
    llm_responses = []
    correct_count = 0
    total_questions = len(questions)

    for question in questions:
        prompt_data = generate_prompt(question, user_prompt)
        print(prompt_data)
        response = list(llm.generate_response(prompt_data['prompt']))[0].strip().lower()
        print(response)

        is_correct = response == question.correct_option.strip().lower()

        if is_correct:
            correct_count += 1

        llm_responses.append({
            "prompt": prompt_data,
            "response": response,
            "correct_option": question.correct_option,
            "is_correct": is_correct
        })

    return llm_responses, correct_count, total_questions


def calculate_results(correct_count, total_questions, llm_responses):
    """
    Calculates summary statistics for evaluated questions.

    Parameters:
    - correct_count: Number of correctly answered questions.
    - total_questions: Total number of evaluated questions.
    - llm_responses: List of individual evaluation results.

    Returns:
    - dict summarizing evaluation results.
    """
    percentage = f"{(correct_count / total_questions) * 100:.2f}" if total_questions > 0 else "0.00"

    return {
        "total_questions": total_questions,
        "correct_count": correct_count,
        "percentage": percentage,
        "responses": llm_responses,
    }
