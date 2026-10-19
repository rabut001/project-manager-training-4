import fs from "node:fs";
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

// GitHub Pages で一覧以外のパスを直接開いても、このアプリが開くようにする
function spaFallback(): Plugin {
  return {
    name: "spa-fallback",
    apply: "build",
    closeBundle() {
      const dist = path.resolve("dist");
      fs.copyFileSync(path.join(dist, "index.html"), path.join(dist, "404.html"));
    },
  };
}

export default defineConfig({
  base: "/project-manager-training-4/",
  plugins: [react(), spaFallback()],
  server: { port: 5173, strictPort: true },
});
