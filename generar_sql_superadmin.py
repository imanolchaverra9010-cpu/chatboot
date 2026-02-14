#!/usr/bin/env python
"""
Genera el SQL para insertar el superadmin con la contraseña correctamente hasheada.
Uso: python generar_sql_superadmin.py
     python generar_sql_superadmin.py MiClave123
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_project.settings')
django.setup()

from django.contrib.auth.hashers import make_password

username = os.getenv('SUPERADMIN_USERNAME', 'admin')
email = os.getenv('SUPERADMIN_EMAIL', 'admin@localhost.com')
password = sys.argv[1] if len(sys.argv) > 1 else os.getenv('SUPERADMIN_PASSWORD', 'Admin123!')

hashed = make_password(password)
# Escapar comillas para SQL
hashed_sql = hashed.replace("'", "''")

print(f"-- SQL generado para superadmin: {username}")
print(f"-- Ejecutar en la base de datos u659323332_ebano_company")
print()
print(f"INSERT INTO auth_user (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)")
print(f"VALUES ('{hashed_sql}', 1, '{username}', '', '', '{email}', 1, 1, NOW())")
print(f"ON DUPLICATE KEY UPDATE password = VALUES(password), is_superuser = 1, is_staff = 1, is_active = 1;")
