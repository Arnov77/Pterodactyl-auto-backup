# Pterodactyl auto backup

This script automates the process of creating backups on a Pterodactyl server, downloading them, and uploading them to Google Drive. It also supports Discord notifications to track the status of backup operations.

## Features

- **Backup Creation**: Automatically creates backups on a Pterodactyl server using its API.
- **Backup Download**: Downloads the created backup from the server once the creation process is completed.
- **Upload to Google Drive**: Uploads the downloaded backup file to Google Drive using the Google Drive API.
- **Discord Notifications**: Sends notifications to Discord for each stage of the backup operation (creation, download, upload).

## Requirements

- Python 3.x installed.
- Required Python packages: `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`, `requests`.

## Installation

1. Clone this repository to your local directory:

   ```
   git clone https://github.com/Arnov77/Pterodactyl-auto-backup.git
   cd Pterodactyl-auto-backup
   ```

2. Install all required dependencies using pip:

   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `config.json` file with the following structure and fill in the information according to your environment:

   ```json
   {
       "discord_webhook_url": "https://YOUR_DISCORD_WEBHOOK_URL",
       "pterodactyl_api_key": "YOUR_PTERODACTYL_API_KEY",
       "pterodactyl_url": "https://YOUR_PTERODACTYL_URL",
       "server_id": "YOUR_SERVER_ID",
       "google_credentials_file": "./credentials.json",
       "drive_folder_id": "YOUR_DRIVE_FOLDER_ID"
   }
   ```

   - `discord_webhook_url`: Discord webhook URL for sending notifications.
   - `pterodactyl_api_key`: API key to access the Pterodactyl API.
   - `pterodactyl_url`: URL of your Pterodactyl panel.
   - `server_id`: ID of the server where backups will be managed.
   - `google_credentials_file`: Path to your Google Drive credentials JSON file.
   - `drive_folder_id`: ID of the Google Drive folder where backups will be uploaded.

2. Save and edit `config.json` with the correct information before running the script.

## Usage

Run the script using Python:

```
python3 backup.py
```

The script will perform the following actions:

- Creates a new backup on the specified Pterodactyl server.
- Downloads the backup once it's completed.
- Uploads the backup to Google Drive.
- Deletes the local backup file after a successful upload.

## Setting Up a Cronjob

To run the script automatically at specified intervals, you can set up a cronjob. Here’s how you can do it:

1. Open the crontab editor:

   ```
   crontab -e
   ```

2. Add the following line to schedule the script. For example, to run the script every day at 2 AM:

   ```
   0 2 * * * /usr/bin/python3 /path/to/your/backup.py >> /path/to/your/backup.log 2>&1
   ```

   Make sure to replace `/usr/bin/python3` with the path to your Python interpreter, and `/path/to/your/backup.py` with the actual path to your script.

3. Save and exit the editor. The script will now run automatically at the specified time.

## Discord Notifications

The script provides Discord notifications for each step of the operation. Ensure your Discord webhook is properly configured to receive notifications.

## Disclaimer

Use it at your own risk. Ensure you understand the implications of automating backups and handle sensitive data appropriately. The author is not responsible for any data loss or other issues that may arise from using this script.

## Notes

- Ensure the computer where the script is running has a stable internet connection.
- You must understand and correctly set all configuration values according to your needs before running the script.
