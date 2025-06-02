from django import template

register = template.Library()

@register.filter
def divisor(value, arg):
    """Divide el valor por el argumento"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def get_item(dictionary, key):
    """Obtiene un elemento de un diccionario por su clave"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def subtract(value, arg):
    """Resta el argumento del valor"""
    try:
        return float(value) - float(arg)
    except ValueError:
        return 0

@register.filter
def add(value, arg):
    """Suma el argumento al valor"""
    try:
        return float(value) + float(arg)
    except ValueError:
        return 0

@register.filter
def percentage(value, arg):
    """Calcula el porcentaje: (value/arg)*100"""
    try:
        return (float(value) / float(arg)) * 100
    except (ValueError, ZeroDivisionError):
        return 0
