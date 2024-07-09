import requests
import json
import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import time
import logging
import pickle

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# kode warna ANSI
reset = "\033[0m"
green = "\033[32m"
red = "\033[31m"
white = "\033[37m"
black = "\033[30m"
bgGreen = "\033[42m"
bgRed = "\033[41m"

# Path ke file konfigurasi
CONFIG_FILE_PATH = 'config.json'

# Template konfigurasi default
default_config = {
    "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
    "pterodactyl_api_key": "YOUR_PTERODACTYL_API_KEY",
    "pterodactyl_url": "YOUR_PTERODACTYL_URL",
    "server_id": "YOUR_SERVER_ID",
    "google_credentials_file": "./credentials.json",
    "drive_folder_id": "YOUR_DRIVE_FOLDER_ID"
}

# Fungsi untuk membuat file konfigurasi default jika tidak ada
def create_default_config():
    with open(CONFIG_FILE_PATH, 'w') as config_file:
        json.dump(default_config, config_file, indent=4)
    print(f"{bgRed}{black}[ERROR]{reset} {red}{CONFIG_FILE_PATH} tidak ditemukan. File konfigurasi default telah dibuat.")
    print(f"{white}Silakan edit {CONFIG_FILE_PATH} dengan informasi yang benar sebelum menjalankan skrip lagi.")

# load konfigurasi dari file
def load_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        create_default_config()
        exit(1)  # Keluar dari skrip setelah membuat file konfigurasi
    with open(CONFIG_FILE_PATH, 'r') as config_file:
        return json.load(config_file)

# load konfigurasi
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
        logging.info(f"{bgGreen}{black}[SUCCESS]{reset} successfully sent message to Discord")
    else:
        logging.error(f"{bgRed}{black}[ERROR]{reset} {red}Failed to send message to Discord: {response.status_code}{reset}")

# Pterodactyl API details
PTERODACTYL_API_KEY = config["pterodactyl_api_key"]
PTERODACTYL_URL = config["pterodactyl_url"]
SERVER_ID = config["server_id"]

# Google Drive API details
SCOPES = ['https://www.googleapis.com/auth/drive.file']
GOOGLE_CREDENTIALS_FILE = config["google_credentials_file"]
DRIVE_FOLDER_ID = config["drive_folder_id"]

# Fungsi autentikasi OAuth 2.0
def authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                # Try to open a browser to authenticate
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Local server authentication failed or no browser available: {e}")
                flow = Flow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
                flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

                auth_url, _ = flow.authorization_url(prompt='consent')
                print(f'Please visit this URL to authorize this application: {auth_url}')

                code = input('Enter the authorization code: ')
                flow.fetch_token(code=code)
                creds = flow.credentials
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

# Fungsi untuk mengunduh dengan retry
def download_with_retry(url, headers, file_path):
    retry_attempts = 5
    chunk_size = 81920  # Meningkatkan ukuran chunk
    try:
        resume_header = {}
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            resume_header = {'Range': f'bytes={file_size}-'}
        else:
            file_size = 0

        for attempt in range(retry_attempts):
            try:
                with requests.get(url, headers={**headers, **resume_header}, stream=True, timeout=30) as r:  # Menambah timeout
                    r.raise_for_status()
                    mode = 'ab' if file_size > 0 else 'wb'
                    with open(file_path, mode) as f:
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            if chunk:  # filter out keep-alive new chunks
                                f.write(chunk)
                return
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt+1} failed: {e}")
                time.sleep(5)  # Tunggu sebelum mencoba lagi
    except Exception as e:
        raise RuntimeError(f"Failed to download file after {retry_attempts} attempts: {str(e)}")

# membuat backup di pterodactyl
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
        return None

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
        return False, None

# Download backup file dengan retry dan cek status
def download_backup(backup_uuid):
    send_discord_notification("<a:loading1:1244939511180558337> Download Start", "Starting download process<a:loading:1244932877171560490>", color=0xffff00)
    
    # Cek status backup
    is_successful, completed_at = False, None
    max_retries = 30  # Jumlah maksimum pengecekan
    retry_interval = 60  # Interval antara pengecekan (dalam detik)
    
    for _ in range(max_retries):
        is_successful, completed_at = check_backup_status(backup_uuid)
        if is_successful:
            break
        time.sleep(retry_interval)
    
    if not is_successful:
        send_discord_notification("<a:failed:1244933213592485928> Backup Failed", "Backup did not complete successfully in the allotted time.", 0xff0000)
        return None
    
    # Lanjutkan ke proses download jika backup sukses
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
        return None

    # memastikan file .temp ada dan membuat file .temp jika tidak ada
    if not os.path.exists('.temp'):
        os.makedirs('.temp')

    # format file dengan nama, tanggal dan waktu
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_name = f'backup-{SERVER_ID}-{now}.tar.gz'
    file_path = os.path.join('.temp', file_name)

    # Menggunakan download_with_retry untuk mengunduh file
    download_with_retry(download_url, headers, file_path)

    send_discord_notification("<a:success:1244932963901243432> Download Successful", "Backup file downloaded successfully.")
    return file_path

# Upload backup ke Google Drive dengan chunked upload
def upload_to_drive(file_path):
    send_discord_notification("<a:loading1:1244939511180558337> Upload Start", "Starting upload process<a:loading:1244932877171560490>", color=0xffff00)
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [DRIVE_FOLDER_ID]
    }
    
    media = MediaFileUpload(file_path, mimetype='application/gzip', resumable=True)
    
    request = service.files().create(body=file_metadata, media_body=media, fields='id')
    response = None
    while response is None:
        try:
            logging.info("Uploading file...")
            status, response = request.next_chunk()
            if status:
                logging.info(f"Uploaded {int(status.progress() * 100)}%")
        except Exception as e:
            logging.error(f"An error occurred during upload: {e}")
            time.sleep(5)
    
    if response:
        send_discord_notification("<a:success:1244932963901243432> Upload Successful", "Backup file uploaded to Google Drive successfully.")
        return response.get('id')
    else:
        send_discord_notification("<a:failed:1244933213592485928> Upload Failed", "Failed to upload file to Google Drive.", 0xff0000)
        return None

def delete_backup(backup_uuid):
    url = f'{PTERODACTYL_URL}/api/client/servers/{SERVER_ID}/backups/{backup_uuid}'
    headers = {
        'Authorization': f'Bearer {PTERODACTYL_API_KEY}',
        'Accept': 'application/json',
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        logging.info(f'{bgGreen}{black}[SUCCESS]{reset} Successfully deleted backup {backup_uuid}')
    else:
        logging.error(f'{bgRed}{black}[ERROR]{reset} {red}Failed to delete backup {backup_uuid}: {response.status_code}')

def main():
    try:
        backup_uuid = create_backup()
        if backup_uuid:
            backup_file = download_backup(backup_uuid)
            if backup_file:
                drive_file_id = upload_to_drive(backup_file)
                if drive_file_id:
                    # Menghapus lokal file setelah selesai upload
                    os.remove(backup_file)
                    logging.info(f"Deleted temporary file: {backup_file}")
                    delete_backup(backup_uuid)
    except Exception as e:
        send_discord_notification("<a:failed:1244933213592485928> Error", f"An error occurred: {str(e)}", 0xff0000)

if __name__ == '__main__':
    main()
