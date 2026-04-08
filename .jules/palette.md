## 2025-02-22 - [Enhancing Interaction Feedback and Accessibility]
**Learning:** In a vanilla JS/CSS application, using `dataset` to store and restore `innerHTML` for loading states is a clean and reliable micro-UX pattern. Adding `aria-label` and `title` to icon-only buttons provides critical accessibility for screen readers and helpful tooltips for sighted users without cluttering the UI.
**Action:** Always check for icon-only buttons and add appropriate labels. Implement `try...finally` blocks for async UI operations to ensure the interface never gets stuck in a loading state.

## 2025-05-15 - [Semantic Labels and Empty States]
**Learning:** Converting generic `<span>` labels to semantic `<label>` elements with `for` attributes significantly improves accessibility for screen readers and form usability (clicking the label focuses the input). Implementing explicit "Empty States" with icons and helpful guidance transforms a "broken" or "empty" feeling into a welcoming onboarding experience.
**Action:** Audit all form inputs for proper `<label>` associations. Always provide a visual and textual empty state for dynamic lists or grids.

## 2025-06-12 - [Navigation Accessibility and SPA Focus Management]
**Learning:** In Single Page Applications (SPAs), updating the visual state of navigation (e.g., active classes) is insufficient for accessibility. Using `aria-pressed` (for buttons) or `aria-selected` (for tabs) communicates the current state to screen readers. Crucially, programmatically moving focus to the new view's heading (which must have `tabindex="-1"`) ensures that assistive technologies announce the transition and place the user at the start of the new content.
**Action:** Implement `aria-pressed` on navigation triggers and manage programmatic focus on view transitions to ensure a seamless and accessible SPA experience.

## 2025-06-25 - [Clean Event Binding and Robust Empty States]
**Learning:** When generating dynamic lists using `innerHTML`, separating the HTML structure from the event logic by using semantic selector classes (e.g., `.js-action`) for JavaScript-based binding is much cleaner and less error-prone than interpolating complex `onclick` strings. Additionally, empty states should be designed to match the parent container's layout; for grids, use `grid-column: 1 / -1` to ensure the empty state spans the full width and provides a centered, balanced appearance.
**Action:** Use semantic JS-only classes for event binding in dynamic templates. Always ensure empty states in grid layouts use column spanning for better visual balance.

## 2026-03-01 - [Multi-View Component Synchronization]
**Learning:** In a multi-view Single Page Application (SPA) where shared components (like a Task Monitor) appear across different views, using IDs for these components prevents reliable simultaneous updates. Converting these to class-based selectors (e.g., `.js-task-monitor-list`) and using `querySelectorAll` in the update logic ensures that state remains consistent across all views without requiring a view-switch to trigger a refresh.
**Action:** Use class-based selectors for shared UI components that exist in multiple DOM branches. Implement global update functions that target all instances of these classes.

## 2026-03-06 - [Deep Tab Focus and Notification Accessibility]
**Learning:** In a layered SPA, focus management must extend to sub-tabs (Inventory, Phonemes, etc.) to prevent keyboard "traps" or orientation loss. Combining `aria-pressed` on the trigger with programmatic focus on the new section's heading (with `tabindex="-1"`) provides the clearest signal to screen readers. For asynchronous feedback, an `aria-live="polite"` container ensures non-disruptive but guaranteed announcement of background task states.
**Action:** Always implement sub-tab focus management and use `aria-live` for dynamic status updates.

## 2026-03-20 - [Semantic Empty States for System Management]
**Learning:** Extending the existing `.empty-state` CSS pattern to administrative views like the System Manager (Audit Log, Phoneme Editor) significantly improves visual consistency and provides clear guidance to the user. Using FontAwesome icons that match the semantic context (e.g., `fa-clipboard-list` for logs, `fa-language` for phonemes) helps with quick visual recognition and reinforces the "Technoid Brutalist" style.
**Action:** Always check for unhandled empty states in data-heavy administrative views and implement icon-based guidance using existing UI patterns.

## 2026-03-22 - [Centralized Media Monitoring and XSS Protection]
**Learning:** Unifying media playback by routing all source URLs to a single, global player element (e.g., `#preview-player`) improves the user experience by providing a consistent set of controls and a centralized "Global Monitor" for all app audio. Furthermore, when generating UI lists from user-provided or external data, importing and applying a centralized `escapeHTML` utility is essential to prevent XSS and ensure visual integrity for names containing special characters.
**Action:** Always route media playback to the designated global player instead of creating detached `Audio` objects. Ensure `escapeHTML` is applied to all dynamic data rendered via `innerHTML`.
