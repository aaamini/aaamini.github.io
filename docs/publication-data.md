# Publication Data

The canonical bibliography for the website should live at
`data/papers.bib`.  Keep standard BibTeX/BibLaTeX fields there for the CV and
LaTeX documents, and keep website-only fields in the same entries.  BibTeX and
BibLaTeX will ignore the website-only fields, while `build.py` uses them.

Useful website fields:

```bibtex
abbr     = {ICLR},
arxiv    = {2406.10686},
html     = {https://...},
pdf      = {paper.pdf},
code     = {https://github.com/...},
abstract = {...},
selected = {true},
site     = {false},
```

Use `site = {false}` for entries that should stay available to the CV but
should not appear on `/publications/`, such as working papers, internal
software/package references, and old preprint records superseded by a published
entry.

## Current Audit

Run:

```sh
.venv/bin/python tools/audit_bibliography.py
```

Current inputs:

- Site: `data/papers.bib`
- CV bibliography: `/Users/arash/Dropbox/latex-docs/cv/mypubs.bib`
- Current CV TeX files:
  - `/Users/arash/Dropbox/latex-docs/cv/cv_aaa.tex`
  - `/Users/arash/Dropbox/latex-docs/cv/merit_pubs_2026.tex`
- Old site: `/Users/arash/Dropbox/Sites/new_site/_bibliography/papers.bib`

As of the current audit, the old-site bibliography keys no longer match the
current site keys because several entries were intentionally normalized during
the 2026 CV/merit migration.  The site bibliography has 57 parsed entries,
including one `site = {false}` working-paper entry; the public site displays 56
papers.  The legacy CV file has 94 parsed entries.  There are 51 exact key
matches, 4 same-arXiv matches with different keys, 22 same-title matches with
different keys, and 16 CV-only unmatched candidates.

The audit also scans active `\cite`, `\nocite`, and `\fullcite` keys in the two
current CV TeX files listed above.  The 2024 merit bibliography is frozen and
continues to use `/Users/arash/Dropbox/latex-docs/cv/mypubs.bib`; the 2026 merit
bibliography and current CV use `papers-unified.bib`, a symlink to
`data/papers.bib`.

Active keys in `cv_aaa.tex` and `merit_pubs_2026.tex` all resolve in the
unified site bibliography.  Six active keys are not present in legacy
`mypubs.bib`; this is expected because those TeX files now cite the normalized
canonical keys.

The only detected duplicate key in the CV file is `shen2024bayesian`.

## Merge Policy

Use one canonical entry per paper when current TeX files can be migrated to the
canonical key.  The 2024 merit bibliography is not migrated.  The site entries
already carry useful public-site metadata (`abbr`, `selected`, `pdf`, `code`,
`abstract`), while the CV entries sometimes carry newer DOI/volume/pages data.
Merge field-by-field; the CV entry is not always better.

Normalized keys chosen during the 2026 migration:

- `akhazhanov2022finding` for the MNRAS quasar paper
- `almohri2023performance` for the Expert Systems with Applications paper
- `josephs2023nested` for the nested SBM preprint
- `kazemitabar2017variable` for the NeurIPS decision-tree paper
- `shen2025bayesian` for the Bayesian Analysis paper
- `zhou2023statistical` for the ICLR consensus clustering paper
- `amini2023spectral` for the hidden working paper

The MNRAS quasar paper had a corrupted author field in
`/Users/arash/Dropbox/latex-docs/cv/mypubs.bib` due to an embedded BibTeX entry.
The canonical entry should use publisher/DOI metadata, plus site fields such as
`abbr`, `arxiv`, `html`, and `pdf`.

CV-only candidates that probably should be added to the canonical file but kept
hidden from the site with `site = {false}`:

- `bayes:cov:sbm`
- `dARCS`
- `hsbm:pkg`
- `label:agg`
- `nett`
- `pois:comp:repo`
- `pois:pkg`
- `reg_lattice_comp`
- `spec:kern`
- `ye2021distributed`

CV-only candidates that need a human decision before adding to the public site:

- `2017estimator`
- `gu2017penalized`
- `raman:ejs`
- `rogatko2004`
- `ye2022distributed`
- `zhou2017uncertainty`

Former duplicate keys normalized away in current TeX files:

- `10.1093/mnras/stac925` -> `akhazhanov2022finding`
- `AlmohriChinnamAmini2023` -> `almohri2023performance`
- `JosephsAminiPaezLin2023` -> `josephs2023nested`
- `amini2017variable` -> `kazemitabar2017variable`
- `glasso:factors` -> `amini2023spectral`
- `shen2022bayesian` / `shen2024bayesian` -> `shen2025bayesian`
- `label-agg` -> `zhou2023statistical`

The external CV directory uses a separate symlink, leaving the legacy
`mypubs.bib` file available for comparison:

```sh
cd /Users/arash/Dropbox/latex-docs/cv
ln -s ../../Sites/aaamini.github.io/data/papers.bib papers-unified.bib
```

Current CV/merit files should use:

```tex
\addbibresource{papers-unified.bib}
```

The legacy `mypubs.bib` should not be deleted until the remaining CV-only
candidates have been reviewed.
