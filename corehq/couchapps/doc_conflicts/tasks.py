from django.core.management import call_command

from celery.schedules import crontab

from corehq.apps.celery import periodic_task


@periodic_task(run_every=crontab(minute="0", hour="2", day_of_week="0"), queue='background_queue')
def remove_doc_conflicts():
    call_command('delete_doc_conflicts')
