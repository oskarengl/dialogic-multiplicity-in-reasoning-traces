# Monologue or Dialogue?

### Measuring Conversational Structure in the Reasoning Traces of Large Language Models

Oskar Engl, Johannes Kepler University Linz, <oskar.engl@ik.me>

**[Read the paper](paper/monologue_or_dialogue.pdf)**

## Abstract

Reasoning models such as DeepSeek-R1 produce a long stretch of intermediate tokens before
they answer. Although each stretch is written by a single model in one pass, one can observe
in a trace that questions receive answers, objections receive concessions, and the argument
turns against itself and starts again. Is a reasoning trace's textual shape more akin to a
monologue or to a dialogue? We examine this with three text-analysis methods, two from
stylometry and one from conversation analysis, and require each to prove itself first on
four corpora whose voice structure is known: human monologue, human dialogue, AI monologue
and AI dialogue. Only a method that separates monologue from dialogue on these known
datasets goes on to measure the traces. Two of the three do. Both place the DeepSeek-R1
traces above the four-instance AI debate on their own measure: the traces change style
between neighbouring sentences more often than the debate does, and they complete more
question-and-answer pairs than the debate, though several times fewer than a single person
thinking aloud. The observed text alone cannot settle whether that comes from several voices
or from one voice writing conversationally.

## Corpora

| Cell | Corpus | N |
|---|---|---|
| ① | human monologue (think-aloud protocols) | 600 |
| ② | human dialogue (DeliData group deliberation) | 500 |
| ③ | AI dialogue (four role-prompted Qwen-2.5-7B) | 600 |
| ④ | AI monologue (one Qwen-2.5-7B) | 600 |
| ⑤ | DeepSeek-R1 reasoning traces (the target) | 600 |

## Methods

| Method | Passes the validity check | Reading of the traces |
|---|---|---|
| 1: author count | no | [between AI monologue and AI debate] |
| 2: style switch | yes | more switches than AI debate |
| 3: adjacency pairs | yes | more pairs than AI debate, fewer than human |

Table 1 of the paper. Method 1's reading is bracketed because it fails the check and so does
not judge the traces.

## Repository map

| Path | Contents |
|---|---|
| [`paper/`](paper/) | The paper, its two figures, and the scripts that generate them |
| [`preregistration/`](preregistration/) | The frozen method specification and a record of deviations from it |
| [`data/`](data/README.md) | The five corpora, their provenance and licences, and preprocessing documentation |
| [`methods/`](methods/) | One folder per method: run instructions, sources, verification, and local changes to upstream code |
| [`outputs/`](outputs/README.md) | Per-document results for all three methods |
| [`scripts/`](scripts/) | Dataset construction, placement, and figure code |
| [`notes/`](notes/README.md) | Working notes and superseded drafts |

## Reproducing

```bash
git clone --recurse-submodules https://github.com/oskarengl/dialogic-multiplicity-in-reasoning-traces.git
cd dialogic-multiplicity-in-reasoning-traces
```

Four directories are upstream repositories pinned by commit. Without
`--recurse-submodules` they arrive empty.

Regenerate the figures from the committed outputs:

```bash
python paper/make_fig_grid.py     # Figure 1
python paper/make_fig_split.py    # Figure 2
```

Running the methods themselves requires more: Method 2 needs the SSPC checkpoint
(`model.ckpt`, 719 MB) from its upstream repository, Method 3 needs API access to Tencent
Hunyuan Hy3, and generating cells ③④⑤ needs Qwen and DeepSeek access. Instructions are in
`methods/*/RUN_METHOD*.md`. Each method's `local_changes/README.md` lists what to apply to
the pinned upstream code before running.

Method 1 runs on patched upstream code. One patch changes the algorithm rather than
compatibility; see
[`methods/1_style_change_detection/local_changes/README.md`](methods/1_style_change_detection/local_changes/README.md).

## Data and licences

| Cell | Source | Licence |
|---|---|---|
| ① | [think-aloud-llms](https://github.com/benpry/think-aloud-llms), Wurgaft et al. 2025 | MIT |
| ② | [DeliData](https://huggingface.co/datasets/gkaradzhov/DeliData), Karadzhov et al. 2023 | CC-BY-4.0 |
| ③④⑤ | generated for this study | CC-BY-4.0 |

Cells ① and ② are redistributed in processed form under the terms above.

The PAN 2019 corpus is not included. It is access-restricted on Zenodo; see
[`data/README.md`](data/README.md) for how to request it. No reported result depends on it.

Literature PDFs are not redistributed. Sources are cited with links in each method's
`sources/SOURCES.md`.

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

Code and documentation: [MIT](LICENSE).

Generated corpora (cells ③④⑤): [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
Third-party corpora keep their upstream licences, listed above. Pinned submodules are
governed by their own repositories' licences.
