def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def get_error_message_from_form(form):
    errors = []
    for field, field_errors in form.errors.items():
        errors.extend(field_errors)
    return errors[0]