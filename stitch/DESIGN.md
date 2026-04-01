# Design System Document: Modern Romanticism & The Academic Soul

## 1. Overview & Creative North Star: "The Curated Encounter"
This design system rejects the frantic, "disposable" nature of modern dating apps. Our Creative North Star is **The Curated Encounter**. We are designing a digital environment that feels like a prestigious university library at golden hour—quiet, intentional, and intellectually intimate. 

To break the "template" look, we move away from rigid, full-width grids. Instead, we embrace **intentional asymmetry** and **editorial pacing**. Use large blocks of white space to isolate content, making every profile and message feel like a featured article in a high-end journal. Overlapping elements (e.g., an image slightly breaking the boundary of its container) should be used to create a sense of tactile depth, moving the experience from a "flat app" to a "digital keepsake."

---

## 2. Colors: Sunrise & Calm
Our palette balances the weight of academia with the warmth of a new beginning.

*   **Primary (Deep Indigo - `#15157d`):** Represents depth, intelligence, and the night sky. Use this for moments of high authority and primary actions.
*   **Secondary (Coral/Peach - `#a43c12`):** The "Sunrise." Used sparingly to draw the eye to "Matching" moments and warm interactions.
*   **Neutral (Creamy Off-White - `#fcf9f2`):** Our "Paper." The foundation of the entire experience.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to section content. Traditional dividers feel "computational" and "cheap." Boundaries must be defined solely through:
1.  **Background Shifts:** Placing a `surface_container_low` card on a `surface` background.
2.  **Tonal Transitions:** Using the subtle difference between `surface_bright` and `surface_dim`.

### Surface Hierarchy & Nesting
Treat the UI as physical layers of fine paper or frosted glass.
*   **Base:** `surface` (#fcf9f2)
*   **Level 1 (Sections):** `surface_container_low` (#f6f3ec)
*   **Level 2 (Cards/Interaction):** `surface_container_highest` (#e5e2db) or `surface_container_lowest` (#ffffff) for maximum "pop."

### Signature Textures & Glass
Main CTAs and Hero moments should utilize a subtle linear gradient transitioning from `primary` (#15157d) to `primary_container` (#2e3192). For floating navigation or modal overlays, apply **Glassmorphism**: use `surface_container_lowest` at 70% opacity with a `20px` backdrop-blur to allow the "Sunrise" colors to bleed through beautifully.

---

## 3. Typography: The Editorial Voice
We pair a sophisticated serif with a modern sans-serif to create a "New York Times Magazine" aesthetic.

*   **Display & Headlines (Noto Serif):** Our "Academic" soul. Use `display-lg` and `headline-lg` for profile names and major section headers. The high contrast of the serif characters conveys prestige.
*   **Body & Titles (Inter):** Our "Modern" clarity. Use `title-md` for interface labels and `body-lg` for bio text. Inter provides the legibility required for long-form campus stories.

**Hierarchy Note:** To achieve a high-end look, use extreme scale. A `display-lg` headline should often sit near a `label-sm` metadata tag. This contrast creates a professional, "designed" feel.

---

## 4. Elevation & Depth: Tonal Layering
We do not use drop shadows to create "floating" objects; we use light and tone.

*   **The Layering Principle:** Depth is achieved by "stacking." A user profile card should be `surface_container_lowest` (#ffffff) sitting on a `surface_container` (#f0eee7) background. This creates a natural "lift" without the "muddy" look of shadows.
*   **Ambient Shadows:** If a floating action button (FAB) or modal requires a shadow, it must be an "Ambient Glow." Use a blur of `32px`, an opacity of `6%`, and a color derived from `on_surface` (#1c1c18).
*   **The Ghost Border:** If a boundary is required for accessibility, use `outline_variant` (#c7c5d4) at **15% opacity**. It should be felt, not seen.

---

## 5. Components: Intentional Interaction

### Buttons (The "Seal")
*   **Primary:** `primary` background with `on_primary` text. **Radius: xl (3rem)**. This pill shape feels friendly yet sophisticated.
*   **Secondary:** `secondary_fixed` background with `on_secondary_fixed` text. Use for "Match" actions.
*   **Tertiary:** No background. Use `primary` text with an underline that only appears on hover.

### Cards (The "Dossier")
*   **Style:** `xl` rounded corners (3rem). 
*   **Padding:** Use `8` (2.75rem) internal padding to give the content "room to breathe."
*   **Constraint:** Absolutely no divider lines. Separate the "Bio" from "Interests" using a `12` (4rem) vertical spacing gap or a subtle background shift to `surface_container_high`.

### Input Fields (The "Inquiry")
*   **Style:** "Minimalist Underline" or "Soft Tray." Use `surface_container_highest` with a bottom-only `outline` token. 
*   **Focus State:** The label should transition from `body-md` to a `label-sm` in the `primary` color, accompanied by a subtle 2px bottom glow.

### The "Match" Indicator
Instead of a "swipe," the match component is a layered "Discovery Card." When a match is made, use a full-screen `surface_tint` overlay with a glassmorphism effect, blurring the background and bringing the two profiles together in the center.

---

## 6. Do’s and Don’ts

### Do:
*   **Use Asymmetry:** Place a profile photo on the left but keep the name and bio right-aligned to create a rhythmic, editorial layout.
*   **Embrace White Space:** If a screen feels "empty," it’s likely working. Avoid the urge to fill gaps with "widgets."
*   **Use Large Radii:** Ensure all containers use at least `lg` (2rem) or `xl` (3rem) corner rounding. Sharp corners are forbidden.

### Don’t:
*   **Don't use 100% Black:** Always use `on_background` (#1c1c18) for text to maintain the "Academic" softness.
*   **Don't "Swipe":** Avoid any interaction that feels like discarding a person. Use taps, fades, and gentle slides.
*   **No Grid-Lock:** Do not force every element to align to a 12-column grid. Let elements "float" in their white space to maintain a premium, bespoke feel.