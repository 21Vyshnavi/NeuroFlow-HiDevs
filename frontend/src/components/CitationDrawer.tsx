'use client';

import React from 'react';

interface CitationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  citation: {
    chunk_content: string;
    document_title: string;
    relevance_score: number;
    metadata: Record<string, any>;
  } | null;
}

export default function CitationDrawer({ isOpen, onClose, citation }: CitationDrawerProps) {
  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div 
        className={`fixed right-0 top-0 h-full w-[480px] z-50 bg-surface-800/95 backdrop-blur-xl border-l border-white/10 transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        {citation && (
          <div className="flex flex-col h-full overflow-hidden">
            <div className="p-6 flex items-center justify-between border-b border-white/10">
              <h2 className="text-xl font-semibold text-white truncate pr-4">{citation.document_title}</h2>
              <button 
                onClick={onClose}
                className="text-gray-400 hover:text-white transition-colors p-2"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Relevance Score</h3>
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                    {Math.round(citation.relevance_score * 100)}% Match
                  </span>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">Chunk Content</h3>
                <div className="bg-black/40 rounded-lg p-4 overflow-x-auto border border-white/5">
                  <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap leading-relaxed">
                    {citation.chunk_content}
                  </pre>
                </div>
              </div>

              {citation.metadata && Object.keys(citation.metadata).length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">Metadata</h3>
                  <div className="grid grid-cols-1 gap-2">
                    {Object.entries(citation.metadata).map(([key, value]) => (
                      <div key={key} className="flex flex-col bg-surface-700/50 rounded-lg p-3 border border-white/5">
                        <span className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="text-sm text-gray-200 mt-1">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
