import React, { useState, useEffect } from 'react';
import { RepoIngestion } from './components/RepoIngestion';
import { AnalysisStatus, StatusData } from './components/AnalysisStatus';
import { RepoOverview } from './components/RepoOverview';
import { FileExplorer } from './components/FileExplorer';
import { CodeViewer } from './components/CodeViewer';
import { AIChat } from './components/AIChat';
import { Cpu, LayoutDashboard, Code, MessageSquare, PlusCircle, RefreshCw, FolderGit2 } from 'lucide-react';
import axios from 'axios';

export function App() {
  const [currentRepoId, setCurrentRepoId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusData | null>(null);
  const [treeNodes, setTreeNodes] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileDetails, setFileDetails] = useState<any | null>(null);
  const [summaryData, setSummaryData] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'code' | 'chat'>('overview');

  const fetchStatus = async () => {
    if (!currentRepoId) return;
    try {
      const res = await axios.get(`/api/v1/repos/${currentRepoId}/status`);
      setStatus(res.data);
      if (res.data.status === 'completed' && treeNodes.length === 0) {
        fetchTree();
        fetchSummary();
      }
    } catch (err) {
      console.error("Failed to fetch status:", err);
    }
  };

  const fetchTree = async () => {
    if (!currentRepoId) return;
    try {
      const res = await axios.get(`/api/v1/repos/${currentRepoId}/tree`);
      setTreeNodes(res.data.nodes || []);
    } catch (err) {
      console.error("Failed to fetch tree:", err);
    }
  };

  const fetchSummary = async () => {
    if (!currentRepoId) return;
    try {
      const res = await axios.get(`/api/v1/repos/${currentRepoId}/summary`);
      setSummaryData(res.data);
    } catch (err) {
      console.error("Failed to fetch summary:", err);
    }
  };

  const fetchFileDetails = async (filePath: string) => {
    if (!currentRepoId) return;
    try {
      const res = await axios.get(`/api/v1/repos/${currentRepoId}/file`, {
        params: { path: filePath }
      });
      setFileDetails(res.data);
    } catch (err) {
      console.error("Failed to fetch file details:", err);
    }
  };

  useEffect(() => {
    if (currentRepoId) {
      fetchStatus();
      setTreeNodes([]);
      setSelectedFile(null);
      setFileDetails(null);
    }
  }, [currentRepoId]);

  const handleSelectFile = (path: string) => {
    setSelectedFile(path);
    fetchFileDetails(path);
    if (activeTab === 'overview') {
      setActiveTab('code');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="bg-slate-900/90 border-b border-slate-800 px-6 py-3 sticky top-0 z-50 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-xl text-white shadow-lg shadow-brand-600/30">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
              <span>Workspace Intelligence Agent</span>
              <span className="text-[10px] px-2 py-0.5 bg-brand-500/10 text-brand-400 border border-brand-500/20 rounded-full font-mono">v0.3 (30%)</span>
            </h1>
            <p className="text-[11px] text-slate-400">AST Code Parsing • Hierarchical Summarizer • NVIDIA NOOA Agent</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {currentRepoId && (
            <button
              onClick={() => setCurrentRepoId(null)}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-all flex items-center space-x-1.5"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Ingest New Repo</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 p-6 max-w-[1600px] w-full mx-auto space-y-6">
        {!currentRepoId ? (
          <div className="max-w-3xl mx-auto pt-10">
            <RepoIngestion onRepoIngested={(id) => setCurrentRepoId(id)} />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Status Tracker */}
            {status && (
              <AnalysisStatus status={status} onRefresh={fetchStatus} />
            )}

            {/* View Tabs */}
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center space-x-2 ${
                  activeTab === 'overview' ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Repository Overview</span>
              </button>

              <button
                onClick={() => setActiveTab('code')}
                className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center space-x-2 ${
                  activeTab === 'code' ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Code className="w-4 h-4" />
                <span>Code & AST Explorer</span>
              </button>

              <button
                onClick={() => setActiveTab('chat')}
                className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center space-x-2 ${
                  activeTab === 'chat' ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                <span>WIA AI Assistant</span>
              </button>
            </div>

            {/* Tab Views */}
            {activeTab === 'overview' && (
              <RepoOverview status={status} summary={summaryData} />
            )}

            {activeTab === 'code' && (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-[750px]">
                <div className="md:col-span-4 h-full">
                  <FileExplorer
                    nodes={treeNodes}
                    selectedFile={selectedFile}
                    onSelectFile={handleSelectFile}
                  />
                </div>
                <div className="md:col-span-8 h-full">
                  <CodeViewer fileDetails={fileDetails} />
                </div>
              </div>
            )}

            {activeTab === 'chat' && (
              <div className="h-[750px] max-w-5xl mx-auto">
                <AIChat repoId={currentRepoId} />
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
