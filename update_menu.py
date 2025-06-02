#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para actualizar el menú de Análisis por Origen en views.py
"""

import re

def update_menu():
    # Ruta al archivo views.py
    file_path = 'd:/CICLO 2025-I/SISTEMAS DE INFORMACIÓN/PROYECTO_WindSurf/citame-cursorV3/core/views.py'
    
    try:
        # Leer el contenido actual
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Definir el patrón de submenu actual (evitando caracteres especiales UTF-8)
        old_menu_pattern = r"'submenus': \[\s*\{\s*'nombre': 'Admisi[^\}]*'\s*\},\s*\{\s*'nombre': 'Derivaci[^\}]*'\s*\},\s*\{\s*'nombre': 'Seguimiento[^\}]*'\s*\}\s*\]"
        
        # Definir el nuevo contenido del submenu
        new_menu = """'submenus': [
                    {
                        'nombre': 'Citas por Reserva Directa',
                        'icono': 'fa-user-check',
                        'ruta': '/administrador/analisis-origen/reserva-directa/'
                    },
                    {
                        'nombre': 'Citas por Admisión',
                        'icono': 'fa-clipboard-list',
                        'ruta': '/administrador/analisis-origen/admision/'
                    },
                    {
                        'nombre': 'Citas por Derivación',
                        'icono': 'fa-share-nodes',
                        'ruta': '/administrador/analisis-origen/derivacion/'
                    },
                    {
                        'nombre': 'Citas por Seguimiento',
                        'icono': 'fa-clipboard-check',
                        'ruta': '/administrador/analisis-origen/seguimiento/'
                    },
                    {
                        'nombre': 'Análisis Comparativo',
                        'icono': 'fa-chart-bar',
                        'ruta': '/administrador/analisis-origen/comparativo/'
                    },
                    {
                        'nombre': 'Evolución Temporal',
                        'icono': 'fa-chart-line',
                        'ruta': '/administrador/analisis-origen/evolucion/'
                    }
                ]"""
        
        # Realizar la sustitución usando expresiones regulares
        updated_content = re.sub(old_menu_pattern, new_menu, content)
        
        # Comprobar si se realizó el cambio
        if updated_content == content:
            print("No se detectaron cambios. El patrón no coincidió.")
            return False
        
        # Guardar el contenido actualizado
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        print("¡Menú actualizado con éxito!")
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    update_menu()
