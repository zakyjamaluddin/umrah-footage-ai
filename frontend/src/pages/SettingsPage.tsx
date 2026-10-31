import React, { useState, useEffect } from 'react';
import { Settings, Key, FolderGit2, Clock, CheckCircle2, Save, ExternalLink, ShieldCheck, AlertTriangle } from 'lucide-react';
import { api, AppSettings } from '../api';

export const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<AppSettings>({
    google_drive_folder_id: '',
    composio_api_key_set: false,
    composio_api_key_masked: '',
    gemini_api_key_set: false,
    gemini_api_key_masked: '',
    polling_interval_minutes: 5,
    auto_polling_enabled: true,
    gdrive_connected: false,
    gdrive_status: '',
    gdrive_auth_url: '',
  });

  const [folderId, setFolderId] = useState('');
  const [composioKey, setComposioKey] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [pollingMinutes, setPollingMinutes] = useState(5);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchSettings = async () => {
    try {
      const res = await api.get('/settings/');
      const data: AppSettings = res.data;
      setConfig(data);
      setFolderId(data.google_drive_folder_id || '');
      setPollingMinutes(data.polling_interval_minutes || 5);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      await api.post('/settings/', {
        google_drive_folder_id: folderId,
        composio_api_key: composioKey || undefined,
        gemini_api_key: geminiKey || undefined,
        polling_interval_minutes: Number(pollingMinutes),
      });

      await fetchSettings();
      setComposioKey('');
      setGeminiKey('');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      alert(err.response?.data?.message || 'Gagal menyimpan pengaturan');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Settings className="w-5 h-5 text-orange-500" />
          <span>Pengaturan Sistem & Integrasi API</span>
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Konfigurasikan Folder ID Google Drive, API Key Composio (OAuth GDrive), dan Gemini API Key untuk pemrosesan AI 24/7 di VPS.
        </p>
      </div>

      {saveSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center gap-3 text-emerald-800 text-sm shadow-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
          <span>Pengaturan berhasil disimpan dan scheduler background 24/7 telah diperbarui!</span>
        </div>
      )}

      {/* Google Drive OAuth Connection Status Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${
              config.gdrive_connected 
                ? 'bg-emerald-50 text-emerald-600' 
                : 'bg-amber-50 text-amber-600'
            }`}>
              {config.gdrive_connected ? <ShieldCheck className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900">Otorisasi Akun Google Drive (Composio)</h3>
                <span className={`text-[11px] px-2.5 py-0.5 rounded-full border font-semibold ${
                  config.gdrive_connected
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border-amber-200'
                }`}>
                  {config.gdrive_connected ? 'Aktif & Terhubung (ACTIVE)' : `Belum Terhubung (${config.gdrive_status || 'INITIALIZING'})`}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {config.gdrive_connected
                  ? 'Akun Google Drive Anda telah terhubung. Sistem dapat membaca folder dan mengindeks video secara otomatis.'
                  : 'Selesaikan otorisasi Google Drive agar AI dapat membaca file video footage di folder Google Drive Anda.'}
              </p>
            </div>
          </div>

          {/* Action button if not connected or to reconnect */}
          {config.gdrive_auth_url && (
            <a
              href={config.gdrive_auth_url}
              target="_blank"
              rel="noopener noreferrer"
              className={`flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl font-bold text-xs transition shadow-sm ${
                config.gdrive_connected
                  ? 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  : 'bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white shadow-orange-500/20'
              }`}
            >
              <span>{config.gdrive_connected ? 'Hubungkan Ulang Drive' : 'Hubungkan Google Drive Sekarang'}</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Google Drive Folder Setting */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center">
              <FolderGit2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Google Drive Root Folder ID</h3>
              <p className="text-xs text-slate-500">
                Sistem akan memindai folder ini dan seluruh subfoldernya secara rekursif.
              </p>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1.5">Google Drive Folder ID:</label>
            <input
              type="text"
              value={folderId}
              onChange={(e) => setFolderId(e.target.value)}
              placeholder="Contoh: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"
              className="w-full px-4 py-2.5 bg-slate-50/70 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 focus:bg-white font-mono transition"
            />
            <p className="text-[11px] text-slate-400 mt-1.5">
              Tips: Buka folder di Google Drive browser, Folder ID adalah string acak setelah <code className="text-slate-600 font-semibold">drive.google.com/drive/folders/<strong>[ID_FOLDER]</strong></code>
            </p>
          </div>
        </div>

        {/* Composio & Gemini API Keys */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-sm space-y-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Integrasi Composio & Gemini API</h3>
              <p className="text-xs text-slate-500">
                Kunci otentikasi untuk membaca file Drive melalui Composio dan menganalisa video menggunakan Gemini.
              </p>
            </div>
          </div>

          {/* Composio Key */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-700">Composio Access Key (ak_...):</label>
              <span className={`text-[11px] px-2.5 py-0.5 rounded-full border font-medium ${config.composio_api_key_set ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'}`}>
                {config.composio_api_key_set ? `Terpasang (${config.composio_api_key_masked})` : 'Belum Terpasang'}
              </span>
            </div>
            <input
              type="password"
              value={composioKey}
              onChange={(e) => setComposioKey(e.target.value)}
              placeholder={config.composio_api_key_set ? 'Biarkan kosong jika tidak ingin mengubah' : 'ak_... (Composio Access Key)'}
              className="w-full px-4 py-2.5 bg-slate-50/70 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 focus:bg-white font-mono transition"
            />
          </div>

          {/* Gemini Key */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-700">Google Gemini API Key:</label>
              <span className={`text-[11px] px-2.5 py-0.5 rounded-full border font-medium ${config.gemini_api_key_set ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'}`}>
                {config.gemini_api_key_set ? `Terpasang (${config.gemini_api_key_masked})` : 'Belum Terpasang'}
              </span>
            </div>
            <input
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder={config.gemini_api_key_set ? 'Biarkan kosong jika tidak ingin mengubah' : 'AIzaSy... (Gemini API Key)'}
              className="w-full px-4 py-2.5 bg-slate-50/70 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 focus:bg-white font-mono transition"
            />
          </div>
        </div>

        {/* Polling Interval Setting */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Interval Background Polling (24/7)</h3>
              <p className="text-xs text-slate-500">
                Sistem akan mengecek folder Google Drive secara berkala di background untuk mendeteksi video baru.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="number"
              min="1"
              max="60"
              value={pollingMinutes}
              onChange={(e) => setPollingMinutes(Number(e.target.value))}
              className="w-24 px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 font-bold focus:outline-none focus:border-orange-500 text-center font-mono"
            />
            <span className="text-xs text-slate-600 font-medium">Menit sekali (Default: 5 Menit)</span>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={isSaving}
            className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-gradient-to-r from-orange-500 via-orange-600 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold text-sm transition shadow-lg shadow-orange-500/20 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{isSaving ? 'Menyimpan...' : 'Simpan Semua Pengaturan'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
