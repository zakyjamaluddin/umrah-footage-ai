import React, { useRef, useEffect, useState } from 'react';
import { X, Play, Pause, RotateCcw, Download, ExternalLink, MapPin, Tag, Sparkles, MonitorPlay, Layers } from 'lucide-react';
import { Scene, FileItem } from '../api';

interface VideoPlayerModalProps {
  isOpen: boolean;
  onClose: () => void;
  scene?: Scene | null;
  file?: FileItem | null;
}

export const VideoPlayerModal: React.FC<VideoPlayerModalProps> = ({
  isOpen,
  onClose,
  scene,
  file
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isLoopingSegment, setIsLoopingSegment] = useState(true);
  const [playerMode, setPlayerMode] = useState<'embed' | 'html5'>('embed');
  const [html5Error, setHtml5Error] = useState(false);

  const fileId = scene?.file_id || file?.file_id;
  const fileName = file?.file_name || scene?.file_name || '';
  const isMov = fileName.toLowerCase().endsWith('.mov');
  const isImage = file?.file_type === 'image' || scene?.file_type === 'image';

  const startSec = scene ? scene.start_time : 0;
  const endSec = scene && scene.end_time > 0 ? scene.end_time : (file ? file.duration_seconds : 0);

  const streamUrl = scene?.stream_url || file?.stream_url || (fileId ? `/api/files/${fileId}/stream` : '');
  const previewUrl = scene?.preview_url || file?.preview_url || (fileId ? `https://drive.google.com/file/d/${fileId}/preview` : '');
  const thumbnailUrl = scene?.thumbnail_url || file?.thumbnail_url || (fileId ? `/api/files/${fileId}/thumbnail` : '');
  const downloadUrl = scene?.storage_url || file?.storage_url || (fileId ? `https://drive.google.com/uc?id=${fileId}&export=download` : '');
  const driveViewUrl = fileId ? `https://drive.google.com/file/d/${fileId}/view` : downloadUrl;

  // For MOV files, Chrome/Edge cannot play raw MOV via HTML5 video, so default to Google Drive embed player
  useEffect(() => {
    if (isMov) {
      setPlayerMode('embed');
    } else {
      setPlayerMode('embed');
    }
    setHtml5Error(false);
  }, [fileId, isMov]);

  useEffect(() => {
    if (isOpen && videoRef.current && playerMode === 'html5' && !isImage) {
      videoRef.current.currentTime = startSec;
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  }, [isOpen, scene, file, startSec, isImage, playerMode]);

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const curr = videoRef.current.currentTime;
    setCurrentTime(curr);

    if (isLoopingSegment && endSec > startSec && curr >= endSec) {
      videoRef.current.currentTime = startSec;
      videoRef.current.play().catch(() => {});
    }
  };

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const restartSegment = () => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = startSec;
    videoRef.current.play();
    setIsPlaying(true);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-950/70 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl bg-white border border-slate-200 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[94vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/80">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span className="truncate max-w-[280px] sm:max-w-md">{fileName || 'Preview Footage'}</span>
              {scene && (
                <span className="text-xs bg-orange-100 text-orange-700 border border-orange-200 px-2.5 py-0.5 rounded-full font-mono font-semibold flex-shrink-0">
                  {scene.start_time}s - {scene.end_time}s ({((scene.end_time - scene.start_time) || 0).toFixed(1)}s)
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5 font-medium">
              <MapPin className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
              <span>{scene?.location || file?.scenes[0]?.location || 'Lokasi Ibadah Umrah'}</span>
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {!isImage && (
              <div className="hidden sm:flex items-center bg-slate-200/70 p-0.5 rounded-xl text-xs font-semibold">
                <button
                  onClick={() => setPlayerMode('embed')}
                  className={`px-2.5 py-1 rounded-lg transition ${
                    playerMode === 'embed' ? 'bg-white text-orange-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                  }`}
                  title="Stream via Google Drive Cloud Transcoder (Mendukung .MOV & semua format)"
                >
                  <span className="flex items-center gap-1"><MonitorPlay className="w-3.5 h-3.5" /> GDrive Cloud</span>
                </button>
                <button
                  onClick={() => setPlayerMode('html5')}
                  className={`px-2.5 py-1 rounded-lg transition ${
                    playerMode === 'html5' ? 'bg-white text-orange-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                  }`}
                  title="HTML5 Player langsung dengan pemotong segmen (Loop)"
                >
                  <span className="flex items-center gap-1"><Layers className="w-3.5 h-3.5" /> HTML5 Loop</span>
                </button>
              </div>
            )}
            
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Media Preview Area */}
        <div className="relative bg-slate-950 flex items-center justify-center flex-1 min-h-[320px] max-h-[55vh] overflow-hidden">
          {isImage ? (
            <img
              src={thumbnailUrl || streamUrl}
              alt={fileName}
              onError={(e) => {
                // fallback to preview URL if thumbnail fails
                if (fileId && e.currentTarget.src !== `https://drive.google.com/thumbnail?id=${fileId}&sz=w1200`) {
                  e.currentTarget.src = `https://drive.google.com/thumbnail?id=${fileId}&sz=w1200`;
                }
              }}
              className="w-full h-full object-contain max-h-[55vh]"
            />
          ) : playerMode === 'embed' || html5Error ? (
            /* Google Drive Transcoded Video Stream (Works for MOV, MP4, etc.) */
            <iframe
              src={previewUrl}
              allow="autoplay; encrypted-media; fullscreen"
              allowFullScreen
              className="w-full h-full min-h-[340px] max-h-[55vh] border-0"
              title={fileName}
            />
          ) : (
            /* HTML5 Native Video Player */
            <video
              ref={videoRef}
              src={streamUrl}
              onTimeUpdate={handleTimeUpdate}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onError={() => {
                console.warn('HTML5 Video player codec error, switching to Google Drive Player...');
                setHtml5Error(true);
                setPlayerMode('embed');
              }}
              className="w-full h-full object-contain max-h-[55vh]"
              controls={false}
              playsInline
            />
          )}

          {/* HTML5 Video Segment Overlay Controls (Only active in HTML5 Mode) */}
          {!isImage && playerMode === 'html5' && !html5Error && (
            <div className="absolute bottom-4 left-4 right-4 bg-slate-900/85 backdrop-blur-md px-4 py-2.5 rounded-2xl border border-slate-700/60 flex items-center justify-between text-xs text-slate-200">
              <div className="flex items-center space-x-3">
                <button
                  onClick={togglePlay}
                  className="p-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white transition shadow-md shadow-orange-500/20"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
                </button>
                <button
                  onClick={restartSegment}
                  className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                  title="Ulangi klip dari awal"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                <div className="font-mono text-xs">
                  <span className="text-orange-400 font-bold">{currentTime.toFixed(1)}s</span> / {endSec.toFixed(1)}s
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <label className="flex items-center space-x-2 cursor-pointer text-slate-300 hover:text-white">
                  <input
                    type="checkbox"
                    checked={isLoopingSegment}
                    onChange={(e) => setIsLoopingSegment(e.target.checked)}
                    className="rounded border-slate-600 text-orange-500 focus:ring-orange-500 bg-slate-800"
                  />
                  <span>Loop Scene ({scene?.start_time}s - {scene?.end_time}s)</span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Scene Metadata Footer */}
        <div className="p-6 bg-white border-t border-slate-100 overflow-y-auto space-y-4">
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-orange-500" />
              Visual Description (Gemini Analysis)
            </h4>
            <p className="text-sm text-slate-800 leading-relaxed bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
              {scene?.visual_description || file?.scenes[0]?.visual_description || 'Deskripsi adegan footage umrah.'}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/70">
              <span className="text-xs text-slate-400 block mb-0.5">Mood & Pacing</span>
              <span className="text-sm font-bold text-orange-600 capitalize">
                {scene?.mood || 'Khusyuk'} ({scene?.pacing || 'Slow'})
              </span>
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/70 sm:col-span-2">
              <span className="text-xs text-slate-400 block mb-1">Kesesuaian Narasi Iklan (Suitability)</span>
              <div className="flex flex-wrap gap-1.5">
                {(scene?.suitability || file?.scenes[0]?.suitability || []).map((suit, idx) => (
                  <span key={idx} className="text-xs px-2.5 py-0.5 rounded-full bg-orange-100/70 text-orange-700 border border-orange-200 font-medium">
                    {suit}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Tags & Action Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <div className="flex flex-wrap gap-1.5 items-center">
              <Tag className="w-3.5 h-3.5 text-slate-400" />
              {(scene?.tags || file?.scenes[0]?.tags || []).map((t, idx) => (
                <span key={idx} className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 font-medium">
                  #{t}
                </span>
              ))}
            </div>

            <div className="flex items-center space-x-2">
              <a
                href={downloadUrl}
                download
                target="_blank"
                rel="noreferrer"
                className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white text-xs font-semibold transition shadow-md shadow-orange-500/15"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download File RAW</span>
              </a>
              <a
                href={driveViewUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Buka di Google Drive</span>
              </a>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
