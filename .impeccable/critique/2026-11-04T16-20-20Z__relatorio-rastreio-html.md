---
target: relatorio_rastreio.html
total_score: 28
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 0
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:c1dc0a960ced7043f55d519716e3a08c6b3a55eab51b1436e5c54090d27b86a7"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-04T16-20-20Z
slug: relatorio-rastreio-html
---
# Critique: relatorio_rastreio.html (décima rodada)

Method: single-context (sub-agents not spawned: not requested explicitly). Detector run on relatorio_rastreio.html, pedidos_atrasados.html, opcoes_frete.html and web/ (11 findings), plus in-page overlay (2 findings).

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|---|---|---|
| 1 | Visibility of System Status | 3 | Data age, next consult and toasts are visible; no per-order error state seen |
| 2 | Match System / Real World | 3 | Operator vocabulary (pedido, rastreio, Precisam de ação) fits |
| 3 | User Control and Freedom | 3 | Limpar filtros, Esc and clear pills; clear button appears only when filtering |
| 4 | Consistency and Standards | 3 | Pills, action chips and summary cards each mean different things, but the rules are documented |
| 5 | Error Prevention | 3 | Cooldown on the Tiny/Correios update; no confirmation |
| 6 | Recognition Rather Than Recall | 3 | Labelled controls; the status legend is one click away |
| 7 | Flexibility and Efficiency | 3 | "/", Esc, sort, three views and a sortable table; no bulk actions |
| 8 | Aesthetic and Minimalist Design | 3 | Calm, but many controls sit above the first order |
| 9 | Error Recovery | 2 | Not exercised in this run |
| 10 | Help and Documentation | 2 | Only the status legend and title tooltips |
| **Total** | | **28/40** | **Good** |

## Design Specificity Verdict

LLM assessment: the summary cards, the "Precisam de ação" strip, the "Tiny desatualizado" badge and the expedition vocabulary are specific to this operation. The filter pills and the big-number cards are still a common dashboard pattern. The product character lives in the status logic, not in the visual language.

Deterministic scan: 11 findings across the four targets. Only 2 are in the overlay on the live panel:
- dark-glow on the active "Painel" nav tab (blue soft shadow). DESIGN.md allows this ("sombra azul suave"), so treat it as a false positive for the panel.
- overused font: Inter. This is a documented decision, so it is not a defect.

Visual overlays: injection succeeded. Overlays are visible in the [Human] tab. The console reported "2 anti-patterns found".

## Overall Impression

It reads as an operator's tool: the state of the orders is the first thing you see and the numbers are large. The biggest opportunity is above the first order: the header, the nav, the banner, four cards, a search, eight pills, a legend, a counter, a view switch and an options button all compete before the list starts.

## What's Working

1. "Precisam de ação" is a separate strip, so the orders that need action are one click away and are not mixed into the totals.
2. Zero Is Calm holds: empty pills and the empty atrasados cards go neutral and dashed.
3. The view switch and the table keep their state, and "Ver cartão" moves the view without overwriting the saved preference.

## Priority Issues

1. **[P2] Several blue decision elements in one area.** The active "Todos" pill, the active view button, the active nav tab and the floating "Consultar Tiny e Correios" button are all solid blue. DESIGN.md says at most one blue decision element per visible area (The One Signal Rule). Why it matters: the eye has no single place to start. Fix: keep blue on the floating action and on the active filter; show the active view as a neutral pressed state (for example a surface with a stronger border). Suggested command: /impeccable quieter.
2. **[P2] Filter pills wrap at narrower desktop widths.** On a 1040px column the eight pills take two lines, and the zero pills move to the second line. DESIGN.md says the pill strip scrolls on mobile and does not wrap. Fix: decide between a horizontal scroll on every width or a row with a fixed order. Suggested command: /impeccable layout.
3. **[P2] Too much above the first order.** Header, two meta lines, nav, banner, cards, search, pills, legend, counter, view switch and options all sit above the list. Fix: move the status legend into the options popover and put the counter next to the search. Suggested command: /impeccable distill.
4. **[P3] Blue glow on the active nav tab.** Documented in DESIGN.md, flagged by the detector. Fix: keep it, or record the exception in DESIGN.md so the detector stops flagging it. Suggested command: /impeccable polish.

## Persona Red Flags

**Jordan (First-Timer):** the status legend ("O que significam os status?") is the only explanation of "Atrasado" and "Aguardando retirada". The eight pills look like a filter bar without labels.

**Alex (Power User):** "/" focuses the search, Esc clears it, and the view and sort are keyboard-reachable. There are no shortcuts for the pills or the view switch.

**Sam (Accessibility):** the view switch uses aria-pressed and the table headers have scope. Contrast on the secondary texts passes 4.5:1 in both themes (checked in this run).

## Minor Observations

- The counter ("17 pedidos") is centred between the legend and the view switch, so it reads as detached from the list it counts.
- "Dados de 04/11 13:00 (há 19 min)" in the header is useful; keep it.

## Questions to Consider

- "What if the active view were shown by a quiet border, leaving blue to the one action that matters?"
- "Does the operator need the legend on the first screen, or only when a status is unclear?"
- "What would the panel look like if the pills were a single row and the counter lived beside the search?"
