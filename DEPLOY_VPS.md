# Panduan Deployment di VPS (Jalan 24/7)

Aplikasi ini sudah dikemas siap produksi agar dapat berjalan terus menerus (24/7) di VPS Linux (Ubuntu / Debian / CentOS / AlmaLinux).

---

## Opsi 1: Menggunakan Docker & Docker Compose (Sangat Direkomendasikan)

Hanya perlu 3 langkah di terminal VPS:

### 1. Clone Repository di VPS
```bash
git clone https://github.com/zakyjamaluddin/umrah-footage-ai.git
cd umrah-footage-ai
```

### 2. Jalankan Deploy Script
```bash
chmod +x deploy.sh
./deploy.sh
```
*Script ini otomatis menginstal Docker jika belum ada, membangun image, dan menyalakan container dengan kebijakan `restart: always` (otomatis menyala kembali jika VPS reboot).*

### 3. Buka di Browser
Akses:
```
http://<IP_VPS_ANDA>:8000
```
Buka menu **Pengaturan & API** untuk memasukkan `Google Drive Folder ID`, `Composio API Key`, dan `Gemini API Key`. Semua data tersimpan di volume Docker `umrah_data`.

---

## Perintah Manajemen Docker di VPS

- **Melihat status & log real-time**:
  ```bash
  docker compose logs -f
  ```
- **Restart aplikasi**:
  ```bash
  docker compose restart
  ```
- **Menghentikan aplikasi**:
  ```bash
  docker compose down
  ```
- **Update kode terbaru dari GitHub**:
  ```bash
  git pull
  docker compose build
  docker compose up -d
  ```

---

## Opsi 2: Menggunakan Systemd (Tanpa Docker)

Jika ingin menjalankan langsung di Python virtualenv:

1. Install Python 3.12+, Node.js 22, dan git di VPS.
2. Build frontend:
   ```bash
   cd frontend && npm install && npm run build && cd ..
   ```
3. Setup virtual environment backend:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Buat systemd service di `/etc/systemd/system/umrah-ai.service`:
   ```ini
   [Unit]
   Description=Umrah Footage AI Indexer 24/7
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/root/umrah-footage-ai/backend
   ExecStart=/root/umrah-footage-ai/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```
5. Aktifkan service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable umrah-ai
   sudo systemctl start umrah-ai
   ```
