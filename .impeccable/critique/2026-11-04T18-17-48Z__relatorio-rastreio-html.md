---
target: relatorio_rastreio.html
total_score: 28
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 0
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:1bd28fc33bc0699604868856d2466e5061fea2a565bfe6f406a4868c124f1ae2"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-04T18-17-48Z
slug: relatorio-rastreio-html
---
# Critique: relatorio_rastreio.html (11ª rodada)

Method: ⚠️ DEGRADED: single-context (sub-agents not spawned: the user did not ask for sub-agents in this session; detector and browser evidence collected inline)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|---|---|---|
| 1 | Visibility of System Status | 3 | Data age, next consult and banner are visible; no per-order error state seen |
| 2 | Match System / Real World | 3 | Operator vocabulary holds (pedido, rastreio, Precisam de ação) |
| 3 | User Control and Freedom | 3 | Limpar filtros, Esc, clear pills; the clear control appears only while filtering |
| 4 | Consistency and Standards | 3 | Counter moved beside search, but the view switch was left alone on its own row |
| 5 | Error Prevention | 3 | Cooldown on the Tiny/Correios update; no confirmation needed (read-only actions) |
| 6 | Recognition Rather Than Recall | 3 | Status legend now sits two taps deep in Opções, so "Atrasado" has no first-screen explanation |
| 7 | Flexibility and Efficiency | 3 | "/", Esc, sort in Opções, three views; no bulk actions |
| 8 | Aesthetic and Minimalist Design | 3 | Calmer than before (pills in one line, neutral view state), but the first order still starts below header, nav, banner, cards, search, pills, view row and Opções |
| 9 | Error Recovery | 2 | Not exercised in this run |
| 10 | Help and Documentation | 2 | Status legend and title tooltips only; legend is no longer on the first screen |
| **Total** | | **28/40** | **Good** |

## Design Specificity Verdict

LLM assessment: operator-specific vocabulary and status logic (Precisam de ação, Tiny desatualizado, Dados consultados em, atrasados por urgência) keep the panel from being interchangeable. The summary cards and filter pills are a familiar dashboard pattern, and the calm, neutral pressed state for the view switch is a real improvement over the previous run.

Deterministic scan (`impeccable detect --json`, relatorio_rastreio.html, pedidos_atrasados.html, opcoes_frete.html, web/): 12 findings, exit code 2.
- overused-font: Inter, in all three HTMLs and web/css/main.css (documented decision, false positive for this product).
- design-system-color (advisory): text colours rgb(22,101,52), rgb(3,105,161), rgb(146,64,14) on status spans, and rgb(191,219,254) border on "Mais barato" in opcoes_frete.html. These are the `--color-*-text` tones described in DESIGN.md, not yet listed as literal tokens, so they read as drift to the detector.
- side-tab: web/css/components.css:484, `border-left: 3px solid var(--color-border)`. A neutral border, not a coloured accent, so a likely false positive.
- design-system-font: web/css/components.css:752, `Sfmono-Regular`. The monospace stack in DESIGN.md lists SFMono, so this is a documented fallback, not a new family.
- Not reproduced: the dark-glow on the active nav tab, which the CLI scan no longer reports thanks to the config exception.

Visual overlays: injection succeeded on the 375px dark view. The [Human] tab shows the overlay. Console reported "2 anti-patterns found": dark-glow on the active "Painel" tab (documented exception, DESIGN.md "Brilho da aba ativa"; the in-page detect.js does not read `.impeccable/config.json`, so it still flags it, while the CLI does not) and overused-font Inter (documented).

## Overall Impression

Better than the last run in the places the previous critique asked for: the filter pills stay in one row at 1280, 1040 and 375; the view switch is neutral; the counter sits beside the search; the legend moved into Opções. The biggest remaining problem is the list-control zone: the view switch and "Opções" now wrap onto their own rows, leaving an orphan control and a gap before the first order. On 375px the first order card starts at y≈668 of 812.

## What's Working

1. The filter pills are a single scrolling row with active pills first and zero pills dashed and neutral (The Zero Is Calm Rule holds in the DOM: Atrasados 0 and Aguardando retirada 0 are dashed).
2. The view switch uses aria-pressed and a neutral pressed state (surface, strong border), so the blue decision colour is kept for the active filter and the floating action.
3. The banner "Nada atrasado nem aguardando retirada" is a calm green line when there are no problems, and the four summary cards keep the number first.

## Priority Issues

1. **[P2] First order starts too low on phones.** At 375px the header has three meta lines, then nav, banner, four cards, search, pills, view switch and "Opções" before the first order (y≈668 of 812). Why: the operator wants to see late orders first. Fix: collapse the header meta to one line, and move the "Opções" link into the view-switch row. Suggested command: /impeccable distill.
2. **[P2] List controls wrap into an orphan row.** At 1280 the view switch sits alone at the right of its own row (y=494, pills at y=441), and at 375 "Opções" is a single left-aligned link below it. DESIGN.md says the view control sits on the list line beside the counter, but the counter now lives on the search row, so the list line has no anchor. Fix: one row above the list with the view switch and Opções on the same line, with the count or list title on the left. Suggested command: /impeccable layout.
3. **[P2] The floating "Consultar Tiny e Correios" button covers actions.** At 375px the 52px circle (x 307–359, y 744–796) overlaps the right end of "Copiar rastreio" (x 224–330) on the first card. At 1280 it overlaps the right-hand card header while scrolling. Fix: add bottom padding to the list equal to the floating button's footprint, and keep the button clear of the first card's action row (for example by adding a bottom-right safe area or by letting the list scroll above it). Suggested command: /impeccable polish.
4. **[P3] Three solid-blue decision elements in one viewport.** The active "Painel" nav tab (with its glow), the active "Todos" pill and the floating button are all solid blue. Improved from the previous run (the view switch is no longer blue), but the nav tab is navigation, not a decision. Fix: give the active nav tab a neutral pressed state with a blue underline, keep blue on the active filter and the floating action. Suggested command: /impeccable quieter.
5. **[P3] The status legend is two taps deep.** "O que significam os status?" now lives in Opções, so "Atrasado" and "Aguardando retirada" have no first-screen explanation (Jordan persona). Fix: add a title tooltip or one-line description to each status pill and badge, and keep the full legend in Opções. Suggested command: /impeccable clarify.
6. **[P3] Detector drift on documented tones.** Status text tones (rgb(22,101,52), rgb(3,105,161), rgb(146,64,14), rgb(191,219,254)) are not listed as tokens, and the in-page overlay ignores the dark-glow exception in `.impeccable/config.json`. Fix: record the `--color-*-text` tones in the DESIGN.md sidecar, and make the overlay read the same exception. Suggested command: /impeccable document.

## Persona Red Flags

**Jordan (First-Timer):** "Atrasado" and "Aguardando retirada" are only explained inside Opções → legend. The eight-plus pills look like a filter bar with no labels, and the view switch reads like a second filter.

**Alex (Power User):** "/" focuses the search, Esc clears it, and the view and sort are keyboard-reachable. The floating button still covers "Copiar rastreio" on the first card when the list is scrolled, which costs a second click.

**Sam (Accessibility):** the view switch uses aria-pressed and the neutral pressed state keeps the contrast. The status tones pass 4.5:1 per DESIGN.md; the overlay flags Inter only as a font choice.

## Minor Observations

- At 375px the "Tabela" view is disabled and the saved preference `painel.visao=tabela` falls back to Compacta silently. Consider a hint or leaving the saved value alone.
- The counter "25 pedidos" truncates the search placeholder on 375px ("Pedido, cliente, rastreio ou"). Fine, but shorter placeholder text would keep the full field readable.
- The header meta ("Dados de 04/11 14:37 (há 37 min)") is useful; keep it.

## Questions to Consider

- "What if the list had one header line with the view switch and Opções on the same side, and the count on the other?"
- "Does the first card need to clear the floating button, or could the button move to the header on phones?"
- "What would the panel look like if the nav tab and the active filter both used neutral pressed states?"
