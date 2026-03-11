/**
 * I18n Engine for Qwen-TTS Studio
 */
export const I18n = {
    translations: {},
    currentLang: 'en',

    async load(lang = 'en') {
        try {
            const res = await fetch(`/static/translations/${lang}.json`);
            if (!res.ok) throw new Error(`No translation for ${lang}`);
            this.translations = await res.json();
            this.currentLang = lang;
            this.apply();
            this.updateSwitcherUI();
        } catch (err) {
            console.warn(`i18n: Failed to load ${lang}, falling back to en`);
            if (lang !== 'en') await this.load('en');
        }
    },

    /**
     * Translate a key (e.g. "sidebar.voice_studio")
     */
    t(key) {
        const parts = key.split('.');
        let value = this.translations;
        for (const part of parts) {
            value = value?.[part];
            if (value === undefined) return key; // Fallback to key
        }
        return value;
    },

    /**
     * Apply translations to all elements with [data-i18n]
     */
    apply() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translated = this.t(key);
            if (translated !== key) {
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    el.placeholder = translated;
                } else {
                    // Preserving icons if any
                    const icon = el.querySelector('i');
                    if (icon) {
                        el.childNodes.forEach(node => {
                            if (node.nodeType === Node.TEXT_NODE) {
                                node.textContent = ' ' + translated;
                            }
                        });
                    } else {
                        el.textContent = translated;
                    }
                }
            }
        });
    },

    async switchTo(lang) {
        await this.load(lang);
        localStorage.setItem('ui_language', lang);
    },

    updateSwitcherUI() {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            const lang = btn.getAttribute('data-lang');
            if (lang === this.currentLang) {
                btn.classList.add('active');
                btn.style.opacity = '1';
                btn.style.borderColor = 'var(--accent)';
            } else {
                btn.classList.remove('active');
                btn.style.opacity = '0.5';
                btn.style.borderColor = 'transparent';
            }
        });
    }
};

// Auto-init on script load
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('ui_language') || 'en';
    I18n.load(saved);
});

window.I18n = I18n;
