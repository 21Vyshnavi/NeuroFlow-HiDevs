'use client';

import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, Area, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';

interface PipelineAnalyticsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  pipeline: { name: string; version: string } | null;
}

export default function PipelineAnalyticsDrawer({ isOpen, onClose, pipeline }: PipelineAnalyticsDrawerProps) {
  const [activeTab, setActiveTab] = useState('latency');

  const latencyData = [
    { percentile: 'P50', ms: 120 },
    { percentile: 'P95', ms: 340 },
    { percentile: 'P99', ms: 890 }
  ];

  const costData = Array.from({ length: 30 }, (_, i) => ({
    day: `Day ${i + 1}`,
    cost: 0.003 + Math.random() * 0.005
  }));

  const metricsData = [
    { metric: 'Faithfulness', value: 0.89 },
    { metric: 'Relevance', value: 0.92 },
    { metric: 'Coherence', value: 0.85 },
    { metric: 'Groundedness', value: 0.78 }
  ];

  const errors = [
    { time: '10 mins ago', run_id: 'run-9a8b7c', msg: 'Connection timeout to OpenAI API after 30s' },
    { time: '2 hours ago', run_id: 'run-3f2e1d', msg: 'Rate limit exceeded - 429 response from Anthropic' },
    { time: '1 day ago', run_id: 'run-5x6y7z', msg: 'Context window exceeded - 128k token limit' }
  ];

  return (
    <>
      {isOpen && <div className="fixed inset-0 bg-black/60 z-40" onClick={onClose} />}
      <div className={`fixed right-0 top-0 h-full w-[560px] z-50 bg-surface-800/95 backdrop-blur-xl border-l border-white/10 transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        {pipeline && (
          <div className="flex flex-col h-full overflow-hidden">
            <div className="p-6 border-b border-white/10 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-white">{pipeline.name}</h2>
                <span className="text-sm text-brand-400">v{pipeline.version} Analytics</span>
              </div>
              <button onClick={onClose} className="text-gray-400 hover:text-white p-2">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            <div className="flex border-b border-white/10 px-6 pt-4">
              {['latency', 'cost', 'metrics', 'errors'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 font-medium text-sm capitalize border-b-2 transition-colors ${activeTab === tab ? 'border-brand-500 text-brand-400' : 'border-transparent text-gray-400 hover:text-gray-300'}`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="p-6 flex-1 overflow-y-auto">
              {activeTab === 'latency' && (
                <div className="h-[300px] w-full">
                  <h3 className="text-sm font-medium text-gray-400 mb-4">Response Latency Percentiles</h3>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={latencyData}>
                      <XAxis dataKey="percentile" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                      <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
                      <Bar dataKey="ms" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {activeTab === 'cost' && (
                <div className="h-[300px] w-full">
                  <h3 className="text-sm font-medium text-gray-400 mb-4">Cost Per Query (30 Days)</h3>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={costData}>
                      <XAxis dataKey="day" hide />
                      <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} domain={['auto', 'auto']} tickFormatter={(v) => `$${v.toFixed(3)}`} />
                      <Tooltip contentStyle={{backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} formatter={(v: number) => `$${v.toFixed(4)}`} />
                      <Line type="monotone" dataKey="cost" stroke="#818cf8" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {activeTab === 'metrics' && (
                <div className="h-[300px] w-full">
                  <h3 className="text-sm font-medium text-gray-400 mb-4">Average Evaluation Scores</h3>
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={metricsData}>
                      <PolarGrid stroke="rgba(255,255,255,0.1)" />
                      <PolarAngleAxis dataKey="metric" tick={{fill: '#94a3b8', fontSize: 12}} />
                      <Radar name="Score" dataKey="value" stroke="#818cf8" fill="#818cf8" fillOpacity={0.4} />
                      <Tooltip contentStyle={{backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {activeTab === 'errors' && (
                <div className="space-y-4">
                  {errors.map((err, i) => (
                    <div key={i} className="glass-card p-4 border-l-4 border-l-red-500">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-mono text-gray-500 bg-black/30 px-2 py-1 rounded">{err.run_id}</span>
                        <span className="text-xs text-gray-400">{err.time}</span>
                      </div>
                      <p className="text-sm text-red-200">{err.msg}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
