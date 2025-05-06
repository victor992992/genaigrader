from django.core.exceptions import ValidationError
from chat.models import Course

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
    if Course.objects.filter(name__iexact=name).exists():
        raise ValidationError("Esta asignatura ya existe")
    return Course.objects.create(name=name, user=user)

def get_existing_course(course_id):
    """Obtiene una asignatura existente"""
    return Course.objects.get(id=course_id)

'''
#TODO Hacer que se añada el usuario activo a una asignatura ya creada
def procces_course(request):
    course_choice = request.POST.get("course_choice")

    if course_choice == "new":
        new_course_name = request.POST.get("new_course", "").strip()

        # añadir este error? el html no deja enviar vacio
        if not new_course_name:
            raise ValueError("El nombre de la nueva asignatura es requerido")
        
        #__iexact es un field lookup de Django que significa:  i: insensitive (no distingue mayúsculas/minúsculas) exact: Coincidencia exacta (no parcial)
        if Course.objects.filter(name__iexact=new_course_name).exists():
            raise ValueError("Esta asignatura ya existe")
        course = Course.objects.create(name=new_course_name, user=request.user)
    else:
        course_id = request.POST.get("course_id")
        course = Course.objects.get(id=course_id)
    return course'
    ''
    '''