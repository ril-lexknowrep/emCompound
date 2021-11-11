#!/usr/bin/env python3

'''Run build_pipeline'''

from xtsv import build_pipeline, parser_skeleton, jnius_config


def main():
    '''Main'''

    argparser = parser_skeleton(
        description='compound - add compound boundaries to lemma')
    opts = argparser.parse_args()

    jnius_config.classpath_show_warning = opts.verbose

    # Set input and output iterators from command line args
    if opts.input_text is not None:
        input_data = opts.input_text
    else:
        input_data = opts.input_stream
    output_iterator = opts.output_stream

    used_tools = ['compound']
    presets = []

    compound = (
        'compound',  # module name
        'Compound',  # class
        'add compound boundaries to lemma',  # friendly name used in REST form
        (),  # args
        {
            'source_fields': {'anas', 'xpostag', 'lemma'},
            'target_fields': ['compound']
        }  # kwargs
    )
    tools = [
        (compound,  # config
            ('compound', 'emCompound')  # aliases
        )
    ]

    output_iterator.writelines(
        build_pipeline(
            input_data,
            used_tools,
            tools,
            presets,
            opts.conllu_comments
        )
    )


if __name__ == '__main__':
    main()
