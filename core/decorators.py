from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    """
    Decorador que verifica si el usuario es un administrador.
    Si no lo es, redirige al dashboard con un mensaje de error.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a esta página.")
            return redirect('login')
        
        if not request.user.rol or request.user.rol.nombre != 'Administrador':
            messages.error(request, "No tiene permisos para acceder a esta página.")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def medico_required(view_func):
    """
    Decorador que verifica si el usuario es un médico.
    Si no lo es, redirige al dashboard con un mensaje de error.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a esta página.")
            return redirect('login')
        
        if not request.user.rol or request.user.rol.nombre != 'Medico':
            messages.error(request, "No tiene permisos para acceder a esta página.")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def paciente_required(view_func):
    """
    Decorador que verifica si el usuario es un paciente.
    Si no lo es, redirige al dashboard con un mensaje de error.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a esta página.")
            return redirect('login')
        
        if not request.user.rol or request.user.rol.nombre != 'Paciente':
            messages.error(request, "No tiene permisos para acceder a esta página.")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def admision_required(view_func):
    """
    Decorador que verifica si el usuario es de admisión.
    Si no lo es, redirige al dashboard con un mensaje de error.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a esta página.")
            return redirect('login')
        
        if not request.user.rol or request.user.rol.nombre != 'Admision':
            messages.error(request, "No tiene permisos para acceder a esta página.")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
