# Umrah Footage AI Indexer & Ads Script Matcher

Sistem cerdas berbasis AI multimodal untuk mengindeks dokumentasi keberangkatan Umrah dari Google Drive (menggunakan Composio OAuth & Google Gemini), memotong metadata detik-demi-detik ke database SQLite, serta membedah naskah iklan (VO Ads Script) menjadi storyboard per 4-5 detik dengan rekomendasi footage yang sesuai.

Dikemas dengan UI modern elegan **White & Sunset Orange Glow** dan navigasi **Sidebar**, serta siap dideploy **24/7 di VPS** menggunakan Docker.

---

## 🌟 Fitur Utama

1. **Desain Elegan & Bersih**:
   - Tampilan bernuansa putih bersih dengan ambient glow halus.
   - Aksen oranye gradasi hangat dan abu-abu minimalis.
   - Navigasi sidebar vertikal di sebelah kiri yang responsif.

2. **Integrasi Google Drive via Composio**:
   - Membaca seluruh file video dan foto di bawah Folder ID Google Drive secara rekursif (termasuk subfolder).
   - Mendukung OAuth Google Drive bawaan Composio.

3. **Analisis Detik-demi-Detik dengan Gemini Multimodal**:
   - Mengekstrak scene visual per detik:
     - `start_time` & `end_time`
     - `location` (contoh: *Masjidil Haram - Mataf*, *Masjid Nabawi - Pelataran Payung*, *Jabal Uhud*)
     - `visual_description`
     - `tags` (keyword terindeks)
     - `mood` (khusyuk, haru, megah, syahdu, ceria, dll)
     - `pacing` (slow, medium, fast)
     - `suitability` (opening, emotional_hook, ibadah, broll, narration_fasilitas, closing)

4. **Background Worker & 24/7 Polling**:
   - Antrian pemrosesan video di latar belakang.
   - Pengecekan otomatis berkala (setiap 5 menit) ke Google Drive untuk mendeteksi file video baru yang diunggah ke subfolder.

5. **Ads Script Studio (Pencocokan Naskah Iklan)**:
   - Masukkan naskah suara (Voice-Over) iklan.
   - AI membedah naskah menjadi segmen per 4-5 detik, menentukan mood & kebutuhan visual ideal.
   - Mencocokkan naskah dengan database adegan video berdasarkan semantic vector search & mood.
   - Menampilkan persentase kecocokan (*Match Score %*).

6. **Integrated Video Player & Preview**:
   - Player video otomatis melompat ke detik `start_time` dan berhenti/loop di `end_time` klip tersebut.
   - Tombol download media dan link langsung ke Google Drive.

---

## 🌐 Deploy di VPS (24/7)

Aplikasi siap dijalankan 24/7 di VPS menggunakan Docker:

```bash
git clone https://github.com/zakyjamaluddin/umrah-footage-ai.git
cd umrah-footage-ai
chmod +x deploy.sh
./deploy.sh
```

Akses web di browser:
```
http://<IP_VPS_ANDA>:8000
```
Untuk panduan detail deployment VPS (Systemd, Nginx, Docker logs), lihat [DEPLOY_VPS.md](DEPLOY_VPS.md).

---

## 💻 Menjalankan di Komputer Lokal (Windows)

Cukup klik dua kali file:
```cmd
start_all.bat
```
Script ini akan otomatis membuka Backend (Port 8000) dan Frontend (Port 5173).

---

## ⚙️ Panduan Pengaturan API di UI

Buka menu **Pengaturan & API** di dashboard web:
1. **Google Drive Root Folder ID**:
   - Buka Google Drive di browser. Buka folder dokumentasi umrah Anda.
   - Salin ID dari URL browser: `https://drive.google.com/drive/folders/`**[AMBIL_ID_INI]**
2. **Composio API Key**:
   - Dapatkan API key dari [Composio Dashboard](https://app.composio.dev/).
3. **Google Gemini API Key**:
   - Dapatkan API key dari [Google AI Studio](https://aistudio.google.com/).
