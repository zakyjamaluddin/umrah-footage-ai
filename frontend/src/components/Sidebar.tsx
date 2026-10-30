import React from 'react';
import { LayoutDashboard, Film, FileText, Settings, Radio, Sparkles, FolderGit2 } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isPollingActive: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, isPollingActive }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard & Antrian', icon: LayoutDashboard, desc: 'Status antrian & polling' },
    { id: 'library', label: 'Footage Library', icon: Film, desc: 'Eksplorasi scene & filter' },
    { id: 'script', label: 'Ads Script Studio', icon: FileText, desc: 'Pecah naskah & cocokkan' },
    { id: 'settings', label: 'Pengaturan & API', icon: Settings, desc: 'Folder ID & API Keys' },
  ];

  return (
    <aside className="w-64 md:w-72 bg-white/95 backdrop-blur-md border-r border-slate-200/90 flex flex-col justify-between h-screen sticky top-0 z-30 transition-all select-none">
      {/* Brand Header */}
      <div>
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-orange-500 via-amber-500 to-amber-400 flex items-center justify-center shadow-lg shadow-orange-500/25">
              <Film className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-base tracking-tight text-slate-900 flex items-center gap-1.5">
                <span>Umrah Footage</span>
                <span className="text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-orange-100 text-orange-600 tracking-wider">
                  AI
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium">Composio + Gemini</p>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-4 space-y-1.5">
          <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Menu Utama
          </div>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3.5 px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-200 text-left group ${
                  isActive
                    ? 'bg-gradient-to-r from-orange-50 to-amber-50 text-orange-600 border border-orange-200/80 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-transparent'
                }`}
              >
                <div
                  className={`p-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md shadow-orange-500/20'
                      : 'bg-slate-100 text-slate-500 group-hover:bg-slate-200 group-hover:text-slate-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className={`font-semibold ${isActive ? 'text-orange-700' : 'text-slate-700'}`}>
                    {item.label}
                  </div>
                  <div className="text-[11px] text-slate-400 leading-none mt-0.5 font-normal">
                    {item.desc}
                  </div>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info & Polling Status */}
      <div className="p-4 border-t border-slate-100 space-y-3">
        <div className="bg-slate-50/80 border border-slate-200/80 rounded-xl p-3 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Radio className={`w-3.5 h-3.5 ${isPollingActive ? 'text-orange-500 animate-pulse' : 'text-slate-400'}`} />
            <span className="text-xs font-medium text-slate-600">Background 24/7</span>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold bg-orange-100/70 text-orange-600">
            5 Min
          </span>
        </div>

        <div className="px-1 text-center">
          <span className="text-[10px] text-slate-400">VPS Ready • v1.0 Production</span>
        </div>
      </div>
    </aside>
  );
};
