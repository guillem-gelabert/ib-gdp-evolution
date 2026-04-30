import type { Config } from "tailwindcss";

export default {
  theme: {
    extend: {
      colors: {
        cream: "#fff1e5",
        "cream-alt": "#f6e9d8",
        surface: "#fff8f4",
        ink: "#211a13",
        muted: "#6b6b6b",
        accent: "#660000",
        "accent-dark": "#3e0000",
        rule: "#d6d5d3",
        "rule-light": "#dfbfba",
        "footer-bg": "#e5d8cc",
      },
      fontFamily: {
        headline: ['"Instrument Serif"', "Georgia", "serif"],
        body: ['"DM Mono"', '"Courier New"', "monospace"],
        label: ['"DM Mono"', '"Courier New"', "monospace"],
      },
    },
  },
} satisfies Config;
