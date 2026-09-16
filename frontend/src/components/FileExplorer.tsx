import React, { useState } from 'react';
import { Folder, FolderOpen, FileCode, ChevronRight, ChevronDown, Search } from 'lucide-react';

interface FileNode {
  id: string;
  path: str;
  relative_path: string;
  name: string;
  is_dir: boolean;
  language?: string;
  loc_count: number;
  parent_path: string;
  depth: number;
}

interface Props {
  nodes: FileNode[];
  selectedFile: string | null;
  onSelectFile: (path: string) => void;
}

export const FileExplorer: React.FC<Props> = ({ nodes, selectedFile, onSelectFile }) => {
  const [filter, setFilter] = useState('');
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({});

  const toggleFolder = (path: string) => {
    setExpandedFolders(prev => ({ ...prev, [path]: !prev[path] }));
  };

  const filteredNodes = nodes.filter(n =>
    n.relative_path.toLowerCase().includes(filter.toLowerCase())
  );

  // Group nodes by parent_path
  const nodesByParent: Record<string, FileNode[]> = {};
  filteredNodes.forEach(n => {
    const parent = n.parent_path || '';
    if (!nodesByParent[parent]) nodesByParent[parent] = [];
    nodesByParent[parent].push(n);
  });

  const renderTree = (parentPath: string = '') => {
    const children = nodesByParent[parentPath] || [];
    if (children.length === 0) return null;

    children.sort((a, b) => (b.is_dir ? 1 : 0) - (a.is_dir ? 1 : 0) || a.name.localeCompare(b.name));

    return (
      <div className="space-y-0.5">
        {children.map((node) => {
          const isExpanded = expandedFolders[node.relative_path] ?? (node.depth <= 1);
          const isSelected = selectedFile === node.relative_path;

          if (node.is_dir) {
            return (
              <div key={node.id} className="select-none">
                <button
                  onClick={() => toggleFolder(node.relative_path)}
                  className="w-full flex items-center space-x-1.5 px-2 py-1 hover:bg-slate-800/60 rounded text-slate-300 text-xs transition-colors text-left"
                  style={{ paddingLeft: `${node.depth * 12 + 8}px` }}
                >
                  {isExpanded ? (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  )}
                  {isExpanded ? (
                    <FolderOpen className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  ) : (
                    <Folder className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  )}
                  <span className="font-medium truncate">{node.name}</span>
                </button>
                {isExpanded && renderTree(node.relative_path)}
              </div>
            );
          }

          return (
            <button
              key={node.id}
              onClick={() => onSelectFile(node.relative_path)}
              className={`w-full flex items-center justify-between px-2 py-1 rounded text-xs transition-all text-left ${
                isSelected
                  ? 'bg-brand-600/30 border border-brand-500/40 text-white font-medium'
                  : 'hover:bg-slate-800/40 text-slate-400 hover:text-slate-200'
              }`}
              style={{ paddingLeft: `${node.depth * 12 + 20}px` }}
            >
              <div className="flex items-center space-x-2 truncate">
                <FileCode className={`w-3.5 h-3.5 flex-shrink-0 ${
                  node.language === 'Python' ? 'text-blue-400' :
                  node.language === 'TypeScript' ? 'text-sky-400' :
                  node.language === 'JavaScript' ? 'text-yellow-400' : 'text-slate-400'
                }`} />
                <span className="truncate">{node.name}</span>
              </div>
              <span className="text-[10px] text-slate-500 ml-2 font-mono flex-shrink-0">{node.loc_count} LOC</span>
            </button>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 h-full flex flex-col">
      <div className="relative mb-3">
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter files..."
          className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500"
        />
        <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
      </div>

      <div className="flex-1 overflow-y-auto pr-1">
        {renderTree('')}
      </div>
    </div>
  );
};
