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
        accent: {
          indigo: '#6366f1',
          purple: '#8b5cf6',
        },
      },
    },
  },
  plugins: [],
}
export default config
