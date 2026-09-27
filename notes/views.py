"""
Web views for SecureNote.

In an interview, explain:
- We use function-based views for simplicity and clear line-by-line traceability.
- Every note view enforces `@login_required` to verify authentication.
- Every note action verifies `note.owner == request.user` to enforce strict authorization (ownership).
- Plaintext is explicitly converted to ciphertext via `encrypt_text()` in creation/update views.
- Ciphertext is explicitly converted back to plaintext via `decrypt_text()` in detail/edit views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q

from .models import Note
from .forms import UserRegisterForm, NoteForm
from .utils import encrypt_text, decrypt_text, DecryptionError


def landing_view(request):
    """
    Public landing page introducing SecureNote.
    If the user is already authenticated, redirects directly to their dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def register_view(request):
    """
    Handles user registration using Django's built-in password validation & PBKDF2 hashing.
    Automatically logs in the user upon successful account creation.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to SecureNote, {user.username}! Your account was created successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    """
    Authenticates an existing user and creates a secure session.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """
    Terminates the user's session and redirects to the landing page.
    """
    logout(request)
    messages.info(request, 'You have been safely logged out.')
    return redirect('landing')


@login_required
def dashboard_view(request):
    """
    Authenticated dashboard showing note metrics, recent notes, and quick actions.
    All data is strictly scoped to `request.user`.
    """
    user_notes = Note.objects.filter(owner=request.user)

    # Note counts by category
    stats = {
        'total': user_notes.count(),
        'personal': user_notes.filter(category='Personal').count(),
        'study': user_notes.filter(category='Study').count(),
        'work': user_notes.filter(category='Work').count(),
        'ideas': user_notes.filter(category='Ideas').count(),
        'journal': user_notes.filter(category='Journal').count(),
    }

    # 5 most recently updated notes
    recent_notes = user_notes.order_by('-updated_at')[:5]

    context = {
        'stats': stats,
        'recent_notes': recent_notes,
    }
    return render(request, 'dashboard.html', context)


@login_required
def note_list_view(request):
    """
    Displays the list of notes owned by the current user.
    Supports filtering by category and searching by title.
    Note content remains encrypted in the database.
    """
    notes = Note.objects.filter(owner=request.user)

    selected_category = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()

    if selected_category and selected_category != 'All':
        notes = notes.filter(category=selected_category)

    if search_query:
        # Search is applied to non-encrypted metadata (title)
        notes = notes.filter(title__icontains=search_query)

    context = {
        'notes': notes,
        'categories': [c[0] for c in Note.CATEGORY_CHOICES],
        'selected_category': selected_category or 'All',
        'search_query': search_query,
    }
    return render(request, 'notes/note_list.html', context)


@login_required
def note_detail_view(request, pk):
    """
    Displays full decrypted note details.
    ENFORCES STRICT OWNERSHIP: If note.owner != request.user, returns HTTP 403 Forbidden.
    """
    note = get_object_or_404(Note, pk=pk)

    # BACKEND AUTHORIZATION CHECK
    if note.owner != request.user:
        return HttpResponseForbidden("Authorization Error: You do not have permission to access this note.")

    # EXPLICIT DECRYPTION
    try:
        decrypted_content = decrypt_text(note.encrypted_content)
        decryption_error = False
    except DecryptionError as exc:
        decrypted_content = f"Error: Unable to decrypt note content. Details: {exc}"
        decryption_error = True

    context = {
        'note': note,
        'decrypted_content': decrypted_content,
        'decryption_error': decryption_error,
    }
    return render(request, 'notes/note_detail.html', context)


@login_required
def note_create_view(request):
    """
    Creates a new note.
    Flow: Form Input (Plaintext) -> encrypt_text() -> Note.encrypted_content -> DB
    """
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            category = form.cleaned_data['category']
            plain_content = form.cleaned_data['content']

            # EXPLICIT ENCRYPTION
            ciphertext = encrypt_text(plain_content)

            note = Note.objects.create(
                owner=request.user,
                title=title,
                category=category,
                encrypted_content=ciphertext
            )
            messages.success(request, f'Note "{note.title}" created and encrypted successfully!')
            return redirect('note_detail', pk=note.pk)
        else:
            messages.error(request, 'Please fix the errors in the form.')
    else:
        form = NoteForm()

    return render(request, 'notes/note_form.html', {'form': form, 'is_edit': False})


@login_required
def note_update_view(request, pk):
    """
    Updates an existing note.
    Pre-fills form with decrypted content, then re-encrypts updated content on save.
    ENFORCES STRICT OWNERSHIP: If note.owner != request.user, returns HTTP 403 Forbidden.
    """
    note = get_object_or_404(Note, pk=pk)

    # BACKEND AUTHORIZATION CHECK
    if note.owner != request.user:
        return HttpResponseForbidden("Authorization Error: You do not have permission to edit this note.")

    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            plain_content = form.cleaned_data['content']

            # EXPLICIT RE-ENCRYPTION
            note.title = form.cleaned_data['title']
            note.category = form.cleaned_data['category']
            note.encrypted_content = encrypt_text(plain_content)
            note.save()

            messages.success(request, f'Note "{note.title}" updated and re-encrypted successfully!')
            return redirect('note_detail', pk=note.pk)
        else:
            messages.error(request, 'Please fix the errors in the form.')
    else:
        # Pre-fill with decrypted content for editing
        try:
            initial_content = decrypt_text(note.encrypted_content)
        except DecryptionError:
            initial_content = ""
            messages.warning(request, 'Warning: Note content could not be decrypted. Editing will overwrite with new content.')

        form = NoteForm(initial={
            'title': note.title,
            'category': note.category,
            'content': initial_content
        })

    return render(request, 'notes/note_form.html', {'form': form, 'is_edit': True, 'note': note})


@login_required
def note_delete_view(request, pk):
    """
    Deletes an existing note.
    ENFORCES STRICT OWNERSHIP: If note.owner != request.user, returns HTTP 403 Forbidden.
    """
    note = get_object_or_404(Note, pk=pk)

    # BACKEND AUTHORIZATION CHECK
    if note.owner != request.user:
        return HttpResponseForbidden("Authorization Error: You do not have permission to delete this note.")

    if request.method == 'POST':
        title = note.title
        note.delete()
        messages.success(request, f'Note "{title}" was permanently deleted.')
        return redirect('note_list')

    # If accessed via GET, redirect to note detail or list
    return redirect('note_detail', pk=note.pk)
