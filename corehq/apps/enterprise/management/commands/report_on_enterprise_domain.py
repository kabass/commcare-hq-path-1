import io
from datetime import datetime

from django.core.management import BaseCommand
from django.core.management.base import CommandError
from django.template.defaultfilters import linebreaksbr

import csv

from corehq.apps.enterprise.enterprise import EnterpriseReport
from corehq.apps.accounting.models import (
    BillingAccount,
)
from corehq.apps.hqwebapp.tasks import send_html_email_async
from corehq.apps.users.models import CouchUser


class Command(BaseCommand):
    help = '''
        Generate four CSVs containing details on an enterprise project's domains, web users,
        mobile workers, and recent form submissions.

        Usage:
           report_on_enterprise_domain ACCOUNT_ID USERNAME
    '''

    def add_arguments(self, parser):
        parser.add_argument('account_id')
        parser.add_argument('username')
        parser.add_argument(
            '-m',
            '--message',
            action='store',
            dest='message',
            help='Message to add to email (optional)',
        )
        parser.add_argument(
            '-c',
            '--cc',
            action='store',
            dest='cc',
            help='Comma-separated emails to CC (optional)',
        )

    def _write_file(self, slug):
        report = EnterpriseReport.create(slug, self.account_id, self.couch_user)

        row_count = 0
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)
        writer.writerow(report.headers)

        rows = report.rows
        row_count = len(rows)
        writer.writerows(rows)

        print('Wrote {} lines of {}'.format(row_count, slug))
        attachment = {
            'title': report.filename,
            'mimetype': 'text/csv',
            'file_obj': csv_file,
        }
        return (attachment, row_count)

    def handle(self, account_id, username, **kwargs):
        self.couch_user = CouchUser.get_by_username(username)
        self.account_id = account_id

        if not self.couch_user:
            raise CommandError("Option: '--username' must be specified")

        self.now = datetime.utcnow()
        account = BillingAccount.objects.get(id=account_id)
        message = ''
        if kwargs.get('message'):
            message += kwargs.get('message') + "\n"
        message += "Report run {}\n".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

        attachments = []
        for slug in (
            EnterpriseReport.DOMAINS,
            EnterpriseReport.WEB_USERS,
            EnterpriseReport.MOBILE_USERS,
            EnterpriseReport.FORM_SUBMISSIONS,
        ):
            (attachment, count) = self._write_file(slug)
            attachments.append(attachment)
            message += "{}: {}\n".format(slug, count)

        cc = []
        if kwargs.get('cc'):
            cc = kwargs.get('cc').split(",")
        send_html_email_async(
            "Report on enterprise account {}".format(account.name), self.couch_user.get_email(),
            linebreaksbr(message), cc=cc, text_content=message, file_attachments=attachments,
        )
        print('Emailed {}{}{}'.format(self.couch_user.username, " and " if cc else "", ", ".join(cc)))
