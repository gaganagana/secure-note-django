"""
Forms for SecureNote.

In an interview, explain:
- UserRegisterForm extends Django's UserCreationForm to leverage built-in password validation and hashing.
- NoteForm is a regular form exposing a plaintext 'content' field.
- The view explicitly calls `encrypt_text()` on the cleaned content before saving to the database.
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Note


class UserRegisterForm(UserCreationForm):
    """
    User registration form with email requirement.
    Uses Django's built-in password validation and hashing (PBKDF2 SHA-256).
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username',
                'autocomplete': 'username'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to password fields inherited from UserCreationForm
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Create a strong password',
                'autocomplete': 'new-password'
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Confirm your password',
                'autocomplete': 'new-password'
            })


class NoteForm(forms.Form):
    """
    Form for creating and editing notes.
    Accepts plaintext in the 'content' field; encryption happens explicitly in the view.
    """
    title = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. System Architecture Notes',
            'autofocus': True
        })
    )
    category = forms.ChoiceField(
        choices=Note.CATEGORY_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    content = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control font-monospace',
            'rows': 8,
            'placeholder': 'Write your confidential note here... (Will be encrypted before saving)'
        }),
        help_text="Your note content is encrypted at the application layer with Fernet before database storage."
    )
