'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import type { Source, Evaluation } from '@/lib/api';

interface Citation {
  index: number;
  source_id: string;
  text: string;
}

interface UseSSEStreamReturn {
  tokens: string;
  sources: Source[];
  citations: Citation[];
  isStreaming: boolean;
  evaluation: Evaluation | null;
}

export function useSSEStream(runId: string | null): UseSSEStreamReturn {
  const [tokens, setTokens] = useState('');
  const [sources, setSources] = useState<Source[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!runId) {
      return;
    }

    // Reset state for new stream
    setTokens('');
    setSources([]);
    setCitations([]);
    setEvaluation(null);
    setIsStreaming(true);

    const es = new EventSource(`/api/query/stream/${runId}`);
    eventSourceRef.current = es;

    es.addEventListener('sources', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setSources(data);
      } catch (e) {
        console.error('Failed to parse sources event:', e);
      }
    });

    es.addEventListener('token', (event: MessageEvent) => {
      setTokens((prev) => prev + event.data);
    });

    es.addEventListener('citation', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setCitations((prev) => [...prev, data]);
      } catch (e) {
        console.error('Failed to parse citation event:', e);
      }
    });

    es.addEventListener('evaluation', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setEvaluation(data);
      } catch (e) {
        console.error('Failed to parse evaluation event:', e);
      }
    });

    es.addEventListener('done', () => {
      setIsStreaming(false);
      cleanup();
    });

    es.onerror = () => {
      setIsStreaming(false);
      cleanup();
    };

    return cleanup;
  }, [runId, cleanup]);

  return { tokens, sources, citations, isStreaming, evaluation };
}
