---
name: thesis-sync
description: Captures new PhD-thesis progress the moment it appears in conversation — a new experimental result, design decision, numeric parameter/measurement, or theoretical idea about the soft-robotics thesis — and produces (1) an English, PhD-level LaTeX section in the user's own established paper style, and (2) a Markdown file the user works from directly, always written, with two parts in order — an intuitive high-level explanation (with a metaphor only if one was actually used/approved in the chat) then a concrete implementation section. Checks the GitHub thesis repo first to avoid duplicating captured work. Use proactively when the user reports a result, states a design choice, gives a numeric experiment/simulation value, or floats a theoretical idea — even without an explicit "write this up." Also trigger on "aggiungi questo al paper", "salva questo risultato", "nuova idea per la tesi", or shared COMSOL/FEM data. Companion skill `thesis-recall` reads back what's saved — consult it first.
---

# thesis-sync

## What this is for

The user is writing a PhD thesis in soft robotics. Progress happens in
conversation, not in a formal writing session: they'll mention a bending
angle they just measured, a decision to switch to a different actuator
material, a control parameter that worked, or an idea for why something
behaves the way it does. Left in the chat, this gets lost. This skill's job
is to notice that a piece of thesis-relevant content just appeared, and turn
it into two durable artifacts, written the way the user actually writes:

1. A LaTeX section (or a few sections), in English, in the user's own
   established style — not generic academic prose.
2. A Markdown implementation plan for Claude Code, but **only when the
   novelty implies future engineering work** (new code to write, a new
   experiment to run, a new part to design). A completed result or a
   settled theoretical idea doesn't need an implementation plan; a design
   decision that implies "now go build X" does.

Both get saved to the user's GitHub repo (`github.com/Baschi464/Thesis`),
under `synthesis/`, so they're available in any future chat, in any
environment.

## Step 1 — Recognize the novelty

Ask yourself: did the user just report one of these four things?

- **Experimental result** — a measurement, an observed behavior, a video/data
  outcome ("il robot ha piegato a 180° con 15 kPa").
- **Design decision** — a choice between alternatives that was just made
  ("usiamo EcoFlex 00-50 per le pareti interne invece di 00-30").
- **Numeric data** — a parameter, constant, or value worth preserving even
  without narrative context yet (a FEM output, a material constant, a
  controller gain).
- **Theoretical idea** — an explanation, hypothesis, or model proposed for
  why something works ("penso che il ballooning non conti perché le camere
  non pressurizzate fanno da strain-limiting layer").

If none of these fit — the user is asking a general question, debugging
code, or chatting about something unrelated to the thesis — don't trigger.

## Step 2 — Check for duplicates before writing anything

Before drafting anything, load `thesis-recall` (or replicate its first step
inline: fetch `synthesis/INDEX.md` from the repo via the GitHub contents API,
`https://api.github.com/repos/Baschi464/Thesis/contents/synthesis/INDEX.md`).
This manifest is a lightweight list of every entry saved so far (type, date,
one-line title). Read it — don't fetch every past synthesis file in full,
that doesn't scale as the repo grows.

Compare the new novelty against the manifest entries semantically, not just
by keyword. If something looks like the same result/decision/idea already
captured (even worded differently), don't write a duplicate — tell the user
what you found and ask whether this is an update to that entry or genuinely
new.

If the repo or `synthesis/INDEX.md` doesn't exist yet, this is the first
entry — proceed and create the structure (see Step 5).

## Step 3 — Draft the LaTeX

Read `references/style-guide.md` and `templates/ieee_section_template.tex`
before writing anything — they encode the user's actual writing conventions
and the real document class (`ieeeconf`), extracted from their own papers.
Don't write generic academic English; match the register, citation style,
and structural conventions documented there.

Map the novelty type to where it belongs structurally:
- Experimental result → a Results/Experiment subsection, following the
  pattern of "setup described, then quantitative outcome stated."
- Design decision → a Methods/Design subsection, framed as a choice among
  alternatives with the reasoning that drove it (this is exactly how the
  style guide's "gap → decision" pattern works at a smaller scale).
- Numeric data → belongs alongside the design/methods content it supports;
  don't create a bare data dump without narrative framing unless the user
  asks for exactly that.
- Theoretical idea → a short model/discussion subsection, hedged
  appropriately if it's not yet experimentally confirmed (the user's own
  papers hedge this way, e.g. "Interestingly, suppressing the ballooning
  effect did not reduce...").

If the content requires a citation and you don't have one, don't invent it —
use `\cite{TODO-<short-description>}` and tell the user directly, following
the same rule as the style guide.

## Step 4 — Always write the .md file

Write `synthesis/<date>_<slug>.md` for every entry, unconditionally. The
user works on the actual code/hardware through these files, so skipping one
because a given novelty seems "purely theoretical" or "already complete"
defeats the purpose — always produce it.

The file has a fixed two-part structure, in this order:

1. **High-level intuitive explanation** (comes first, and is the bulk of the
   file). Written informally, for someone picking the file back up weeks
   later without the .tex's formal register. Include a metaphor **only if
   one actually exists from the conversation** — either the user proposed it,
   or Claude proposed one and the user approved/accepted it in that chat. Do
   not invent a metaphor that wasn't actually used or endorsed just to fill
   this section; if no metaphor came up, write the intuitive explanation
   without one. Fabricating one would misrepresent what was actually
   discussed.
2. **Implementation** (last section, and only the last section). What needs
   to change, in which files/hardware, and what "done" looks like — concrete
   and actionable for a future Claude Code session. Don't restate context
   from section 1 or from the .tex file; this section is for the concrete
   next steps only.

If the novelty genuinely has no follow-up engineering work (e.g. a fully
settled result with nothing left to build), the Implementation section can
say so explicitly ("No further implementation needed — this entry is
complete.") rather than being omitted or padded.

## Step 5 — Images

- Ask the user which figure(s), if any, this entry needs.
- **In Claude Code**: also check the workspace's `figures/` folder for files
  that look relevant (recent modification time, filename overlap with the
  novelty's topic) and offer them as candidates — don't assume a match
  silently, confirm with the user before using one.
- **In Claude.ai / Cowork**: no local filesystem access to the user's
  workspace exists, so only ask; don't claim to be able to look somewhere
  you can't reach.

## Step 6 — Save and sync to GitHub

File layout in the repo:
```
synthesis/
  INDEX.md                      <- manifest, one line per entry
  YYYY-MM-DD_<slug>.tex         <- the LaTeX section(s)
  YYYY-MM-DD_<slug>.md          <- intuitive explanation + implementation (always written, see Step 4)
```

Append one line to `INDEX.md` per entry: date, type, short title, and the
filename(s). This is what keeps future duplicate-checking cheap.

**How you actually write these files depends on the environment:**

- **Claude Code**: use `git` directly (native `bash_tool` access) — create/
  update the files, `git add`, `git commit`, `git push`. This is fully
  automatable; no need to ask permission for each file write since it's
  local-first, but do tell the user what you committed and pushed.
- **Claude.ai / Cowork**: there is no GitHub write connector available. Use
  Claude in Chrome to navigate to the repo on github.com and create/edit the
  file through GitHub's own web UI. **Always show the user the exact content
  and the target path before clicking any commit/confirm button, and wait
  for explicit go-ahead.** Committing changes to a public repo is exactly the
  kind of action that needs a live yes from the user each time — a prior
  approval for one file doesn't carry over to the next one.

## What NOT to do

- Don't write a synthesis entry for something the user is just thinking out
  loud about or exploring hypothetically — wait until it's stated as an
  actual result, decision, value, or idea they're committing to.
- Don't silently skip the duplicate check because "it's probably fine" —
  the whole point of `INDEX.md` is to make that check cheap enough to never
  skip.
- Don't fabricate citations, part numbers, or numeric values to fill gaps in
  what the user told you. Ask, or mark the gap explicitly.
