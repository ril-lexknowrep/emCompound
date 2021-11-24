SHELL:=/bin/bash

all:
	@echo "choose explicit target = type 'make ' and press TAB"

S=compound
I=data
O=out

MODULE=compound

# ===== MAIN STUFF


FILE=11341_prev

INFILE=$I/$(FILE).tsv
OUTFILE=$O/$(FILE).compound


analyse_compounds:
	cat $(INFILE) | python3 $(MODULE) | sed "s/	$$/	./" > $(OUTFILE)
# using a sed hack for patch xtsv
# not to strip empty fields at the end of line

