import React from 'react';
import { Code2, Files, Cpu, Box, PackageCheck, Anchor, Sparkles } from 'lucide-react';

interface Props {
  status: any;
  summary: any;
}

export const RepoOverview: React.FC<Props> = ({ status, summary }) => {
  const repoSummary = summary?.repository_summary;

  return (
    <div className="space-y-6">
      {/* High Level Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
          <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg">
            <Files className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{status?.total_files || 0}</div>
            <div className="text-xs text-slate-400">Total Source Files</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
          <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg">
            <Code2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{(status?.total_loc || 0).toLocaleString()}</div>
            <div className="text-xs text-slate-400">Lines of Code</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg">
            <PackageCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{status?.dependencies?.length || 0}</div>
            <div className="text-xs text-slate-400">Dependencies</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
          <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg">
            <Anchor className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{status?.entry_points?.length || 0}</div>
            <div className="text-xs text-slate-400">Entry Points</div>
          </div>
        </div>
      </div>

      {/* Repository Architecture Summary */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
        <div className="flex items-center space-x-2 text-brand-400 font-semibold mb-3">
          <Sparkles className="w-5 h-5" />
          <span>AI Architecture & Workspace Summary</span>
        </div>
        <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line bg-slate-950/70 p-4 rounded-lg border border-slate-800">
          {repoSummary?.summary_text || 'Summarizing workspace architecture...'}
        </p>

        {/* Tech Stack Distribution */}
        <div className="mt-6">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Detected Tech Stack & Languages</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(status?.tech_stack || {}).map(([lang, loc]: [string, any]) => (
              <div key={lang} className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-brand-500"></span>
                <span className="font-medium text-slate-200">{lang}</span>
                <span className="text-slate-500">({loc.toLocaleString()} LOC)</span>
              </div>
            ))}
          </div>
        </div>

        {/* Key Entry Points & Configs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Detected Entry Points</h4>
            <div className="space-y-1">
              {(status?.entry_points || []).map((ep: string) => (
                <div key={ep} className="text-xs bg-slate-950 p-2 rounded border border-slate-800/80 font-mono text-brand-300">
                  {ep}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Configuration Files</h4>
            <div className="space-y-1">
              {(status?.config_files || []).map((cf: string) => (
                <div key={cf} className="text-xs bg-slate-950 p-2 rounded border border-slate-800/80 font-mono text-indigo-300">
                  {cf}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
