'use client';

import React, { useState, useRef } from 'react';

const DOCUMENTS = [
  { id: 'd1', name: 'research_paper.pdf', type: 'PDF', status: 'completed', chunks: 47, ingestedAt: '2 hours ago', chunkList: [{idx:0,preview:'Abstract: This paper explores...',embedded:true},{idx:1,preview:'Introduction: Large language...',embedded:true},{idx:2,preview:'Methods: We employed...',embedded:true}] },
  { id: 'd2', name: 'quarterly_report.docx', type: 'DOCX', status: 'completed', chunks: 23, ingestedAt: '5 hours ago', chunkList: [{idx:0,preview:'Executive Summary...',embedded:true},{idx:1,preview:'Financial Overview...',embedded:true}] },
  { id: 'd3', name: 'training_data.csv', type: 'CSV', status: 'processing', chunks: 0, ingestedAt: '1 min ago', chunkList: [] },
  { id: 'd4', name: 'architecture_diagram.png', type: 'Image', status: 'completed', chunks: 3, ingestedAt: '1 day ago', chunkList: [{idx:0,preview:'OCR: System architecture...',embedded:true}] },
  { id: 'd5', name: 'api_documentation.pdf', type: 'PDF', status: 'completed', chunks: 89, ingestedAt: '3 days ago', chunkList: [{idx:0,preview:'API Reference: NeuroFlow...',embedded:true},{idx:1,preview:'Authentication: Bearer...',embedded:true},{idx:2,preview:'Endpoints: POST /ingest...',embedded:true}] },
  { id: 'd6', name: 'product_specs.docx', type: 'DOCX', status: 'failed', chunks: 0, ingestedAt: '4 hours ago', chunkList: [] },
];

export default function DocumentsPage() {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingFile, setUploadingFile] = useState('');
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);
  const [similarChunks, setSimilarChunks] = useState<number[]>([]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      simulateUpload(e.dataTransfer.files[0].name);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      simulateUpload(e.target.files[0].name);
    }
  };

  const simulateUpload = (filename: string) => {
    setIsUploading(true);
    setUploadingFile(filename);
    setUploadProgress(0);
    
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            setIsUploading(false);
            setUploadProgress(0);
            setUploadingFile('');
          }, 1000);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const findSimilar = () => {
    setSimilarChunks([]);
    setTimeout(() => {
      setSimilarChunks([0, 2]); // highlight first and third chunk as simulation
    }, 600);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'PDF': return <span className="text-red-400 bg-red-400/10 p-1.5 rounded-md mr-2 text-xs font-bold">PDF</span>;
      case 'DOCX': return <span className="text-blue-400 bg-blue-400/10 p-1.5 rounded-md mr-2 text-xs font-bold">DOC</span>;
      case 'CSV': return <span className="text-green-400 bg-green-400/10 p-1.5 rounded-md mr-2 text-xs font-bold">CSV</span>;
      case 'Image': return <span className="text-purple-400 bg-purple-400/10 p-1.5 rounded-md mr-2 text-xs font-bold">IMG</span>;
      default: return <span className="text-gray-400 bg-gray-400/10 p-1.5 rounded-md mr-2 text-xs font-bold">FILE</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-green-500/20 text-green-400 border border-green-500/20">Completed</span>;
      case 'processing': return (
        <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/20 flex items-center gap-2 w-fit">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
          </span>
          Processing
        </span>
      );
      case 'failed': return <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-red-500/20 text-red-400 border border-red-500/20">Failed</span>;
      default: return <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-gray-500/20 text-gray-400 border border-gray-500/20">Pending</span>;
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Documents</h1>
        <p className="text-gray-400 mt-1">Manage files and vector embeddings</p>
      </div>

      <div 
        className={`glass-card relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
          isDragOver ? 'border-brand-400 bg-brand-500/5' : 'border-white/20 hover:border-brand-500/50 hover:bg-white/5'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          className="hidden" 
          ref={fileInputRef} 
          onChange={handleFileInput}
          multiple 
        />
        
        {!isUploading ? (
          <div className="flex flex-col items-center cursor-pointer" onClick={() => fileInputRef.current?.click()}>
            <div className="p-4 bg-brand-500/10 rounded-full mb-4">
              <svg className="w-8 h-8 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Drag & drop files here or click to browse</h3>
            <p className="text-sm text-gray-400">Supports PDF, DOCX, CSV, PNG, JPG up to 50MB</p>
            <div className="mt-6 flex gap-3">
              {['PDF', 'DOCX', 'CSV', 'Image'].map(type => (
                <div key={type} className="px-3 py-1 bg-surface-800 rounded-lg text-xs font-medium text-gray-400 border border-white/5 shadow-sm">
                  {type}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="w-full max-w-md mx-auto py-4 text-left">
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium text-white truncate">{uploadingFile}</span>
              <span className="text-brand-400 font-medium">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-surface-900 rounded-full h-2 overflow-hidden border border-white/5">
              <div 
                className="bg-brand-500 h-full rounded-full transition-all duration-300 ease-out" 
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-3 text-center">Extracting text and generating embeddings...</p>
          </div>
        )}
      </div>

      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-surface-800/50 border-b border-white/10">
              <tr>
                <th className="py-4 px-6 text-xs font-medium text-gray-400 uppercase tracking-wider">File Name</th>
                <th className="py-4 px-6 text-xs font-medium text-gray-400 uppercase tracking-wider">Type</th>
                <th className="py-4 px-6 text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                <th className="py-4 px-6 text-xs font-medium text-gray-400 uppercase tracking-wider">Chunks</th>
                <th className="py-4 px-6 text-xs font-medium text-gray-400 uppercase tracking-wider">Ingested At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {DOCUMENTS.map((doc) => (
                <React.Fragment key={doc.id}>
                  <tr 
                    className="hover:bg-white/5 transition-colors cursor-pointer"
                    onClick={() => setExpandedDoc(expandedDoc === doc.id ? null : doc.id)}
                  >
                    <td className="py-4 px-6">
                      <div className="flex items-center">
                        <svg className={`w-4 h-4 mr-3 transition-transform ${expandedDoc === doc.id ? 'rotate-90 text-brand-400' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="font-medium text-white">{doc.name}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 flex items-center">
                      {getTypeIcon(doc.type)}
                    </td>
                    <td className="py-4 px-6">
                      {getStatusBadge(doc.status)}
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-sm font-medium text-gray-300 bg-surface-800 px-2.5 py-1 rounded-md border border-white/5 shadow-sm">
                        {doc.chunks}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-sm text-gray-400">
                      {doc.ingestedAt}
                    </td>
                  </tr>
                  
                  {expandedDoc === doc.id && doc.chunkList.length > 0 && (
                    <tr className="bg-black/20 border-b-0">
                      <td colSpan={5} className="py-6 px-12 border-l-2 border-brand-500">
                        <div className="flex justify-between items-center mb-4">
                          <h4 className="text-sm font-medium text-white">Extracted Chunks ({doc.chunkList.length})</h4>
                          <button 
                            onClick={findSimilar}
                            className="text-xs font-medium bg-brand-500/10 text-brand-400 hover:bg-brand-500/20 px-3 py-1.5 rounded-lg transition-colors border border-brand-500/20 flex items-center gap-2"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                            Find Similar Chunks
                          </button>
                        </div>
                        <div className="grid grid-cols-1 gap-3">
                          {doc.chunkList.map((chunk) => (
                            <div 
                              key={chunk.idx} 
                              className={`bg-surface-800 p-4 rounded-lg border flex items-center justify-between transition-all duration-300 ${
                                similarChunks.includes(chunk.idx) 
                                  ? 'border-brand-500 ring-1 ring-brand-500 bg-brand-500/5 shadow-[0_0_15px_rgba(99,102,241,0.1)]' 
                                  : 'border-white/5'
                              }`}
                            >
                              <div className="flex items-center gap-4">
                                <span className="text-xs font-mono text-gray-500 bg-surface-900 px-2 py-1 rounded w-10 text-center">#{chunk.idx}</span>
                                <span className="text-sm text-gray-300 font-mono">{chunk.preview}</span>
                              </div>
                              {chunk.embedded && (
                                <span className="text-[10px] uppercase tracking-wider font-semibold text-green-400 bg-green-500/10 px-2 py-0.5 rounded border border-green-500/20">
                                  Embedded
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
