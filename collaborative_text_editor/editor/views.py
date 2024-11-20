# editor/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegisterForm, DocumentForm
from .models import Document
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

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

@csrf_exempt  # Add this decorator
@login_required
def document_edit(request, pk):
    print(pk)
    document = get_object_or_404(Document, pk=pk, collaborators=request.user)
    if request.method == 'POST':
        print(request.POST)
        if request.POST.get("title"):
            # Update the title
            new_title = request.POST.get('title')
            if new_title:
                document.title = new_title
                document.save()
                return JsonResponse({'status': 'success'})
            else:
                return HttpResponseBadRequest('Invalid title')
        else:
            # Update the document
            form = DocumentForm(request.POST, instance=document)
            if form.is_valid():
                document = form.save()
                form.save_m2m()
                # document.collaborators = 
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
