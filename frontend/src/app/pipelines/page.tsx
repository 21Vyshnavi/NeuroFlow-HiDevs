'use client';

import React, { useState } from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import Editor from '@monaco-editor/react';
import PipelineAnalyticsDrawer from '@/components/PipelineAnalyticsDrawer';

const PIPELINES = [
  { name: 'production-v2', version: '2.1.0', queries: 1247, avgScore: 0.87, trend: [0.82,0.84,0.86,0.88,0.87,0.89,0.87], status: 'active' },
  { name: 'experimental-v3', version: '3.0.0-beta', queries: 356, avgScore: 0.72, trend: [0.68,0.70,0.71,0.73,0.74,0.72,0.72], status: 'active' },
  { name: 'baseline', version: '1.0.0', queries: 2891, avgScore: 0.65, trend: [0.66,0.64,0.65,0.66,0.65,0.64,0.65], status: 'active' },
  { name: 'fine-tuned-v1', version: '1.2.0', queries: 189, avgScore: 0.91, trend: [0.85,0.87,0.89,0.90,0.91,0.91,0.91], status: 'active' },
];

const SAMPLE_CONFIG = {
  retrieval: {
    strategy: "hybrid",
    top_k: 10,
    semantic_weight: 0.7,
    keyword_weight: 0.3,
    reranker: {
      enabled: true,
      model: "cross-encoder/ms-marco-MiniLM-L-6-v2",
      top_n: 5
    }
  },
  generation: {
    model: "gpt-4",
    temperature: 0.1,
    max_tokens: 2048,
    system_prompt: "You are a helpful assistant."
  },
  evaluation: {
    enabled: true,
    metrics: ["faithfulness", "relevance", "coherence", "groundedness"]
  }
};

export default function PipelinesPage() {
  const [selectedPipeline, setSelectedPipeline] = useState<any>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [pipelineName, setPipelineName] = useState('');
  const [jsonConfig, setJsonConfig] = useState(JSON.stringify(SAMPLE_CONFIG, null, 2));
  const [jsonError, setJsonError] = useState<string | null>(null);

  const handleJsonChange = (value: string | undefined) => {
    if (!value) return;
    setJsonConfig(value);
    try {
      JSON.parse(value);
      setJsonError(null);
    } catch (e: any) {
      setJsonError(e.message);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400 bg-green-500/20';
    if (score >= 0.6) return 'text-yellow-400 bg-yellow-500/20';
    return 'text-red-400 bg-red-500/20';
  };

  const getStrokeColor = (score: number) => {
    if (score >= 0.8) return '#4ade80';
    if (score >= 0.6) return '#facc15';
    return '#f87171';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-white">Pipeline Manager</h1>
          <p className="text-gray-400 mt-1">Configure and monitor RAG pipelines</p>
        </div>
        <button 
          onClick={() => setShowCreateModal(true)}
          className="px-6 py-2 bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 text-white font-medium rounded-lg transition-colors"
        >
          Create Pipeline
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {PIPELINES.map((pipeline) => (
          <div 
            key={pipeline.name} 
            className="glass-card-hover p-6 cursor-pointer"
            onClick={() => setSelectedPipeline(pipeline)}
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-white">{pipeline.name}</h3>
                <span className="inline-block mt-1 text-xs font-medium bg-brand-500/20 text-brand-300 px-2 py-0.5 rounded-full">v{pipeline.version}</span>
              </div>
            </div>
            
            <div className="flex justify-between items-end mb-4">
              <div>
                <div className="text-2xl font-bold text-white">{pipeline.queries.toLocaleString()}</div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">Queries (7d)</div>
              </div>
              <div className="text-right">
                <div className={`text-xl font-bold px-3 py-1 rounded-lg ${getScoreColor(pipeline.avgScore)}`}>
                  {pipeline.avgScore.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 uppercase tracking-wider mt-1">Avg Score</div>
              </div>
            </div>

            <div className="h-10 w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={pipeline.trend.map((val, i) => ({ i, val }))}>
                  <Line type="monotone" dataKey="val" stroke={getStrokeColor(pipeline.avgScore)} strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowCreateModal(false)} />
          <div className="glass-card relative w-full max-w-3xl flex flex-col max-h-[90vh]">
            <div className="p-6 border-b border-white/10">
              <h2 className="text-xl font-bold text-white">Create New Pipeline</h2>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Pipeline Name</label>
                <input 
                  type="text" 
                  value={pipelineName}
                  onChange={(e) => setPipelineName(e.target.value)}
                  placeholder="e.g., experimental-v4"
                  className="w-full bg-surface-900 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Configuration (JSON)</label>
                <div className="border border-white/10 rounded-lg overflow-hidden h-[400px]">
                  <Editor
                    height="100%"
                    defaultLanguage="json"
                    theme="vs-dark"
                    value={jsonConfig}
                    onChange={handleJsonChange}
                    options={{ minimap: { enabled: false }, fontSize: 14, formatOnPaste: true }}
                  />
                </div>
                {jsonError && (
                  <p className="mt-2 text-sm text-red-400 bg-red-500/10 p-2 rounded border border-red-500/20">
                    Invalid JSON: {jsonError}
                  </p>
                )}
              </div>
            </div>

            <div className="p-6 border-t border-white/10 flex justify-end gap-3 bg-surface-800/50">
              <button 
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button 
                disabled={!!jsonError || !pipelineName}
                className="px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 rounded-lg disabled:opacity-50 transition-colors"
              >
                Create Pipeline
              </button>
            </div>
          </div>
        </div>
      )}

      <PipelineAnalyticsDrawer 
        isOpen={!!selectedPipeline} 
        onClose={() => setSelectedPipeline(null)} 
        pipeline={selectedPipeline} 
      />
    </div>
  );
}
