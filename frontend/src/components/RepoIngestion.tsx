import React, { useState } from 'react';
import { FolderGit2, Github, Folder, ArrowRight, Loader2, Sparkles } from 'lucide-react';
import axios from 'axios';

interface Props {
  onRepoIngested: (repoId: string) => void;
}

export const RepoIngestion: React.FC<Props> = ({ onRepoIngested }) => {
  const [sourcePath, setSourcePath] = useState('');
  const [repoName, setRepoName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourcePath.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await axios.post('/api/v1/ingest', {
        source_path: sourcePath.trim(),
        name: repoName.trim() || undefined
      });
      if (res.data && res.data.repo_id) {
        onRepoIngested(res.data.repo_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to start repository ingestion.');
    } finally {
      setLoading(false);
    }
  };

  const setSampleRepo = (path: string, name: string) => {
    setSourcePath(path);
    setRepoName(name);
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-2xl backdrop-blur-md">
      <div className="flex items-center space-x-3 mb-4">
        <div className="p-2.5 bg-brand-500/10 border border-brand-500/20 rounded-lg text-brand-500">
          <FolderGit2 className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">Ingest Workspace Repository</h2>
          <p className="text-sm text-slate-400">Analyze local directories or GitHub repositories using AST & hierarchical AI understanding.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Repository URL or Local Path
          </label>
          <div className="relative">
            <input
              type="text"
              value={sourcePath}
              onChange={(e) => setSourcePath(e.target.value)}
              placeholder="e.g. https://github.com/fastapi/fastapi or C:\Projects\MyRepo"
              className="w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
            />
            {sourcePath.startsWith('http') ? (
              <Github className="w-5 h-5 text-slate-500 absolute left-3 top-3.5" />
            ) : (
              <Folder className="w-5 h-5 text-slate-500 absolute left-3 top-3.5" />
            )}
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <span>Quick Test:</span>
            <button
              type="button"
              onClick={() => setSampleRepo('C:\\Users\\pulig\\OneDrive\\Desktop\\WIA\\Workspace-Intelligence-Agent', 'WIA Core Repo')}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition-all flex items-center space-x-1"
            >
              <Sparkles className="w-3.5 h-3.5 text-brand-500" />
              <span>Current WIA Workspace</span>
            </button>
          </div>

          <button
            type="submit"
            disabled={loading || !sourcePath.trim()}
            className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-medium rounded-lg transition-all flex items-center space-x-2 shadow-lg shadow-brand-600/20 cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Starting...</span>
              </>
            ) : (
              <>
                <span>Analyze Repository</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
