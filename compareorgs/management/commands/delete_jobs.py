from django.core.management.base import NoArgsCommand, CommandError, BaseCommand
from compareorgs.models import Job
import datetime

class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        
        one_day_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
        jobs = Job.objects.filter(created_date__lt = one_day_ago)
        jobs.delete()


