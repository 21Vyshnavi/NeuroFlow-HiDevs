'use client';

import React, { useState, useEffect } from 'react';

const INITIAL_EVALUATIONS = [
  { id: 'eval-001', query: 'How does retrieval-augmented generation improve LLM accuracy?', pipeline: 'production-v2', scores: {faithfulness:0.92,relevance:0.88,coherence:0.91,groundedness:0.85}, overall: 0.89, timestamp: '2 min ago', answer: 'RAG improves accuracy by grounding LLM outputs...', chunks: ['Chunk 1: RAG combines retrieval...','Chunk 2: Vector databases enable...','Chunk 3: Evaluation metrics ensure...'] },
  { id: 'eval-002', query: 'What are the best practices for vector database indexing?', pipeline: 'experimental-v3', scores: {faithfulness:0.78,relevance:0.82,coherence:0.75,groundedness:0.71}, overall: 0.77, timestamp: '5 min ago', answer: 'Best practices include choosing appropriate index types...', chunks: ['Chunk 1: HNSW indexes provide...','Chunk 2: IVF-PQ offers memory...','Chunk 3: Index parameters should...'] },
  { id: 'eval-003', query: 'Explain the circuit breaker pattern for API resilience', pipeline: 'production-v2', scores: {faithfulness:0.95,relevance:0.93,coherence:0.89,groundedness:0.91}, overall: 0.92, timestamp: '8 min ago', answer: 'The circuit breaker pattern prevents cascade failures...', chunks: ['Chunk 1: Circuit breakers monitor...','Chunk 2: State transitions include...','Chunk 3: Redis-backed state enables...'] },
  { id: 'eval-004', query: 'How to implement hybrid search with RRF fusion?', pipeline: 'baseline', scores: {faithfulness:0.55,relevance:0.62,coherence:0.58,groundedness:0.48}, overall: 0.56, timestamp: '12 min ago', answer: 'Hybrid search combines semantic and keyword...', chunks: ['Chunk 1: Semantic search uses...','Chunk 2: BM25 provides keyword...','Chunk 3: RRF formula combines...'] },
  { id: 'eval-005', query: 'What metrics should be used to evaluate RAG systems?', pipeline: 'fine-tuned-v1', scores: {faithfulness:0.91,relevance:0.95,coherence:0.93,groundedness:0.88}, overall: 0.92, timestamp: '15 min ago', answer: 'Key metrics for RAG evaluation include...', chunks: ['Chunk 1: Faithfulness measures...','Chunk 2: Relevance assesses...','Chunk 3: Groundedness verifies...'] },
  { id: 'eval-006', query: 'Describe the fine-tuning pipeline architecture', pipeline: 'experimental-v3', scores: {faithfulness:0.67,relevance:0.71,coherence:0.69,groundedness:0.63}, overall: 0.68, timestamp: '22 min ago', answer: 'The fine-tuning pipeline extracts training data...', chunks: ['Chunk 1: Training data extraction...','Chunk 2: MLflow tracks experiments...','Chunk 3: Model registration enables...'] },
  { id: 'eval-007', query: 'How does cross-encoder reranking improve retrieval precision?', pipeline: 'production-v2', scores: {faithfulness:0.88,relevance:0.90,coherence:0.86,groundedness:0.82}, overall: 0.87, timestamp: '30 min ago', answer: 'Cross-encoder reranking applies a more sophisticated...', chunks: ['Chunk 1: Cross-encoders process...','Chunk 2: Unlike bi-encoders...','Chunk 3: The reranking step...'] },
  { id: 'eval-008', query: 'What is prompt injection and how to defend against it?', pipeline: 'baseline', scores: {faithfulness:0.45,relevance:0.52,coherence:0.48,groundedness:0.41}, overall: 0.47, timestamp: '45 min ago', answer: 'Prompt injection is an attack where...', chunks: ['Chunk 1: Injection attacks...','Chunk 2: Defense strategies...','Chunk 3: Input validation...'] }
];

const NEW_QUERIES = [
  "How to configure MLflow tracking?",
  "What is the optimal chunk size for PDF ingestion?",
  "Explain LLM-as-a-judge evaluation methodology."
];

export default function EvaluationsPage() {
  const [evaluations, setEvaluations] = useState(INITIAL_EVALUATIONS);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Simulated SSE
  useEffect(() => {
    let count = 0;
    const interval = setInterval(() => {
      count++;
      const newEval = {
        id: `eval-new-${count}`,
        query: NEW_QUERIES[count % NEW_QUERIES.length],
        pipeline: count % 2 === 0 ? 'production-v2' : 'experimental-v3',
        scores: {
          faithfulness: 0.7 + Math.random() * 0.25,
          relevance: 0.7 + Math.random() * 0.25,
          coherence: 0.7 + Math.random() * 0.25,
          groundedness: 0.7 + Math.random() * 0.25,
        },
        get overall() { return (this.scores.faithfulness + this.scores.relevance + this.scores.coherence + this.scores.groundedness) / 4; },
        timestamp: 'Just now',
        answer: 'Simulated streaming answer based on the query...',
        chunks: ['Chunk 1: Data...', 'Chunk 2: More data...', 'Chunk 3: Context...']
      };
      
      setEvaluations(prev => [newEval, ...prev].slice(0, 50));
    }, 8000);
    
    return () => clearInterval(interval);
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getBadgeColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400 bg-green-500/20 ring-green-500/30';
    if (score >= 0.6) return 'text-yellow-400 bg-yellow-500/20 ring-yellow-500/30';
    return 'text-red-400 bg-red-500/20 ring-red-500/30';
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            Evaluation Feed
            <span className="flex items-center gap-2 text-xs font-medium bg-green-500/20 text-green-400 px-3 py-1 rounded-full uppercase tracking-wider">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              Live
            </span>
          </h1>
          <p className="text-gray-400 mt-1">Real-time LLM-as-a-judge quality metrics</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-green-400 bg-surface-800/50 px-3 py-1.5 rounded-lg border border-green-500/20">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
          Connected to SSE
        </div>
      </div>

      <div className="glass-card p-4 flex flex-wrap gap-4 items-center">
        <select className="bg-surface-700 border border-white/10 text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none">
          <option>All Pipelines</option>
          <option>production-v2</option>
          <option>experimental-v3</option>
          <option>baseline</option>
        </select>
        <div className="flex items-center gap-2 bg-surface-700 border border-white/10 rounded-lg px-2 text-sm">
          <select className="bg-transparent text-white py-2 outline-none">
            <option>Faithfulness</option>
            <option>Relevance</option>
            <option>Coherence</option>
            <option>Groundedness</option>
          </select>
          <span className="text-gray-500">&lt;</span>
          <input type="number" step="0.1" placeholder="0.7" className="w-16 bg-transparent text-white py-2 outline-none text-center" />
        </div>
        <div className="flex items-center gap-2">
          <input type="date" className="bg-surface-700 border border-white/10 text-gray-300 rounded-lg px-3 py-2 text-sm outline-none" />
          <span className="text-gray-500">to</span>
          <input type="date" className="bg-surface-700 border border-white/10 text-gray-300 rounded-lg px-3 py-2 text-sm outline-none" />
        </div>
        <button className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors">
          Reset Filters
        </button>
      </div>

      <div className="space-y-4">
        {evaluations.map((ev, index) => {
          const isExpanded = expandedId === ev.id;
          return (
            <div 
              key={ev.id} 
              className={`glass-card-hover p-5 cursor-pointer animate-slide-up`}
              style={{ animationDelay: `${index * 50}ms` }}
              onClick={() => setExpandedId(isExpanded ? null : ev.id)}
            >
              <div className="flex flex-col lg:flex-row gap-6">
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-base font-medium text-white truncate pr-4">{ev.query.length > 100 ? ev.query.substring(0, 100) + '...' : ev.query}</h3>
                    <span className="text-xs text-gray-500 whitespace-nowrap">{ev.timestamp}</span>
                  </div>
                  <span className="inline-block px-2.5 py-1 text-xs font-medium bg-brand-500/20 text-brand-300 rounded-full border border-brand-500/20">
                    {ev.pipeline}
                  </span>
                </div>

                <div className="flex items-center gap-6 lg:w-1/2 shrink-0">
                  <div className="flex-1 space-y-3">
                    {[
                      { label: 'Faithfulness', val: ev.scores.faithfulness },
                      { label: 'Relevance', val: ev.scores.relevance },
                      { label: 'Coherence', val: ev.scores.coherence },
                      { label: 'Groundedness', val: ev.scores.groundedness }
                    ].map(metric => (
                      <div key={metric.label} className="flex items-center gap-3">
                        <span className="text-xs text-gray-400 w-24">{metric.label}</span>
                        <div className="flex-1 bg-surface-900 rounded-full h-1.5 overflow-hidden">
                          <div className={`h-full rounded-full ${getScoreColor(metric.val)}`} style={{ width: `${metric.val * 100}%` }} />
                        </div>
                        <span className="text-xs font-medium text-gray-300 w-8 text-right">{metric.val.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex flex-col items-center justify-center pl-6 border-l border-white/10">
                    <span className={`text-2xl font-bold px-4 py-2 rounded-xl ring-1 ${getBadgeColor(ev.overall)}`}>
                      {ev.overall.toFixed(2)}
                    </span>
                    <span className="text-[10px] text-gray-500 uppercase tracking-widest mt-2">Overall</span>
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="mt-6 pt-6 border-t border-white/10 space-y-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">Full Query</h4>
                    <p className="text-white bg-surface-900/50 p-4 rounded-lg border border-white/5">{ev.query}</p>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">Generated Answer</h4>
                      <div className="bg-surface-900/50 p-4 rounded-lg border border-white/5 h-48 overflow-y-auto">
                        <p className="text-gray-300 text-sm">{ev.answer}</p>
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">Retrieved Chunks</h4>
                      <div className="bg-surface-900/50 p-4 rounded-lg border border-white/5 h-48 overflow-y-auto space-y-3">
                        {ev.chunks.map((chunk, i) => (
                          <div key={i} className="text-sm text-gray-400 pb-3 border-b border-white/5 last:border-0 last:pb-0">
                            {chunk}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
