from wordfreq_builder.config import (
    CONFIG, data_filename, wordlist_filename, all_languages, source_names
)
import sys
import pathlib

HEADER = """# This file is automatically generated. Do not edit it.
# You can regenerate it using the 'wordfreq-build-deps' command.
"""
TMPDIR = data_filename('tmp')


def add_dep(lines, rule, input, output, extra=None, params=None):
    if isinstance(output, list):
        output = ' '.join(output)
    if isinstance(input, list):
        input = ' '.join(input)
    if extra:
        if isinstance(extra, list):
            extra = ' '.join(extra)
        extrastr = ' | ' + extra
    else:
        extrastr = ''
    build_rule = "build {output}: {rule} {input}{extra}".format(
        output=output, rule=rule, input=input, extra=extrastr
    )
    lines.append(build_rule)
    if params:
        for key, val in params.items():
            lines.append("  {key} = {val}".format(key=key, val=val))
    lines.append("")


def make_ninja_deps(rules_filename, out=sys.stdout):
    """
    Output a complete Ninja file describing how to build the wordfreq data.
    """
    print(HEADER, file=out)
    # Copy in the rules section
    with open(rules_filename, encoding='utf-8') as rulesfile:
        print(rulesfile.read(), file=out)

    lines = []
    # The first dependency is to make sure the build file is up to date.
    add_dep(lines, 'build_deps', 'rules.ninja', 'build.ninja',
            extra='wordfreq_builder/ninja.py')
    lines.extend(
        twitter_deps(
            data_filename('raw-input/twitter/all-2014.txt'),
            slice_prefix=data_filename('slices/twitter/tweets-2014'),
            combined_prefix=data_filename('generated/twitter/tweets-2014'),
            slices=40,
            languages=CONFIG['sources']['twitter']
        )
    )
    lines.extend(
        wikipedia_deps(
            data_filename('raw-input/wikipedia'),
            CONFIG['sources']['wikipedia']
        )
    )
    lines.extend(
        google_books_deps(
            data_filename('raw-input/google-books')
        )
    )
    lines.extend(
        leeds_deps(
            data_filename('source-lists/leeds'),
            CONFIG['sources']['leeds']
        )
    )
    lines.extend(
        opensubtitles_deps(
            data_filename('source-lists/opensubtitles'),
            CONFIG['sources']['opensubtitles']
        )
    )
    lines.extend(combine_lists(all_languages()))

    print('\n'.join(lines), file=out)


def wikipedia_deps(dirname_in, languages):
    lines = []
    path_in = pathlib.Path(dirname_in)
    for language in languages:
        # Find the most recent file for this language
        input_file = max(path_in.glob('{}wiki*.bz2'.format(language)))
        plain_text_file = wordlist_filename('wikipedia', language, 'txt')
        count_file = wordlist_filename('wikipedia', language, 'counts.txt')

        add_dep(lines, 'wiki2text', input_file, plain_text_file)
        if language == 'ja':
            mecab_token_file = wordlist_filename('wikipedia', language, 'mecab-tokens.txt')
            add_dep(lines, 'tokenize_japanese', plain_text_file, mecab_token_file)
            add_dep(lines, 'count', mecab_token_file, count_file, params={'lang': language})
        else:
            add_dep(lines, 'count', plain_text_file, count_file, params={'lang': language})

    return lines


def google_books_deps(dirname_in):
    # Get English data from the split-up files of the Google Syntactic N-grams
    # 2013 corpus.
    lines = []

    # Yes, the files are numbered 00 through 98 of 99. This is not an
    # off-by-one error. Not on my part, anyway.
    input_files = [
        '{}/nodes.{:>02d}-of-99.gz'.format(dirname_in, i)
        for i in range(99)
    ]
    output_file = wordlist_filename('google-books', 'en', 'counts.txt')
    add_dep(lines, 'convert_google_syntactic_ngrams', input_files, output_file)
    return lines


def twitter_deps(input_filename, slice_prefix, combined_prefix, slices, languages):

    lines = []

    slice_files = ['{prefix}.part{num:0>2d}'.format(prefix=slice_prefix, num=num)
                   for num in range(slices)]
    # split the input into slices
    add_dep(lines, 'split', input_filename, slice_files,
            params={'prefix': '{}.part'.format(slice_prefix), 'slices': slices})

    for slicenum in range(slices):
        slice_file = slice_files[slicenum]
        language_outputs = [
            '{prefix}.{lang}.txt'.format(prefix=slice_file, lang=language)
            for language in languages
        ]
        add_dep(lines, 'tokenize_twitter', slice_file, language_outputs,
                params={'prefix': slice_file})

    for language in languages:
        combined_output = wordlist_filename('twitter', language, 'tokens.txt')

        language_inputs = [
            '{prefix}.{lang}.txt'.format(prefix=slice_files[slicenum], lang=language)
            for slicenum in range(slices)
        ]

        add_dep(lines, 'cat', language_inputs, combined_output)

        count_file = wordlist_filename('twitter', language, 'counts.txt')

        if language == 'ja':
            mecab_token_file = wordlist_filename('twitter', language, 'mecab-tokens.txt')
            add_dep(lines, 'tokenize_japanese', combined_output, mecab_token_file)
            combined_output = mecab_token_file

        add_dep(lines, 'count', combined_output, count_file, extra='wordfreq_builder/tokenizers.py',
                params={'lang': language})

    return lines


def leeds_deps(dirname_in, languages):
    lines = []
    for language in languages:
        input_file = '{prefix}/internet-{lang}-forms.num'.format(
            prefix=dirname_in, lang=language
        )
        reformatted_file = wordlist_filename('leeds', language, 'counts.txt')
        add_dep(lines, 'convert_leeds', input_file, reformatted_file)

    return lines


def opensubtitles_deps(dirname_in, languages):
    lines = []
    for language in languages:
        input_file = '{prefix}/{lang}.txt'.format(
            prefix=dirname_in, lang=language
        )
        reformatted_file = wordlist_filename('opensubtitles', language, 'counts.txt')
        add_dep(lines, 'convert_opensubtitles', input_file, reformatted_file)

    return lines


def combine_lists(languages):
    lines = []
    for language in languages:
        sources = source_names(language)
        input_files = [
            wordlist_filename(source, language, 'counts.txt')
            for source in sources
        ]
        output_file = wordlist_filename('combined', language)
        add_dep(lines, 'merge', input_files, output_file,
                extra='wordfreq_builder/word_counts.py')

        output_cBpack = wordlist_filename('combined-dist', language, 'msgpack.gz')
        add_dep(lines, 'freqs2cB', output_file, output_cBpack,
                extra='wordfreq_builder/word_counts.py')

        lines.append('default {}'.format(output_cBpack))

        # Write standalone lists for Twitter frequency
        if language in CONFIG['sources']['twitter']:
            input_file = wordlist_filename('twitter', language, 'counts.txt')
            output_cBpack = wordlist_filename('twitter-dist', language, 'msgpack.gz')
            add_dep(lines, 'freqs2cB', input_file, output_cBpack,
                    extra='wordfreq_builder/word_counts.py')

            lines.append('default {}'.format(output_cBpack))

    return lines


def main():
    make_ninja_deps('rules.ninja')


if __name__ == '__main__':
    main()
