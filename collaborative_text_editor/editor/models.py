# FILE: ./editor/models.py

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

# Add the DocumentVersion model below the Document model
class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'Version of "{self.document.title}" at {self.created_at}'

# Add the Comment model below the DocumentVersion model
class Comment(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Store the range as JSON: {'index': int, 'length': int}
    range = models.JSONField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.document.title}'