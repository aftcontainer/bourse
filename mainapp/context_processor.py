from mainapp.forms import DeviseForm, QualiteForm, CategorieClientForm, TypeOperationForm, TypeTitreForm


def devise_form(request):
    return {"devise_form": DeviseForm()}

def qualite_form(request):
    return {"qualite_form": QualiteForm()}

def cat_client_form(request):
    return {"cat_client_form": CategorieClientForm()}

def t_operation_form(request):
    return {"t_operation_form": TypeOperationForm()}

def t_titre_form(request):
    return {"t_titre_form": TypeTitreForm()}
