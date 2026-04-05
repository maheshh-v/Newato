/**
 * Overlay — top-right assistant surface with a continuous dot → preview → panel transition.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import './Overlay.css';

const PLACEHOLDER = 'What should I do?';
const HOVER_DELAY_MS = 50;
const OPEN_DURATION_MS = 360;
const CLOSE_DURATION_MS = 280;
const PREVIEW_SUMMARY = "What's happening in the tab: Watching current page context, clipboard, and recent task updates.";

/**
 * @param {{ onSubmit?: (task: string) => void }} props
 */
export default function Overlay({ onSubmit }) {
  const [input, setInput] = useState('');
  const [uiState, setUiState] = useState('idle'); // idle | preview | active | closing
  const [isReducedMotion, setIsReducedMotion] = useState(false);
  const inputRef = useRef(null);
  const hoverTimerRef = useRef(null);
  const closeTimerRef = useRef(null);

  const previewScale = useMemo(() => {
    const chars = PREVIEW_SUMMARY.length;
    const previewWidth = Math.max(140, Math.min(260, 140 + Math.round(chars * 0.6)));
    return Number((previewWidth / 400).toFixed(3));
  }, []);

  const clearTimers = () => {
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  };

  const focusInput = () => {
    const focusDelay = isReducedMotion ? 0 : 36;
    setTimeout(() => inputRef.current?.focus(), focusDelay);
  };

  const openPanel = () => {
    clearTimers();
    setUiState('active');
    focusInput();
    window.aria?.setOverlayActive?.(true);
  };

  const closeToDot = () => {
    clearTimers();
    setUiState('closing');
    window.aria?.setOverlayActive?.(false);
    closeTimerRef.current = setTimeout(() => {
      setUiState('idle');
    }, isReducedMotion ? 120 : CLOSE_DURATION_MS);
  };

  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    const updateMotionPref = () => setIsReducedMotion(Boolean(mq?.matches));
    updateMotionPref();
    mq?.addEventListener?.('change', updateMotionPref);

    if (window.aria?.onAssistantOpenPanel) {
      window.aria.onAssistantOpenPanel(() => {
        setInput('');
        openPanel();
      });
    }

    if (window.aria?.onAssistantCollapseToDot) {
      window.aria.onAssistantCollapseToDot(() => {
        closeToDot();
      });
    }

    const handleGlobalShortcut = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openPanel();
      }
      if (e.key === 'Escape' && (uiState === 'active' || uiState === 'preview')) {
        e.preventDefault();
        closeToDot();
      }
    };

    window.addEventListener('keydown', handleGlobalShortcut);

    return () => {
      window.removeEventListener('keydown', handleGlobalShortcut);
      mq?.removeEventListener?.('change', updateMotionPref);
      clearTimers();
    };
  }, [uiState, isReducedMotion]);

  useEffect(() => {
    if (uiState === 'active') {
      focusInput();
    }
  }, []);

  useEffect(() => {
    let currentIgnore = null;
    const handleGlobalPointer = (e) => {
      // Find if we are hovering anything clickable
      const isClickable = !!e.target.closest('.assistant-hit-target, .assistant-shell, .assistant-preview, .assistant-backdrop, button, input, .assistant-chip');
      const shouldIgnore = !isClickable;

      if (currentIgnore !== shouldIgnore) {
        currentIgnore = shouldIgnore;
        window.aria?.setIgnoreMouseEvents?.(shouldIgnore, { forward: true });
      }
    };

    window.addEventListener('mousemove', handleGlobalPointer);
    return () => {
      window.removeEventListener('mousemove', handleGlobalPointer);
    };
  }, []);

  const handleHoverStart = () => {
    clearTimers();
    if (uiState !== 'idle') return;
    hoverTimerRef.current = setTimeout(() => {
      setUiState('preview');
    }, HOVER_DELAY_MS);
  };

  const handleHoverEnd = () => {
    if (uiState === 'preview') {
      setUiState('idle');
    }
    if (uiState === 'idle') {
      clearTimers();
    }
  };

  const handleActivationClick = () => {
    clearTimers();
    openPanel();
  };

  const handlePanelKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      closeToDot();
      return;
    }
    if (e.key === 'Enter' && input.trim()) {
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    const task = input.trim();
    if (!task) return;

    if (window.aria) {
      window.aria.submitTask(task);
    } else {
      onSubmit?.(task);
    }

    setInput('');
    closeToDot();
  };

  const shellClass = `assistant-shell ${uiState === 'active' ? 'active' : ''}`;

  return (
    <div
      className={`assistant-root state-${uiState} ${isReducedMotion ? 'reduced-motion' : ''}`}
      style={{
        '--open-ms': `${isReducedMotion ? 160 : OPEN_DURATION_MS}ms`,
        '--close-ms': `${isReducedMotion ? 140 : CLOSE_DURATION_MS}ms`,
        '--preview-scale': previewScale,
      }}
      onMouseEnter={handleHoverStart}
      onMouseLeave={handleHoverEnd}
    >
      {(uiState === 'active' || uiState === 'closing') && (
        <button
          type="button"
          className="assistant-backdrop"
          aria-label="Close assistant"
          onMouseDown={closeToDot}
        />
      )}

      <button
        type="button"
        className="assistant-hit-target"
        aria-label="Open assistant"
        onClick={handleActivationClick}
      />

      <div className="assistant-dot-wrap">
        <div className="assistant-dot" />
      </div>

      <div 
        className="assistant-preview" 
        aria-hidden={uiState !== 'preview'}
        onClick={handleActivationClick}
      >
        <p className="assistant-preview-title">What's happening in the tab</p>
        <p className="assistant-preview-text">{PREVIEW_SUMMARY.replace("What's happening in the tab: ", '')}</p>
      </div>

      <div
        className={shellClass}
        onClick={uiState === 'preview' ? handleActivationClick : undefined}
      >
        <div className="assistant-panel" aria-hidden={uiState !== 'active'}>
          <div className="assistant-panel-header">
            <span className="assistant-panel-title">NEWATO</span>
            <button
              type="button"
              className="assistant-close"
              onClick={closeToDot}
              aria-label="Collapse assistant"
            >
              Esc
            </button>
          </div>

          <div className="assistant-input-wrap">
            <input
              ref={inputRef}
              type="text"
              className="assistant-input"
              placeholder={PLACEHOLDER}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handlePanelKeyDown}
              autoComplete="off"
              spellCheck="false"
            />
            <button
              type="button"
              className="assistant-send"
              onClick={handleSubmit}
              disabled={!input.trim()}
            >
              Run
            </button>
          </div>

          <div className="assistant-suggestions" aria-label="Context-aware suggestions">
            <button type="button" className="assistant-chip" onClick={() => setInput('Summarize this tab and suggest next actions')}>
              Summarize this tab
            </button>
            <button type="button" className="assistant-chip" onClick={() => setInput('Draft a reply based on this context')}>
              Draft response
            </button>
            <button type="button" className="assistant-chip" onClick={() => setInput('List blockers and quick fixes')}>
              Find blockers
            </button>
          </div>

          <p className="assistant-shortcuts">Ctrl/Cmd + K to open · Esc to collapse</p>
        </div>
      </div>
    </div>
  );
}
