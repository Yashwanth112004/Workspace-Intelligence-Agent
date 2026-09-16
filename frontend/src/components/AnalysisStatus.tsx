import React, { useEffect } from 'react';
import { Activity, CheckCircle2, Clock, Cpu, FileCode2, Layers, AlertCircle } from 'lucide-react';

export interface StatusData {
  repo_id: string;
  name: str;
  status: string;
  progress_pct: number;
  status_message: string;
  total_files: number;
  total_loc: number;
  tech_stack: Record<string, number>;
  error_message?: string;
}

interface Props {
  status: StatusData;
  onRefresh: () => void;
}

export const AnalysisStatus: React.FC<Props> = ({ status, onRefresh }) => {
  useEffect(() => {
    if (status.status !== 'completed' && status.status !== 'failed') {
      const interval = setInterval(onRefresh, 2000);
      return () => clearInterval(interval);
    }
  }, [status.status, onRefresh]);

  const steps = [
    { key: 'ingesting', label: '1. Ingestion', icon: Clock },
    { key: 'parsing', label: '2. AST Code Parser', icon: FileCode2 },
    { key: 'summarizing', label: '3. Hierarchical Summaries', icon: Layers },
    { key: 'vectorizing', label: '4. Vector Indexing', icon: Cpu },
    { key: 'completed', label: '5. Ready', icon: CheckCircle2 },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Repository Status</span>
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <span>{status.name}</span>
            <span className={`text-xs px-2.5 py-0.5 rounded-full border ${
              status.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
              status.status === 'failed' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
              'bg-brand-500/10 text-brand-400 border-brand-500/20 animate-pulse'
            }`}>
              {status.status.toUpperCase()}
            </span>
          </h3>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-brand-400">{status.progress_pct}%</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden mb-4 border border-slate-800">
        <div
          className="bg-gradient-to-r from-brand-600 to-indigo-400 h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${status.progress_pct}%` }}
        />
      </div>

      <p className="text-sm text-slate-300 flex items-center space-x-2 mb-4 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
        <Activity className="w-4 h-4 text-brand-400 animate-spin" />
        <span>{status.status_message}</span>
      </p>

      {/* Pipeline Steps Tracker */}
      <div className="grid grid-cols-5 gap-2 pt-2 border-t border-slate-800/60">
        {steps.map((step) => {
          const Icon = step.icon;
          const isDone = status.progress_pct === 100 || (
            (step.key === 'ingesting' && status.progress_pct >= 35) ||
            (step.key === 'parsing' && status.progress_pct >= 65) ||
            (step.key === 'summarizing' && status.progress_pct >= 85) ||
            (step.key === 'vectorizing' && status.progress_pct >= 100)
          );
          const isCurrent = status.status === step.key;

          return (
            <div
              key={step.key}
              className={`p-2 rounded-lg text-center text-xs flex flex-col items-center space-y-1 transition-all ${
                isDone ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' :
                isCurrent ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 animate-pulse' :
                'bg-slate-950 text-slate-500 border border-slate-900'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="font-medium truncate w-full">{step.label}</span>
            </div>
          );
        })}
      </div>

      {status.error_message && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{status.error_message}</span>
        </div>
      )}
    </div>
  );
};
