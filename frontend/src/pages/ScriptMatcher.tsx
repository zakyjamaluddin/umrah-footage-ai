import React, { useState } from 'react';
import { FileText, Sparkles, Wand2, Play, Download, CheckCircle } from 'lucide-react';
import { api, ScriptAnalysisResult, Scene } from '../api';

const SAMPLE_SCRIPTS = [
  {
    title: 'Iklan Umrah Ramadhan Penuh Haru',
    text: `Kerinduan mendalam akhirnya terjawab saat sepasang mata ini menatap langsung Ka'bah yang mulia. Air mata haru tak terbendung di pelataran Mataf, mengucap syukur atas panggilan suci ini. Rasakan ketenangan ibadah di Masjid Nabawi, di bawah naungan payung nan syahdu. Didampingi muthawif berpengalaman dan fasilitas hotel bintang 5 tepat di depan pelataran. Wujudkan niat suci Anda bersama keluarga tahun ini. Hubungi kami sekarang dan amankan seat Anda.`,
  },
  {
    title: 'Iklan Umrah Eksklusif & Nyaman',
    text: `Ibadah tenang tanpa rasa lelah. Hotel mewah bintang lima hanya selangkah dari Masjidil Haram. Nikmati kemudahan ziarah ke Jabal Uhud dan tempat bersejarah bersama pembimbing ahli. Dapatkan pengalaman umrah yang tak terlupakan dengan layanan VIP seutuhnya. Konsultasikan jadwal keberangkatan Anda hari ini.`,
  },
];

interface ScriptMatcherProps {
  onSelectScene: (scene: Scene) => void;
}

export const ScriptMatcher: React.FC<ScriptMatcherProps> = ({ onSelectScene }) => {
  const [scriptText, setScriptText] = useState(SAMPLE_SCRIPTS[0].text);
  const [targetDuration, setTargetDuration] = useState(4.5);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<ScriptAnalysisResult | null>(null);

  const handleAnalyze = async () => {
    if (!scriptText.trim()) {
      alert('Silakan masukkan naskah iklan terlebih dahulu.');
      return;
    }

    setIsAnalyzing(true);
    try {
      const res = await api.post('/script/analyze-match', {
        script_text: scriptText,
        target_duration_per_scene: targetDuration,
      });
      setResult(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Gagal menganalisa naskah');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <FileText className="w-5 h-5 text-orange-500" />
          <span>Ads Script Matcher Studio</span>
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Masukkan naskah voice-over iklan Anda. Gemini akan memecah narasi per 4-5 detik dan mencocokkan footage paling relevan dari database.
        </p>
      </div>

      {/* Script Input Area */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <Wand2 className="w-4 h-4 text-orange-500" />
            Naskah Iklan (Voice-Over Script)
          </label>

          {/* Quick presets */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 hidden sm:inline">Contoh Cepat:</span>
            {SAMPLE_SCRIPTS.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setScriptText(s.text)}
                className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-orange-50 hover:text-orange-600 text-slate-600 border border-slate-200 transition"
              >
                {s.title}
              </button>
            ))}
          </div>
        </div>

        <textarea
          rows={5}
          value={scriptText}
          onChange={(e) => setScriptText(e.target.value)}
          placeholder="Ketik atau paste naskah iklan Anda di sini..."
          className="w-full p-4 bg-slate-50/70 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 focus:bg-white transition leading-relaxed font-sans"
        />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
          <div className="flex items-center gap-3">
            <label className="text-xs font-medium text-slate-600 flex items-center gap-1">
              <span>Target Durasi per Cut:</span>
            </label>
            <div className="flex items-center space-x-1.5">
              {[3.5, 4.5, 6.0].map((sec) => (
                <button
                  key={sec}
                  type="button"
                  onClick={() => setTargetDuration(sec)}
                  className={`px-3 py-1 rounded-lg text-xs font-mono font-bold transition ${
                    targetDuration === sec
                      ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md shadow-orange-500/15'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {sec}s
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 via-orange-600 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-semibold text-sm transition shadow-lg shadow-orange-500/20 disabled:opacity-50"
          >
            <Sparkles className={`w-4 h-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
            <span>{isAnalyzing ? 'Menganalisa & Mencari Footage...' : 'Pecah & Cari Footage Cocok'}</span>
          </button>
        </div>
      </div>

      {/* Storyboard Matching Results */}
      {result && (
        <div className="space-y-4">
          <div className="bg-orange-50/70 border border-orange-200 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 text-orange-900 font-medium">
              <CheckCircle className="w-4 h-4 text-orange-500 flex-shrink-0" />
              <span>{result.summary}</span>
            </div>
            <div className="font-mono font-bold text-orange-700 bg-white px-3 py-1 rounded-lg border border-orange-200 shadow-sm self-start sm:self-auto">
              Total Durasi: ~{result.total_estimated_duration}s
            </div>
          </div>

          {/* Segment by segment list */}
          <div className="space-y-4">
            {result.segments.map((seg) => (
              <div
                key={seg.segment_index}
                className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm space-y-4"
              >
                {/* Segment Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-xl bg-gradient-to-tr from-orange-500 to-amber-400 text-white font-mono font-bold text-sm flex items-center justify-center shadow-md shadow-orange-500/15">
                      #{seg.segment_index}
                    </span>
                    <div>
                      <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                        <span>{seg.topic}</span>
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-orange-50 text-orange-700 border border-orange-200 capitalize font-medium">
                          Mood: {seg.recommended_mood}
                        </span>
                      </h3>
                      <p className="text-xs text-slate-400 font-mono mt-0.5">
                        Timestamp Timeline: {seg.estimated_start}s - {seg.estimated_end}s ({seg.duration}s)
                      </p>
                    </div>
                  </div>
                </div>

                {/* Narration & Visual Need */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="bg-slate-50/70 p-3.5 rounded-xl border border-slate-200/70">
                    <span className="text-slate-400 font-semibold block mb-1">🗣️ Teks Narasi Voice-Over:</span>
                    <p className="text-slate-800 italic leading-relaxed">"{seg.narration_text}"</p>
                  </div>
                  <div className="bg-orange-50/40 p-3.5 rounded-xl border border-orange-200/60">
                    <span className="text-orange-700 font-semibold block mb-1">🎯 Kebutuhan Visual Adegan:</span>
                    <p className="text-slate-800 leading-relaxed">{seg.visual_requirement}</p>
                  </div>
                </div>

                {/* Recommended Footages */}
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-orange-500" />
                    Opsi Footage Rekomendasi Gemini (Top Match):
                  </h4>

                  {seg.matched_scenes.length === 0 ? (
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-center text-xs text-slate-400">
                      Belum ada footage dengan kemiripan visual yang cukup. Tambahkan video baru ke Google Drive.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {seg.matched_scenes.map((scene, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-50/70 border border-slate-200 hover:border-orange-300 rounded-xl p-4 transition flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-mono font-bold text-orange-700 bg-orange-100/70 px-2 py-0.5 rounded border border-orange-200">
                                {scene.start_time}s - {scene.end_time}s
                              </span>
                              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                                {scene.relevance_score || 90}% Match
                              </span>
                            </div>

                            <p className="text-xs font-medium text-slate-800 line-clamp-2 leading-relaxed mb-2">
                              {scene.visual_description}
                            </p>

                            <div className="text-[11px] text-slate-500 flex items-center gap-1 mb-2">
                              <span>📍 {scene.location}</span>
                            </div>
                          </div>

                          <div className="pt-2.5 border-t border-slate-200 flex items-center justify-between gap-2">
                            <span className="text-[10px] text-slate-400 truncate max-w-[120px]">
                              {scene.file_name}
                            </span>
                            <div className="flex items-center gap-1.5">
                              <button
                                onClick={() => onSelectScene(scene)}
                                className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-orange-50 hover:bg-orange-100 text-orange-600 text-xs font-semibold border border-orange-200 transition"
                              >
                                <Play className="w-3 h-3 fill-current" />
                                <span>Preview</span>
                              </button>
                              <a
                                href={scene.storage_url}
                                download
                                target="_blank"
                                rel="noreferrer"
                                className="p-1.5 rounded-lg bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 transition"
                                title="Download Klip"
                              >
                                <Download className="w-3 h-3" />
                              </a>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
