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
    """Multiplica un valor por otro"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Obtiene un elemento de un diccionario por su clave"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def subtract(value, arg):
    """Resta un valor de otro"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Suma el argumento al valor"""
    try:
        return float(value) + float(arg)
    except ValueError:
        return 0

@register.filter
def percentage(value, total):
    """Calcula el porcentaje de un valor respecto al total"""
    try:
        if total == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def stock_class(medicamento):
    """Devuelve la clase CSS según el nivel de stock"""
    if medicamento.stock_actual <= medicamento.stock_minimo:
        return 'bg-danger'
    elif medicamento.stock_actual <= medicamento.stock_minimo * 2:
        return 'bg-warning'
    else:
        return 'bg-success'

@register.filter
def stock_status(medicamento):
    """Devuelve el estado textual del stock"""
    if medicamento.stock_actual <= medicamento.stock_minimo:
        return 'Crítico'
    elif medicamento.stock_actual <= medicamento.stock_minimo * 2:
        return 'Bajo'
    else:
        return 'Normal'
