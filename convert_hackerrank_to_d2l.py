#!/usr/bin/env python3
import csv
import argparse


def convert_hackerrank_to_d2l(hackerrank_csv, d2l_csv, assignment_name):
    hr_reader = csv.DictReader(open(hackerrank_csv, 'r'))
    grade_column = assignment_name + " Points Grade"
    d2l_fieldnames = header = ("Username",
              grade_column,
              "End-of-Line Indicator")
    d2l_writer = csv.DictWriter(open(d2l_csv, 'w'), fieldnames=d2l_fieldnames)
    d2l_writer.writeheader()

    for row in hr_reader:
        new_row = {}
        new_row["Username"] = row["Login ID"].split('@')[0]
        new_row[grade_column] = row["Total score"]
        new_row["End-of-Line Indicator"] = '#'
        d2l_writer.writerow(new_row)

def main():
    """
    Main function that parses the arguments and calls the convert function.
    """
    parser = argparse.ArgumentParser(description="""
    This is a short script to convert the csv test results that
    HackerRank provides to a form that D2L can import.""")
    parser.add_argument('HackerRank_csv_input_file')
    parser.add_argument('D2L_csv_output_file')
    parser.add_argument('assignment_name')

    args = parser.parse_args()
    convert_hackerrank_to_d2l(args.HackerRank_csv_input_file,
                                     args.D2L_csv_output_file,
                                     args.assignment_name)

if __name__ == "__main__":
    main()
