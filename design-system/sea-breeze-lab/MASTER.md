# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Sea Breeze Lab
**Audience:** 小五學生、堂上投影展示
**Generated / Adapted:** 2026-10-01
**Category:** Educational interactive (classroom)

---

## Global Rules

### Style
**Claymorphism** — soft 3D, chunky, playful, thick borders (3–4px), double shadows, rounded 20–24px.

### Color Palette (ocean education — indigo avoided for classroom clarity)

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#0284C7` | `--primary` |
| Primary deep | `#0369A1` | `--primary-deep` |
| Secondary / teal | `#14B8A6` | `--secondary` |
| Sun / accent | `#F59E0B` | `--sun` |
| CTA / success | `#16A34A` | `--cta` |
| Background sky | `#E0F2FE` | `--bg-sky` |
| Text | `#0C4A6E` | `--ink` |
| Night | `#1E3A5F` | `--night` |

### Typography
- **Display:** Baloo 2 (fallback Nunito / Noto Sans TC)
- **Body:** Nunito (fallback Noto Sans TC)
- Classroom: larger type for projection distance

### Motion
- Soft press ~180–200ms, cubic-bezier bounce on buttons
- Respect `prefers-reduced-motion`
- No decorative infinite bounce on UI chrome

### Touch / Classroom
- Min touch target 44–48px (nav / quiz 48–52px)
- Gap ≥ 8px between controls
- High contrast light mode only (no dark UI chrome)

### Anti-patterns
- No emoji-as-icons for chrome
- No indigo/purple default education theme
- No tiny projector-unfriendly text
- No hover-only critical actions

### Pre-Delivery Checklist
- [x] Clay borders + soft outer/inner shadows
- [x] cursor-pointer on controls
- [x] Focus-visible rings
- [x] prefers-reduced-motion
- [x] Responsive 375 / 768 / 1024+
- [x] Self-contained HTML (fonts optional CDN with fallbacks)
