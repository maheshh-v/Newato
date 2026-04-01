/**
 * Overlay — the global task input overlay window.
 * Handles task submission and communicates with Electron via window.aria.
 */
import { useState, useEffect, useRef } from 'react';
import './Overlay.css';

const PLACEHOLDER = 'What should I do?';

/**
 * @param {{ onSubmit?: (task: string) => void }} props
 */
export default function Overlay({ onSubmit }) {
  const [input, setInput] = useState('');
  const [isFadingOut, setIsFadingOut] = useState(false);
  const inputRef = useRef(null);

  // Focus input on mount and when overlay is shown (via IPC)
  useEffect(() => {
    inputRef.current?.focus();

    if (window.aria?.onOverlayFocus) {
      window.aria.onOverlayFocus(() => {
        setInput('');
        setIsFadingOut(false);
        inputRef.current?.focus();
      });
    }
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setInput('');
      // In Electron, blur hides the overlay automatically (main.js blur handler)
      // Just clear the input; don't send anything to the backend
      if (window.aria?.resizeOverlay) {
        window.aria.resizeOverlay(56); // Reset to default height
      }
      return;
    }
    if (e.key === 'Enter' && input.trim()) {
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    const task = input.trim();
    if (!task) return;

    setIsFadingOut(true);

    // Notify via Electron IPC (in Electron context)
    if (window.aria) {
      window.aria.submitTask(task);
    } else {
      // Fallback: direct WS submit (browser dev mode)
      onSubmit?.(task);
    }

    setTimeout(() => {
      setInput('');
      setIsFadingOut(false);
    }, 200);
  };

  return (
    <div className={`overlay-container ${isFadingOut ? 'fade-out' : 'fade-in'}`}>
      <div className="overlay-window">
        {/* Input row */}
        <div className="overlay-input-row">
          <div className="overlay-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Z" />
              <path d="M12 8v4l3 3" />
            </svg>
          </div>
          <input
            ref={inputRef}
            type="text"
            className="overlay-input"
            placeholder={PLACEHOLDER}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            autoComplete="off"
            spellCheck="false"
          />
          {input.trim() && (
            <button
              className="overlay-submit-hint"
              onClick={handleSubmit}
              title="Run task"
            >
              ↵
            </button>
          )}
        </div>

        {/* Bottom hint */}
        <div className="overlay-footer">
          <span className="overlay-shortcut">Ctrl+Shift+Space</span>
          <span className="overlay-hint-text">↵ to run • Esc to dismiss</span>
        </div>
      </div>
    </div>
  );
}
