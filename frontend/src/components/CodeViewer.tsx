import React, { useState } from 'react';
import { FileText, Code2, Sparkles, Layers, Box, Info } from 'lucide-react';

interface Props {
  fileDetails: any;
}

export const CodeViewer: React.FC<Props> = ({ fileDetails }) => {
  const [activeTab, setActiveTab] = useState<'code' | 'ast' | 'summary'>('code');

  if (!fileDetails || !fileDetails.file) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500 h-full flex flex-col items-center justify-center">
        <Code2 className="w-12 h-12 mb-3 text-slate-700 stroke-[1.5]" />
        <p className="text-sm font-medium">Select a file from the explorer to view AST structure, functions, and code</p>
      </div>
    );
  }

  const { file, content, symbols, summary } = fileDetails;
  const lines = (content || '').split('\n');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl h-full flex flex-col overflow-hidden">
      {/* File Header & Tabs */}
      <div className="bg-slate-950 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-brand-400" />
          <span className="font-mono text-sm font-medium text-white">{file.relative_path}</span>
          <span className="text-xs px-2 py-0.5 bg-slate-800 rounded text-slate-400 font-mono">
            {file.language || 'Code'} • {file.loc_count} LOC
          </span>
        </div>

        <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('code')}
            className={`px-3 py-1 rounded-md transition-all flex items-center space-x-1.5 ${
              activeTab === 'code' ? 'bg-brand-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Code</span>
          </button>
          <button
            onClick={() => setActiveTab('ast')}
            className={`px-3 py-1 rounded-md transition-all flex items-center space-x-1.5 ${
              activeTab === 'ast' ? 'bg-brand-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Box className="w-3.5 h-3.5" />
            <span>AST Symbols ({symbols?.length || 0})</span>
          </button>
          <button
            onClick={() => setActiveTab('summary')}
            className={`px-3 py-1 rounded-md transition-all flex items-center space-x-1.5 ${
              activeTab === 'summary' ? 'bg-brand-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Summary</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-4 font-mono text-xs">
        {activeTab === 'code' && (
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 overflow-x-auto">
            {lines.map((line: string, i: number) => (
              <div key={i} className="flex hover:bg-slate-900/60 leading-5">
                <span className="w-10 text-right pr-4 text-slate-600 select-none font-mono text-[11px]">{i + 1}</span>
                <span className="text-slate-200 whitespace-pre">{line}</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'ast' && (
          <div className="space-y-4 font-sans">
            <h4 className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-2">Parsed AST Symbols & Relationships</h4>
            {(!symbols || symbols.length === 0) ? (
              <p className="text-slate-500 text-xs italic">No explicit function or class AST symbols parsed for this file format.</p>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {symbols.map((sym: any) => (
                  <div key={sym.id} className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className={`px-2 py-0.5 rounded font-mono text-[10px] uppercase font-bold ${
                        sym.symbol_type === 'function' ? 'bg-blue-500/20 text-blue-300' :
                        sym.symbol_type === 'class' ? 'bg-purple-500/20 text-purple-300' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {sym.symbol_type}
                      </span>
                      <span className="text-slate-500 font-mono text-[11px]">Lines {sym.start_line} - {sym.end_line}</span>
                    </div>

                    <div className="font-mono text-sm font-semibold text-white">{sym.signature || sym.name}</div>
                    
                    {sym.docstring && (
                      <p className="text-slate-400 italic bg-slate-900/80 p-2 rounded border border-slate-800/80">{sym.docstring}</p>
                    )}

                    {sym.calls && sym.calls.length > 0 && (
                      <div className="text-[11px] text-slate-400 flex items-center space-x-1">
                        <span className="font-semibold text-slate-500">Calls:</span>
                        <span className="font-mono text-brand-300">{sym.calls.join(', ')}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'summary' && (
          <div className="font-sans space-y-4">
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
              <div className="flex items-center space-x-2 text-brand-400 font-semibold mb-2 text-sm">
                <Sparkles className="w-4 h-4" />
                <span>File Summary</span>
              </div>
              <p className="text-slate-300 text-sm leading-relaxed">{summary}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
