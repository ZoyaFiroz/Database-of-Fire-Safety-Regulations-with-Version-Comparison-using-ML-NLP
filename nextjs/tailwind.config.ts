import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      colors: {
        modified: '#f59e0b',
        added: '#10b981',
        removed: '#ef4444',
        unchanged: '#6b7280',
        // Kept as the site-wide interactive-accent tokens (buttons, focus
        // rings, badges) so every component built against them picks up the
        // "Veritext" teal/gold identity automatically - the names are
        // legacy, the values are the brand palette.
        accent: {
          indigo: '#14b8a6',
          purple: '#d4af37',
        },
        brand: {
          teal: '#14b8a6',
          tealDark: '#0f766e',
          tealDeep: '#0a2e2b',
          gold: '#d4af37',
          goldLight: '#f4d878',
          goldDark: '#a67c1e',
          ink: '#071a1f',
          ink2: '#0b232b',
        },
      },
    },
  },
  plugins: [],
}
export default config
