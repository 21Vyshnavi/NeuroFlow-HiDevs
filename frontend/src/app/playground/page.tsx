'use client';

import React, { useState } from 'react';
import MetricGauge from '@/components/MetricGauge';
import CitationDrawer from '@/components/CitationDrawer';
import RetrievalInspector from '@/components/RetrievalInspector';

const SAMPLE_PIPELINES = [
  { name: 'production-v2', avg_score: 0.87, version: '2.1.0' },
  { name: 'experimental-v3', avg_score: 0.72, version: '3.0.0-beta' },
  { name: 'baseline', avg_score: 0.65, version: '1.0.0' }
];

const SAMPLE_SOURCES = [
  { title: 'Research Paper: RAG Systems', relevance: 0.94, chunk_preview: 'Retrieval-augmented generation combines...' },
  { title: 'API Documentation v2.1', relevance: 0.87, chunk_preview: 'The query endpoint accepts...' },
  { title: 'Technical Blog: Vector Search', relevance: 0.76, chunk_preview: 'Modern vector databases enable...' }
];

const SAMPLE_RESPONSE = 'Retrieval-Augmented Generation (RAG) is a technique that enhances Large Language Model outputs by retrieving relevant context from a knowledge base before generating responses. The process involves three key stages: First, the user query is embedded into a vector representation using a model like text-embedding-ada-002. Second, this embedding is used to search a vector database (such as pgvector) for semantically similar document chunks using approximate nearest neighbor search. Third, the retrieved chunks are assembled into a prompt alongside the original query and sent to the LLM for generation. This approach significantly reduces hallucination by grounding the model\'s output in verified source material, and enables the system to access knowledge beyond its training data cutoff. Production RAG systems typically add hybrid search (combining semantic and keyword approaches), cross-encoder reranking for precision, and automated evaluation using metrics like faithfulness, relevance, coherence, and groundedness.';

const SAMPLE_CITATIONS = [
  { id: 1, text: '[1]', chunk_content: 'Retrieval-augmented generation combines the strengths of retrieval-based and generation-based approaches...', document_title: 'Research Paper: RAG Systems', relevance_score: 0.94, metadata: { author: 'Smith et al.', year: '2024', pages: '12-15' } },
  { id: 2, text: '[2]', chunk_content: 'Vector databases enable efficient similarity search across millions of document embeddings...', document_title: 'Technical Blog: Vector Search', relevance_score: 0.87, metadata: { source: 'Engineering Blog', published: '2024-01' } },
  { id: 3, text: '[3]', chunk_content: 'The evaluation framework measures faithfulness, relevance, coherence, and groundedness to ensure RAG quality...', document_title: 'API Documentation v2.1', relevance_score: 0.76, metadata: { version: '2.1.0', section: 'Evaluation' } }
];

const SAMPLE_EVAL = { faithfulness: 0.89, relevance: 0.92, coherence: 0.85, groundedness: 0.78 };
const SAMPLE_RETRIEVAL = { query: 'How does RAG work?', semantic_results: 45, keyword_results: 32, hybrid_results: 28, rrf_fused: 60, reranked: 15, final_context: 5 };

export default function PlaygroundPage() {
  const [selectedPipeline, setSelectedPipeline] = useState(SAMPLE_PIPELINES[0].name);
  const [comparePipeline, setComparePipeline] = useState(SAMPLE_PIPELINES[1].name);
  const [query, setQuery] = useState('');
  const [compareMode, setCompareMode] = useState(false);
  
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState('');
  const [showEval, setShowEval] = useState(false);
  const [showInspector, setShowInspector] = useState(false);
  
  const [isStreaming2, setIsStreaming2] = useState(false);
  const [streamedText2, setStreamedText2] = useState('');
  const [showEval2, setShowEval2] = useState(false);

  const [selectedCitation, setSelectedCitation] = useState<any>(null);

  const handleSubmit = () => {
    if (!query) return;
    
    setIsStreaming(true);
    setStreamedText('');
    setShowEval(false);
    
    if (compareMode) {
      setIsStreaming2(true);
      setStreamedText2('');
      setShowEval2(false);
    }

    const words = SAMPLE_RESPONSE.split(' ');
    let currentIndex = 0;
    
    const interval = setInterval(() => {
      if (currentIndex < words.length) {
        setStreamedText(prev => prev + (prev ? ' ' : '') + words[currentIndex]);
        if (compareMode) {
          setStreamedText2(prev => prev + (prev ? ' ' : '') + words[currentIndex]);
        }
        currentIndex++;
      } else {
        clearInterval(interval);
        setIsStreaming(false);
        if (compareMode) setIsStreaming2(false);
        
        setTimeout(() => {
          setShowEval(true);
          if (compareMode) setShowEval2(true);
        }, 2000);
      }
    }, 30);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Query Playground</h1>
        <p className="text-gray-400 mt-1">Test and compare pipeline responses in real-time</p>
      </div>

      <div className="glass-card p-4 flex items-center gap-6 flex-wrap">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-gray-400">Pipeline:</label>
          <select 
            value={selectedPipeline}
            onChange={(e) => setSelectedPipeline(e.target.value)}
            className="bg-surface-700 border border-white/10 text-white rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {SAMPLE_PIPELINES.map(p => (
              <option key={p.name} value={p.name}>{p.name} (v{p.version} - Avg: {p.avg_score})</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3 border-l border-white/10 pl-6">
          <label className="text-sm font-medium text-gray-400">Compare Mode:</label>
          <button 
            type="button" 
            className="toggle-switch"
            style={{ backgroundColor: compareMode ? '#6366f1' : '#334155' }}
            onClick={() => setCompareMode(!compareMode)}
          >
            <span className={`toggle-switch-dot ${compareMode ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        {compareMode && (
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-400">Pipeline 2:</label>
            <select 
              value={comparePipeline}
              onChange={(e) => setComparePipeline(e.target.value)}
              className="bg-surface-700 border border-white/10 text-white rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {SAMPLE_PIPELINES.map(p => (
                <option key={p.name} value={p.name}>{p.name} (v{p.version} - Avg: {p.avg_score})</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="glass-card p-6">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your query here..."
          className="w-full h-32 bg-surface-900/50 border border-white/10 rounded-lg p-4 text-white focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
        />
        <div className="flex justify-between items-center mt-3">
          <span className="text-xs text-gray-500">{query.length}/2000</span>
          <div className="flex gap-3">
            <button 
              onClick={() => setShowInspector(!showInspector)}
              className="px-4 py-2 text-sm font-medium text-gray-300 bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/10"
            >
              🔍 Retrieval Inspector
            </button>
            <button 
              onClick={handleSubmit}
              disabled={isStreaming || !query}
              className="px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 rounded-lg transition-colors disabled:opacity-50"
            >
              {isStreaming ? 'Generating...' : 'Submit Query'}
            </button>
          </div>
        </div>
      </div>

      {showInspector && <RetrievalInspector retrievalData={streamedText ? SAMPLE_RETRIEVAL : null} />}

      {streamedText && (
        compareMode ? (
          <div className="grid grid-cols-2 gap-6">
            {/* Panel 1 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-brand-400">{selectedPipeline}</h3>
              <div className="glass-card p-5 min-h-[200px]">
                <p className="text-gray-200 leading-relaxed">
                  {streamedText}
                  {isStreaming && <span className="animate-pulse ml-1 inline-block w-2 h-4 bg-white" />}
                </p>
                {!isStreaming && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {SAMPLE_CITATIONS.map(cit => (
                      <button key={cit.id} onClick={() => setSelectedCitation(cit)} className="text-xs font-medium bg-brand-500/20 text-brand-300 px-3 py-1 rounded-full cursor-pointer hover:bg-brand-500/30 transition-colors border border-brand-500/20">
                        {cit.text} {cit.document_title}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {showEval && (
                <div className="glass-card p-6 grid grid-cols-4 gap-4 animate-fade-in">
                  <MetricGauge label="Faithfulness" value={SAMPLE_EVAL.faithfulness} />
                  <MetricGauge label="Relevance" value={SAMPLE_EVAL.relevance} />
                  <MetricGauge label="Coherence" value={SAMPLE_EVAL.coherence} />
                  <MetricGauge label="Groundedness" value={SAMPLE_EVAL.groundedness} />
                </div>
              )}
            </div>
            
            {/* Panel 2 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-brand-400">{comparePipeline}</h3>
              <div className="glass-card p-5 min-h-[200px]">
                <p className="text-gray-200 leading-relaxed">
                  {streamedText2}
                  {isStreaming2 && <span className="animate-pulse ml-1 inline-block w-2 h-4 bg-white" />}
                </p>
                {!isStreaming2 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {SAMPLE_CITATIONS.map(cit => (
                      <button key={cit.id} onClick={() => setSelectedCitation(cit)} className="text-xs font-medium bg-brand-500/20 text-brand-300 px-3 py-1 rounded-full cursor-pointer hover:bg-brand-500/30 transition-colors border border-brand-500/20">
                        {cit.text} {cit.document_title}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {showEval2 && (
                <div className="glass-card p-6 grid grid-cols-4 gap-4 animate-fade-in">
                  <MetricGauge label="Faithfulness" value={SAMPLE_EVAL.faithfulness - 0.1} />
                  <MetricGauge label="Relevance" value={SAMPLE_EVAL.relevance - 0.05} />
                  <MetricGauge label="Coherence" value={SAMPLE_EVAL.coherence - 0.12} />
                  <MetricGauge label="Groundedness" value={SAMPLE_EVAL.groundedness - 0.08} />
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-6 animate-fade-in">
            {/* Sources */}
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">Retrieved Sources</h3>
              <div className="grid grid-cols-3 gap-4">
                {SAMPLE_SOURCES.map((source, idx) => (
                  <div key={idx} className="glass-card p-4">
                    <h4 className="text-sm font-semibold text-white truncate mb-2">{source.title}</h4>
                    <div className="w-full bg-surface-900 rounded-full h-1.5 mb-1 relative overflow-hidden">
                      <div className="bg-brand-500 h-1.5 rounded-full" style={{ width: `${source.relevance * 100}%` }} />
                    </div>
                    <span className="text-xs text-gray-500">{Math.round(source.relevance * 100)}% match</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Answer */}
            <div className="glass-card p-6 min-h-[200px] flex flex-col">
              <div className="flex-1">
                <p className="text-gray-200 leading-relaxed text-lg">
                  {streamedText}
                  {isStreaming && <span className="animate-pulse ml-1 inline-block w-2 h-5 bg-white align-middle" />}
                </p>
              </div>
              
              {!isStreaming && (
                <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between">
                  <div className="flex flex-wrap gap-2">
                    {SAMPLE_CITATIONS.map(cit => (
                      <button key={cit.id} onClick={() => setSelectedCitation(cit)} className="text-xs font-medium bg-brand-500/20 text-brand-300 px-3 py-1 rounded-full cursor-pointer hover:bg-brand-500/30 transition-colors border border-brand-500/20">
                        {cit.text} {cit.document_title}
                      </button>
                    ))}
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="p-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 rounded-lg transition-colors">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" /></svg>
                    </button>
                    <button className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" /></svg>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Eval Metrics */}
            {showEval && (
              <div className="glass-card p-6 grid grid-cols-4 gap-4 animate-slide-up">
                <MetricGauge label="Faithfulness" value={SAMPLE_EVAL.faithfulness} />
                <MetricGauge label="Relevance" value={SAMPLE_EVAL.relevance} />
                <MetricGauge label="Coherence" value={SAMPLE_EVAL.coherence} />
                <MetricGauge label="Groundedness" value={SAMPLE_EVAL.groundedness} />
              </div>
            )}
          </div>
        )
      )}

      <CitationDrawer 
        isOpen={!!selectedCitation} 
        onClose={() => setSelectedCitation(null)} 
        citation={selectedCitation} 
      />
    </div>
  );
}
