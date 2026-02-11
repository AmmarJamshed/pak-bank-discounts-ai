import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#7C3AED",
        accent: "#22D3EE",
        muted: "#94A3B8",
        surface: "#0B1020",
        ink: "#E2E8F0",
        border: "#1E293B"
      }
    }
  },
  plugins: []
};

export default config;
