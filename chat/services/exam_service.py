from typing import List
from ..models import Question, QuestionOption, Exam
import re

def create_exam(uploaded_file, course, user, request):
    exam_name = request.POST.get("user_exam", "").strip()
    description = exam_name if exam_name else uploaded_file.name
    return Exam.objects.create(
        description=description,
        course=course,
        creator_username=user
    )

def process_exam_file(file_path, exam) -> List[Question]:
    questions = []
    statement = []
    options = []
    correct_option = None
    state = "statement"
    
    with open(file_path, "r") as f:
        for line in f:
            stripped_line = line.strip()
            
            if state == "statement":
                if stripped_line and re.match(r'^[a-zA-Z]\)', stripped_line):
                    new_question = Question.objects.create(
                        statement="\n".join(statement),
                        exam=exam,
                    )
                    questions.append(new_question)
                    options.append(stripped_line)
                    state = "options"
                else:
                    if stripped_line or statement:
                        statement.append(stripped_line)
                    
            elif state == "options":
                if not stripped_line:
                    state = "correct"
                else:
                    options.append(stripped_line)
                    
            elif state == "correct":
                correct_option = stripped_line.lower()
                for opt in options:
                    new_option = QuestionOption.objects.create(
                        content=opt,
                        question=new_question
                    )
                    option_letter = new_option.content.split(')')[0].strip().lower()
                    if option_letter == correct_option:
                        new_question.correct_option = new_option
                        new_question.save()
                
                # Reinicia para la siguiente pregunta
                statement = []
                options = []
                state = "statement"
    
    return questions