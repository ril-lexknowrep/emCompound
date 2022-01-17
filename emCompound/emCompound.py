#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""
An emtsv module to extract compound boundaries using morph and pos output.
"""

import os
from collections import defaultdict
import json
import regex

from types import SimpleNamespace


BOUNDARY_REGEX = r"\+\w+\[/"
PREVERB_POSTAG = '[/Prev]'
VERB_POSTAG = '[/V]'
SUPERLATIVE_POSTAG = '[/Supl]'
ROMAN_NUMBER_POSTAG = 'Roman'
ARABIC_NUMBER_POSTAG = 'Digit'


class Word(SimpleNamespace):
    """
    Convenience class to access predefined word features as attributes.
    Set Word.features = ... before using this class!
    The class is iterable, so a list of all feature values can be accessed
    by calling list(w) on an object w of class Word.
    """

    features = []

    def __init__(self, vals):
        if len(vals) != len(self.features):
            raise RuntimeError(
                f"{len(self.features)} values expected, {len(vals)} provided:\n"
                + "Features: " + str(self.features) + "\n"
                + "Values: " + str(vals))
        super().__init__(**dict(zip(self.features, vals)))

#    def as_list(self): # XXX best practice? can I define list(...) for this class?
#        return self.__dict__.values()
#
#   a list(...) definiálása úgy történik, hogy iterálhatóként definiáljuk az
#   osztályt, ehhez az __iter__ és a __next__ metódust kell implementálni.
#   Ha ez megtörtént, akkor már hívható a wd = Word(tok) objektumra a list(wd),
#   ami a kívánt eredményt adja.
#   Azt viszont nem tudom, hogy ez-e a helyes, pythonic gyakorlat. Mindenesetre
#   szerintem se rosszabb, mint az as_list metódus.
#   Ettől függetlenül az as_list implementációja (vagy a neve) így nem szerencsés,
#   mert a values() metódus nem listát ad vissza. Ahhoz, hogy lista legyen, az
#   kellene, hogy return list(self.__dict__.values())

    def __iter__(self):
        self._iter_index = 0
        return self

    def __next__(self):
        if self._iter_index < len(self.features):
            return_value = self.__dict__[self.features[self._iter_index]]
            self._iter_index += 1
            return return_value
        else:
            raise StopIteration


class EmCompound:
    '''Required by xtsv.'''

    def __init__(self, *_, source_fields=None, target_fields=None):
        """
        Required by xtsv.
        Initialise the module.
        """

        # Field names for xtsv (the code below is mandatory for an xtsv module)
        if source_fields is None:
            source_fields = set()

        if target_fields is None:
            target_fields = []

        self.source_fields = source_fields
        self.target_fields = target_fields

        self.false_dict = load_non_compounds(os.path.dirname(__file__) +
                                             '/non_compounds.txt')
        self.cache = {}
        # TODO: cache kiírása munkamenet végén (__main__.py ?) és betöltése

    def process_sentence(self, sen, _):
        """
        Required by xtsv.
        Process one sentence per function call.
        :return: sen object augmented with output field values for each token
        """

        return_sen = list()

        for tok in sen:
            wd = Word(tok + [''] * len(self.target_fields))
            wd_pos = get_pos(wd.xpostag)

            # Retrieve from cache
            cached_data = self.cache.get(wd.lemma + wd_pos)
            if cached_data:
                boundary_lists, preverb_flag = cached_data

                # Mit kerestünk ki a cache-ből?
                # print("Cache:", wd.lemma + wd_pos, cached_data)
                if boundary_lists != [[]]:
                    cached_compounds = []
                    for boundaries in boundary_lists:
                        cached_compounds.append('#'.
                                         join(split_at(wd.lemma, boundaries)))
                    wd.compound = ', '.join(cached_compounds)
#                    if preverb_flag:
#                        tok[self.xpostag_index] = PREVERB_POSTAG + wd.xpostag
                else:
                    wd.compound = wd.lemma
                return_sen.append(list(wd))
                continue

            # Handle verbs with preverbs
            #
            if (PREVERB_POSTAG in wd.anas and VERB_POSTAG in wd.xpostag
                and VERB_POSTAG in wd.anas):
                for ana in json.loads(wd.anas):
                    if ana["lemma"] == wd.lemma and ana["tag"] == wd.xpostag:
                        last_good_ana = ana
                if PREVERB_POSTAG in last_good_ana['morphana']:
                    preverb = last_good_ana['readable'].split(' + ')[0].\
                                    replace(PREVERB_POSTAG, '')
                    boundaries = [len(preverb)]
                    wd.compound = '#'.join(split_at(wd.lemma, boundaries))
                    self.cache[wd.lemma + wd_pos] = ([boundaries], False)
                else:
                    wd.compound = wd.lemma
                    self.cache[wd.lemma + wd_pos] = ([[]], False)

            # Handle other potential compounds
            elif (regex.search(BOUNDARY_REGEX, wd.anas) and
                  ROMAN_NUMBER_POSTAG not in wd.xpostag and
                  ARABIC_NUMBER_POSTAG not in wd.xpostag):
                relevant_anas = []
                preverb_flag = False

                for ana in json.loads(wd.anas):
                    if (ana["lemma"] == wd.lemma
                        and ana["tag"] == wd.xpostag):
                        relevant_anas.append(ana)
                if not any(regex.search(BOUNDARY_REGEX, ana['morphana'])
                           for ana in relevant_anas):
                    wd.compound = wd.lemma
                    self.cache[wd.lemma + wd_pos] = ([[]], False)
                    return_sen.append(list(wd))
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

                    if morphemes[0]['mtag'] == PREVERB_POSTAG:
#                      and not wd.xpostag.startswith(PREVERB_POSTAG)):
#                        tok[self.xpostag_index] = PREVERB_POSTAG + wd.xpostag
                        preverb_flag = True

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
                            comp_ana['boundaries'] = boundaries
                            add_flag = False

                    if add_flag:
                        compound_analyses.append({'boundaries': boundaries})

                sorted_boundaries = [sorted(list(comp_ana['boundaries']))
                                     for comp_ana in compound_analyses]
                wd.compound = ', '.join(['#'.join(split_at(comp_lemma, sb))
                                      for sb in sorted_boundaries])
                self.cache[wd.lemma + wd_pos] =\
                                    (sorted_boundaries, preverb_flag)

            # Handle non-compounds
            else:
                wd.compound = wd.lemma
                # Úgy sejtem, ezeket nem érdemes cache-elni, mert idáig
                # gyorsan eljut a futás, de érdemes lehet tesztelni
                # a memória-sebesség tradeoffot nagy fájlokon, és
                # ha igen, akkor:
                # self.cache[wd.lemma + wd_pos] = ([[]], False)

            return_sen.append(list(wd))

        return return_sen

    def prepare_fields(self, field_names):
        """
        Required by xtsv.
        :param field_names: the dictionary of the names of the input fields
        :return: the list of the initialised feature classes as required for
                process_sentence
        """
        field_names = {k: v for k, v in field_names.items()
                                if isinstance(k, str)}
        Word.features = list(field_names.keys())
#        self.xpostag_index = field_names['xpostag']
        return field_names


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


def get_pos(postag):
    '''Extract the POS label from the xpostag attribute'''

    s = regex.search(f'\[/.+?]', postag)
    if s:
        return s[0]
    return ''


def split_at(in_list, indices):
    '''Split in_list at indices into sublists'''

    if len(indices) == 0:
        return [in_list]

    if not (all(isinstance(x, int) for x in indices)
            and indices == sorted(list(set(indices)))):
        raise ValueError("Indices must be a sorted list of integers " +
                         "without duplicates")

    if indices[-1] >= len(in_list):
        raise IndexError(f"index beyond bounds: {indices[-1]} in {in_list}")

    return_list = []
    start_index = 0
    for end_index in indices:
        return_list.append(in_list[start_index:end_index])
        start_index = end_index
    return_list.append(in_list[start_index:])

    return return_list
