import requests
import json
import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Path ke file konfigurasi
CONFIG_FILE_PATH = 'config.json'

# Template konfigurasi default
default_config = {
    "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
    "pterodactyl_api_key": "YOUR_PTERODACTYL_API_KEY",
    "pterodactyl_url": "YOUR_PTERODACTYL_URL",
    "server_id": "YOUR_SERVER_ID",
    "google_service_account_file": "./credentials.json",
    "drive_folder_id": "YOUR_DRIVE_FOLDER_ID"
}

# Fungsi untuk membuat file konfigurasi default jika tidak ada
def create_default_config():
    with open(CONFIG_FILE_PATH, 'w') as config_file:
        json.dump(default_config, config_file, indent=4)
    print(f"{CONFIG_FILE_PATH} tidak ditemukan. File konfigurasi default telah dibuat.")
    print(f"Silakan edit {CONFIG_FILE_PATH} dengan informasi yang benar sebelum menjalankan skrip lagi.")

# Memuat konfigurasi dari file
def load_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        create_default_config()
        exit(1)  # Keluar dari skrip setelah membuat file konfigurasi
    with open(CONFIG_FILE_PATH, 'r') as config_file:
        return json.load(config_file)

# Memuat konfigurasi
config = load_config()

# Discord webhook
def send_discord_notification(title, description, color=0x00ff00):
    url = config["discord_webhook_url"]
    data = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 204:
        print("Successfully sent message to Discord")
    else:
        print(f"Failed to send message to Discord: {response.status_code}")

# Pterodactyl API details
PTERODACTYL_API_KEY = config["pterodactyl_api_key"]
PTERODACTYL_URL = config["pterodactyl_url"]
SERVER_ID = config["server_id"]

# Google Drive API details
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = config["google_service_account_file"]
DRIVE_FOLDER_ID = config["drive_folder_id"]

# Create a backup on Pterodactyl
def create_backup():
    send_discord_notification("<a:loading1:1244939511180558337> Backup Start", "Starting backup process<a:loading:1244932877171560490>", color=0xffff00)
    url = f'{PTERODACTYL_URL}/api/client/servers/{SERVER_ID}/backups'
    headers = {
        'Authorization': f'Bearer {PTERODACTYL_API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    response = requests.post(url, headers=headers)
    
    response_data = response.json()
    
    if 'attributes' in response_data:
        backup_uuid = response_data['attributes']['uuid']
        send_discord_notification("<a:success:1244932963901243432> Backup Created", f"Backup created with UUID: {backup_uuid}")
        return backup_uuid
    else:
        send_discord_notification("<a:failed:1244933213592485928> Backup Failed", f"Failed to create backup. Response: {response.text}", 0xff0000)
        # Hapus atau komentar baris ini untuk menghilangkan pesan kesalahan
        # raise Exception("Failed to create backup: 'attributes' key not found in response")

# Check backup status
def check_backup_status(backup_uuid):
    url = f'{PTERODACTYL_URL}/api/client/servers/{SERVER_ID}/backups/{backup_uuid}'
    headers = {
        'Authorization': f'Bearer {PTERODACTYL_API_KEY}',
        'Accept': 'application/json',
    }
    response = requests.get(url, headers=headers)
    
    response_data = response.json()
    
    if 'attributes' in response_data:
        return response_data['attributes']['is_successful'], response_data['attributes']['completed_at']
    else:
        # Hapus atau komentar baris ini untuk menghilangkan pesan kesalahan
        # raise Exception(f"Failed to check backup status: 'attributes' key not found in response for backup UUID {backup_uuid}")
        return False, None

# Download backup file
def download_backup(backup_uuid):
    send_discord_notification("<a:loading1:1244939511180558337> Download Start", "Starting download process<a:loading:1244932877171560490>", color=0xffff00)
    url = f'{PTERODACTYL_URL}/api/client/servers/{SERVER_ID}/backups/{backup_uuid}/download'
    headers = {
        'Authorization': f'Bearer {PTERODACTYL_API_KEY}',
        'Accept': 'application/json',
    }
    response = requests.get(url, headers=headers)
    
    response_data = response.json()
    
    if 'attributes' in response_data:
        download_url = response_data['attributes']['url']
    else:
        send_discord_notification("<a:failed:1244933213592485928> Download Failed", f"Failed to retrieve download URL. Response: {response.text}", 0xff0000)
        # Hapus atau komentar baris ini untuk menghilangkan pesan kesalahan
        # raise Exception(f"Failed to retrieve download URL: 'attributes' key not found in response for backup UUID {backup_uuid}")
        return None

    # Ensure .temp folder exists
    if not os.path.exists('.temp'):
        os.makedirs('.temp')

    # Format file name with server UUID and current date-time
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_name = f'backup-{SERVER_ID}-{now}.tar.gz'
    file_path = os.path.join('.temp', file_name)

    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    send_discord_notification("<a:success:1244932963901243432> Download Successful", "Backup file downloaded successfully.")
    return file_path

# Upload backup to Google Drive
def upload_to_drive(file_path):
    send_discord_notification("<a:loading1:1244939511180558337> Upload Start", "Starting upload process<a:loading:1244932877171560490>", color=0xffff00)
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [DRIVE_FOLDER_ID]  # Specify Google Drive folder ID
    }
    media = MediaFileUpload(file_path, mimetype='application/gzip')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    send_discord_notification("<a:success:1244932963901243432> Upload Successful", "Backup file uploaded to Google Drive successfully.")
    return file.get('id')

def delete_backup(backup_uuid):
    url = f'{PTERODACTYL_URL}/api/client/servers/{SERVER_ID}/backups/{backup_uuid}'
    headers = {
        'Authorization': f'Bearer {PTERODACTYL_API_KEY}',
        'Accept': 'application/json',
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f'Successfully deleted backup {backup_uuid}')
    else:
        print(f'Failed to delete backup {backup_uuid}: {response.status_code}')

def main():
    try:
        backup_uuid = create_backup()
        backup_file = download_backup(backup_uuid)
        if backup_file:
            drive_file_id = upload_to_drive(backup_file)
            if drive_file_id:
                # Delete the local backup file after successful upload
                os.remove(backup_file)
                print(f"Deleted temporary file: {backup_file}")
                delete_backup(backup_uuid)
    except Exception as e:
        send_discord_notification("<a:failed:1244933213592485928> Error", f"An error occurred: {str(e)}", 0xff0000)

if __name__ == '__main__':
    main()
