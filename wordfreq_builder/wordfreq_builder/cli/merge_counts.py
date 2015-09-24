from wordfreq_builder.word_counts import read_values, merge_counts, write_wordlist
import argparse


def merge_lists(input_names, output_name):
    count_dicts = []
    for input_name in input_names:
        values, total = read_values(input_name, cutoff=0)
        count_dicts.append(values)
    merged = merge_counts(count_dicts)
    write_wordlist(merged, output_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', help='filename to write the output to', default='combined-counts.csv')
    parser.add_argument('inputs', help='names of input files to merge', nargs='+')
    args = parser.parse_args()
    merge_lists(args.inputs, args.output)
