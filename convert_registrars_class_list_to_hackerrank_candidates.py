#!/usr/bin/env python3
"""
Converts the class list provided by MSU's Office of the Registrar to a format
that HackerRank can use to invite candidates.
"""
import csv
import argparse


def convert_class_list(
        class_list_filename,
        hackerrank_candidate_list_filename):
    reader = csv.DictReader(open(class_list_filename, 'r'))
    hackerrank_fieldnames = ["Email", "Name"]
    hackerrank_writer = csv.DictWriter(
        open(hackerrank_candidate_list_filename, 'w'), hackerrank_fieldnames)

    hackerrank_writer.writeheader()
    for input_row in reader:
        email = input_row["MSUNet_ID"] + "@msu.edu"
        comma_name = input_row["Student_Name"]
        last_name, comma, first_name = comma_name.partition(", ")
        name = first_name + " " + last_name
        hackerrank_row = {"Email": email, "Name": name}
        hackerrank_writer.writerow(hackerrank_row)


def main():
    """
    Main function that parses the arguments and calls the convert function.
    """
    parser = argparse.ArgumentParser(description="""
    Converts the class list provided by MSU's Office of the Registrar
    to a format that HackerRank can use to invite candidates.
    """)
    parser.add_argument('class_list_filename')
    parser.add_argument('hackerrank_candidate_list_filename')

    args = parser.parse_args()
    convert_class_list(args.class_list_filename,
                       args.hackerrank_candidate_list_filename)

if __name__ == "__main__":
    main()
