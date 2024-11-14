# editor/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegisterForm, DocumentForm
from .models import Document
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('document_list')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def document_list(request):
    documents = Document.objects.filter(owner=request.user)
    return render(request, 'document_list.html', {'documents': documents})

@login_required
def document_create(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            document.save()
            return redirect('document_edit', pk=document.pk)
    else:
        form = DocumentForm()
    return render(request, 'document_create.html', {'form': form})

@login_required
def document_edit(request, pk):
    document = get_object_or_404(Document, pk=pk, owner=request.user)
    return render(request, 'editor.html', {'document': document})