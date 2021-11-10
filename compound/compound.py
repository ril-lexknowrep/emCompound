#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""
An emtsv module to extract compound boundaries using morph and pos output.
"""

from collections import defaultdict
import json
import regex
from word import Word


BOUNDARY_REGEX = r"\+\w+\[/"
PREVERB_POSTAG = '[/Prev]'
VERB_POSTAG = '[/V]'
SUPERLATIVE_POSTAG = '[/Supl]'
ROMAN_NUMBER_POSTAG = 'Roman'
ARABIC_NUMBER_POSTAG = 'Digit'


class Compound:
    '''Required by xtsv.'''

    def __init__(self, *_, source_fields=None, target_fields=None):
        """
        Required by xtsv.
        Initialise the module.
        """
        # Tudom, hogy ezeket elvileg a source_fields és a target_fields
        # adná át, de nem látom be, hogy miért kellene fájlok között ugrálnom,
        # hogy megtudjam, mik a használt mezők, ezért csak azért is így
        # inicializálom őket.
        self.source_fields = {'anas', 'xpostag'}
        self.target_fields = ['compound']
        self.false_dict = load_non_compounds('non_compounds.txt')

    def process_sentence(self, sen, _):
        """
        Required by xtsv.
        Process one sentence per function call.
        :return: sen object augmented with output field values for each token
        """
        for tok in sen:
            wd = Word(tok)

            # Handle verbs with preverbs
            if PREVERB_POSTAG in wd.anas and VERB_POSTAG in wd.xpostag:
                for ana in json.loads(wd.anas):
                    if ana["lemma"] == wd.lemma and ana["tag"] == wd.xpostag:
                        last_good_ana = ana
                if PREVERB_POSTAG in last_good_ana['morphana']:
                    preverb = last_good_ana['readable'].split(' + ')[0].\
                                    replace(PREVERB_POSTAG, '')
                    tok.append(wd.lemma.replace(preverb, preverb + '#', 1))
                else:
                    tok.append(wd.lemma)

            # TODO: áttenni a connec_prev-ből ide a '[/Prev]' címke beszúrását
            # az xpostag mezőbe. A nem igei igekötős összetételeknél
            # (ki#adás, haza#vonuló) lentebb ez már megtörténik.
            # A connect_prev-ben most nem tudom/akarom megcsinálni a
            # folyamatban lévő PR-ek miatt.

            # Handle other potential compounds
            elif (regex.search(BOUNDARY_REGEX, wd.anas) and
                  ROMAN_NUMBER_POSTAG not in wd.xpostag and
                  ARABIC_NUMBER_POSTAG not in wd.xpostag):
                relevant_anas = []

                for ana in json.loads(wd.anas):
                    if (ana["lemma"] == wd.lemma
                        and ana["tag"] == wd.xpostag):
                        relevant_anas.append(ana)
                if not any(regex.search(BOUNDARY_REGEX, ana['morphana'])
                           for ana in relevant_anas):
                    tok.append(wd.lemma)
                    continue

                compound_analyses = []

                for ana in relevant_anas:
                    morphemes_raw = ana['morphana'].split("+")
                    morphemes = [regex.match(
                                   r"(?<mlemma>.*)(?<mtag>\[.+])=(?<mform>.*)",
                                   morph)
                                 for morph in morphemes_raw]
                    pos_lemma = wd.lemma
                    comp_lemma = ""
                    boundaries = set()

                    if (morphemes[0]['mtag'] == PREVERB_POSTAG
                      and not wd.xpostag.startswith(PREVERB_POSTAG)):
                        tok[self.xpostag_index] = PREVERB_POSTAG + wd.xpostag

                    previous_component = ''

                    for m in morphemes:
                        if m['mtag'] == SUPERLATIVE_POSTAG:
                            continue
                        if m['mtag'].startswith('[/') and comp_lemma != '':
                            if (previous_component == '' or
                                previous_component not in self.false_dict or
                                not any(pos_lemma.startswith(suffix)
                                    for suffix
                                    in self.false_dict[previous_component])
                               ):
                                boundaries.add(len(comp_lemma))
                                previous_component = ''

                        if len(m['mform']) > len(m['mlemma']):
                            try_forms = [m['mform'], m['mlemma']]
                        else:
                            try_forms = [m['mlemma'], m['mform']]
                        found_flag = False
                        for tf in try_forms:
                            if tf == '':
                                found_flag = True
                                break
                            if pos_lemma.startswith(tf):
                                comp_lemma += tf
                                previous_component += tf
                                pos_lemma = pos_lemma[len(tf):]
                                found_flag = True
                                break

                        if comp_lemma == wd.lemma:
                            break

                        if not found_flag:
                            comp_lemma += pos_lemma
                            break

                    add_flag = True

                    for comp_ana in compound_analyses:
                        if boundaries <= comp_ana['boundaries']:
                            add_flag = False
                            break
                        if comp_ana['boundaries'] < boundaries:
                            comp_ana['c_lemma'] = '#'.join(split_at(comp_lemma,
                                                    sorted(list(boundaries))))
                            comp_ana['boundaries'] = boundaries
                            add_flag = False

                    if add_flag:
                        compound_analyses.append(
                            {'c_lemma': '#'.join(split_at(comp_lemma,
                                                 sorted(list(boundaries)))),
                             'boundaries': boundaries})

                tok.append(', '.join([comp_ana['c_lemma']
                                      for comp_ana in compound_analyses]))

            # Handle non-compound
            else:
                tok.append(wd.lemma)

        return sen

    def prepare_fields(self, field_names):
        """
        Required by xtsv.
        :param field_names: the dictionary of the names of the input fields
        :return: the list of the initialised feature classes as required for
                process_sentence
        """
        input_column_count = len(field_names) // 2 - len(self.target_fields)
        input_fields = [field_names[i] for i in range(input_column_count)]
        Word.features = input_fields
        self.xpostag_index = field_names['xpostag']
        return input_fields


def load_non_compounds(file_name):
    '''Load list of false compound boundaries from file'''
    false_dict = defaultdict(list)

    with open(file_name, encoding='utf-8') as infile:
        for line in infile:
            pair = line.strip()
            if pair == '':
                continue
            prefix, suffix = pair.split('+')
            false_dict[prefix].append(suffix)

    return false_dict


def split_at(in_list, indices):
    '''Split in_list at indices into sublists'''

    if len(indices) == 0:
        return [in_list]

    if not (all(isinstance(x, int) for x in indices)
            and indices == sorted(list(set(indices)))):
        raise ValueError("Indices must be a sorted list of integers " +
                         "without duplicates")

    if indices[-1] >= len(in_list):
        raise IndexError(f"index beyond bounds: {indices[-1]}")

    return_list = []
    start_index = 0
    for end_index in indices:
        return_list.append(in_list[start_index:end_index])
        start_index = end_index
    return_list.append(in_list[start_index:])

    return return_list
