from django.core.management.base import NoArgsCommand, CommandError, BaseCommand
from compareorgs.models import Job
import datetime

class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        
        one_hour_ago = datetime.datetime.now() - datetime.timedelta(minutes=60)
        jobs = Job.objects.filter(finished_date__lt = one_hour_ago)
        jobs.delete()


