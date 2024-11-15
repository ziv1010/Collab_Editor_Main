# editor/models.py

from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default='')  # Store the document content as JSON
    # Remove the owner field
    # owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    # Add collaborators field
    collaborators = models.ManyToManyField(User, related_name='documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        
    def __str__(self):
        return self.title
