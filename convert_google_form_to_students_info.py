#!/usr/bin/env python3
"""
Converts the class list provided by MSU's Office of the Registrar to a format
that HackerRank can use to invite candidates.
"""
import csv
import argparse


def convert_form_to_student_info(
        form_csv,
        student_info_csv):
    reader = csv.DictReader(open(form_csv, 'r'))
    info_fieldnames = ["github_username", "msu_net_id", "full_name"]
    writer = csv.DictWriter(
        open(student_info_csv, 'w'), info_fieldnames)
    writer.writeheader()
    msu_net_id_to_row = {}
    for input_row in reader:
        msu_net_id = input_row["""MSU Net ID (without the "@msu.edu" part)"""]
        if "@" in msu_net_id:
            msu_net_id = msu_net_id.partition('@')[0]
        full_name = input_row["First name"] + " " + input_row["Last name"]
        github_username = input_row["GitHub Username"]

        row = {"github_username": github_username,
               "msu_net_id": msu_net_id,
               "full_name": full_name}
        msu_net_id_to_row[msu_net_id] = row
    for row in msu_net_id_to_row.values():
        writer.writerow(row)


def main():
    """
    Main function that parses the arguments and calls the convert function.
    """
    parser = argparse.ArgumentParser(description="""
    Converts the csv from Google Forms survey to students_info csv
    """)
    parser.add_argument('form_csv')
    parser.add_argument('student_info_csv')

    args = parser.parse_args()
    convert_form_to_student_info(args.form_csv,
                                 args.student_info_csv)

if __name__ == "__main__":
    main()
