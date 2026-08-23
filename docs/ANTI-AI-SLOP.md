# Fabrient Anti-AI-Slop Design Standard

This is a permanent design-quality guardrail for Fabrient. It is not a ban on using AI. It prevents generic generated UI from becoming the visual identity.

## Core rule
Every visual decision must have a product reason. Do not add a section, card, icon, animation, gradient, badge, metric, or decorative object merely because it is a common SaaS pattern.

## Hard avoid list
- Purple/indigo/blue gradients as a default accent
- Gradient text
- Aurora/mesh blobs without a functional reason
- Glassmorphism and frosted panels as the default surface
- Excessive backdrop blur
- Inter/Roboto/system sans as an unexamined default
- Centered marketing hero + two equal CTAs
- Three identical feature cards solely to fill a row
- Repeated rounded-2xl cards
- Pill-shaped buttons everywhere
- Gradient pill CTAs
- Emoji used as interface icons
- Decorative Lucide/icon grids where typography or data would be clearer
- Generic "Supercharge", "revolutionize", "seamless", "unlock", "next-generation" hype copy
- Invented customer logos, testimonials, usage counts, metrics, or trust badges
- Decorative charts with no real data or decision attached
- Hover scale/bounce on nearly every interactive element
- Scroll-triggered fade-up for every section
- Excessive floating blobs, particles, neon glows, or shadows
- Left-border-card pattern as a repeated component identity
- Generic bento grids used only because they look modern
- Giant headline followed by a generic feature-card wall
- Identical layouts repeated across routes when the content needs a different composition
- Placeholder/demo data presented as real
- Buttons that do not perform a real action
- Empty states that are merely blank cards

## Fabrient visual direction
Use Fabrient's existing green/yellow palette as the brand foundation. Keep the interface technical, warm, confident, and editorial rather than futuristic or "AI startup" themed.

Prefer:
- Strong typographic hierarchy
- Asymmetric but intentional compositions
- Thin engineering-style rules and measurement cues
- Real product states and real data
- Dense information where engineers need density; spacious composition where explanation needs room
- Square or restrained corner radii rather than universal pills
- Shadows only when they establish physical layering
- Motion that explains state or physical relationships, not decoration
- Small labels, annotations, dimensions, revision markers, and evidence trails when they communicate something real
- Original visual motifs derived from engineering workflows rather than generic SaaS illustrations
- One dominant focal point per section
- One primary action per section
- Deliberate whitespace and rhythm

## Typography
Do not blindly use a default font. Choose typography by role. Display typography should have character; utility text may use a compact technical face. Avoid using one font at every size and weight merely for convenience.

## Layout
Do not force every route into the same hero/cards/grid template. Compose around the user's actual task. Product/workspace screens should prioritize information hierarchy and interaction; marketing screens should prioritize the story without turning every section into a card.

## Color
Existing Fabrient colors are intentional. Do not introduce a trendy purple/indigo accent to make a screen feel "modern." Use the existing green/yellow system with neutral surfaces and controlled contrast. Color should encode state, action, or hierarchy.

## Icons and graphics
No decorative icon soup. Use icons only when they improve recognition or interaction. Prefer original engineering diagrams, real product geometry, data visualizations, or typography when those communicate better.

## Motion
Motion must have a reason: state transition, continuity, spatial relationship, feedback, or orientation. Respect prefers-reduced-motion. No blanket fade-up, bounce, scale, or parallax on every section.

## Content
Never invent proof. If a metric, testimonial, customer, capability, or claim is not verified in the product, omit it or clearly label it as illustrative.

## Functional quality gate
Before shipping any UI change, inspect desktop and mobile layouts and verify loading, empty, success, error, disabled, focus, keyboard, and reduced-motion states where applicable. A beautiful screenshot is not sufficient.

## Review question
If the Fabrient logo were removed, could this interface still be mistaken for a generic AI-generated SaaS template? If yes, revise the composition until the product's engineering identity is obvious from the visual system itself.
