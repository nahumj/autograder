#!/usr/bin/env python3
import sys
from zipfile import ZipFile
from glob import glob
import os.path
import subprocess
import shutil
import argparse


def unzip_directories(zipfilename):
    zipfile = ZipFile(zipfilename)
    working_dir = zipfilename + "_extracted"
    filenames = zipfile.namelist()
    final_filenames = [name for name in filenames if "FINAL.zip" in name]

    for name in final_filenames:
        zipfile.extract(name, path=working_dir)
    final_zipped_code = [os.path.join(working_dir, name)
                         for name in final_filenames]

    student_submissions = []
    for zipped_code in final_zipped_code:
        final_code = ZipFile(zipped_code)
        working_subdir = zipped_code + "_extracted"
        final_code.extractall(path=working_subdir)
        student_submissions.append(working_subdir)
    return student_submissions, working_dir


def submit_to_moss(student_submissions,
                   path_to_file_to_check,
                   unzipped_folder):
    files = [os.path.join(submission, path_to_file_to_check)
             for submission in student_submissions]
    files_that_exist = [file_ for file_ in files if os.path.exists(file_)]
    if not files_that_exist:
        print("Couldn't find any files at that path: ", path_to_file_to_check)
        exit(1)
    call_args = ["./moss", "-l", "python"] + files_that_exist
    subprocess.call(call_args)
    shutil.rmtree(unzipped_folder)


def main():
    parser = argparse.ArgumentParser(description="""
    This is a short script to extract out the final code
    submitted by a student from Mimir.
    """)
    parser.add_argument('zip_file')
    parser.add_argument('path_to_file_to_check')
    args = parser.parse_args()
    student_submissions, unzipped_folder = unzip_directories(args.zip_file)
    submit_to_moss(student_submissions,
                   args.path_to_file_to_check,
                   unzipped_folder)


if __name__ == "__main__":
    main()
