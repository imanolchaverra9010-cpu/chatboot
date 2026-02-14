-- ============================================================
-- SCRIPT PARA CREAR SUPERADMIN EN LA BASE DE DATOS
-- ============================================================
--
-- OPCIÓN 1 (Recomendada): Usar el comando Django
--   cd chatboot-main
--   python manage.py create_superadmin
--   python manage.py create_superadmin --username admin --email admin@local.com --password TuClaveSegura
--
-- OPCIÓN 2: Generar SQL con hash correcto y ejecutarlo
--   python generar_sql_superadmin.py > sql_superadmin.sql
--   python generar_sql_superadmin.py --password MiClave > sql_superadmin.sql
--   mysql -h HOST -u USER -p u659323332_ebano_company < sql_superadmin.sql
--
-- OPCIÓN 3: Reemplaza HASH_AQUI con el hash generado por:
--   python manage.py shell -c "from django.contrib.auth.hashers import make_password; print(make_password('Admin123!'))"
-- ============================================================

INSERT INTO auth_user (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)
VALUES ('HASH_AQUI', 1, 'admin', '', '', 'admin@localhost.com', 1, 1, NOW())
ON DUPLICATE KEY UPDATE password = VALUES(password), is_superuser = 1, is_staff = 1, is_active = 1;
