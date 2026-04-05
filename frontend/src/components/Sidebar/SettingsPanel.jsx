/**
 * SettingsPanel — API key management and LLM provider selection.
 * Just paste your key → provider + model auto-detected → saved to .env
 */
import { useState, useEffect, useCallback } from 'react';
import './SettingsPanel.css';

const API_BASE = 'http://127.0.0.1:8765';

const PROVIDERS = [
  { value: 'groq',      label: 'Groq',      keyField: 'groq_api_key',      envKey: 'groq' },
  { value: 'anthropic',  label: 'Anthropic', keyField: 'anthropic_api_key', envKey: 'anthropic' },
  { value: 'openai',     label: 'OpenAI',    keyField: 'openai_api_key',    envKey: 'openai' },
  { value: 'deepseek',   label: 'DeepSeek',  keyField: 'deepseek_api_key',  envKey: 'deepseek' },
];

const DEFAULT_MODELS = {
  groq: 'llama-3.3-70b-versatile',
  anthropic: 'claude-sonnet-4-20250514',
  openai: 'gpt-4o',
  deepseek: 'deepseek-chat',
};

function EyeIcon({ open }) {
  if (open) {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    );
  }
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

export default function SettingsPanel() {
  const [provider, setProvider] = useState('groq');
  const [model, setModel] = useState('');
  const [keys, setKeys] = useState({ anthropic: '', groq: '', deepseek: '', openai: '' });
  const [maskedKeys, setMaskedKeys] = useState({});
  const [showKey, setShowKey] = useState({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);
  const [loaded, setLoaded] = useState(false);

  // Fetch current settings from backend
  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/settings`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setProvider(data.llm_provider || 'groq');
      setModel(data.llm_model || '');
      setMaskedKeys(data.api_keys || {});
      setKeys({ anthropic: '', groq: '', deepseek: '', openai: '' });
      setLoaded(true);
    } catch (err) {
      console.error('Failed to fetch settings:', err);
      setToast({ type: 'error', message: 'Cannot reach backend. Is it running?' });
      setLoaded(true);
    }
  }, []);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  // Auto-clear toast
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(t);
  }, [toast]);

  const handleProviderChange = (newProvider) => {
    setProvider(newProvider);
    setModel(DEFAULT_MODELS[newProvider] || '');
  };

  const handleSave = async () => {
    setSaving(true);

    // Build the request body
    const body = {};

    // Always send provider and model
    body.llm_provider = provider;
    body.llm_model = model || DEFAULT_MODELS[provider] || '';

    // Send any API keys the user typed (non-empty)
    let hasAnyNewKey = false;
    PROVIDERS.forEach((p) => {
      const val = keys[p.envKey];
      if (val && val.trim()) {
        body[p.keyField] = val.trim();
        hasAnyNewKey = true;
      }
    });

    // Check: does the selected provider have a key (either new or existing)?
    const selectedProviderMasked = maskedKeys[provider] || '';
    const selectedProviderNewKey = keys[provider] || '';
    if (!selectedProviderMasked && !selectedProviderNewKey.trim()) {
      // No key for selected provider — check if any key was entered at all
      if (!hasAnyNewKey) {
        setToast({ type: 'error', message: `Enter an API key for ${provider} (or any provider)` });
        setSaving(false);
        return;
      }
    }

    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (data.saved) {
        // Update UI with what the backend actually set
        if (data.active_provider) setProvider(data.active_provider);
        if (data.active_model) setModel(data.active_model);
        setToast({ type: 'success', message: `Saved! Using ${data.active_provider} / ${data.active_model}` });
        await fetchSettings();
      } else {
        setToast({ type: 'error', message: data.error || 'Save failed' });
      }
    } catch (err) {
      console.error('Save error:', err);
      setToast({ type: 'error', message: 'Network error — is the backend running?' });
    } finally {
      setSaving(false);
    }
  };

  if (!loaded) {
    return (
      <div className="settings-panel" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Loading settings…</span>
      </div>
    );
  }

  return (
    <div className="settings-panel">
      {/* Provider & Model */}
      <div className="settings-section">
        <div className="settings-section-title">LLM Provider</div>

        <div className="settings-field">
          <label className="settings-label" htmlFor="settings-provider">Provider</label>
          <select
            id="settings-provider"
            className="settings-select"
            value={provider}
            onChange={(e) => handleProviderChange(e.target.value)}
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>

        <div className="settings-field">
          <label className="settings-label" htmlFor="settings-model">Model</label>
          <input
            id="settings-model"
            className="settings-input"
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={DEFAULT_MODELS[provider] || 'Enter model name'}
          />
        </div>
      </div>

      {/* API Keys */}
      <div className="settings-section">
        <div className="settings-section-title">API Keys</div>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>
          Paste any one key — provider & model auto-detected
        </div>

        {PROVIDERS.map((p) => {
          const masked = maskedKeys[p.envKey] || '';
          const isConfigured = masked.length > 0;
          const isActive = provider === p.value;

          return (
            <div className="settings-field" key={p.value}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <label className="settings-label" htmlFor={`settings-key-${p.value}`}>
                  {p.label}
                  {isActive && (
                    <span style={{ marginLeft: '6px', fontSize: '9px', color: 'var(--accent-blue)', fontWeight: 600 }}>
                      ACTIVE
                    </span>
                  )}
                </label>
                <span className="settings-key-status">
                  <span className={`settings-key-dot ${isConfigured ? 'configured' : 'missing'}`} />
                  {isConfigured ? masked : 'Not set'}
                </span>
              </div>
              <div className="settings-key-wrapper">
                <input
                  id={`settings-key-${p.value}`}
                  className="settings-input"
                  type={showKey[p.value] ? 'text' : 'password'}
                  value={keys[p.envKey]}
                  onChange={(e) => setKeys((prev) => ({ ...prev, [p.envKey]: e.target.value }))}
                  placeholder={isConfigured ? 'Enter new key to replace' : 'Paste your API key'}
                  autoComplete="off"
                />
                <button
                  className="settings-key-toggle"
                  type="button"
                  title={showKey[p.value] ? 'Hide' : 'Show'}
                  onClick={() => setShowKey((s) => ({ ...s, [p.value]: !s[p.value] }))}
                >
                  <EyeIcon open={showKey[p.value]} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Save */}
      <button
        className="settings-save-btn"
        onClick={handleSave}
        disabled={saving}
      >
        {saving ? 'Saving…' : 'Save Settings'}
      </button>

      {toast && (
        <div className={`settings-toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
