<!-- SEED: re-run /impeccable document once there's code to capture the actual tokens and components. -->
---
name: Farmer Advisor
description: Multilingual sovereign AI agronomic advisory with verified ICAR groundedness
---

# Design System: Farmer Advisor

## 1. Overview

**Creative North Star: "The Living Field Guide"**

The Farmer Advisor design system embodies the serene, authoritative, and grounded clarity of an expert botanist's field guide fused with the intuitive conversational ease of modern search. Built for desktop terminals and rural kiosk displays in high ambient daylight, the interface strips away all machine telemetry, dark-mode terminal tropes, and bureaucratic government bloat. It presents an immediate, calm, and uncluttered environment where farmers and CSC operators can ask questions naturally in their native language—via voice or text—and receive straightforward, actionable crop intelligence within seconds.

The visual atmosphere balances fertile organic greens with clean, daylight-readable surfaces. Rather than overwhelming users with dense data tables or exposing raw LLM outputs, complex agronomic schedules (NPK fertilization windows, critical irrigation milestones, pest advisories) are presented as structured, legible advisories. Verification is always one gesture away through a dedicated groundedness drawer showcasing ICAR citations and scientific references without obstructing the primary conversation.

**Key Characteristics:**
- **Organic Earthiness**: Grounded foliage and deep moss greens anchored by clean daylight surfaces and warm loam accents.
- **Immediate First-Action Clarity**: The query interface and voice input mic are prominent focal points with zero distraction.
- **Multilingual Dignity**: Balanced typographic rendering designed specifically for complex Brahmic scripts (Hindi, Tamil, Telugu, Kannada, Punjabi, Marathi) alongside English.
- **Subtle Layered Verification**: High-trust ICAR source verification tucked neatly into an expandable groundedness drawer.

## 2. Colors

**The Committed Earthy Green Rule.** Saturated botanical greens and foliage tones carry 35%–45% of key surfaces (header branding, active conversational cards, and primary action controls), anchored by crisp daylight neutrals (≥4.5:1 contrast against ink text) and earthy loam/clay accents for stage indicators.

- **Primary**: Deep Forest Foliage & Moss Green `[hex / oklch tokens to be resolved during implementation]`
- **Secondary**: Fertile Loam & Warm Clay `[to be resolved during implementation]`
- **Tertiary / Utility**: Clear Sky Blue (irrigation & moisture indicators) `[to be resolved during implementation]`
- **Neutrals**: Daylight Off-White background, crisp clean card surfaces, and deep charcoal-soil ink `[to be resolved during implementation]`

## 3. Typography

**Display & Body Pairing:** Single Humanist Sans Family (Noto Sans / Inter stack) `[font tokens and font-face configurations to be resolved during implementation]`

**Character:** Warm, friendly, highly legible, and neutral. Provides exceptional readability at desktop distances under varied ambient lighting, with native rendering support for complex conjuncts in Indic scripts.

### Hierarchy
- **Display / Title**: Medium to Semi-bold, calm letter-spacing, balanced line height for advisory headings.
- **Body Text**: Regular weight, generous 1.5–1.6 line-height, capped at 65–75 characters per line for rapid comprehension.
- **Label / Metadata**: Crisp medium weight, high-contrast, for ICAR source tags, crop categories, and language pills.

**The Script Equality Rule.** English and regional Indic scripts must share identical typographic weight, vertical rhythm, and line-height balance so that translations never disrupt visual geometry.

## 4. Elevation

**The Flat-By-Default Rule.** The interface remains clean and flat at rest, relying on subtle borders and tonal contrast rather than heavy drop shadows. Elevation is reserved strictly as a responsive state: a soft ambient lift on active cards, gentle waveform pulses on voice input, and a smooth tactile slide for the groundedness verification drawer.

## 5. Do's and Don'ts

### Do:
- **Do** maintain a prominent, intuitive voice input microphone with clear visual feedback (active recording waveform / listening state).
- **Do** display ICAR and Ministry of Agriculture citation badges clearly to establish instant institutional trust.
- **Do** ensure all body and advisory text passes WCAG AA contrast (≥4.5:1) against background surfaces.
- **Do** keep groundedness verification accessible via an expandable drawer or pill without cluttering the direct farmer answer.

### Don't:
- **Don't** use SaaS AI clichés: no dark neon hacker modes, purple/magenta gradients, or glowing particle backgrounds.
- **Don't** mimic labyrinthine government portals: no crowded multi-level banner menus, PDF dumps, or nested scrolling tables.
- **Don't** create a generic ChatGPT clone: no low-contrast light-gray text on white backgrounds or bare empty text boxes without prompt guidance.
- **Don't** use decorative side-stripe borders (`border-left > 1px`) on advisory cards or alerts.
