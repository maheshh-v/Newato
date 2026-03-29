/**
 * ARIA Root App Component
 * Routes to either the Overlay or Sidebar based on window type.
 * In development (browser), shows both with a toggle.
 */
import { useEffect } from 'react';
import Overlay from './components/Overlay/Overlay.jsx';
import Sidebar from './components/Sidebar/Sidebar.jsx';
import { useWebSocket } from './hooks/useWebSocket.js';

function getWindowType() {
  // In Electron, window type is passed via URL query param
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const type = params.get('window');
    if (type) return type;
    // Fallback: use aria bridge
    if (window.aria?.getWindowType) return window.aria.getWindowType();
  }
  return 'sidebar'; // default in browser dev mode
}

export default function App() {
  const windowType = getWindowType();
  const { submitTask } = useWebSocket();

  useEffect(() => {
    // In Electron sidebar: listen for task-submitted from IPC
    if (windowType === 'sidebar' && window.aria?.onTaskSubmitted) {
      window.aria.onTaskSubmitted((description) => {
        submitTask(description);
      });
    }
  }, [windowType, submitTask]);

  if (windowType === 'overlay') {
    return (
      <div style={{ width: '100vw', height: '100vh', background: 'transparent' }}>
        <Overlay onSubmit={submitTask} />
      </div>
    );
  }

  // Sidebar window
  return (
    <div style={{ width: '320px', height: '100vh', overflow: 'hidden' }}>
      <Sidebar />
    </div>
  );
}
