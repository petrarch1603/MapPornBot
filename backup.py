from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from shutil import copyfile
import time

def upload_file(filepath, filename):
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()

    gauth.SaveCredentialsFile("mycreds.txt")
    drive = GoogleDrive(gauth)
    mapporn_db_backups_folder = '1KkrnuRRIWKA0oI102FmP-lGiRkeRxnYT'

    f = drive.CreateFile({"parents": [{"kind": "drive", "id": mapporn_db_backups_folder}], 'title': filename})
    f.SetContentFile(filepath)
    f.Upload()


def make_backup(source_db_path='data/mapporn.db'):
    backup_filename = 'backup' + str(time.strftime("%Y%m%d")) + '.db'
    backup_filepath = 'data/backup/' + backup_filename
    copyfile(source_db_path, backup_filepath)
    upload_file(backup_filepath, backup_filename)


if __name__ == "__main__":
    make_backup()
