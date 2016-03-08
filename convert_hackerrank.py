#!/usr/bin/env python3
import csv
import argparse

def convert_hackerrank_to_autograder(input_file, output_file, number_of_questions):
        
    reader = csv.DictReader(open(input_file, 'r'))
    questions = ["Question {}".format(i) for i in range(1, number_of_questions + 1)]
    fieldnames = ["MSU_Net_ID", "GitHub_Username", "Full_Name", "Commit", "Late_Penalty","grade"]
    fieldnames += questions
    writer = csv.DictWriter(open(output_file, 'w'), fieldnames=fieldnames)
    writer.writeheader()
    
    for row in reader:
        new_row = {}
        new_row["MSU_Net_ID"] = row["Login ID"].split('@')[0]
        new_row["GitHub_Username"] = "NA"
        new_row["Full_Name"] = row["Full name"]
        new_row["Commit"] = "NA"
        new_row["Late_Penalty"] = 0.0
        grade = 0
        for question in questions:
            score = row[question]
            grade += float(score)
            new_row[question] = score
        grade /= 10.0
        new_row["grade"] = str(grade)
        writer.writerow(new_row)
            
    
    


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    parser.add_argument('number_of_questions')

    args = parser.parse_args()
    convert_hackerrank_to_autograder(args.input_file,
                                     args.output_file,
                                     int(args.number_of_questions))

if __name__ == "__main__":
    main()
