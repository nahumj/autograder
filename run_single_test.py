#!/usr/bin/env python3
"""
The purpose of this module is to run a single test associated
with a project.
"""

import argparse
import traceback
import os
import subprocess
import sys
import re

# Number of seconds before killing command
TEST_TIMEOUT = 2
PROJECT_EXECUTABLE = "cli.py"


def remove(filename):
    if os.path.exists(filename):
        os.remove(filename)


class TestRunnerException(Exception):
    """
    Exception used to distinguish if the test runner failed.
    """
    pass


def get_output_from_args(args, timeout):
    output = []
    try:
        stdout = subprocess.check_output(args,
                                         stderr=subprocess.STDOUT,
                                         universal_newlines=True,
                                         timeout=timeout)
        output.append(stdout)
    except subprocess.CalledProcessError as cpe:
        output.append("Non-Zero Return Code")
    except subprocess.TimeoutExpired as te:
        output.append("TestRunner: {} took too long, killing it.".format(
            args[0]))
    return output


def get_input(test_file):
    """
    Returns the contents of the test.
    """
    return test_file.read()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    Runs a single test.
    If no arguments (apart from the test filename) are given,
    it outputs your project's test output.
    """)
    parser.add_argument('test_file', type=argparse.FileType('r'),
                        help="The file containing the test contents.")
    parser.add_argument('output_file', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout, help="""The file to write the output of this program to.
If not given, outputs to stdout.""")
    parser.add_argument('--correct', action='store_true', help="""
    If given, outputs the correct output for a test.""")
    parser.add_argument('--input', action='store_true', help="""
If given, outputs the contents of the test.""")

    args = parser.parse_args()
    if args.input:
        output = args.test_file.read()
    elif args.correct:
        chars_to_remove = len("input.txt")
        correct_file_name = args.test_file.name[:-chars_to_remove]
        correct_file_name += "correct.txt"
        output = open(correct_file_name, 'r').read()
    else:
        executable_args = ["python3",
                           PROJECT_EXECUTABLE,
                           args.test_file.name,
                           "output.txt"]
        get_output_from_args(executable_args, TEST_TIMEOUT)
        output = open("output.txt", 'r').read()

    args.output_file.write(output)
    remove("output.txt")
