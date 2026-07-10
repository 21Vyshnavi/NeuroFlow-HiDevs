import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// Pipeline types
export interface Pipeline {
  id: string;
  name: string;
  description: string;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
  created_at: string;
  updated_at: string;
}

export interface CreatePipelinePayload {
  name: string;
  description?: string;
  model: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
}

export interface QueryPayload {
  pipeline_id: string;
  query: string;
  use_rag?: boolean;
}

export interface QueryResponse {
  run_id: string;
  pipeline_id: string;
  query: string;
  response: string;
  sources?: Source[];
  evaluation?: Evaluation;
}

export interface Source {
  document_id: string;
  chunk_id: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown>;
}

export interface Evaluation {
  run_id: string;
  relevance: number;
  faithfulness: number;
  coherence: number;
  latency_ms: number;
  token_count: number;
  timestamp: string;
}

export interface Document {
  id: string;
  filename: string;
  content_type: string;
  chunk_count: number;
  status: string;
  created_at: string;
}

export interface RatePayload {
  run_id: string;
  rating: number;
  feedback?: string;
}

// API functions
export async function getPipelines(): Promise<Pipeline[]> {
  const response = await api.get('/pipelines');
  return response.data;
}

export async function getPipeline(id: string): Promise<Pipeline> {
  const response = await api.get(`/pipelines/${id}`);
  return response.data;
}

export async function createPipeline(payload: CreatePipelinePayload): Promise<Pipeline> {
  const response = await api.post('/pipelines', payload);
  return response.data;
}

export async function submitQuery(payload: QueryPayload): Promise<QueryResponse> {
  const response = await api.post('/query', payload);
  return response.data;
}

export async function rateRun(payload: RatePayload): Promise<void> {
  const response = await api.post('/query/rate', payload);
  return response.data;
}

export async function getDocuments(): Promise<Document[]> {
  const response = await api.get('/documents');
  return response.data;
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function getEvaluations(): Promise<Evaluation[]> {
  const response = await api.get('/evaluations');
  return response.data;
}

export default api;
