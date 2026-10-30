import React from 'react';
import { LayoutDashboard, Film, FileText, Settings, Radio } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isPollingActive: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, isPollingActive }) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard & Antrian', icon: LayoutDashboard },
    { id: 'library', label: 'Footage Library', icon: Film },
    { id: 'script', label: 'Ads Script Studio', icon: FileText },
    { id: 'settings', label: 'Pengaturan & API', icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Film className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
                Umrah Footage AI
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                Composio + Gemini
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Status Indicator */}
          <div className="flex items-center space-x-2 text-xs bg-slate-950 px-3 py-1.5 rounded-full border border-slate-800">
            <Radio className={`w-3.5 h-3.5 ${isPollingActive ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
            <span className="text-slate-400 hidden sm:inline">Pooling 5 Min:</span>
            <span className={isPollingActive ? 'text-emerald-400 font-semibold' : 'text-slate-500'}>
              {isPollingActive ? 'Active' : 'Idle'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
