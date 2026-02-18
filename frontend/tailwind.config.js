/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                end: {
                    bg: '#111111',
                    card: '#1a1a1a',
                    accent: '#f59e0b', // Amber-500
                    'accent-hover': '#d97706', // Amber-600
                    text: '#ffffff',
                    'text-sec': '#a3a3a3',
                    border: '#333333',
                    success: '#10b981', // Emerald-500
                    error: '#ef4444',   // Red-500
                    warning: '#f59e0b', // Amber-500
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
