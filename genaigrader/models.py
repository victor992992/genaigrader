from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Course(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Exam(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE) 
    user = models.ForeignKey(User, on_delete=models.CASCADE)  

    def __str__(self):
        return self.description

class QuestionOption(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.CharField(max_length=255)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)

    def __str__(self):
        return self.content

class Question(models.Model):
    id = models.AutoField(primary_key=True)
    statement = models.TextField()
    correct_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, null=True, related_name='correct_option_for')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.statement[:50]  

class Model(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=255)

    # Optional fields for external models
    api_url = models.URLField(max_length=500, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        super().clean()
        if self.is_external and not self.user:
            raise ValidationError("The 'user' field is required for external models")
        if not self.is_external and self.user:
            raise ValidationError("The 'user' field should only be used for external models")
        
    def __str__(self):
        return self.description

    @property
    def is_external(self):
        return self.api_url is not None and self.api_key is not None

class Evaluation(models.Model):
    id = models.AutoField(primary_key=True)
    prompt = models.TextField()
    ev_date = models.DateField()
    grade = models.FloatField()
    time = models.FloatField()
    model = models.ForeignKey(Model, on_delete= models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.prompt} {self.grade}'

class QuestionEvaluation(models.Model):
    id = models.AutoField(primary_key=True)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    question_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE)

    def __str__(self):
        return f"Evaluation {self.evaluation.id}, Question {self.question.id}, Option {self.question_option.id}"