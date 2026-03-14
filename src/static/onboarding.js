/**
 * OnboardingManager - Guided Tour for Qwen-TTS Studio
 */

export const OnboardingManager = {
    steps: [
        // Voice Studio Tour
        {
            view: 'speech',
            target: '.sidebar-nav',
            title: 'Welcome to the Studio!',
            content: 'Use the sidebar to navigate between Voice Design, Project Studio, and other specialized tools.',
            position: 'right'
        },
        {
            view: 'speech',
            target: '#speech-view .card-brutalist:nth-child(3)', // Voice Design is usually 3rd child in the grid-3 after header
            title: 'Voice Design',
            content: 'Describe a voice in natural language (e.g., "A deep, soothing male voice") to generate a new AI persona.',
            position: 'right'
        },
        {
            view: 'speech',
            target: '#speech-view .card-brutalist:nth-child(4)',
            title: 'Voice Cloning',
            content: 'Upload or record a 5-10 second sample to clone any speaker with high fidelity.',
            position: 'left'
        },
        {
            view: 'speech',
            target: '#speech-view .card-brutalist:nth-child(5)',
            title: 'Voice Mixer',
            content: 'Blend two voices together to create the perfect hybrid for your project.',
            position: 'left'
        },
        
        // Project Studio Tour
        {
            view: 'projects',
            target: '#nav-projects',
            title: 'Multi-Character Projects',
            content: 'Switch to Project Studio to build complex audio dramas with multiple speakers and scenes.',
            position: 'right',
            action: () => window.switchView('projects')
        },
        {
            view: 'projects',
            target: '#script-editor',
            title: 'Script Editor',
            content: 'Write your script using "Speaker: Text" lines. Use the SAMPLES menu for inspiration!',
            position: 'right'
        },
        {
            view: 'projects',
            target: '#btn-promote',
            title: 'Granular Control',
            content: 'Click PROMOTE to turn your script into manageable audio blocks where you can adjust individual parameters.',
            position: 'bottom'
        },
        {
            view: 'projects',
            target: '.sidebar-controls',
            title: 'Production Settings',
            content: 'Configure BGM, Reverb, and EQ. You can also enable AI Video generation here!',
            position: 'left'
        },
        {
            view: 'projects',
            target: '#btn-produce',
            title: 'Final Production',
            content: 'Ready? Click PRODUCE FINAL to generate your complete audio or video masterpiece.',
            position: 'top'
        }
    ],

    currentStepIndex: -1,
    overlay: null,
    popover: null,
    highlight: null,

    init() {
        this.injectStyles();
    },

    start() {
        if (this.currentStepIndex !== -1) return;
        this.currentStepIndex = 0;
        this.createUI();
        this.showStep();
    },

    createUI() {
        if (this.overlay) return;

        this.overlay = document.createElement('div');
        this.overlay.className = 'onboarding-overlay';
        
        this.highlight = document.createElement('div');
        this.highlight.className = 'onboarding-highlight';
        
        this.popover = document.createElement('div');
        this.popover.className = 'card-brutalist onboarding-popover';
        
        document.body.appendChild(this.overlay);
        document.body.appendChild(this.highlight);
        document.body.appendChild(this.popover);

        this.overlay.onclick = () => this.stop();
    },

    showStep() {
        const step = this.steps[this.currentStepIndex];
        if (!step) return this.stop();

        // Perform view switch if required
        if (step.action) step.action();
        
        // Wait for DOM to update if we switched views
        setTimeout(() => {
            const el = document.querySelector(step.target);
            if (!el) {
                console.warn(`Onboarding target not found: ${step.target}`);
                this.next();
                return;
            }

            this.updateHighlight(el);
            this.updatePopover(step, el);
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
    },

    updateHighlight(el) {
        const rect = el.getBoundingClientRect();
        const padding = 8;
        
        this.highlight.style.top = `${rect.top - padding + window.scrollY}px`;
        this.highlight.style.left = `${rect.left - padding + window.scrollX}px`;
        this.highlight.style.width = `${rect.width + padding * 2}px`;
        this.highlight.style.height = `${rect.height + padding * 2}px`;
    },

    updatePopover(step, targetEl) {
        const rect = targetEl.getBoundingClientRect();
        const padding = 20;
        
        this.popover.innerHTML = `
            <div style="margin-bottom:12px;">
                <span class="label-industrial" style="font-size:0.6rem; color:var(--accent);">STEP ${this.currentStepIndex + 1} OF ${this.steps.length}</span>
                <h3 style="margin:4px 0 0 0; font-size:1.1rem; border-bottom:1px solid var(--accent); padding-bottom:8px;">${step.title.toUpperCase()}</h3>
            </div>
            <p style="font-size:0.85rem; line-height:1.5; margin-bottom:20px; font-family:var(--font-mono);">${step.content}</p>
            <div style="display:flex; justify-content:space-between; gap:12px;">
                <button class="btn btn-secondary btn-sm" id="ob-skip">SKIP</button>
                <div style="display:flex; gap:8px;">
                    ${this.currentStepIndex > 0 ? '<button class="btn btn-secondary btn-sm" id="ob-back">BACK</button>' : ''}
                    <button class="btn btn-primary btn-sm" id="ob-next">${this.currentStepIndex === this.steps.length - 1 ? 'FINISH' : 'NEXT'}</button>
                </div>
            </div>
        `;

        document.getElementById('ob-skip').onclick = () => this.stop();
        if (this.currentStepIndex > 0) {
            document.getElementById('ob-back').onclick = () => this.back();
        }
        document.getElementById('ob-next').onclick = () => this.next();

        // Position popover
        const popRect = this.popover.getBoundingClientRect();
        let top, left;

        if (step.position === 'right') {
            top = rect.top + window.scrollY;
            left = rect.right + padding + window.scrollX;
        } else if (step.position === 'left') {
            top = rect.top + window.scrollY;
            left = rect.left - popRect.width - padding + window.scrollX;
        } else if (step.position === 'top') {
            top = rect.top - popRect.height - padding + window.scrollY;
            left = rect.left + window.scrollX;
        } else { // bottom
            top = rect.bottom + padding + window.scrollY;
            left = rect.left + window.scrollX;
        }

        // Boundary check
        if (left < 10) left = 10;
        if (left + popRect.width > window.innerWidth - 10) left = window.innerWidth - popRect.width - 10;
        if (top < 10) top = 10;
        if (top + popRect.height > window.innerHeight - 10) top = window.innerHeight - popRect.height - 10;

        this.popover.style.top = `${top}px`;
        this.popover.style.left = `${left}px`;
    },

    next() {
        this.currentStepIndex++;
        if (this.currentStepIndex >= this.steps.length) {
            this.stop();
        } else {
            this.showStep();
        }
    },

    back() {
        this.currentStepIndex--;
        if (this.currentStepIndex < 0) this.currentStepIndex = 0;
        this.showStep();
    },

    stop() {
        this.currentStepIndex = -1;
        if (this.overlay) this.overlay.remove();
        if (this.highlight) this.highlight.remove();
        if (this.popover) this.popover.remove();
        this.overlay = null;
        this.highlight = null;
        this.popover = null;
        localStorage.setItem('studio_onboarding_complete', 'true');
    },

    injectStyles() {
        if (document.getElementById('onboarding-styles')) return;
        const style = document.createElement('style');
        style.id = 'onboarding-styles';
        style.textContent = `
            .onboarding-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.4);
                z-index: 9998;
                cursor: pointer;
            }
            .onboarding-highlight {
                position: absolute;
                z-index: 9999;
                box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.7);
                border: 2px solid var(--accent);
                pointer-events: none;
                transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
            }
            .onboarding-popover {
                position: absolute;
                z-index: 10000;
                width: 320px;
                background: var(--bg-dark);
                padding: 24px;
                border: 2px solid var(--accent);
                transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
                box-shadow: 8px 8px 0px #000;
            }
        `;
        document.head.appendChild(style);
    }
};
