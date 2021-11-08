#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import json
from word import Word


class Compound:
    """
    An emtsv module to extract compound boundaries using morph and pos output.
    """

    def __init__(self, *_, source_fields=None, target_fields=None):
        """
        Initialise the module.
        """
        self.source_fields = {'anas', 'xpostag'}
        self.target_fields = ['compound']


    def process_sentence(self, sen, _):
        """
        Process one sentence per function call.
        :return: the sen object augmented with the output field values for each token
        """
        for tok in sen:
            wd = Word(tok)
            if "/Prev" in wd.anas and "/V" in wd.xpostag:
                anas_list = json.loads(wd.anas)
                for ana in anas_list:
                    if ana["lemma"] == wd.lemma and ana["tag"] == wd.xpostag:
                        last_good_ana = ana
                if '[/Prev]' in last_good_ana['readable']:
                    preverb = ana['readable'].split(' + ')[0].replace('[/Prev]','')
                    tok.append(wd.lemma.replace(preverb, preverb + '#', 1))
                else:
                    tok.append(wd.lemma)
            else:
                tok.append(wd.lemma)
        return sen

    def prepare_fields(self, field_names):
        """
        Required by xtsv. This function is called once before processing the input. It can be used to initialise field conversion classes
         to accomodate the current order of fields (eg. field to features)
        :param field_names: the dictionary of the names of the input fields mapped to their order in the input stream
        :return: the list of the initialised feature classes as required for process_sentence (in most cases the
         columnnumbers of the required field in the required order are sufficient
         eg. return [field_names['form'], field_names['lemma'], field_names['xpostag'], ...] )
        """
        input_column_count = len(field_names) // 2 - len(self.target_fields)
        input_fields = [field_names[i] for i in range(input_column_count)]
        Word.features = input_fields
        return input_fields
