# emCompound

## An emtsv module to _annotate compound component boundaries_

This emtsv module expects output generated by (at least) the tok,morph,pos emtsv modules and outputs a field labeled `compound`.

The `compound` field always contains exactly the value of the `lemma` field **except** when the word token is a compound. In that case the `compound` field contains the compound word's lemma with an '#' component boundary symbol inserted between each pair of component words, e.g. `form`: beleereszkedtek, `lemma`: beleereszkedik, `compound`: bele#ereszkedik for a verb with a preverb, or `form`: madzagkötőfék, `lemma`: madzagkötőfék, `compound`: madzag#kötő#fék for a N+A+N compound.

## Testing by hand

`pip install -r requirements.txt`
`make analyse_compounds`

## Python package creation

Just type `make` to run all the following.

1. A virtual environment is created in `venv`.
2. `emCompound` Python package is created in `dist/emCompound-*-py3-none-any.whl`.
3. The package is installed in `venv`. 
4. The package is unit tested on `tests/inputs/11341_prev.in` and the output is compared to `tests/outputs/11341_prev.out`.

The above steps can be performed by `make venv`, `make build`, `make install` and `make test` respectively.

The Python package can be installed anywhere by direct path:
```bash
pip install ./dist/emCompound-*-py3-none-any.whl
```

## Python package release

1. Check `emCompound/version.py`.
2. `make release-major` or `make release-minor` or `make release-patch`.\
   This will update the version number appropriately make a `git commit` with a new `git` TAG.
3. `make` to recreate the package with the new tag in `dist/emCompound-TAG-py3-none-any.whl`.
4. Go to `https://github.com/THISUSER/emCompound` and _"Create release from tag"_.
5. Add wheel file from `dist/emCompound-TAG-py3-none-any.whl` manually to the release.

## Add the released package to `emtsv`

1. Install [`emtsv`](https://github.com/nytud/emtsv/blob/master/docs/installation.md): 1st and 2nd point + `cython` only.
2. Go to the `emtsv` directory (`cd emtsv`).
1. Add `emCompound` by adding this line to `requirements.txt`:\
   `https://github.com/THISUSER/emCompound/releases/download/vTAG/emCompound-TAG-py3-none-any.whl`
2. Complete `config.py` by adding `em_compound` and `tools` from `emCompound/__main__.py` appropriately.
3. Complete `emtsv` installation by `make venv`.
4. `echo "Megtörtént volna a kutyasétáltatás." | venv/bin/python3 ./main.py tok,morph,pos > old`
5. `echo "Megtörtént volna a kutyasétáltatás." | venv/bin/python3 ./main.py tok,morph,pos,compound > new`
6. See results by `diff old new`.
7. If everything is in order, create a PR for `emtsv`.

## Remarks

Readme based on [`emPreverb`](https://github.com/ril-lexknowrep/emPreverb)