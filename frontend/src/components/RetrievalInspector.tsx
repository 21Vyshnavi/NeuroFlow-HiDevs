'use client';

import React from 'react';
import { ReactFlow, Background, Controls, Edge, Node, MarkerType } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface RetrievalInspectorProps {
  retrievalData: {
    query: string;
    semantic_results: number;
    keyword_results: number;
    hybrid_results: number;
    rrf_fused: number;
    reranked: number;
    final_context: number;
  } | null;
}

export default function RetrievalInspector({ retrievalData }: RetrievalInspectorProps) {
  if (!retrievalData) {
    return (
      <div className="glass-card p-12 text-center text-gray-500">
        Run a query to see the retrieval pipeline visualization.
      </div>
    );
  }

  const defaultEdgeOptions = {
    animated: true,
    style: { stroke: '#818cf8', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#818cf8' },
  };

  const nodeStyle = {
    background: '#1e293b',
    border: '1px solid rgba(99, 102, 241, 0.3)',
    borderRadius: '0.5rem',
    padding: '0.75rem',
    color: '#e2e8f0',
    fontSize: '12px',
    width: 150,
    textAlign: 'center' as const,
  };

  const nodes: Node[] = [
    { id: 'query', position: { x: 250, y: 0 }, data: { label: <div className="font-semibold text-brand-300">Query</div> }, style: { ...nodeStyle, background: '#312e81', borderColor: '#6366f1' } },
    { id: 'semantic', position: { x: 50, y: 120 }, data: { label: <div><div>Semantic Search</div><div className="mt-1 bg-surface-900 text-xs rounded px-2 py-0.5 inline-block">{retrievalData.semantic_results} chunks</div></div> }, style: nodeStyle },
    { id: 'keyword', position: { x: 250, y: 120 }, data: { label: <div><div>Keyword Search</div><div className="mt-1 bg-surface-900 text-xs rounded px-2 py-0.5 inline-block">{retrievalData.keyword_results} chunks</div></div> }, style: nodeStyle },
    { id: 'hybrid', position: { x: 450, y: 120 }, data: { label: <div><div>Hybrid Search</div><div className="mt-1 bg-surface-900 text-xs rounded px-2 py-0.5 inline-block">{retrievalData.hybrid_results} chunks</div></div> }, style: nodeStyle },
    { id: 'rrf', position: { x: 250, y: 240 }, data: { label: <div><div className="font-semibold text-brand-300">RRF Fusion</div><div className="mt-1 bg-surface-900 text-xs rounded px-2 py-0.5 inline-block">{retrievalData.rrf_fused} fused</div></div> }, style: { ...nodeStyle, borderColor: '#818cf8' } },
    { id: 'reranker', position: { x: 250, y: 340 }, data: { label: <div><div>Cross-Encoder Reranker</div><div className="mt-1 bg-surface-900 text-xs rounded px-2 py-0.5 inline-block">{retrievalData.reranked} scored</div></div> }, style: nodeStyle },
    { id: 'context', position: { x: 250, y: 440 }, data: { label: <div><div className="font-semibold text-green-400">Final Context</div><div className="mt-1 bg-surface-900 text-xs rounded px-2 py-0.5 inline-block">{retrievalData.final_context} selected</div></div> }, style: { ...nodeStyle, borderColor: '#22c55e', background: 'rgba(34,197,94,0.1)' } },
  ];

  const edges: Edge[] = [
    { id: 'e1', source: 'query', target: 'semantic', ...defaultEdgeOptions },
    { id: 'e2', source: 'query', target: 'keyword', ...defaultEdgeOptions },
    { id: 'e3', source: 'query', target: 'hybrid', ...defaultEdgeOptions },
    { id: 'e4', source: 'semantic', target: 'rrf', ...defaultEdgeOptions },
    { id: 'e5', source: 'keyword', target: 'rrf', ...defaultEdgeOptions },
    { id: 'e6', source: 'hybrid', target: 'rrf', ...defaultEdgeOptions },
    { id: 'e7', source: 'rrf', target: 'reranker', ...defaultEdgeOptions },
    { id: 'e8', source: 'reranker', target: 'context', ...defaultEdgeOptions },
  ];

  return (
    <div className="glass-card p-6 mt-6">
      <h3 className="text-lg font-semibold text-white mb-4">Retrieval Inspector</h3>
      <div className="h-[500px] w-full bg-surface-900/50 rounded-lg border border-white/5">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          attributionPosition="bottom-right"
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#334155" gap={16} />
        </ReactFlow>
      </div>
    </div>
  );
}
