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
  - `/Users/arash/Dropbox/latex-docs/cv/merit_pubs_2024.tex`
- Old site: `/Users/arash/Dropbox/Sites/new_site/_bibliography/papers.bib`

As of the current audit, the old-site bibliography keys match the current site
keys.  The site has 56 entries; the CV file has 94 parsed entries.  There are
53 exact key matches, 3 same-arXiv matches with different keys, 20 same-title
matches with different keys, and 17 CV-only unmatched candidates.

The audit also scans active `\cite`, `\nocite`, and `\fullcite` keys in the two
current CV TeX files listed above.  It finds 55 active citation keys.  Of those,
7 are not present in the site bibliography, and none are missing from the
current CV bibliography.  This means the final merge must either preserve those
7 current CV citation keys as hidden aliases or update the two current TeX
files before replacing the CV bibliography with a symlink.

The only detected duplicate key in the CV file is `shen2024bayesian`.

## Merge Policy

Use the current site entry as the base when the same publication appears in
both files.  The site entries already carry the public-site metadata (`abbr`,
`selected`, `pdf`, `code`, `abstract`) and stable HTML anchors.  Copy newer
standard metadata from the CV entry into the site entry when it is clearly an
update, but avoid changing the site key unless there is a strong reason.

For same-paper duplicate keys, prefer the existing site key:

- `josephs2023nested` over `JosephsAminiPaezLin2023`
- `wu2024graph-rlc` over `wu2024graph-arxiv`
- `akhazhanov2021finding` over `10.1093/mnras/stac925`
- `label-agg` over `zhou2023statistical`
- `amini2022perfectness` over `perfect` and `perfect:aistats`
- `ZhangAmini2023` over `zhang2020adjusted`
- `amini2021spectrally` over `st:krr`

However, the current CV TeX files cite some alternate keys directly.  Until
those two TeX files are migrated, keep those alternate keys in the canonical
file with `site = {false}` rather than deleting them.

CV-only candidates that probably should be added to the canonical file but kept
hidden from the site with `site = {false}`:

- `bayes:cov:sbm`
- `dARCS`
- `glasso:factors`
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

Active citation keys in `cv_aaa.tex` or `merit_pubs_2024.tex` that are not in
the current site bibliography:

- `10.1093/mnras/stac925`
- `AlmohriChinnamAmini2023`
- `JosephsAminiPaezLin2023`
- `amini2017variable`
- `glasso:factors`
- `shen2022bayesian`
- `zhou2023statistical`

After the canonical file is merged and verified, the external CV path can be
made a symlink to it:

```sh
cd /Users/arash/Dropbox/latex-docs/cv
mv mypubs.bib mypubs.bib.backup
ln -s ../../Sites/aaamini.github.io/data/papers.bib mypubs.bib
```

That final symlink step edits files outside this repository and should be done
only after confirming the merged bibliography still builds the CV.
