from genaigrader.models import Model

def get_or_create_model(request):
    model=request.POST.get("model", "llama3.2:1b")
    model_name = model or "llama3.2:1b"
    model, created = Model.objects.get_or_create(description=model_name)
    return model

'''
def process_model(request):
    model = request.POST.get("model", "llama3.2:1b")

    if(Model.objects.exists()):
        for models in Model.objects.all():
            if(models.description==model):
                return models
            
    return Model.objects.create(
        description=model
    )    
'''