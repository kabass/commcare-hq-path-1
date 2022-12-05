from collections import defaultdict

from django.core.management.base import BaseCommand

from corehq.apps.userreports.dbaccessors import (
    drop_ucr_tables,
    get_deletable_ucrs,
    get_orphaned_tables_by_engine_id,
)


class Command(BaseCommand):
    """
    An orphaned UCR table is one where the related datasource no longer exists
    This command is designed to delete orphaned tables
    """
    help = "Delete orphaned UCR tables"

    def add_arguments(self, parser):
        parser.add_argument(
            '--engine_id',
            action='store',
            help='Only check this DB engine',
        )
        parser.add_argument(
            '--force-delete',
            action='store_true',
            default=False,
            help='Drop orphaned tables on active domains'
        )
        parser.add_argument(
            '--domain',
            action='store',
            help='Drop orphaned tables for a specific domain'
        )

    def handle(self, **options):
        orphaned_tables_by_engine_id = get_orphaned_tables_by_engine_id(options.get('engine_id'))
        try:
            ucrs_to_delete = get_deletable_ucrs(orphaned_tables_by_engine_id, force_delete=options['force_delete'],
                                                domain=options['domain'])
        except AssertionError as e:
            suggestions = """
            Use the '--domain' option to further inspect a specific domain.
            Use the '--force-delete' option if you are sure you want to
            delete all orphaned ucrs.
            """
            print(str(e))
            print(suggestions)
            exit(0)

        tablenames_to_drop = confirm_deletion_with_user(ucrs_to_delete)
        if not tablenames_to_drop:
            exit(0)

        drop_ucr_tables(tablenames_to_drop)


def confirm_deletion_with_user(ucrs_to_delete):
    if not ucrs_to_delete:
        print("There aren't any UCRs to delete.")
        return None

    tablenames_to_drop = defaultdict(list)
    for engine_id, ucr_infos in ucrs_to_delete.items():
        print(f"The following UCRs will be deleted in the {engine_id} database:")
        for ucr_info in ucr_infos:
            print(f"\t{ucr_info['tablename']} with {ucr_info['row_count']} rows.")
            tablenames_to_drop[engine_id].append(ucr_info['tablename'])

    if not tablenames_to_drop:
        print("No orphaned tables were found")
        return None

    if input("Are you sure you want to run the delete operation? (y/n)") == 'y':
        return tablenames_to_drop

    return None
