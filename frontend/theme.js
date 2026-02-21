// ============================================================================
// THEME MANAGER - Light/Dark Mode Toggle (Global)
// ============================================================================

class ThemeManager {
    constructor() {
        this.STORAGE_KEY = 'emailcraft-theme';
        this.LIGHT = 'light';
        this.DARK = 'dark';
        this.init();
    }

    init() {
        console.log('[Theme] Initializing theme manager...');
        
        // Apply theme immediately
        this.applyThemeImmediately();
        
        // Setup listeners when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                console.log('[Theme] DOM loaded, setting up listeners...');
                this.setupListeners();
            });
        } else {
            console.log('[Theme] DOM already loaded, setting up listeners...');
            this.setupListeners();
        }
    }

    applyThemeImmediately() {
        // Get saved theme or use system preference
        const savedTheme = localStorage.getItem(this.STORAGE_KEY);
        const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? this.DARK : this.LIGHT;
        const theme = savedTheme || systemPreference;
        
        console.log('[Theme] Applying theme:', theme, '(saved:', savedTheme, ', system:', systemPreference, ')');
        
        // Apply to html
        document.documentElement.setAttribute('data-theme', theme);
        console.log('[Theme] Set data-theme on html:', document.documentElement.getAttribute('data-theme'));
        
        // Apply to body when ready
        if (document.body) {
            document.body.setAttribute('data-theme', theme);
            console.log('[Theme] Set data-theme on body:', document.body.getAttribute('data-theme'));
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                document.body.setAttribute('data-theme', theme);
                console.log('[Theme] Set data-theme on body (after DOM):', document.body.getAttribute('data-theme'));
            });
        }
    }

    setTheme(theme) {
        // Validate theme
        if (theme !== this.LIGHT && theme !== this.DARK) {
            console.warn('[Theme] Invalid theme:', theme, '- using light');
            theme = this.LIGHT;
        }
        
        console.log('[Theme] Setting theme to:', theme);
        
        // Apply to both html and body
        document.documentElement.setAttribute('data-theme', theme);
        if (document.body) {
            document.body.setAttribute('data-theme', theme);
        }
        
        // Save to localStorage
        localStorage.setItem(this.STORAGE_KEY, theme);
        console.log('[Theme] Saved to localStorage:', localStorage.getItem(this.STORAGE_KEY));
        
        // Update button
        this.updateToggleButton();
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || this.LIGHT;
        console.log('[Theme] Current theme:', currentTheme);
        const newTheme = currentTheme === this.LIGHT ? this.DARK : this.LIGHT;
        console.log('[Theme] Toggling to:', newTheme);
        this.setTheme(newTheme);
    }

    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || this.LIGHT;
    }

    updateToggleButton() {
        const toggleBtns = document.querySelectorAll('[id="theme-toggle"]');
        const currentTheme = this.getCurrentTheme();
        
        console.log('[Theme] Updating', toggleBtns.length, 'toggle buttons to theme:', currentTheme);
        
        toggleBtns.forEach((btn, index) => {
            const icon = btn.querySelector('i');
            if (icon) {
                // Remove both classes
                icon.classList.remove('fa-moon', 'fa-sun');
                
                // Add correct class
                if (currentTheme === this.DARK) {
                    icon.classList.add('fa-sun');
                    btn.setAttribute('title', 'Switch to Light Mode');
                    console.log('[Theme] Button', index, '- showing sun icon');
                } else {
                    icon.classList.add('fa-moon');
                    btn.setAttribute('title', 'Switch to Dark Mode');
                    console.log('[Theme] Button', index, '- showing moon icon');
                }
            }
        });
    }

    setupListeners() {
        console.log('[Theme] Setting up event listeners...');
        
        // Setup click listeners for theme toggle buttons
        const toggleBtns = document.querySelectorAll('[id="theme-toggle"]');
        console.log('[Theme] Found', toggleBtns.length, 'toggle buttons');
        
        toggleBtns.forEach((btn, index) => {
            btn.addEventListener('click', () => {
                console.log('[Theme] Toggle button', index, 'clicked');
                this.toggleTheme();
            });
        });

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            console.log('[Theme] System theme changed to:', e.matches ? 'dark' : 'light');
            if (!localStorage.getItem(this.STORAGE_KEY)) {
                this.setTheme(e.matches ? this.DARK : this.LIGHT);
            }
        });
        
        console.log('[Theme] Event listeners setup complete');
    }
}

// Initialize theme manager globally
console.log('[Theme] Creating ThemeManager instance...');
if (!window.themeManager) {
    window.themeManager = new ThemeManager();
    console.log('[Theme] ThemeManager created successfully');
} else {
    console.log('[Theme] ThemeManager already exists');
}
