/**
 * useWebSocket — manages the WebSocket connection to the ARIA backend.
 * Auto-reconnects with exponential backoff. Processes events into Zustand store.
 */
import { useEffect, useRef, useCallback } from 'react';
import useTaskStore from '../store/taskStore.js';

const WS_URL = 'ws://127.0.0.1:8765/ws';
const MAX_RECONNECT_DELAY_MS = 10_000;

export function useWebSocket() {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectDelayRef = useRef(1000);
  const mountedRef = useRef(true);

  const { upsertTask, addStep, setScreenshot, completeTask, failTask, setSidebarVisible, setOutputDir } = useTaskStore();

  const handleMessage = useCallback((event) => {
    let msg;
    try {
      msg = JSON.parse(event.data);
    } catch {
      return;
    }

    if (!msg.event_type) return; // ping or unknown

    const { task_id, event_type, data } = msg;

    // Handle settings event (no task_id)
    if (event_type === 'settings') {
      if (data?.output_dir) setOutputDir(data.output_dir);
      return;
    }

    switch (event_type) {
      case 'task_created':
        upsertTask({
          id: task_id,
          description: data.description,
          status: data.status || 'queued',
          created_at: msg.timestamp,
          ...data,
        });
        setSidebarVisible(true);
        break;

      case 'task_started':
        upsertTask({ id: task_id, status: 'running', ...data });
        break;

      case 'step_update':
        addStep(task_id, {
          step_number: data.step_number,
          tool_name: data.tool_name,
          step_text: data.step_text,
          timestamp: msg.timestamp,
          progress: data.progress,
        });
        upsertTask({ id: task_id, progress: data.progress, current_step_text: data.step_text });
        break;

      case 'screenshot_update':
        setScreenshot(task_id, data.image_b64);
        break;

      case 'task_completed':
        completeTask(task_id, data);
        break;

      case 'task_failed':
        failTask(task_id, data);
        break;

      default:
        break;
    }
  }, [upsertTask, addStep, setScreenshot, completeTask, failTask, setSidebarVisible, setOutputDir]);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[ARIA WS] Connected');
      reconnectDelayRef.current = 1000; // Reset backoff
    };

    ws.onmessage = handleMessage;

    ws.onclose = () => {
      if (!mountedRef.current) return;
      console.log(`[ARIA WS] Disconnected — reconnecting in ${reconnectDelayRef.current}ms`);
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 1.5, MAX_RECONNECT_DELAY_MS);
        connect();
      }, reconnectDelayRef.current);
    };

    ws.onerror = (err) => {
      console.warn('[ARIA WS] Error:', err);
      ws.close();
    };
  }, [handleMessage]);

  /** Send a task submission message over the WebSocket. */
  const submitTask = useCallback((description) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'submit_task', description }));
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { submitTask };
}
