# Web Design Research — Stack Landing Page

> Deep-research synthesis from 107 sub-agents, 25 sources, 13 verified claims (12 refuted). Late 2025 / early 2026. Bias: actionable, named tools.

## TL;DR — The 4 MCPs To Install

| MCP | What it does | AgentRank score |
|-----|--------------|----------------|
| **Figma MCP** (GLips/Figma-Context-MCP, or official Figma Dev Mode) | Reads design context (layers, auto-layout, variables, components) AND writes back to canvas. The design-to-code source of truth. | 89.86 (#1) |
| **Magic UI MCP** (`@magicuidesign/mcp`) | 150+ animated React/Tailwind/Motion components — animated-beam, border-beam, shine-border, meteors, particles, orbiting-circles. Drop-in marketing sections. | 85.07 |
| **shadcn-ui MCP** (`Jpisnice/shadcn-ui-mcp-server`) | Exposes exact TypeScript interfaces + live component source. Kills hallucinated props (e.g. `onClose` on Dialog when correct is `onOpenChange`). | 83.64 |
| **BrowserMCP** (Chrome extension) | Controls YOUR logged-in Chrome profile — load levels.health + localhost side-by-side. Distinct from Playwright (headless/CI). | — |

## Component Library Stack (verified)

1. **shadcn/ui** = the foundation. MIT, Radix + Tailwind, the substrate every other library assumes. ⚠️ But default shadcn = "visual sameness" — third-party 2026 audit found only 34/48 components pass WCAG 2.2 AA out-of-box, and the "shadcn look" is recognizable. **Must customize tokens, fonts, spacing aggressively.**
2. **Magic UI** layered on top — animated marketing sections (open-source, 21.2k ⭐)
3. **Aceternity UI** sparingly — react+ts+tailwind+framer-motion. ⚠️ Raw overuse = recognizable 3D-card/beam cliche. Use 1-2 components per page, restyle to brand.
4. **Tailark** ($249–$399 lifetime, 300+ blocks, 4 design themes) — when "cohesive bespoke marketing look" matters more than breadth. Built deliberately so your site **won't** look like every other shadcn build.

## Verified REFUTATIONS (do NOT repeat these from blogs)

- ❌ "Aceternity is used by Vercel, Linear, and YC startups" — refuted 0-3
- ❌ "Shadcnblocks is the #1 shadcn block library" — refuted 1-2
- ❌ "Magic UI popularized the bento grid trend" — refuted 0-3
- ❌ "Chrome DevTools MCP is broadly available" — refuted 0-3

## The Honest Caveat (matters for Stack)

**Every premium-tier finding above assumes React + Tailwind + Next.js.** Stack's site is currently plain HTML/CSS/vanilla JS. The MCPs and libraries don't directly apply — to use them, the project needs to migrate.

That's a real decision: stay on the lean static stack (fast, simple, deploys anywhere) OR migrate to Next.js + Tailwind + shadcn (unlock the entire premium tooling ecosystem).

## Workflow for Premium Output (when migrated)

1. **Reference-load first.** Open 3-5 sites in BrowserMCP from Mobbin / Land-book / Lapa Ninja in the same category (wellness / dashboard / SaaS).
2. **Design context** — if a Figma exists, pull tokens via Figma MCP (`get_variable_defs`).
3. **Generate sections** via Magic UI MCP / shadcn MCP (real props, real source — no hallucination).
4. **Iterate visually** via BrowserMCP — side-by-side with reference.
5. **Verify in Playwright MCP** for desktop/mobile screenshots.

## Open Questions the Research Could NOT Verify

- Specific typography/color/grid systems used by Linear, Levels, Family, Apple (needs primary-source CSS inspection)
- Concrete anti-patterns that mark "AI-generated" (only weak blog evidence)
- Whether v0.dev → Cursor pipeline beats direct MCP generation (no measured comparison)
- Official Figma Dev Mode MCP vs GLips/Figma-Context-MCP for landing-page work

## Useful Sources (read these)

- **mantlr.com/blog/stripe-linear-vercel-premium-ui** — premium design principles
- **landdding.com** — bento grid by website category (where the pattern wins)
- **dev.to/alanwest** — "Why every AI-built website looks the same: blame Tailwind's indigo-500"
- **mindstudio.ai/blog/claude-design-avoid-ai-slop** — Claude-specific guidance
- **lapa.ninja/post/mobbin/** — using Mobbin as reference source

## Caveat on Methodology

~70% of verified claims rest on AgentRank's design-MCP ranking (popularity composite — stars + freshness + issue health — NOT output-fidelity benchmark) and mid-tier dev blogs. Strongest claims (MCP capabilities, shadcn license/stack, Magic UI registry, BrowserMCP architecture) are corroborated by primary docs / GitHub repos. Weaker claims (subjective design quality of Tailark, Aceternity premium-feel) rest on blog consensus only.

CVE-2025-53967 RCE in Figma-Context-MCP was patched in v0.6.3 (Sept 2025) — keep current.
