from django.core.management.base import BaseCommand
from CRM.models import CRMUser


class Command(BaseCommand):
    help = 'Create a CRM admin user'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Full name')
        parser.add_argument('--mobile', type=str, required=True, help='Mobile number')
        parser.add_argument('--pin', type=str, required=True, help='4-digit PIN')

    def handle(self, *args, **options):
        name = options['name']
        mobile = options['mobile']
        pin = options['pin']

        if len(pin) != 4 or not pin.isdigit():
            self.stderr.write(self.style.ERROR('PIN must be exactly 4 digits.'))
            return

        if CRMUser.objects.filter(mobile=mobile).exists():
            self.stderr.write(self.style.ERROR(f'User with mobile {mobile} already exists.'))
            return

        user = CRMUser(name=name, mobile=mobile, role='admin')
        user.set_pin(pin)
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f'CRM Admin created: {name} ({mobile})'
        ))
