#!/usr/bin/env python3
import argparse
import sys
import os
import io
import traceback
import subprocess

# Number of seconds before killing command
TEST_TIMEOUT = 2

class TestRunnerException(Exception):
    """
    Exception used to distinguish if the test runner failed.
    """
    pass


def get_project_output(test_file):
    """
    Converts the test_file (file handle) to the
    student's project output (string).
    """
    output = []
    contents = test_file.read()
    args = ["python3", "tube.py"]
    try:
        stdout = subprocess.check_output(args,
                                         stderr=subprocess.STDOUT,
                                         universal_newlines=True,
                                         input=contents,
                                         timeout=TEST_TIMEOUT)
        output.append(stdout)
    except subprocess.CalledProcessError as cpe:
        output = ["Non-Zero Return Code"]
    except subprocess.TimeoutExpired as te:
        output = ["TestRunner: Command took too long, killing it."]
    except Exception as e:
        output.append("Exception Raised!!!")
        output.append(traceback.format_exc())
    return "\n".join(output) + "\n"


def get_correct_output(test_file):
    """
    Converts the test_file (file handle) to correct output (string).
    """
    output = []
    test_filepath = test_file.name
    args = ["../ReferenceCode/project1_lexer", test_filepath]
    try:
        stdout = subprocess.check_output(args,
                                         stderr=subprocess.STDOUT,
                                         universal_newlines=True,
                                         timeout=TEST_TIMEOUT)
        output.append(stdout)
    except subprocess.CalledProcessError as cpe:
        output = ["Non-Zero Return Code"]
    except Exception as e:
        raise e
    return "\n".join(output) + "\n"


def get_input(test_file):
    """
    Returns the contents of the test.
    """
    return test_file.read()


def main():
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
    If given, outputs the project's output for a test.""")

    args = parser.parse_args()

    if args.correct:
        output = get_correct_output(args.test_file)
    elif args.input:
        output = get_input(args.test_file)
    else:
        output = get_project_output(args.test_file)
    args.output_file.write(output)


if __name__ == "__main__":
    main()
