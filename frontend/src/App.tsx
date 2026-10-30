import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { FootageLibrary } from './pages/FootageLibrary';
import { ScriptMatcher } from './pages/ScriptMatcher';
import { SettingsPage } from './pages/SettingsPage';
import { VideoPlayerModal } from './components/VideoPlayerModal';
import { api, Scene, FileItem } from './api';

export function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedScene, setSelectedScene] = useState<Scene | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isPollingActive, setIsPollingActive] = useState(true);

  useEffect(() => {
    const checkPolling = async () => {
      try {
        const res = await api.get('/scan/status');
        setIsPollingActive(res.data.is_processing_queue || res.data.is_scanning || true);
      } catch (e) {
        setIsPollingActive(false);
      }
    };
    checkPolling();
    const interval = setInterval(checkPolling, 6000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenPreview = (scene: Scene, file?: FileItem) => {
    setSelectedScene(scene);
    setSelectedFile(file || null);
    setIsModalOpen(true);
  };

  const handleClosePreview = () => {
    setIsModalOpen(false);
    setSelectedScene(null);
    setSelectedFile(null);
  };

  return (
    <div className="min-h-screen flex text-slate-800 antialiased selection:bg-orange-500 selection:text-white">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isPollingActive={isPollingActive}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        <main className="flex-1 p-6 sm:p-8 max-w-7xl w-full mx-auto">
          {activeTab === 'dashboard' && (
            <Dashboard onNavigateToSettings={() => setActiveTab('settings')} />
          )}
          {activeTab === 'library' && (
            <FootageLibrary onSelectScene={handleOpenPreview} />
          )}
          {activeTab === 'script' && (
            <ScriptMatcher onSelectScene={handleOpenPreview} />
          )}
          {activeTab === 'settings' && <SettingsPage />}
        </main>

        {/* Minimalist Footer */}
        <footer className="border-t border-slate-200/60 py-4 px-8 text-center text-xs text-slate-400">
          Umrah Footage AI Indexer • Google Drive Composio & Gemini Scene Breakdown 24/7
        </footer>
      </div>

      {/* Video Preview Modal */}
      <VideoPlayerModal
        isOpen={isModalOpen}
        onClose={handleClosePreview}
        scene={selectedScene}
        file={selectedFile}
      />
    </div>
  );
}

export default App;
