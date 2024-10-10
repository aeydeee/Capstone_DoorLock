import os
import subprocess
import time
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# Function to perform MySQL dump and save the file without exposing the password in the command
def backup_database_with_retry(db_user, db_password, db_name, db_host='localhost', retries=3, delay=5):
    backup_filename = os.path.join(os.path.dirname(__file__),
                                   f"{db_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")

    # Set the MYSQL_PWD environment variable temporarily
    env = os.environ.copy()
    env["MYSQL_PWD"] = db_password  # Securely pass the password via environment variable

    dump_command = f"mysqldump -u {db_user} -h {db_host} {db_name} > {backup_filename}"

    for attempt in range(retries):
        result = subprocess.run(dump_command, shell=True, env=env)  # Pass the env variable here
        if result.returncode == 0:
            return backup_filename
        else:
            print(f"Backup attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)

    raise Exception(f"Error during MySQL dump after {retries} retries: Command '{dump_command}' failed.")


# Function to delete all files in the specified Google Drive folder
def delete_all_files_in_drive_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print("No files found in the folder.")
    else:
        for item in items:
            service.files().delete(fileId=item['id']).execute()
            print(f"Deleted file '{item['name']}' with ID {item['id']}")


# Function to authenticate with Google Drive API and upload the backup file
def upload_to_google_drive(file_name, folder_id=None):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = None
    credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=5000, access_type='offline')  # Ensure offline access for refresh token
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    # Delete all files in the target folder
    if folder_id:
        delete_all_files_in_drive_folder(service, folder_id)

    # Upload the new backup file
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    media = MediaFileUpload(file_name, mimetype='application/sql')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"Backup uploaded to Google Drive with file ID: {file.get('id')}")


# Main function to trigger the backup and upload
def backup_and_upload(db_user, db_password, db_name, folder_id=None, db_host='localhost'):
    backup_file = backup_database_with_retry(db_user, db_password, db_name, db_host)
    upload_to_google_drive(backup_file, folder_id)
    if os.path.exists(backup_file):
        os.remove(backup_file)
        print(f"Local backup file '{backup_file}' deleted.")


# Function to trigger full backup (existing logic)
def run_full_backup():
    DB_USER = os.environ.get('DB_USERNAME')  # Now properly getting environment variable as string
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')  # Optionally use DB_HOST, default to localhost
    DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID')

    if not all([DB_USER, DB_PASSWORD, DB_NAME]):
        raise Exception("Database credentials or name missing from environment variables.")

    # Run backup and upload
    backup_and_upload(DB_USER, DB_PASSWORD, DB_NAME, DRIVE_FOLDER_ID, DB_HOST)
