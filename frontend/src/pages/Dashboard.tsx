import React, { useState, useEffect } from 'react';
import { RefreshCw, Video, Image as ImageIcon, Sparkles, AlertCircle, CheckCircle2, Clock, FolderGit2, ArrowRight, ExternalLink } from 'lucide-react';
import { api, FileItem, QueueTaskItem } from '../api';

export const Dashboard: React.FC<{ onNavigateToSettings: () => void }> = ({ onNavigateToSettings }) => {
  const [stats, setStats] = useState({
    totalFiles: 0,
    totalVideos: 0,
    totalImages: 0,
    totalScenes: 0,
  });
  const [queueTasks, setQueueTasks] = useState<QueueTaskItem[]>([]);
  const [scanStatus, setScanStatus] = useState<any>(null);
  const [isScanning, setIsScanning] = useState(false);

  const fetchData = async () => {
    try {
      const [filesRes, scenesRes, statusRes, queueRes] = await Promise.all([
        api.get('/files/'),
        api.get('/files/scenes/all'),
        api.get('/scan/status'),
        api.get('/scan/queue'),
      ]);

      const files: FileItem[] = filesRes.data.items || [];
      const scenes = scenesRes.data.items || [];
      const videos = files.filter((f) => f.file_type === 'video').length;
      const images = files.filter((f) => f.file_type === 'image').length;

      setStats({
        totalFiles: files.length,
        totalVideos: videos,
        totalImages: images,
        totalScenes: scenes.length,
      });

      setScanStatus(statusRes.data);
      setQueueTasks(queueRes.data.items || []);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerScan = async () => {
    setIsScanning(true);
    try {
      await api.post('/scan/trigger');
      await fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Gagal memicu scan');
    } finally {
      setIsScanning(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> Selesai
          </span>
        );
      case 'ANALYZING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200 animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-orange-500" /> Analisis Gemini...
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertCircle className="w-3.5 h-3.5 text-rose-500" /> Gagal
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <Clock className="w-3.5 h-3.5 text-slate-400" /> Antri (Pending)
          </span>
        );
    }
  };

  return (
    <div className="space-y-7">
      {/* Welcome Banner */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-7 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-orange-400/10 via-amber-300/10 to-transparent rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 border border-orange-200/80 text-orange-600 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              Sistem AI Metadata Dokumentasi Umrah
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Overview & Antrian Indexer
            </h1>
            <p className="text-sm text-slate-500 max-w-2xl leading-relaxed">
              Sistem otomatis menyusuri Google Drive secara rekursif, mengantrikan video dan foto, serta mengekstrak scene detik-demi-detik dengan Gemini AI. Background polling berjalan otomatis setiap 5 menit 24/7.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleTriggerScan}
              disabled={isScanning}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 via-orange-600 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-medium text-sm transition shadow-lg shadow-orange-500/20 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />
              <span>{isScanning ? 'Memindai Drive...' : 'Pindai Drive Sekarang'}</span>
            </button>
            <button
              onClick={onNavigateToSettings}
              className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium text-sm border border-slate-200 transition"
            >
              <FolderGit2 className="w-4 h-4 text-orange-500" />
              <span>Ubah Folder ID</span>
            </button>
          </div>
        </div>
      </div>

      {/* Warning if scan error or pending Google Drive Auth */}
      {scanStatus?.last_error && (
        <div className="bg-amber-50 border border-amber-200/90 rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-amber-900 leading-relaxed">
              <span className="font-bold">Status Koneksi Google Drive: </span>
              {scanStatus.last_error}
            </div>
          </div>
          {scanStatus?.composio_auth_url && (
            <a
              href={scanStatus.composio_auth_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center space-x-2 px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs transition shadow-sm flex-shrink-0"
            >
              <span>Hubungkan Google Drive</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total File</span>
            <div className="w-9 h-9 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center">
              <FolderGit2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-slate-900">{stats.totalFiles}</div>
          <span className="text-xs text-slate-400 mt-1 block">Video & Foto Tersimpan</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Video RAW</span>
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Video className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-slate-900">{stats.totalVideos}</div>
          <span className="text-xs text-slate-400 mt-1 block">Tawaf, Ziarah, Manasik</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Scene Terindeks</span>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-orange-500 to-amber-400 text-white flex items-center justify-center shadow-md shadow-orange-500/15">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent">
            {stats.totalScenes}
          </div>
          <span className="text-xs text-slate-400 mt-1 block">Scene terpotong per detik</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Foto & Landmark</span>
            <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center">
              <ImageIcon className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-slate-900">{stats.totalImages}</div>
          <span className="text-xs text-slate-400 mt-1 block">Hotel, Masjid, Jamaah</span>
        </div>
      </div>

      {/* Queue Monitoring Section */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-orange-500" />
              <span>Status Antrian AI & Background Polling</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Interval: {scanStatus?.polling_interval_minutes || 5} menit • Pengecekan terakhir:{' '}
              {scanStatus?.last_poll_time ? new Date(scanStatus.last_poll_time).toLocaleTimeString() : 'Belum pernah'}
            </p>
          </div>
          <button
            onClick={fetchData}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
            title="Refresh Antrian"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {queueTasks.length === 0 ? (
          <div className="p-12 text-center">
            <CheckCircle2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-slate-700">Antrian Kosong</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Tidak ada file yang sedang diantrikan. Sistem akan otomatis memeriksa file baru tiap 5 menit atau Anda dapat mengklik "Pindai Drive Sekarang".
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50/75 text-xs uppercase font-semibold text-slate-400 border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Nama File</th>
                  <th className="px-6 py-3.5">Tipe</th>
                  <th className="px-6 py-3.5">Status AI</th>
                  <th className="px-6 py-3.5">Waktu Update</th>
                  <th className="px-6 py-3.5 text-right">Drive ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {queueTasks.map((task) => (
                  <tr key={task.id || task.file_id} className="hover:bg-slate-50/70 transition">
                    <td className="px-6 py-4 font-medium text-slate-900 flex items-center gap-2.5">
                      {task.file_type === 'video' ? (
                        <div className="w-7 h-7 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center flex-shrink-0">
                          <Video className="w-3.5 h-3.5" />
                        </div>
                      ) : (
                        <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center flex-shrink-0">
                          <ImageIcon className="w-3.5 h-3.5" />
                        </div>
                      )}
                      <span className="truncate max-w-sm font-mono text-xs text-slate-800">{task.file_name}</span>
                    </td>
                    <td className="px-6 py-4 text-xs capitalize text-slate-500">{task.file_type}</td>
                    <td className="px-6 py-4">{getStatusBadge(task.status)}</td>
                    <td className="px-6 py-4 text-xs text-slate-400 font-mono">
                      {task.updated_at ? new Date(task.updated_at).toLocaleTimeString() : '-'}
                    </td>
                    <td className="px-6 py-4 text-right text-xs font-mono text-slate-400 truncate max-w-[140px]">
                      {task.file_id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
