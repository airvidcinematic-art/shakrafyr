import { defineConfig } from "vite";

export default defineConfig({
  clearScreen: false,
  server: {
    port: 1432,
    strictPort: true,
    watch: { ignored: ["**/src-tauri/**", "**/ConvertedLibrary/**", "**/fixtures/**"] },
  },
});
