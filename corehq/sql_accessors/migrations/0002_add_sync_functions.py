from django.db import migrations

from corehq.form_processor.models import CommCareCaseIndex
from corehq.sql_db.operations import RawSQLMigration

migrator = RawSQLMigration(('corehq', 'sql_accessors', 'sql_templates'), {
    'RELATIONSHIP_TYPE_EXTENSION': CommCareCaseIndex.EXTENSION
})


class Migration(migrations.Migration):

    dependencies = [
        ('sql_accessors', '0001_initial')
    ]

    operations = [
        migrator.get_migration('get_case_last_modified_dates.sql'),
        migrator.get_migration('case_has_transactions_since_sync.sql'),
    ]
