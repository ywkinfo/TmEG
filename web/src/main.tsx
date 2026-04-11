import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";

import { App } from "./App";
import { applyLegacyHashRedirect } from "./lib/legacy-hash";
import "./styles.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Missing #root mount point for the reader application.");
}

const root = ReactDOM.createRoot(rootElement);

function mountApp(): void {
  root.render(
    <React.StrictMode>
      <HashRouter>
        <App />
      </HashRouter>
    </React.StrictMode>
  );
}

window.addEventListener("hashchange", () => {
  applyLegacyHashRedirect(window.location, window.history);
});

applyLegacyHashRedirect(window.location, window.history);
mountApp();
