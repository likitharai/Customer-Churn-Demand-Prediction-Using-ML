import React from 'react';

export default class PageErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (!this.state.error) return this.props.children;
    return <section className="panel route-error">
      <p className="eyebrow">PAGE ERROR</p>
      <h2>This page could not be displayed.</h2>
      <p>{this.state.error.message}</p>
      <button className="primary-button compact" onClick={() => window.location.assign('/')}>Return to dashboard</button>
    </section>;
  }
}

