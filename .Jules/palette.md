## 2025-02-22 - [Enhancing Interaction Feedback and Accessibility]
**Learning:** In a vanilla JS/CSS application, using `dataset` to store and restore `innerHTML` for loading states is a clean and reliable micro-UX pattern. Adding `aria-label` and `title` to icon-only buttons provides critical accessibility for screen readers and helpful tooltips for sighted users without cluttering the UI.
**Action:** Always check for icon-only buttons and add appropriate labels. Implement `try...finally` blocks for async UI operations to ensure the interface never gets stuck in a loading state.

## 2025-05-15 - [Semantic Labels and Empty States]
**Learning:** Converting generic `<span>` labels to semantic `<label>` elements with `for` attributes significantly improves accessibility for screen readers and form usability (clicking the label focuses the input). Implementing explicit "Empty States" with icons and helpful guidance transforms a "broken" or "empty" feeling into a welcoming onboarding experience.
**Action:** Audit all form inputs for proper `<label>` associations. Always provide a visual and textual empty state for dynamic lists or grids.

## 2025-06-12 - [Navigation Accessibility and SPA Focus Management]
**Learning:** In Single Page Applications (SPAs), updating the visual state of navigation (e.g., active classes) is insufficient for accessibility. Using `aria-pressed` (for buttons) or `aria-selected` (for tabs) communicates the current state to screen readers. Crucially, programmatically moving focus to the new view's heading (which must have `tabindex="-1"`) ensures that assistive technologies announce the transition and place the user at the start of the new content.
**Action:** Implement `aria-pressed` on navigation triggers and manage programmatic focus on view transitions to ensure a seamless and accessible SPA experience.
