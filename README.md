# emCompound

This is an emtsv module that annotates compound component boundaries based on the output of the tok, morph and pos emtsv modules.

## User's guide

The emCompound module takes the output of `emtsv tok,morph,pos` as its input and makes a heuristic decision for each token based on this input, determining whether the token's lemma is a compound or a non-compound word, and where the component boundaries are exactly situated in the lemma if it is a compound.

### Output

The module's output appears in the `compound` field. This field always contains exactly the value of the `lemma` field **except** when the token is a compound.

If the token is a compound, then this field contains the lemma annotated with '#' component boundary symbols, which are inserted between pairs of component stems. For example, the verb form _beleereszkednek,_ which consists of a preverb followed by a verb stem and is thus regarded by some linguists as a compound, receives the `lemma` _beleereszkedik_ from emtsv pos. Based on this lemma and the content of the morphological information found in the `anas` field, emCompound assigns the value `bele#ereszkedik` to its `compound` output field.

For multiple compounds, multiple boundary symbols are inserted, one at each boundary: `form`: _madzagkötőfék,_ `lemma`: _madzagkötőfék,_ `compound`: `madzag#kötő#fék` for a N+A+N compound.

In the rare case that a lemma can receive several possible distinct compound analyses, and none of these are explicitly excluded via the exclusion list (see below), the alternative compound analyses are all listed in the `compound` field separated by a comma followed by a space, e.g. `lemma`: _csőszállító,_ `compound`: `cső#szállító, csősz#állító`; `lemma`: kardél, `compound`: `kar#dél, kard#él`.

### Exclusion list

Some lemmas are assigned a spurious compound analysis by emMorph in the sense that these analyses are very unlikely to reflect the intended structure of any token. Some of these might be semantically conceivable but still wrong, e.g. _szakács_ `szak#ács` (cf. `szak#orvos`), _kisülés_ `kis#ülés` (cf. `kis#térség`), or _kommentár_ `komment#ár` (cf. `komment#cunami`). Others are just plain crazy, e.g. _sóhaj_ `só#haj`, _idomár_ `idom#ár` or _erdőség_ `erdős#ég`, or possible puns, e.g. _halász_ `hal#ász` or _varázsló_ `varázs#ló`.

When deciding whether a compound analysis is potentially correct or spurious, this module relies on an exclusion list, which is contained in the file [non_compounds.txt](https://github.com/ril-lexknowrep/emCompound/blob/main/emCompound/non_compounds.txt) in the emCompound subdirectory. This list specifies pairs of stems that can safely be assumed not to appear as subsequent components in a compound, and thus emCompound is forbidden to split a lemma at the boundaries between them.

The exclusion list contains a pair of stems connected by a plus sign on each of its lines. Each such pair essentially constitutes an exclusion rule, e.g. `elme+nő`, which essentially says that a lemma must not be split on a boundary between the stem _elme_ and the stem _nő_ in a morphological analysis (since this analysis is possible in principle, but incorrect in practice).

The part before the `+` sign (in this case, _elme_) must be a full compound component, i.e. it must match the compound component to the left of a potential boundary exactly. This means that the rule `elme+nő` forbids the splitting of the lemma _elmenő_ into _elme#nő,_ but it would not forbid e.g. the split _kelme#nő_ of the lemma _kelmenő_ if this lemma were ever used. This compound component can be either a monomorphemic root (like _elme_), but it can also be morphologically complex, i.e. a root followed by one or more derivational suffixes, like in the rule `társas+ág`.

On the other hand, the part after the `+` sign is not (necessarily) a full compound component, but rather an initial substring of the compound component to the right of the potential boundary. This substring can be equal to the actual second component, or it can be shorter (but must obviously not be longer than the second component). Thus for example the rule `társas+ág` not only blocks the splitting of the lemma _társaság,_ but also of _társasági,_ _társaságú,_ etc.

Note that the rules in the exclusion list are not only triggered at the beginning of a lemma, but also within a lemma if it contains any compound components to the left. For example, the rule above will block the splitting of _társaság_ not only when it appears as a separate word, but also in compounds like _asztal#társaság, hölgy#társaság,_ etc.

The exclusion list can be freely edited by users to handle spurious compounds that are not currently covered. We would appreciate pull requests with improvements to the exclusion list.

### Linguistic background

Although emtsv's emMorph morphological analyser (emtsv morph) divides token forms up into morphemes, including compound components, extracting information on compound structure from this output is generally not a straightforward matter. On the one hand, emMorph often assigns compound analyses to words that could in principle be compounds but are non-compounds in their by far most frequent interpretation. For example, the form _haladó_ receives at least two potential compound analyses from emMorph: the adjective (present participle) _hal+ad+ó_ 'fish-giving', the noun _hal+adó_ 'fish tax', while its normal interpretation is that of an adjective (present participle), _halad+ó_, meaning either 'progressing' or 'progressive'. Conversely, for most lexicalised compounds (even if they are both morphologically and semantically perfectly transparent), and even for many that are arguably not lexicalised, emMorph outputs a non-compound analysis in addition to the correct compound analysis. For example, although for the compound _önleleplezés_ 'exposing one's own lie, crime, secret etc.' it generates the compound analysis _ön+leleplezés_, it also outputs an analysis where this appears as a single morpheme, _önleleplezés._

The PurePos POS-tagger module (emtsv pos) partially disambiguates between the alternative analyses provided by emMorph, but this disambiguation only concerns the lemma and POS tag to be assigned to a token in the given context. For example, the form _hasadnak_ receives two alternative analyses from emMorph (both non-compounds): it can be either a 3rd person plural form of the verb lemma _hasad,_ or a 2nd person singular possessive and dative form of the noun lemma _has._ This level of disambiguation is sometimes sufficient to decide whether the form in question is a compound or not. For example, if the POS-tagger decides that the form _falak_ is a plural noun, then the alternative compound  analysis _fa+lak,_ which would be a singular noun, can be excluded. But in general the level of disambiguation that is carried out by PurePos is not sufficient to decide whether the form in question has a compound or non-compound (monomorphemic or derived) stem, and the POS output does not mark morpheme boundaries, including compound component boundaries, in any way.

The emCompound module accepts the lemma and POS tag assigned by emtsv pos to a token, examines the content of the morphological analysis field (`anas`) output by emMorph, ignores those alternative analyses that are not consistent with the POS and lemma labels assigned by the POS-tagger, and makes a heuristic decision whether out of the remaining possible analyses the form should receive a compound or a non-compound analysis. This decision does not consider semantic factors and linguistic context, but is instead based on the exclusion list described above, i.e. a manually defined list of potential stem combinations that are unlikely to be true compound components. Simply put, this means that when a token of the form _haladó_ is encountered, and the POS-tagger determines that this is an adjective in the given context, the above-mentioned analysis _hal+adó_ 'fish tax' is discarded from the outset, since it has the wrong POS tag (noun rather than adjective). Then emCompound examines its list of potential stem combinations that should not be analysed as compounds. If the stem combination `hal+ad` is included in this list — which it is indeed, as the noun _hal_ and the verb _ad_ are in fact extremely unlikely to form a compound —, then the 'fish-giving' compound interpretation is also discarded by emCompound, and the correct decision is reached that this form should not be annotated as a compound. Otherwise, i.e. if this potential stem combination does not appear in the exclusion list, the compound analysis is chosen, and emCompound annotates the form with a compound lemma which contains a compound boundary symbol between the relevant morphemes, e.g. `súly#adó` in the `compound` field.

Note that since this decision solely relies on the exclusion list as described above, emCompound is unable to take semantic or grammatical cues into consideration that would dramatically increase the conditional probability of a compound interpretation. E.g. although it is extremely unlikely a priori that _haladó_ should be interpreted and analysed as a compound, this interpretation and analysis become much more reasonable in a linguistic context like _haladót fizet_. This module is not designed to take such contextual cues into consideration.

Note also that there are some cases where a compound and a non-compound analysis are more or less equally reasonable, so neither systematically excluding the compound analysis, nor always choosing it seems to be the right decision. Although this might occasionally present a real problem, most such cases are correctly handled since the POS tag is taken into account by emCompound. For example, the lemma _felül_ could reasonably be the non-compound adverb _felül_ or the compound verb _fel#ül,_ and similarly, _megint_ could be the adverb _megint_ or the compound verb _meg#int._ In these cases, however, the POS tag of the given token disambiguates between the compound (verb) and the non-compound (adverb) analyses, and thus the value of the `compound` field will always be correct whenever the POS tag is.

### Usage examples

Depending on the current configuration of your system, you might have to add the path to the emCompound module on your machine (i.e. the path to your clone of the emCompound repository) to the `PYTHONPATH` environmental variable like this before executing the commands below, otherwise you might get a 'module not found' error from the Python interpreter:

```
export PYTHONPATH="${PYTHONPATH}:/path/to/emCompound/"
```

(Replace the part "`/path/to/emCompound/`" by the actual absolute path to emCompound on your machine.)

EmCompound can be executed as an individual Python module. The file 'input.txt' in this example is a raw text file:

```
cat input.txt | docker run -i --rm mtaril/emtsv tok,morph,pos > pos_output.tsv
cat pos_output.tsv | python3 -m emCompound > compound_output.tsv
```

Note that for compound verbs that contain a preverb, emCompound only annotates the correct compound lemma if the preverb is not separated from its verb, but prefixed to it. However, emCompound can be run in combination with our [emPreverb](https://github.com/ril-lexknowrep/emPreverb/) module, which identifies most occurrences of such compound verb lemmas where the preverb is separated from the verb. Please refer to the documentation of emPreverb for details. The emCompound module should always be run **before** emPreverb.

```
cat input.txt | docker run -i --rm mtaril/emtsv tok,morph,pos > pos_output.tsv
cat pos_output.tsv | python3 -m emCompound | python3 -m emPreverb > prev_output.tsv
```

Alternatively, emCompound can be run within emtsv as part of a processing pipeline:
```
cat input.txt | docker run -i --rm mtaril/emtsv tok,morph,pos,compound > compound_output.tsv
```
Or together with emPreverb:
```
cat input.txt | docker run -i --rm mtaril/emtsv tok,morph,pos,compound,preverb > prev_output.tsv
```

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
