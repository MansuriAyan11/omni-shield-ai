---
kind: frontend_style
name: Tailwind CSS + Vite/Next.js Dual Frontend Styling System
category: frontend_style
scope:
    - '**'
source_files:
    - nudenet_project/frontend/tailwind.config.js
    - nudenet_project/frontend/src/index.css
    - nudenet_project/frontend/package.json
    - nudenet_project/frontend/src/components/Layout.tsx
    - nudenet_project/frontend/src/pages/Dashboard.tsx
    - nudenet_project/frontend-nextjs-backup/src/app/globals.css
    - nudenet_project/frontend-nextjs-backup/src/components/ThemeToggle.tsx
---

The repository contains two separate frontend styling systems for the OmniShield platform: a primary Vite+React SPA and a Next.js backup implementation, both using Tailwind CSS as the core styling framework.

**Primary Frontend (Vite + React)**
The active frontend (`frontend/`) uses Tailwind CSS v3 with a custom dark theme. The design system is defined in `tailwind.config.js` through extended color palettes — custom `black`, `white`, and `gray` scales replacing default Tailwind tokens. Global styles in `src/index.css` establish a cybersecurity-themed dark UI with base layer resets, custom animations (`fadeIn`, `scanLine`, `progressBar`), and utility classes via `@layer`. Components are styled exclusively with Tailwind utility classes applied directly in JSX (e.g., `bg-black text-white rounded-lg p-6 border border-gray-700`). Icons come from `lucide-react` rather than a component library. State-driven styling uses conditional class concatenation patterns like `${card.bgColor} ${card.textColor}`.

**Next.js Backup Frontend**
The `frontend-nextjs-backup/` directory implements a more polished variant using Tailwind CSS v4 (`@import "tailwindcss"`) with CSS custom properties for theming (`--background`, `--primary`, `--accent`, etc.). It introduces glassmorphism effects (`.glass-panel`, `.glass-panel-glow`), custom scrollbars, and a `ThemeToggle` component that persists user preference to localStorage and toggles a `dark` class on `document.documentElement`. This version demonstrates a more advanced pattern with CSS variables driving the theme system.

**Styling Conventions**
- No CSS-in-JS or SCSS — pure Tailwind utilities plus minimal global CSS
- Dark-first design with high-contrast black/white palette
- Responsive layouts use Tailwind's responsive prefixes (`md:grid-cols-2 lg:grid-cols-4`)
- Animation keyframes defined globally in CSS files, reused via utility classes
- Iconography standardized on `lucide-react` across both frontends
- Conditional styling via template literals and className composition rather than state-driven style objects