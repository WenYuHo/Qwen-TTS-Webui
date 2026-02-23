export const TaskPoller = {
    async poll(taskId, onProgress, interval = 1000) {
        return new Promise((resolve, reject) => {
            const timer = setInterval(async () => {
                try {
                    const res = await fetch(`/api/tasks/${taskId}`);
                    if (!res.ok) throw new Error("Status check failed");

                    const task = await res.json();
                    if (onProgress) onProgress(task);

                    if (task.status === 'completed') {
                        clearInterval(timer);
                        const resultRes = await fetch(`/api/tasks/${taskId}/result`);
                        if (!resultRes.ok) throw new Error("Failed to download result");
                        const blob = await resultRes.blob();
                        resolve(blob);
                    } else if (task.status === 'failed') {
                        clearInterval(timer);
                        reject(new Error(task.error || "Task failed"));
                    }
                } catch (e) {
                    clearInterval(timer);
                    reject(e);
                }
            }, interval);
        });
    }
};

export async function getVoicePreview(profile) {
    try {
        const res = await fetch('/api/voice/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profile)
        });
        if (!res.ok) throw new Error("Preview failed");
        return await res.blob();
    } catch (e) {
        console.error("Preview error:", e);
        return null;
    }
}
