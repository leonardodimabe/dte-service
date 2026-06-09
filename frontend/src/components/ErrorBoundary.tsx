import { Component, type ErrorInfo, type ReactNode } from "react";

interface State {
  error: Error | null;
}

export default class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Error de render:", error, info);
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="center">
          <div className="card" style={{ maxWidth: 480 }}>
            <h2>Algo salió mal</h2>
            <p className="error">{this.state.error.message}</p>
            <button onClick={() => window.location.reload()}>Recargar</button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
