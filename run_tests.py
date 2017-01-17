#!/usr/bin/env python3
"""
The purpose of this module is to run the tests associated
with a project. The primary mechanism for doing so involves
calling run_single_test.py and collecting the information
returned.
"""

import argparse
import contextlib
import collections
import difflib
import fnmatch
import functools
import glob
import itertools
import os
import subprocess
import sys

# These global variables are unlikely to need to change
PROJECT_EXECUTABLE = "run_single_test.py"
TEST_SUITE_FOLDER = "Test_Suite"
TEST_FILES_TO_POINTS = collections.OrderedDict()
EXTRA_CREDIT_TEST_FILES_TO_POINTS = collections.OrderedDict([
    ("Test_Suite/extra.*", 1)
])
POINTS_FOR_PASSING_ALL = 1
POINTS_FILENAME = os.path.join(TEST_SUITE_FOLDER, "points.txt")
with open(POINTS_FILENAME, 'r') as file_handle:
    for line in file_handle:
        category, point_str = line.split()
        point_value = float(point_str)

        category_path = os.path.join(TEST_SUITE_FOLDER, category)
        TEST_FILES_TO_POINTS[category_path] = point_value

NEEDED_FILES_FILENAME = os.path.join(TEST_SUITE_FOLDER, "needed_files.txt")
with open(NEEDED_FILES_FILENAME, 'r') as file_handle:
    NEEDED_FILES = [line.strip() for line in file_handle]

# These Global Variables may need to be changed depending on the project
NEEDED_FILES_POINTS = 0.5

# Number of seconds to let each test run before calling it a fail.
# Make sure this is strictly larger than the timeout in run_single_test.py.
TEST_TIMEOUT = 20

# Struc that holds per test result
TestOutcome = collections.namedtuple('TestOutcome',
                                     ['file', 'passed', 'output'])


class TestResult(Exception):
    """
    Test results are raised as exceptions.
    """
    pass


class TestFailed(TestResult):
    """
    This is a Failed TestResult.
    """
    pass


class TestPassed(TestResult):
    """
    This is a Passed TestResult.
    """
    pass


class NoMatchingTestsFound(Exception):
    """
    This class is used to indicate no matching tests found.
    """
    pass


class InternalTestSuiteException(Exception):
    """
    This class is used to indicate a failure of
    the testing apparatus (not the student's code).
    """

    def __init__(self, message):
        super(InternalTestSuiteException, self).__init__(message)
        long_message = """
Test Suite or Script is broken:
{}
Contact instructors on Piazza so they can fix it (entirely their fault).
Please include this message and stack trace to assist debugging.
""".format(message)
        self.args = [long_message]


def calculate_grade(outcomes, print_output=True):
    """
    Takes an iterable of TestOutcomes and returns the points
    (and extra credit points) awarded. It also can print the tests outcomes.
    """

    def grade_category(file_token, test_to_passed, weight, proportional=False):
        """
        Takes a pattern (i.e. "test.initial.*"),
        a dictionary of test_names to if passed booleans,
        the weigth in points of the category,
        and if the points are proportional
        (in accordance with the number of tests passed)
        or not (all-or-nothing).
        """
        score = 0
        tests = []
        output = ["Grading tests '{}'.".format(file_token)]
        for test, passed in test_to_passed.items():
            if fnmatch.fnmatch(test, file_token):
                tests.append(passed)

        if not tests:
            raise NoMatchingTestsFound()

        if not proportional:
            if all(tests):
                score = weight
                output.append("All tests in category passed: "
                              "{0} of {1} points awarded.".format(
                                  score, weight))
            else:
                output.append("Not all tests in category passed: "
                              "{0} of {1} points awarded.".format(
                                  score, weight))
            return output, score

        number_of_passes = sum(tests)
        number_of_tests = len(tests)
        output.append("Passed {} of {} tests in category.".format(
            number_of_passes, number_of_tests))
        if number_of_tests >= 0:
            score = weight * (number_of_passes / number_of_tests)
        output.append("Proportional Score is: {} of {} points awarded.".format(
            score, weight))
        return output, score

    def get_output_score(test_to_passed, category_to_weight):
        """
        Returns the output and score for every test category.
        """
        output = []
        total = 0.0
        total_weight = 0.0
        for test_type, weight in category_to_weight.items():
            try:
                partial_output, partial_score = grade_category(
                    test_type, test_to_passed,
                    weight=weight, proportional=True)
                output += partial_output
                total += partial_score
                total_weight += weight
            except NoMatchingTestsFound:
                pass
        return output, total, total_weight

    def get_needed_files_score(test_to_passed):
        criteria_name = "Pre-test checks for needed files: "
        needed_file_score = 0.0
        if test_to_passed["has_needed_files"]:
            needed_file_score = NEEDED_FILES_POINTS
        output = [criteria_name + "{0} of {1} points".format(
            needed_file_score, NEEDED_FILES_POINTS)]
        return output, needed_file_score

    test_to_passed = {outcome.file: outcome.passed for outcome in outcomes}
    output = ["Grade Calculation (Provisional)"]
    total = 0.0

    needed_output, needed_score = get_needed_files_score(test_to_passed)
    output += needed_output
    total += needed_score

    test_output, test_score, total_weight = get_output_score(
        test_to_passed, TEST_FILES_TO_POINTS)

    if test_score == total_weight:
        points_for_passing_all_awarded = POINTS_FOR_PASSING_ALL
    else:
        points_for_passing_all_awarded = 0
    test_output.append(
        "Points for passing every test is: "
        "{} of {} points awarded.".format(
                points_for_passing_all_awarded, POINTS_FOR_PASSING_ALL))
    total += points_for_passing_all_awarded

    output += test_output
    total += test_score

    extra_output, extra_score, extra_weight = get_output_score(
        test_to_passed, EXTRA_CREDIT_TEST_FILES_TO_POINTS)
    if extra_output:
        output += ["", "Extra credit (not actually worth points):"]
        output += extra_output + [""]

    if print_output:
        print("\n".join(output))
        possible_points = NEEDED_FILES_POINTS + sum(
            TEST_FILES_TO_POINTS.values()) + POINTS_FOR_PASSING_ALL
        print("Current tentative grade is: {:.1f} of {:.1f}".format(
            total, possible_points))
    return total, extra_score


def check_needed_files():
    """
    Raise appropiate TestResult for if the NEEDED_FILES are present.
    """
    for filename in NEEDED_FILES:
        if not os.path.exists(filename):
            raise TestFailed([
                "Failed ('{}' file doesn't exist)".format(filename)])
    raise TestPassed(["Passed (has all required files)"])


def call_and_get_output(args, timeout=None):
    """
    Run command (and possible timeout), returning the output and returncode.
    If the command times out or raises an OSError (likely file not found),
    raise a TestFailed.
    """
    try:
        output = subprocess.check_output(args, stderr=subprocess.STDOUT,
                                         universal_newlines=True,
                                         timeout=timeout)
        returncode = 0
    except subprocess.CalledProcessError as cpe:
        output = cpe.output
        returncode = cpe.returncode
    except subprocess.TimeoutExpired as te:
        command_str = " ".join(args)
        output = ["""
        Command: {} took too long.
        Process took longer than {} seconds. Killing it.""".format(
            command_str, te.timeout),
            "Failed (execution took too long)"]
        raise TestFailed(output)
    except OSError as ose:
        output = ["Command: \"" + " ".join(args) + "\" raised OSError",
                  ose.strerror,
                  "Failed (couldn't run command {})".format(" ".join(args))]
        raise TestFailed(output)

    return output, returncode


def run_test(test_file_path):
    """
    Runs a given test file (uses PROJECT_EXECUTABLE),
    raises either TestPassed or TestFailed.
    """

    @contextlib.contextmanager
    def add_lines_to_TestResult(lines):
        """
        Captures TestResult exceptions and adds lines to them.
        """
        try:
            yield
        except TestResult as tr:
            tr.args = (lines + tr.args[0],)
            raise tr

    def run_executable(args):
        """
        Runs the PROJECT_EXECUTABLE to get the needed output.
        """
        test_path = args[0]
        base_command = ["./" + PROJECT_EXECUTABLE, test_path]
        project_command = base_command
        correct_command = base_command + ["--correct"]
        input_command = base_command + ["--input"]

        correct_stdout, correct_returncode = call_and_get_output(
            correct_command, timeout=TEST_TIMEOUT)
        if correct_returncode:
            raise InternalTestSuiteException("""
            Error raised by test runner generating correct output.
            Command: {}
            Output: {}
            """.format(correct_command, correct_stdout))
        project_stdout, project_returncode = call_and_get_output(
            project_command, timeout=TEST_TIMEOUT)
        input_stdout, _ = call_and_get_output(input_command)

        lines = ["Test Contents:", input_stdout]
        if project_returncode:
            lines += ["Failed (Executable returned a non-zero error code)"]
            raise TestFailed(lines)
        return lines, correct_stdout, project_stdout

    def run_diff(correct_stdout, project_stdout):
        """
        Raises appropiate TestResult according to diff of created files.
        """
        correct_output = correct_stdout.splitlines(True)
        project_output = project_stdout.splitlines(True)
        diff_lines = list(difflib.context_diff(correct_output, project_output,
                                               fromfile="Correct Output",
                                               tofile="Student Output",
                                               lineterm='\n'))
        if not diff_lines:
            raise TestPassed(["Passed"])
        else:
            lines = ["Diff Output:"]
            lines.append("".join(diff_lines))
            lines.append("Failed")
            raise TestFailed(lines)

    lines = ["Testing: " + test_file_path]
    with add_lines_to_TestResult(lines):
        more_lines, correct_output, project_output = run_executable(
            [test_file_path])
        lines += more_lines
        run_diff(correct_output, project_output)


def test_files_in_order(test_globs):
    """
    Generator for determining the order to run the test files.
    """
    for test_glob in test_globs:
        test_files = sorted(glob.glob(test_glob))
        for test_file in test_files:
            yield test_file


def get_test_result(test_file_path):
    """
    Runs the test file and returns if the test passed and what the output was.
    """
    try:
        run_test(test_file_path)
    except TestFailed as tf:
        passed = False
        output = tf.args[0]
    except TestPassed as tp:
        passed = True
        output = tp.args[0]
    else:
        message = "No TestResult Exception Raised On Test: {}".format(
            test_file_path)
        raise InternalTestSuiteException(message)
    return passed, output


def print_first_failure(outcomes):
    """
    Prints the first failed test's output.
    """
    try:
        first_failure = next(itertools.dropwhile(
            lambda outcome: outcome.passed, outcomes))
    except StopIteration as si:
        print("No Failures To Display!")
    else:
        print("\n".join(first_failure.output))


def run_tests(test_globs_to_points):
    """
    Runs the tests, and returns a list of TestOutcomes.
    """
    outcomes = []
    test_globs = test_globs_to_points.keys()
    for test_file_path in test_files_in_order(test_globs):
        passed, output = get_test_result(test_file_path)
        outcome = TestOutcome(test_file_path, passed, output)
        outcomes.append(outcome)
    return outcomes


def get_all_outcomes(tests, extra=None):
    """
    Generates a list of TestOutcomes from the tests and has_needed_files
    (including extra credit if provided).
    """
    all_outcomes = []

    check = try_to_outcome_wrapper("has_needed_files", check_needed_files)
    all_outcomes.append(check())

    all_outcomes.extend(run_tests(tests))
    if extra is not None:
        all_outcomes.extend(run_tests(extra))
    return all_outcomes


def try_to_outcome_wrapper(test_name, func):
    """
    Calls the provided function and generates a TestOutcome from the result.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except TestFailed as tf:
            return TestOutcome(test_name, False, tf.args[0])
        except TestPassed as tp:
            return TestOutcome(test_name, True, tp.args[0])
        raise InternalTestSuiteException(
            "Test Name = {} isn't passing or failing.")
    return wrapper


def check_for_uncommitted_work():
    """
    Runs a simple check for unstaged and uncommitted files.
    """
    unstaged_command = ["git", "diff", "--no-patch", "--exit-code"]
    uncommitted_command = ["git", "diff",
                           "--no-patch", "--staged", "--exit-code"]
    try:
        subprocess.check_call(unstaged_command)
        subprocess.check_call(uncommitted_command)
    except subprocess.CalledProcessError as cpe:
        print("Warning: You have uncommitted work. Run 'git status' for info.")
    unmerged_commits_command = ["git", "rev-list",
                                "master...origin/master", "--count"]
    output = subprocess.check_output(unmerged_commits_command)
    if int(output.strip()) != 0:
        print("Your current master branch doesn't match the "
              "origin/master branch.\n"
              "Be sure to use 'git push'.")


def machine_mode():
    """
    This function is called when --run-machine-mode is specified.
    The output is made to be parsed by the autograder.
    """
    outcomes = get_all_outcomes(
        TEST_FILES_TO_POINTS,
        EXTRA_CREDIT_TEST_FILES_TO_POINTS)

    lines = []
    for outcome in outcomes:
        file_basename = os.path.basename(outcome.file)
        passed = 1 if outcome.passed else 0
        lines.append("{}, {}".format(file_basename, passed))
    regular_grade, extra_grade = calculate_grade(outcomes, print_output=False)
    lines.append("{}, {}".format("grade", regular_grade))
    lines.append("{}, {}".format("extra_credit", extra_grade))
    print("\n".join(lines))


def normal_mode(args):
    """
    Default function that runs the tests and pretty outputs the test results,
    the grade, and the details regarding the first failure.
    """
    # check_for_uncommitted_work()
    print("Starting Tests")
    sys.stdout.flush()

    if args['extra']:
        outcomes = get_all_outcomes(
            TEST_FILES_TO_POINTS,
            EXTRA_CREDIT_TEST_FILES_TO_POINTS)
    else:
        outcomes = get_all_outcomes(TEST_FILES_TO_POINTS)

    def passed_all_tests(outcomes):
        return all(outcome.passed for outcome in outcomes)

    for outcome in outcomes:
        output = "{:<40} {}".format(outcome.file, outcome.output[-1])
        print(output)

    print()
    regular_grade, extra_grade = calculate_grade(outcomes, print_output=True)
    print()

    if passed_all_tests(outcomes):
        print("Passes all tests!")
        exit(0)
    else:
        print()
        print("First Failure's Details:")
        print_first_failure(outcomes)
        exit(1)


if __name__ == "__main__":
    """
    Runs the tests and chooses output mode.
    """

    parser = argparse.ArgumentParser(description="""
    Runs the tests for the project.
    By default it tests all files (indicated by the points.txt file)
    in the Test_Suite and shows detailed output for the first failure.
    """)
    parser.add_argument('--run-machine-mode', action="store_true", help="""
    Outputs the test result as 1's and 0's. For instructor use only.
    """)
    parser.add_argument('--extra', action="store_true", help="""
    Runs the extra credit tests and reports their results as well.
    """)

    args = vars(parser.parse_args())

    if args['run_machine_mode']:
        machine_mode()
    else:
        normal_mode(args)
