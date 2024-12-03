# FILE: ./editor/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegisterForm, DocumentForm, CollaboratorsForm 
from .models import Document, Comment, DocumentVersion  # Import DocumentVersion
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
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

@csrf_exempt  # Add this decorator
@login_required
def document_edit(request, pk):
    document = get_object_or_404(Document, pk=pk, collaborators=request.user)
    if request.method == 'POST':
        if request.content_type == 'application/json':
            # Handle AJAX request for title update
            data = json.loads(request.body)
            new_title = data.get('title')
            if new_title:
                document.title = new_title
                document.save()
                return JsonResponse({'status': 'success'})
            else:
                return HttpResponseBadRequest('Invalid title')
        elif 'form_type' in request.POST and request.POST.get('form_type') == 'collaborators_form':
            # Handle collaborators form submission
            collaborators_form = CollaboratorsForm(request.POST, instance=document)
            if collaborators_form.is_valid():
                collaborators_form.save()
                return redirect('document_edit', pk=document.pk)
            else:
                print(collaborators_form.errors)
        else:
            return HttpResponseBadRequest('Invalid form submission')
    else:
        collaborators_form = CollaboratorsForm(instance=document)
    return render(request, 'editor.html', {'document': document, 'collaborators_form': collaborators_form})

@login_required
def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk, collaborators=request.user)
    if request.method == 'POST':
        document.delete()
        return redirect('document_list')
    return render(request, 'document_confirm_delete.html', {'document': document})

@login_required
def get_comments(request, pk):
    document = get_object_or_404(Document, pk=pk, collaborators=request.user)
    comments = document.comments.filter(resolved=False).select_related('user')
    comments_list = []
    for comment in comments:
        comments_list.append({
            'id': comment.id,
            'range': comment.range,
            'content': comment.content,
            'username': comment.user.username,
        })
    return JsonResponse({'comments': comments_list})

# --- Version Control View Functions ---

@csrf_exempt
@login_required
def save_version(request, pk):
    if request.method == 'POST':
        document = get_object_or_404(Document, pk=pk, collaborators=request.user)
        try:
            data = json.loads(request.body)
            content = data.get('content')
            description = data.get('description', '')  # Get description from request
            if content:
                # Create a new DocumentVersion
                DocumentVersion.objects.create(
                    document=document,
                    content=json.dumps(content),
                    description=description,  # Add description
                    user=request.user
                )
                return JsonResponse({'status': 'success'})
            else:
                return HttpResponseBadRequest('No content provided.')
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON.')
    else:
        return HttpResponseBadRequest('Invalid request method.')

@login_required
def list_versions(request, pk):
    document = get_object_or_404(Document, pk=pk, collaborators=request.user)
    versions = document.versions.order_by('-created_at').select_related('user')
    versions_list = []
    for version in versions:
        versions_list.append({
            'id': version.id,
            'username': version.user.username if version.user else 'Unknown',
            'created_at': version.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'description': version.description
        })
    return JsonResponse({'versions': versions_list})

@csrf_exempt
@login_required
def restore_version(request, pk):
    if request.method == 'POST':
        document = get_object_or_404(Document, pk=pk, collaborators=request.user)
        try:
            data = json.loads(request.body)
            version_id = data.get('version_id')
            if version_id:
                version = get_object_or_404(DocumentVersion, pk=version_id, document=document)
                document.content = version.content
                document.save()
                return JsonResponse({
                    'status': 'success',
                    'content': version.content  # Return the content
                })
            else:
                return HttpResponseBadRequest('No version ID provided.')
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON.')
    else:
        return HttpResponseBadRequest('Invalid request method.')

@login_required
def preview_version(request, pk, version_id):
    document = get_object_or_404(Document, pk=pk, collaborators=request.user)
    version = get_object_or_404(DocumentVersion, pk=version_id, document=document)
    return JsonResponse({
        'content': json.loads(version.content),
        'description': version.description,
        'created_at': version.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'username': version.user.username if version.user else 'Unknown'
    })