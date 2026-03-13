const I18n = {
    translations: {},
    currentLang: 'en',

    async load(lang = 'en') {
        try {
            const res = await fetch(`/static/translations/${lang}.json`);
            if (!res.ok) throw new Error(`No translation for ${lang}`);
            this.translations = await res.json();
            this.currentLang = lang;
            this.apply();
        } catch (err) {
            console.warn(`i18n: Failed to load ${lang}, falling back to en`);
            if (lang !== 'en') await this.load('en');
        }
    },

    t(key) {
        const parts = key.split('.');
        let value = this.translations;
        for (const part of parts) {
            value = value?.[part];
            if (value === undefined) return key;  // Fallback to key
        }
        return value;
    },

    apply() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translated = this.t(key);
            if (translated !== key) {
                if (el.tagName === 'INPUT') {
                    el.placeholder = translated;
                } else {
                    el.textContent = translated;
                }
            }
        });
        
        // Update switcher buttons
        document.querySelectorAll('.lang-btn').forEach(btn => {
            const lang = btn.dataset.lang;
            btn.style.opacity = lang === this.currentLang ? '1' : '0.5';
            btn.style.borderColor = lang === this.currentLang ? 'var(--accent)' : 'transparent';
        });
    },

    async switchTo(lang) {
        await this.load(lang);
        localStorage.setItem('ui_language', lang);
    }
};

// Auto-load saved language on startup:
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('ui_language') || 'en';
    I18n.load(saved);
});

window.I18n = I18n;
export { I18n };