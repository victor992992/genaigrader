from django.core.exceptions import ValidationError
from genaigrader.models import Course

def get_or_create_course(request):
    """Gestiona la creación o selección de una asignatura"""
    course_choice = request.POST.get("course_choice")
    
    if course_choice == "new":
        new_course_name = request.POST.get("new_course", "").strip()
        if not new_course_name:
            raise ValidationError("El nombre de la asignatura es requerido")
        return create_new_course(new_course_name, request.user)
    else:
        return get_existing_course(request.POST.get("course_id"))

def create_new_course(name, user):
    """Crea una nueva asignatura validando su unicidad"""
    if Course.objects.filter(name__iexact=name, user=user).exists():
        raise ValidationError("Esta asignatura ya existe")
    return Course.objects.create(name=name, user=user)

def get_existing_course(course_id):
    """Obtiene una asignatura existente"""
    return Course.objects.get(id=course_id)
