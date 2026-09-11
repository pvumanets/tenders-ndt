import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

async function boot() {
  const root = createRoot(document.getElementById("root")!);

  if (import.meta.env.DEV) {
    const params = new URLSearchParams(window.location.search);
    if (params.get("lab") === "run-chrome") {
      const { default: RunChromeLabPage } = await import("./lab/RunChromeLabPage");
      root.render(
        <StrictMode>
          <RunChromeLabPage />
        </StrictMode>,
      );
      return;
    }
  }

  root.render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}

void boot();
