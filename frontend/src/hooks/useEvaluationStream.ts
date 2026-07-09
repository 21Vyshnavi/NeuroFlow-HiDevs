'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import type { Evaluation } from '@/lib/api';

interface UseEvaluationStreamReturn {
  evaluations: Evaluation[];
  isConnected: boolean;
}

const MAX_EVALUATIONS = 100;

export function useEvaluationStream(): UseEvaluationStreamReturn {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    // Clean up any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource('/api/evaluations/stream');
    eventSourceRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
    };

    es.onmessage = (event: MessageEvent) => {
      try {
        const evaluation: Evaluation = JSON.parse(event.data);
        setEvaluations((prev) => {
          const updated = [evaluation, ...prev];
          return updated.slice(0, MAX_EVALUATIONS);
        });
      } catch (e) {
        console.error('Failed to parse evaluation stream data:', e);
      }
    };

    es.onerror = () => {
      setIsConnected(false);
      es.close();
      eventSourceRef.current = null;

      // Auto-reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [connect]);

  return { evaluations, isConnected };
}
