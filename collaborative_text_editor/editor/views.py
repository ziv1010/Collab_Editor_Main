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
    # Include documents where the user is a collaborator
    documents = Document.objects.filter(collaborators=request.user)
    return render(request, 'document_list.html', {'documents': documents})

@login_required
def document_create(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            document = form.save(commit=False)
            document.save()
            form.save_m2m()  # Save the collaborators
            document.collaborators.add(request.user)  # Add the creator as a collaborator
            return redirect('document_edit', pk=document.pk)
    else:
        form = DocumentForm()
    return render(request, 'document_create.html', {'form': form})

@login_required
def document_edit(request, pk):
    document = get_object_or_404(Document, pk=pk, collaborators=request.user)
    if request.method == 'POST':
        form = DocumentForm(request.POST, instance=document)
        if form.is_valid():
            form.save()
            return redirect('document_edit', pk=document.pk)
    else:
        form = DocumentForm(instance=document)
    return render(request, 'editor.html', {'document': document, 'form': form})

@login_required
def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk, collaborators=request.user)
    if request.method == 'POST':
        document.delete()
        return redirect('document_list')
    return render(request, 'document_confirm_delete.html', {'document': document})
