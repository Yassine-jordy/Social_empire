"""Local administrator commands. Never expose save imports as a public route."""
import argparse
from getpass import getpass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    importer = commands.add_parser('import-save', help='Copy a 0.04a UUID save into a new account')
    importer.add_argument('save_file')
    importer.add_argument('--username', required=True)
    args = parser.parse_args()
    username = args.username.strip()
    if not username or len(username) > 80:
        parser.error('Username must contain 1–80 characters')
    password = getpass('New account password: ')
    if not password or len(password) > 1024 or password != getpass('Confirm password: '):
        parser.error('Passwords must match and contain 1–1024 characters')
    from database import init_database, register_user
    from sessions import load_saved_villages, import_village, discard_new_village
    init_database()
    load_saved_villages()
    try:
        created = register_user(username, password, create_village=lambda: import_village(args.save_file),
                                discard_village=discard_new_village)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    if not created:
        parser.error('Username or player identity already belongs to an account')
    print('Save copied and linked. Original file preserved. Start the server and log in.')


if __name__ == '__main__':
    main()
