/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#000000',
          primary: '#00f2ff',
          purple: '#8b00ff',
          green: '#00ff9d',
          dark: '#0a0a0f',
          darker: '#050508',
        }
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.5s ease-out',
        'fade-in': 'fadeIn 0.3s ease-out',
        'pulse-cyber': 'pulseCyber 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        glow: {
          '0%, 100%': { 
            boxShadow: '0 0 20px rgba(0, 242, 255, 0.5)' 
          },
          '50%': { 
            boxShadow: '0 0 40px rgba(0, 242, 255, 0.8)' 
          }
        },
        slideUp: {
          '0%': { 
            transform: 'translateY(10px)', 
            opacity: '0' 
          },
          '100%': { 
            transform: 'translateY(0)', 
            opacity: '1' 
          }
        },
        slideDown: {
          '0%': { 
            transform: 'translateY(-10px)', 
            opacity: '0' 
          },
          '100%': { 
            transform: 'translateY(0)', 
            opacity: '1' 
          }
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        pulseCyber: {
          '0%, 100%': { 
            opacity: '1',
            transform: 'scale(1)'
          },
          '50%': { 
            opacity: '0.8',
            transform: 'scale(1.05)'
          }
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-cyber': 'linear-gradient(135deg, #00f2ff 0%, #8b00ff 50%, #00ff9d 100%)',
      }
    },
  },
  plugins: [],
}
