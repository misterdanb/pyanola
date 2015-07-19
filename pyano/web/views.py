from django.shortcuts import render
from .models import pyanoroll
from django.http import HttpResponse
def index(request):
    pyanoroll_object = pyanoroll.objects.get(pk=1)
    pyanoroll_title="Schmetterling"
    #context = {'pyanoroll_object': pyanoroll_object}
    return render(request, 'web/index.html', {'pyanoroll': pyanoroll_object})
# Create your views here.
