import React from "react";
import ErrorState from "./ErrorState.jsx";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  componentDidCatch(error, info) {
    console.error("ErrorBoundary caught", error, info);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="p-8">
          <ErrorState
            title="Unexpected error"
            description={this.state.error.message}
            onRetry={() => this.setState({ error: null })}
          />
        </div>
      );
    }
    return this.props.children;
  }
}