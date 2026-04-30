// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/eslint", "@nuxtjs/tailwindcss"],
  app: {
    head: {
      link: [
        {
          rel: "preconnect",
          href: "https://fonts.googleapis.com",
        },
        {
          rel: "preconnect",
          href: "https://fonts.gstatic.com",
          crossorigin: "",
        },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300;1,400;1,500&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,500;1,7..72,400&family=Source+Sans+3:wght@400;600;700&display=swap",
        },
      ],
      bodyAttrs: {
        class: "bg-cream",
      },
    },
  },
  vite: {
    optimizeDeps: { exclude: ["d3"] },
  },
});
