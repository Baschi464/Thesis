$out_dir = 'build';
$aux_dir = 'build';

# Ensure bibtex finds references.bib even when run from the build/ output
# directory (MiKTeX runs bibtex with cwd=build; without this it can pick up a
# stray references.bib from the TeX tree). Additive and harmless under TeXLive.
ensure_path('BIBINPUTS', '.', '..');