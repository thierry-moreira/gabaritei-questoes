# Skill: Guardião do Design - Gabaritei Questões
Description: Garante que todas as modificações e novos componentes do site sigam o design system, suportando perfeitamente os temas Dark e Light.

## Instructions

1.  **Strict Adherence to Visual Identity:** All modifications must follow the existing dual-theme color palette, typography, and spacing defined below. Never hardcode colors; always use CSS variables.
2.  **Color Palette (Dark Mode - Default/Fallback):**
    -   `--bg-main`: `#0E1117`
    -   `--bg-card`: `#1D232A`
    -   `--text-primary`: `#F0F3F5`
    -   `--text-secondary`: `#7C838F`
    -   `--border-main`: `#2F3640`
3.  **Color Palette (Light Mode):**
    -   `--bg-main`: `#F4F6F8` (Light gray background)
    -   `--bg-card`: `#FFFFFF` (Pure white cards)
    -   `--text-primary`: `#1E293B` (Dark slate for readability)
    -   `--text-secondary`: `#64748B`
    -   `--border-main`: `#E2E8F0`
4.  **Shared Accents (Both Modes):**
    -   `--accent-blue`: `#3b82f6` (Primary active, charts, "RESOLVER QUESTÕES")
    -   `--accent-purple`: `#8b5cf6` (Secondary actions like "Raio-X Completo")
    -   `--accent-green`: `#10b981` (Success, Offensive card)
5.  **Typography:** Utilize a clean Sans-serif font ('Inter' or similar). Body text should be `16px` for comfortable long reading sessions.
6.  **Component Design:**
    -   **Cards:** Standard `border-radius: 8px`. In Light Mode, use a subtle shadow (`box-shadow: 0 1px 3px rgba(0,0,0,0.1)`). In Dark Mode, shadows should be minimal or non-existent, relying on border colors.
    -   **Buttons:** `border-radius: 8px`. Maintain solid fills for primary actions and subtle outlines/ghost styles for secondary ones.
    -   **Question Alternatives:** In Light Mode, alternatives must have a white background and a light gray border (`--border-main`), turning to a subtle blue/green upon selection or hovering.

## Constraints

-   **Do Not:** Hardcode HEX or RGB values in component CSS (e.g., `background-color: #FFF;`). ALWAYS use the CSS variables (e.g., `background-color: var(--bg-card);`) so the theme switch works automatically.
-   **Do Not:** Alter the `border-radius: 8px` standard.
-   **Do Not:** Create elements that are illegible in either theme. Always ensure high contrast for text.