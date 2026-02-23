import { CanvasManager } from './store.js';

export const TimelineManager = {
    wavesurfer: null,
    wsRegions: null,

    init() {
        if (this.wavesurfer) return;

        this.wavesurfer = WaveSurfer.create({
            container: '#waveform',
            waveColor: '#4F4A85',
            progressColor: '#383351',
            url: '',
            height: 100,
            plugins: [
                WaveSurfer.Timeline.create({
                    container: '#waveform-timeline'
                }),
                WaveSurfer.Regions.create()
            ]
        });

        this.wsRegions = this.wavesurfer.plugins[1];

        this.wsRegions.on('region-updated', (region) => {
            const block = CanvasManager.blocks.find(b => b.id === region.id);
            if (block) {
                block.startTime = region.start;
            }
        });
    },

    renderTimeline() {
        if (!this.wavesurfer) this.init();
        this.wsRegions.clearRegions();

        let currentTime = 0;
        CanvasManager.blocks.forEach(block => {
            if (block.status === 'ready' && block.audioUrl) {
                let dur = block.duration || 5;
                this.wsRegions.addRegion({
                    id: block.id,
                    start: block.startTime,
                    end: block.startTime + dur,
                    color: this.getColorForRole(block.role),
                    content: block.role + ": " + block.text.substring(0, 10) + "...",
                    drag: true,
                    resize: false
                });
                if (block.startTime + dur > currentTime) {
                    currentTime = block.startTime + dur;
                }
            }
        });
    },

    getColorForRole(role) {
        let hash = 0;
        for (let i = 0; i < role.length; i++) {
            hash = role.charCodeAt(i) + ((hash << 5) - hash);
        }
        const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '#' + "00000".substring(0, 6 - c.length) + c + "80";
    }
};
