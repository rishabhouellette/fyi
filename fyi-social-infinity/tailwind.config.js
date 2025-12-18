/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './desktop/src/**/*.{js,jsx,ts,tsx,html}',
    './shared/ui/**/*.{js,jsx,ts,tsx}',
    './web-pro/**/*.{js,jsx,ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        'cyber-bg': '#000000',
        'cyber-void': '#0a0a1f',
        'cyber-primary': '#00f2ff',
        'cyber-purple': '#8b00ff',
        'cyber-green': '#00ff9d',
        'cyber-glass': 'rgba(10, 10, 31, 0.09)',
        'cyber-border': 'rgba(0, 242, 255, 0.4)',
      },
      fontFamily: {
        satoshi: ['Satoshi', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'cyber-glow': '0 0 30px rgba(0, 242, 255, 0.4)',
        'cyber-inner': 'inset 0 0 20px rgba(0, 242, 255, 0.1)',
        'cyber-glow-lg': '0 0 50px rgba(0, 242, 255, 0.6)',
        'purple-glow': '0 0 30px rgba(139, 0, 255, 0.5)',
        'green-glow': '0 0 30px rgba(0, 255, 157, 0.5)',
      },
      backdropBlur: {
        xs: '4px',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'breathe': 'breathe 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'rotate-slow': 'rotate 10s linear infinite',
        'shimmer': 'shimmer 3s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' }
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.05)', opacity: '0.9' }
        },
        glow: {
          'from': { boxShadow: '0 0 20px rgba(0,242,255,0.4)' },
          'to': { boxShadow: '0 0 40px rgba(0,242,255,0.8)' }
        },
        rotate: {
          'from': { transform: 'rotate(0deg)' },
          'to': { transform: 'rotate(360deg)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' }
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      }
    },
  },
  plugins: [],
}
