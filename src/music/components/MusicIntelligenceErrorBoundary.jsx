import { Component } from "react";

export default class MusicIntelligenceErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorMessage: "" };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      errorMessage: error?.message || "Unknown Music Intelligence error",
    };
  }

  componentDidCatch(error, info) {
    console.error("Music Intelligence crashed:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-2xl border border-red-300 bg-red-50 p-5 text-red-900">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-red-500">
            Music Intelligence Error
          </p>
          <h3 className="mt-2 text-lg font-black">This section failed safely.</h3>
          <p className="mt-2 text-sm">
            The rest of Defending Sisyphus should remain usable.
          </p>
          <pre className="mt-3 overflow-auto rounded-xl bg-white/70 p-3 text-xs">
            {this.state.errorMessage}
          </pre>
        </div>
      );
    }

    return this.props.children;
  }
}
