# Monologue or Dialogue?

### Measuring conversational structure in the reasoning traces of large language models

Oskar Engl · Johannes Kepler University Linz · <oskar.engl@ik.me>

**📄 [Read the paper](paper/monologue_or_dialogue.pdf)** · [LaTeX source](paper/monologue_or_dialogue.tex)

---

A reasoning model such as DeepSeek-R1 writes a long stretch of intermediate tokens before it
answers. One model writes each one in a single pass, yet inside a trace questions get
answers, objections get concessions, and the argument turns against itself and starts again.
Is a trace's textual shape closer to a monologue or to a dialogue?

The study puts that question to three text-analysis methods — two from stylometry, one from
conversation analysis — and makes each prove itself first on four corpora whose voice
structure is already known. Only a method that separates monologue from dialogue on the
known corpora gets to measure the traces.

**Two of the three qualify, and both place the traces above the four-instance AI debate on
their own measure.** The traces switch style between neighbouring sentences more often than
the debate does, and they complete more question-and-answer pairs — though several times
fewer than one person thinking aloud. The text alone cannot settle whether that comes from
several voices or from one voice writing conversationally.

## The design

| | monologue | dialogue |
|---|---|---|
| **human** | think-aloud protocols, N = 600 | DeliData group deliberation, N = 500 |
| **AI** | one Qwen-2.5-7B, N = 600 | four role-prompted Qwen-2.5-7B, N = 600 |

Plus the target: **DeepSeek-R1 native reasoning traces, N = 600.** The AI cells and the
human monologue cell all solve Game of 24, so a method cannot separate them on subject
matter instead of voice structure.

| Method | Reads | Passes the check | Reading of the traces |
|---|---|---|---|
| 1 · author count ([Nath 2019](https://github.com/pan-webis-de/nath19)) | function-word clusters across windows | **no** | *[between AI monologue and AI debate]* |
| 2 · style switch ([Schmidt et al. 2025](https://github.com/glsch/better-call-claude_pan25-multi-author-style-analysis)) | style change between adjacent sentences | **yes** | more switches than the AI debate |
| 3 · adjacency pairs (CAMS tagging) | completed question-and-answer structure | **yes** | more pairs than the AI debate, far fewer than human |

Method 1 fails because it reads *all 500* human debates and a majority of the AI debates as
single-author. DeliData turns average 8.4 words, so a paragraph-sized window swallows
several speakers at once.

## Repository map

| Path | What is in it |
|---|---|
| **[`paper/`](paper/)** | The paper, its two figures, and the scripts that regenerate them |
| **[`preregistration/`](preregistration/)** | The frozen method spec, and an honest record of every deviation from it |
| **[`data/`](data/README.md)** | The five corpora, their provenance and licences, and preprocessing decisions |
| **[`methods/`](methods/)** | One folder per method: run instructions, sources, verification, and local changes to upstream code |
| **[`outputs/`](outputs/README.md)** | Frozen per-document results — every number in the paper comes from here |
| **[`scripts/`](scripts/)** | Dataset construction, placement, and figure code |
| **[`notes/`](notes/README.md)** | Working notes and superseded drafts. Not part of the result |

## Reproducing

```bash
git clone --recurse-submodules https://github.com/oskarengl/dialogic-multiplicity-in-reasoning-traces.git
cd dialogic-multiplicity-in-reasoning-traces
```

The `--recurse-submodules` matters: four directories are upstream repositories pinned by
commit, and without it they arrive empty.

**The figures regenerate from the committed outputs, with no GPU and no API key:**

```bash
python paper/make_fig_grid.py     # Figure 1 — design schematic
python paper/make_fig_split.py    # Figure 2 — both methods' measurements
```

**The measurement stages need more.** Method 2 needs upstream's 719 MB SSPC checkpoint;
Method 3 needs API access to Tencent Hunyuan Hy3; the generation of cells ③④⑤ needs Qwen
and DeepSeek access. Their outputs are committed so nothing downstream depends on re-running
them. Per-method instructions are in `methods/*/RUN_METHOD*.md`, and each method's
`local_changes/README.md` explains what to apply to the pinned upstream code before running.

## What to be sceptical about

Four things a reviewer should know before trusting a number here. Each is documented in
place, not just mentioned.

**The validity check replaced the pre-registered gates, after the gate results were known.**
This is the study's one substantive deviation, and it is the situation pre-registration
exists to constrain. The gates would have admitted Method 1 — which cannot recognise a
dialogue — and excluded Method 3, which sorts all four known cells correctly. The full
reasoning, and what can and cannot be checked about it, is in
[`preregistration/DEVIATIONS.md`](preregistration/DEVIATIONS.md).

**Method 1's failure comes from patched code.** The 2019 implementation does not run on a
current Python stack. Most patches are compatibility fixes, but one changes the algorithm:
clustering thresholds are divided by cluster size alone rather than by cluster size times
average intra-cluster distance. See
[`methods/1_style_change_detection/local_changes/README.md`](methods/1_style_change_detection/local_changes/README.md).

**Method 3's labels are moderate, not good.** The automatic tagger agrees with a human
annotator on 74.2% of 503 utterances, κ = 0.54 (0.62 tree-weighted) — below the 0.70 the
study pre-registered. Most disagreements are near misses on the general `inform` label and
split evenly in both directions. The paper carries Method 3 forward on cell separation
rather than label accuracy, and names this the weakest link in its chain.

**The AI debate anchor is weak in absolute terms.** Its four voices are four instances of
one model separated by role prompt, completing adjacency pairs at 0.025 against real human
conversation's 0.235. Clearing it is a low bar. The paper defends the *direction* of the
placement, not its size.

## Data and licences

Cells ① and ② are third-party corpora, redistributed here in processed form under their
original terms:

- **think-aloud** — [Wurgaft et al. 2025](https://github.com/benpry/think-aloud-llms), MIT
- **DeliData** — [Karadzhov et al. 2023](https://huggingface.co/datasets/gkaradzhov/DeliData), CC-BY-4.0

Cells ③④⑤ were generated for this study.

**The PAN 2019 corpus is not included.** It is access-restricted on Zenodo and not ours to
redistribute; see [`data/README.md`](data/README.md) for how to request it. No reported
result depends on it.

Literature PDFs are not redistributed either. Every source is cited with a resolvable link
in the per-method `sources/SOURCES.md`.

## Citing

```bibtex
@misc{engl2026monologue,
  author = {Engl, Oskar},
  title  = {Monologue or Dialogue? Measuring Conversational Structure
            in the Reasoning Traces of Large Language Models},
  year   = {2026},
  school = {Johannes Kepler University Linz}
}
```

## Licence

Code and documentation in this repository: [MIT](LICENSE).

The generated corpora (cells ③④⑤) are released under
[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). The third-party corpora keep
their upstream licences, listed above. Pinned submodules are governed by their own
repositories' licences.
