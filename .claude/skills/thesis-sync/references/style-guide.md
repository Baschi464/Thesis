# Style guide — Alessandro Baschiera, soft robotics writing

Derived from two writing samples (n=2): the inchworm climbing robot paper
(RoboMech, actual publication) and a draft introduction for a lizard-inspired
soft robot paper (IEEE conference format, in progress). Both are single-author
(with advisor) technical papers in the same lab/subfield. Confidence levels
below reflect the size of the sample — this is a plausible authorial profile,
not a validated statistical model. Where the two samples disagree, both are
noted rather than papered over.

## Document class (decided, not inferred)

Use `ieeeconf` (IEEE conference template), per explicit instruction — not the
`robomech_en` class the inchworm paper actually shipped with. See
`templates/ieee_section_template.tex` for the skeleton pulled directly from
the user's own `.tex`/`.cls` source.

## Structural patterns (High confidence — consistent across both samples)

- **Introduction arc**: broad domain claim → survey of related work, one
  cluster of prior work per paragraph, each ending in a limitation
  ("However, ...", "Nevertheless, ...") → explicit statement of the gap →
  "To address this limitation, we propose..." / "Motivated by this gap, this
  paper presents...".
- **Citations**: BibTeX keys of the form `AuthorYYYYShortTitle`
  (e.g. `Gu2018SoftWallClimbing`, `Qin2019Versatile`), rendered as numeric
  brackets via `\bibliographystyle{IEEEtran}`. Never invent a key or a
  reference — if a claim needs a citation and none exists in `references.bib`,
  flag it as `\cite{TODO}` and tell the user explicitly rather than fabricating
  a source.
- **Methodology register**: passive voice, third person
  ("was optimized via...", "were conducted using...", "is governed by...").
  "We propose" / "This paper presents" is reserved for the contribution
  statement, not general methodology narration.
- **Quantitative precision**: every claim about hardware or materials is
  anchored to a specific part number, model, or manufacturer
  (e.g. "Arduino Mega 2560", "DP0110T-Y1, Nitto Kohki", "EcoFlex 00-30").
  Never write a generic placeholder ("a microcontroller") when the real
  component is known — ask the user for the missing spec instead of
  generalizing.
- **Equations**: numbered, referenced as "(1)" not "Eq. (1)" except at a
  sentence start. Roman symbols italicized, Greek symbols upright. Symbols
  defined in the sentence immediately before or after the equation, never
  left undefined.
- **Figure/table captions**: full descriptive sentences below figures /
  above tables. Multi-panel figures get a lettered breakdown, e.g.
  "(a) ... (b) ... (c) ...", each with its own descriptive clause — not just
  a label.

## Divergence between the two samples (flag, do not silently resolve)

- The lizard-robot draft has an explicit numbered "main contributions" list
  after the Introduction narrative:
  `The main contributions of this work are as follows: \begin{enumerate}...`.
  The inchworm paper folds the contribution into prose instead, with no
  explicit list. **Default: use the explicit contributions list** (it's the
  more recent sample and matches the now-decided `ieeeconf` template), but
  this is a moderate-confidence choice from n=2 — if the user pushes back,
  don't argue the point, just switch.

## Explicit non-rules (things NOT to infer from n=2)

- Section count, subsection depth, and paper length vary by content and
  should not be forced into a fixed template beyond what's in
  `ieee_section_template.tex`.
- Do not infer a "target journal/conference" style beyond IEEE conference
  format unless the user specifies one.

## What this file is for

When `thesis-sync` drafts a `.tex` section, it should read this file plus
`templates/ieee_section_template.tex`, and write new content that a reader
familiar with the user's existing papers would not flag as stylistically
inconsistent. It is not a checklist to satisfy mechanically — if a rule above
doesn't fit the content being written, say so rather than forcing it.
