import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ARIA UI] Renderer error', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            width: '100%',
            height: '100%',
            background: '#0b0f19',
            color: '#d0d7e2',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '24px',
            textAlign: 'center',
            fontFamily: 'system-ui, sans-serif',
          }}
        >
          <p style={{ fontSize: '14px', fontWeight: 700, marginBottom: '8px' }}>ARIA sidebar hit a renderer error</p>
          <p style={{ fontSize: '12px', opacity: 0.8 }}>
            Restart the sidebar window. The app will keep logging details in the console.
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}
