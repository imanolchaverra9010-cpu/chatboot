"""
Comando para crear superadmin en la base de datos
Uso: python manage.py create_superadmin
     python manage.py create_superadmin --username admin --email admin@local.com --password MiClaveSegura123
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un superusuario admin (o actualiza si ya existe)'

    def add_arguments(self, parser):
        parser.add_argument('--username', default=os.getenv('SUPERADMIN_USERNAME', 'admin'))
        parser.add_argument('--email', default=os.getenv('SUPERADMIN_EMAIL', 'admin@localhost.com'))
        parser.add_argument('--password', default=os.getenv('SUPERADMIN_PASSWORD', 'Admin123!'))

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superadmin "{username}" actualizado correctamente.'))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superadmin "{username}" creado correctamente.'))

        self.stdout.write(f'   Usuario: {username}')
        self.stdout.write(f'   Email:  {email}')
        self.stdout.write(f'   Password: {"*" * len(password)}')
