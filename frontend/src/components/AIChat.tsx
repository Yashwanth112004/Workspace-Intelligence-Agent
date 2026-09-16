import React, { useState } from 'react';
import { Bot, Send, User, Sparkles, Loader2, FileText, CornerDownRight } from 'lucide-react';
import axios from 'axios';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
}

interface Props {
  repoId: string;
}

export const AIChat: React.FC<Props> = ({ repoId }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I am the **WIA Code Understanding Agent** built on NVIDIA NOOA framework. Ask me any question about code functions, architecture, dependencies, or file responsibilities in this repository.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`/api/v1/repos/${repoId}/query`, {
        query: userMsg.content
      });

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.data.response || 'No response generated.',
        citations: res.data.citations || []
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Error: Failed to fetch query response from WIA Agent. Please ensure the backend server is running.'
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-slate-950 px-4 py-3 border-b border-slate-800 flex items-center space-x-2">
        <div className="p-1.5 bg-brand-500/10 text-brand-400 rounded-lg">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">WIA Code Understanding Agent</h3>
          <p className="text-[11px] text-slate-400">NVIDIA NOOA Framework • RAG Context-Aware Q&A</p>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start space-x-3 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.role === 'assistant' && (
              <div className="p-2 bg-brand-600/20 text-brand-400 border border-brand-500/30 rounded-lg flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div className={`max-w-[85%] rounded-xl p-3 space-y-2 leading-relaxed ${
              msg.role === 'user'
                ? 'bg-brand-600 text-white font-medium rounded-tr-none'
                : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none'
            }`}>
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-slate-800/80 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-500 flex items-center space-x-1">
                    <FileText className="w-3 h-3 text-brand-400" />
                    <span>RAG Source Context ({msg.citations.length} Citations):</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {msg.citations.map((c: any, idx: number) => (
                      <span key={idx} className="px-2 py-0.5 bg-slate-900 border border-slate-800 text-brand-300 font-mono text-[10px] rounded flex items-center space-x-1">
                        <CornerDownRight className="w-2.5 h-2.5 text-slate-500" />
                        <span>{c.file_path}</span>
                        {c.start_line > 0 && <span className="text-slate-500">(L{c.start_line})</span>}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="p-2 bg-slate-800 text-slate-300 rounded-lg flex-shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-brand-600/20 text-brand-400 border border-brand-500/30 rounded-lg">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-slate-950 border border-slate-800 text-slate-400 p-3 rounded-xl rounded-tl-none flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
              <span>Analyzing context & generating response...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSend} className="p-3 bg-slate-950 border-t border-slate-800 flex items-center space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask WIA agent about functions, architecture, dependencies..."
          className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="p-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg transition-all shadow-md shadow-brand-600/20"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
