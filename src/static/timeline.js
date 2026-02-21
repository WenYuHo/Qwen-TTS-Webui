// timeline.js - Handles WaveSurfer visualization

const TimelineManager = {
    wavesurfer: null,
    wsRegions: null,

    init() {
        if (this.wavesurfer) return;

        this.wavesurfer = WaveSurfer.create({
            container: '#waveform',
            waveColor: '#4F4A85',
            progressColor: '#383351',
            url: '', // No global audio yet
            height: 100,
            plugins: [
                WaveSurfer.Timeline.create({
                    container: '#waveform-timeline'
                }),
                WaveSurfer.Regions.create()
            ]
        });

        this.wsRegions = this.wavesurfer.plugins[1]; // Index 1 is Regions based on init above

        // Handle region updates (dragging)
        this.wsRegions.on('region-updated', (region) => {
            const block = CanvasManager.blocks.find(b => b.id === region.id);
            if (block) {
                block.startTime = region.start;
                // Optional: Sync back to UI or save
                console.log(`Block ${block.id} moved to ${block.startTime}`);
            }
        });

        this.wavesurfer.on('click', () => {
            // Sync global player to timeline position?
        });
    },

    // Sync blocks to timeline regions
    renderTimeline() {
        if (!this.wavesurfer) this.init();

        this.wsRegions.clearRegions();

        let currentTime = 0;

        // Calculate implicit start times if they are 0 (freshly generated)?
        // Or trust the block.startTime?
        // For now, let's lay them out sequentially if they overlap or are all 0
        // But the goal is to be a DAW.

        CanvasManager.blocks.forEach(block => {
            if (block.status === 'ready' && block.audioUrl) {
                // If duration is 0, we need to get it from audio. 
                // But we can't easily get duration until loaded.
                // Assuming we might have duration from generation? 
                // Currently backend doesn't return duration explicitly, but we can guess or update it.

                // For visualization, we use a default length if unknown, or try to load.
                // WaveSurfer regions need explicit start/end.

                // Hack: If duration is unknown, default to 5s or estimate from text length?
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

                // Update currentTime for next block if we were doing linear
                if (block.startTime + dur > currentTime) {
                    currentTime = block.startTime + dur;
                }
            }
        });

        // Update the main waveform to be empty but long enough?
        // WaveSurfer needs a main audio file to show a timeline properly usually.
        // Or we can just use it as a container for regions.
        // If we don't load a "main track", the timeline might not show or be 0 length.

        // Workaround: Load a silent audio file of sufficient length.
        // Or use the "Generated Podcast" as the background if it exists.

        // Let's create a silent buffer for now if nothing exists.
        // this.wavesurfer.loadDecodedBuffer(...)
    },

    getColorForRole(role) {
        // Deterministic color hash
        let hash = 0;
        for (let i = 0; i < role.length; i++) {
            hash = role.charCodeAt(i) + ((hash << 5) - hash);
        }
        const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '#' + "00000".substring(0, 6 - c.length) + c + "80"; // 50% opacity
    }
};
