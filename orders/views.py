# orders/views.py
from django.http import HttpResponse

def health(request):
    return HttpResponse("orders ok")
