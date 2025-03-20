from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction

class Command(BaseCommand):
    help = 'Sets up the entire system including users, roles, permissions, and test data'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting system setup...'))
        
        # Step 1: Create user roles
        self.stdout.write(self.style.NOTICE('Step 1: Creating user roles...'))
        call_command('create_user_roles')
        
        # Step 2: Assign permissions
        self.stdout.write(self.style.NOTICE('Step 2: Assigning permissions...'))
        call_command('assign_permissions')
        
        # Step 3: Set up test data if it doesn't exist yet
        self.stdout.write(self.style.NOTICE('Step 3: Setting up test data...'))
        call_command('setup_test_data')
        
        self.stdout.write(self.style.SUCCESS('System setup completed successfully!')) 