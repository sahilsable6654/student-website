// Theme handling
const themeToggle = {
    init() {
        // Check for saved theme preference or default to 'system'
        const savedTheme = localStorage.getItem('theme') || 'system';
        this.setTheme(savedTheme);
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
            if (localStorage.getItem('theme') === 'system') {
                this.applySystemTheme();
            }
        });
    },

    setTheme(theme) {
        localStorage.setItem('theme', theme);
        
        if (theme === 'system') {
            this.applySystemTheme();
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
        
        // Update active state of buttons
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.theme === theme) {
                btn.classList.add('active');
            }
        });
    },

    applySystemTheme() {
        const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    }
};

// Initialize theme system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => themeToggle.init()); 