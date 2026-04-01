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
  const taskQueueRef = useRef([]); // Queue tasks if WS isn't ready

  const { upsertTask, addStep, setScreenshot, completeTask, failTask, setSidebarVisible, setTasks } = useTaskStore();

  const handleMessage = useCallback((event) => {
    let msg;
    try {
      msg = JSON.parse(event.data);
    } catch {
      return;
    }

    if (!msg.event_type) return; // ping or unknown

    console.log('[ARIA WS] Message received:', msg.event_type, msg.task_id);

    const { task_id, event_type, data } = msg;

    switch (event_type) {
      case 'task_created':
        console.log('[ARIA WS] Task created:', task_id);
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
        console.log('[ARIA WS] Task started:', task_id);
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
        console.log('[ARIA WS] Task completed:', task_id);
        completeTask(task_id, data);
        break;

      case 'task_failed':
        console.log('[ARIA WS] Task failed:', task_id);
        failTask(task_id, data);
        break;

      default:
        break;
    }
  }, [upsertTask, addStep, setScreenshot, completeTask, failTask, setSidebarVisible, setTasks]);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = async () => {
      console.log('[ARIA WS] Connected');
      reconnectDelayRef.current = 1000; // Reset backoff
      
      // Fetch initial tasks on first connection
      try {
        const resp = await fetch('http://127.0.0.1:8765/tasks');
        const tasks = await resp.json();
        setTasks(tasks);
      } catch (err) {
        console.warn('[ARIA WS] Failed to fetch initial tasks:', err);
      }

      // Flush any queued tasks
      while (taskQueueRef.current.length > 0) {
        const queuedTask = taskQueueRef.current.shift();
        console.log('[ARIA WS] Flushing queued task:', queuedTask.description);
        ws.send(JSON.stringify(queuedTask));
      }
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
    const msg = JSON.stringify({ type: 'submit_task', description });
    console.log('[ARIA] Submitting task:', description);
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[ARIA WS] Sending task immediately');
      wsRef.current.send(msg);
    } else {
      console.log('[ARIA WS] WebSocket not ready, queuing task');
      taskQueueRef.current.push({ type: 'submit_task', description });
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
