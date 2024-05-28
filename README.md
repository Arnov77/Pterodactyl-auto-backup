# Auto Backup Server Pterodactyl dan Upload ke Google Drive

Script ini melakukan backup otomatis pada server Pterodactyl dan mengupload ke Google Drive menggunakan Google Drive API dari Google Cloud dan API Pterodactyl. Setelah backup berhasil diupload, script juga akan menghapus backup lokal dan mengirimkan notifikasi ke Discord menggunakan webhook.

## Persyaratan

- Python 3.6 atau lebih baru
- Akun Google Cloud dengan credentials akun layanan untuk Google Drive API
- API key Pterodactyl
- Webhook URL Discord

## Instalasi

1. **Clone repositori ini:**

    ```bash
    git clone https://github.com/Arnov77/Pterodactyl-auto-backup.git
    cd repository
    ```

2. **Install dependensi:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Tambahkan credentials Google Drive:**

    Unduh file credentials account service dari Google Cloud Console dan letakkan di direktori project sebagai `credentials.json`.

## Penggunaan

Jalankan script untuk melakukan backup dan upload ke Google Drive:

```bash
python backup.py
