import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // ダーク HUD パレット（IMPLEMENTATION_PLAN_INTERIM.md §5.1 準拠）
        bg: "#0A0E1A",
        panel: "#101728",
        border: "#1F2A44",
        text: "#E5ECFF",
        sub: "#8B97B8",
        cyan: "#00E5FF",
        magenta: "#FF2D95",
        success: "#00FFA3",
        warning: "#FFB800",
        error: "#FF4D6D",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        "glow-cyan": "0 0 24px rgba(0, 229, 255, 0.35)",
        "glow-magenta": "0 0 24px rgba(255, 45, 149, 0.35)",
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 0 rgba(0, 229, 255, 0)" },
          "50%": { boxShadow: "0 0 18px rgba(0, 229, 255, 0.7)" },
        },
      },
      animation: {
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
