# Specification: Modern UI and Real-Time Feedback

## Overview
This track transforms the Qwen-TTS Podcast Studio into a modern, responsive application with real-time feedback and robust monitoring. It addresses issues of UI non-responsiveness by shifting heavy model tasks to an asynchronous model.

## Problem Statement
The current UI is synchronous and appears "outdated." Users are unsure if the model is actually running because there are no real-time progress indicators, and the interface becomes unresponsive during inference.

## Objectives
- **Asynchronous Execution:** Offload model synthesis to background tasks to keep the main event loop free.
- **Real-Time Status:** Implement a notification system (WebSockets or Polling) to provide immediate feedback on model loading, progress, and execution.
- **Modern Design:** Redesign the UI using modern principles (e.g., Tailwind-like utility classes, enhanced Glassmorphism, better typography).
- **Performance Monitoring:** Integrate frontend and backend metrics to track responsiveness and inference speed.
- **User Experience:** Validate the new flow with UX testing.

## Proposed Changes
### Backend
- **Task Management:** Introduce a task manager to handle asynchronous synthesis requests.
- **WebSocket / Event Endpoints:** Add endpoints for real-time progress broadcasting.
- **Metrics API:** Expose inference time and resource utilization (CPU/MEM) metrics.

### Frontend
- **Real-Time Dashboard:** A new status panel showing active tasks and system health.
- **Modern CSS Refresh:** Overhaul `style.css` with a more polished "Classic Studio" look (better shadows, borders, and animations).
- **Responsiveness Diagnostics:** Add an overlay or indicator that shows the app's internal "heartbeat" or latency.

### Testing
- **UX Scenarios:** Define and execute a set of manual tests to verify the improved user journey.

## Success Criteria
- The UI remains completely responsive (no freezing) during 1.7B model synthesis.
- A progress bar or status text updates in real-time during generation.
- The UI follows modern design standards (verified by visual inspection).
- Latency and synthesis time are recorded and visible in logs or diagnostics.
