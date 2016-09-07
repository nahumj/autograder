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
        hackerrank_row = {"Email":email, "Name":name}
        hackerrank_writer.writerow(hackerrank_row)

def convert_to_lab_list(class_list_filename, lab_list_filename):
    reader = csv.DictReader(open(class_list_filename, 'r'))
    fieldnames = ["Username", "Assignment Points Grade", "First_Names", "Last_Name", "End-of-Line Indicator"]
    writer = csv.DictWriter(
        open(lab_list_filename, 'w'), fieldnames)
    writer.writeheader()
    for input_row in reader:
        row = {}
        row["Username"] = input_row["MSUNet_ID"]
        comma_name = input_row["Student_Name"]
        last_name, comma, first_name = comma_name.partition(", ")
        row["First_Names"] = first_name
        row["Last_Name"] = last_name
        row["End-of-Line Indicator"] = '#'
        writer.writerow(row)

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

    #convert_to_lab_list(args.class_list_filename, "cse220_lab.csv")
if __name__ == "__main__":
    main()
