from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from .models import Project, Task
from .forms import CreateNewTask, CreateNewProject
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# Create your views here.


def index(request):
    title = 'Welcome to Django Course'
    return render(request, 'index.html', {
        'title': title
    })


def about(request):
    username = 'isao'
    return render(request, 'about.html', {
        'username': username
    })


def hello(request, username):
    return HttpResponse('<h1>Hello %s<h1>' % username)


def projects(request):
    # projects = list(Project.objects.values())
    projects = Project.objects.all()
    return render(request, 'projects/projects.html', {
        'projects': projects
    })


def create_project(request):
    if request.method == 'GET':
        return render(request, 'projects/create_project.html', {
            'form': CreateNewProject
        })
    else:
        Project.objects.create(name=request.POST['name'])
        return redirect('projects')


def tasks(request):
    tasks = Task.objects.all()
    # task = get_object_or_404(Task, id=id)
    return render(request, 'tasks/tasks.html', {
        'tasks': tasks
    })


def create_task(request):
    if request.method == 'GET':
        return render(request, 'tasks/create_task.html', {
            'form': CreateNewTask()
        })
    else:
        Task.objects.create(
            title=request.POST['title'], description=request.POST['description'], project_id=1)
        return redirect('tasks')
    
def project_detail(request, id):
    project = get_object_or_404(Project, id=id)
    tasks = Task.objects.filter(project_id=project)
    return render(request, 'projects/detail.html', {
        'nombre': project,
        'tasks': tasks
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index') # Redirige al inicio después del registro
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {
        'form': form
    })

def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # Log in the user
            user = form.get_user()
            login(request, user)
            return redirect('index') # Redirige al inicio después del login
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {
        'form': form
    })

def signout(request):
    logout(request)
    return redirect('index') # Redirige al inicio después del logout