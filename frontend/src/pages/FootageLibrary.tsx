import React, { useState, useEffect } from 'react';
import { Search, Play, Download, Clock, MapPin, Film, Image as ImageIcon, ExternalLink } from 'lucide-react';
import { api, FileItem, Scene } from '../api';

interface FootageLibraryProps {
  onSelectScene: (scene: Scene, file?: FileItem) => void;
}

export const FootageLibrary: React.FC<FootageLibraryProps> = ({ onSelectScene }) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMood, setSelectedMood] = useState('all');
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [selectedSuitability, setSelectedSuitability] = useState('all');
  const [activeView, setActiveView] = useState<'files' | 'scenes'>('files');
  const [loading, setLoading] = useState(true);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const res = await api.get('/files/?limit=1000');
      setFiles(res.data.items || []);
    } catch (err) {
      console.error('Error fetching files:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  // Collect all scenes flat
  const allScenes: (Scene & { parentFile: FileItem })[] = [];
  files.forEach((f) => {
    f.scenes.forEach((s) => {
      allScenes.push({
        ...s,
        file_name: f.file_name,
        storage_url: f.storage_url,
        stream_url: f.stream_url,
        preview_url: f.preview_url,
        thumbnail_url: f.thumbnail_url,
        file_type: f.file_type,
        parentFile: f,
      });
    });
  });

  // Filter scenes
  const filteredScenes = allScenes.filter((s) => {
    const matchesSearch =
      !searchQuery ||
      s.visual_description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesMood = selectedMood === 'all' || s.mood.toLowerCase() === selectedMood.toLowerCase();
    const matchesLocation = selectedLocation === 'all' || s.location.toLowerCase().includes(selectedLocation.toLowerCase());
    const matchesSuitability =
      selectedSuitability === 'all' || s.suitability.some((st) => st.toLowerCase() === selectedSuitability.toLowerCase());

    return matchesSearch && matchesMood && matchesLocation && matchesSuitability;
  });

  const uniqueMoods = Array.from(new Set(allScenes.map((s) => s.mood).filter(Boolean)));
  const uniqueLocations = Array.from(new Set(allScenes.map((s) => s.location).filter(Boolean)));

  const getMoodBadge = (mood: string) => {
    switch (mood.toLowerCase()) {
      case 'khusyuk':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'haru':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'megah':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'syahdu':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'ceria':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Film className="w-5 h-5 text-orange-500" />
            <span>Footage Library & Scene Index</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Jelajahi dokumentasi Umrah yang telah dipotong dan dianalisa oleh Gemini per adegan detik.
          </p>
        </div>

        {/* View Switcher */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200/80 self-start sm:self-auto">
          <button
            onClick={() => setActiveView('files')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeView === 'files'
                ? 'bg-white text-orange-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Per File Video ({files.length})
          </button>
          <button
            onClick={() => setActiveView('scenes')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeView === 'scenes'
                ? 'bg-white text-orange-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Semua Scene ({allScenes.length})
          </button>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-sm grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Cari deskripsi, lokasi, tag..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50/70 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 focus:bg-white transition"
          />
        </div>

        <div>
          <select
            value={selectedMood}
            onChange={(e) => setSelectedMood(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50/70 border border-slate-200 rounded-xl text-xs text-slate-700 focus:outline-none focus:border-orange-500 focus:bg-white transition"
          >
            <option value="all">Semua Mood</option>
            {uniqueMoods.map((m) => (
              <option key={m} value={m}>
                {m.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        <div>
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50/70 border border-slate-200 rounded-xl text-xs text-slate-700 focus:outline-none focus:border-orange-500 focus:bg-white transition"
          >
            <option value="all">Semua Lokasi</option>
            {uniqueLocations.map((loc) => (
              <option key={loc} value={loc}>
                {loc}
              </option>
            ))}
          </select>
        </div>

        <div>
          <select
            value={selectedSuitability}
            onChange={(e) => setSelectedSuitability(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50/70 border border-slate-200 rounded-xl text-xs text-slate-700 focus:outline-none focus:border-orange-500 focus:bg-white transition"
          >
            <option value="all">Kesesuaian Iklan</option>
            <option value="opening">Opening / Hook</option>
            <option value="emotional_hook">Emotional Hook</option>
            <option value="ibadah">Ibadah / Khusyuk</option>
            <option value="broll">B-Roll Footage</option>
            <option value="narration_fasilitas">Fasilitas & Hotel</option>
            <option value="closing">Closing / CTA</option>
          </select>
        </div>
      </div>

      {/* Content View */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-sm">Memuat metadata footage...</div>
      ) : activeView === 'files' ? (
        /* Video Files Group View */
        <div className="space-y-4">
          {files.map((file) => (
            <div
              key={file.file_id}
              className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm hover:border-orange-300 transition"
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                <div className="flex items-start gap-4">
                  <div
                    onClick={() => onSelectScene(file.scenes[0] || { file_id: file.file_id, start_time: 0, end_time: file.duration_seconds, location: '', visual_description: file.file_name, tags: [], mood: '', pacing: '', suitability: [] }, file)}
                    className="w-16 h-16 rounded-xl bg-slate-900 text-orange-500 overflow-hidden flex items-center justify-center flex-shrink-0 relative group cursor-pointer border border-slate-200"
                  >
                    <img
                      src={file.thumbnail_url || `/api/files/${file.file_id}/thumbnail`}
                      alt=""
                      className="w-full h-full object-cover group-hover:scale-110 transition duration-300"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                    <div className="absolute inset-0 bg-black/30 flex items-center justify-center group-hover:bg-black/10 transition">
                      {file.file_type === 'video' ? (
                        <Play className="w-5 h-5 text-white fill-current drop-shadow" />
                      ) : (
                        <ImageIcon className="w-5 h-5 text-white drop-shadow" />
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                      <span className="truncate max-w-[280px] sm:max-w-md">{file.file_name}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">
                        {file.duration_seconds > 0 ? `${file.duration_seconds.toFixed(1)}s` : 'Photo'}
                      </span>
                    </h3>
                    <p className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                      <span className="flex items-center gap-1 font-medium">
                        <MapPin className="w-3.5 h-3.5 text-orange-500" />
                        {file.scenes[0]?.location || 'Dokumentasi Umrah'}
                      </span>
                      <span>•</span>
                      <span>{file.scenes.length} Scenes terdeteksi</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onSelectScene(file.scenes[0] || { file_id: file.file_id, start_time: 0, end_time: file.duration_seconds, location: '', visual_description: file.file_name, tags: [], mood: '', pacing: '', suitability: [] }, file)}
                    className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white text-xs font-semibold shadow-md shadow-orange-500/15 transition"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Preview Video</span>
                  </button>
                  <a
                    href={file.storage_url}
                    download
                    target="_blank"
                    rel="noreferrer"
                    className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
                    title="Download RAW File"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </div>

              {/* Scene Timeline Strip */}
              {file.scenes.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
                    Pecahan Scene Detik-demi-Detik:
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {file.scenes.map((scene, idx) => (
                      <div
                        key={idx}
                        onClick={() => onSelectScene(scene, file)}
                        className="cursor-pointer group p-3.5 bg-slate-50/70 hover:bg-orange-50/40 border border-slate-200/80 hover:border-orange-300 rounded-xl transition flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="font-mono text-xs font-bold text-orange-600 bg-orange-100/60 px-2 py-0.5 rounded border border-orange-200">
                              {scene.start_time}s - {scene.end_time}s
                            </span>
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border capitalize ${getMoodBadge(scene.mood)}`}>
                              {scene.mood}
                            </span>
                          </div>
                          <p className="text-xs text-slate-700 line-clamp-2 leading-relaxed">
                            {scene.visual_description}
                          </p>
                        </div>

                        <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-200/60">
                          <span className="text-[11px] text-slate-400 truncate max-w-[150px]">
                            {scene.location}
                          </span>
                          <span className="text-xs text-orange-600 font-semibold group-hover:translate-x-0.5 transition flex items-center gap-1">
                            Play <Play className="w-3 h-3 fill-current" />
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        /* Flat All Scenes Grid View with Visual Thumbnails */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredScenes.map((scene, idx) => (
            <div
              key={idx}
              onClick={() => onSelectScene(scene, scene.parentFile)}
              className="bg-white border border-slate-200/90 hover:border-orange-300 rounded-2xl overflow-hidden p-4 transition cursor-pointer flex flex-col justify-between group shadow-sm hover:shadow"
            >
              <div>
                {/* Visual Thumbnail Banner */}
                <div className="w-full h-36 rounded-xl bg-slate-950 overflow-hidden relative mb-3 border border-slate-200/60">
                  <img
                    src={scene.thumbnail_url || `/api/files/${scene.file_id}/thumbnail`}
                    alt=""
                    className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent p-2.5 flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono font-bold text-white bg-black/60 backdrop-blur-sm px-2 py-0.5 rounded border border-white/20">
                        {scene.start_time}s - {scene.end_time}s
                      </span>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border capitalize ${getMoodBadge(scene.mood)}`}>
                        {scene.mood}
                      </span>
                    </div>

                    <div className="flex items-center justify-center opacity-80 group-hover:opacity-100 transition">
                      <div className="w-9 h-9 rounded-full bg-orange-500/90 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition">
                        <Play className="w-4 h-4 fill-current ml-0.5" />
                      </div>
                    </div>
                  </div>
                </div>

                <h4 className="text-xs font-semibold text-slate-800 mb-1 flex items-center gap-1 truncate">
                  <MapPin className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
                  <span>{scene.location}</span>
                </h4>

                <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed mt-1.5 bg-slate-50/80 p-2.5 rounded-xl border border-slate-100">
                  {scene.visual_description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-400 text-[11px] truncate max-w-[140px]">
                  {scene.file_name}
                </span>
                <span className="text-orange-600 font-semibold group-hover:underline flex items-center gap-1">
                  Lihat Klip <Play className="w-3 h-3 fill-current" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
