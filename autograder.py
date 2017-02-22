#!/usr/bin/env python3
"""
The purpose of this module is to facilitate the automated grading of
student projects hosted on GitHub.
"""
import csv
import collections
import argparse
import contextlib
import subprocess
import os
import datetime
import sys
import multiprocessing

TEST_SCRIPT_NAME = "run_tests.py"
IN_TESTED_DIR_NEEDS = ["Test_Suite", TEST_SCRIPT_NAME,
                       "run_single_test.py", "cli.py"]
REPO_SUFFIX = "database"
BASE_REPO_NAME = "instructor-database"
GITHUB_ORG = "CSE480-MSU"
LATE_DAY_PENALTY = 1.0
NUM_POOL_WORKERS = 20
MULTI_ALLOWED = True
INSTRUCTOR_EMAIL = "nahumjos@cse.msu.edu"
PULL_CHANGES_FOR_BASE_REPO = False

Student = collections.namedtuple('Student',
                                 ['github_username',
                                  'msu_net_id',
                                  'full_name'])


class AutograderError(Exception):
    pass


def get_students_from_file(csv_handle):
    with contextlib.closing(csv_handle):
        reader = csv.reader(csv_handle, strict=True)
        header = next(reader)
        assert tuple(header) == Student._fields
        return list(map(Student._make, reader))


def clone_repos_from_github(students, repo_dir):
    print("Cloning Student Repos into: {}".format(repo_dir))
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)
    for student in students:
        clone_url = convert_student_to_clone_url(student)
        stu_repo_path = get_repo_dir(student, repo_dir)
        if not os.path.exists(stu_repo_path):
            print("Cloning: {}".format(stu_repo_path))
            subprocess.check_call(['git', 'clone', clone_url], cwd=repo_dir)
        else:
            print("Skipping {} already exists".format(stu_repo_path))


def get_repo_dir(student, repo_dir):
    repo_name = get_repo_name(student)
    return os.path.join(repo_dir, repo_name)


def run_command_on_repos(command, students, repo_dir):
    print("Running command on repos: {}".format(" ".join(command)))
    pool = multiprocessing.Pool(NUM_POOL_WORKERS)
    args = [(command, student, repo_dir) for student in students]
    pool.map(run_command_on_repo, args)


def run_command_on_repo(arg):
    command, student, repo_dir = arg
    stu_repo_path = get_repo_dir(student, repo_dir)
    try:
        subprocess.check_output(command,
                                cwd=stu_repo_path,
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        print("Problem with repo: " + stu_repo_path)
        raise cpe


def run_arbitary_command_on_repos(students, repo_dir, command_str):
    print("Running arbitary command on repos: '{}'".format(command_str))
    for student in students:
        stu_repo_path = get_repo_dir(student, repo_dir)
        try:
            subprocess.check_output(command_str,
                                    shell=True,
                                    cwd=stu_repo_path,
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as cpe:
            print("Problem with repo: " + stu_repo_path)
            raise cpe


def pull_repos(students, repo_dir):
    clean_repos(students, repo_dir)
    run_command_on_repos(['git', 'fetch', 'origin', 'master'],
                         students, repo_dir)
    run_command_on_repos(['git', 'checkout', 'origin/master'],
                         students, repo_dir)


def checkout_repos(students, repo_dir, tag_name):
    clean_repos(students, repo_dir)
    run_command_on_repos(['git', 'checkout', tag_name], students, repo_dir)


def clean_repos(students, repos_dir):
    commands = [['git', 'clean', '-f', '-d', '-x'],
                ['git', 'reset', '--hard']]
    for command in commands:
        run_command_on_repos(command, students, repos_dir)


def tag_repos(students, repo_dir, tag_name):
    now = datetime.datetime.now()
    tag_message = ("Instructor tag for tracking progress. "
                   "Current time: {}".format(now))

    create_tag = ['git', 'tag', '-f', '-a', tag_name, '-m', tag_message]
    try:
        run_command_on_repos(create_tag, students, repo_dir)
    except subprocess.CalledProcessError as cpe:
        print("Error: Likely duplicating tag names")
        exit(1)
    """
    push_tag = ['git', 'push', 'origin', tag_name]
    try:
        run_command_on_repos(push_tag, students, repo_dir)
    except subprocess.CalledProcessError as cpe:
        print("Error: Likely that tag is already in remote repo")
        exit(1)
    """


def send_email(subject_line, csv_file):
    def send_single_email(address, subject_line, body, attachment=None):
        command = ['mutt',
                   '-e',
                   '""set from=do-not-reply@cse.msu.edu""',
                   '-s',
                   subject_line]
        if attachment is not None:
            command += ["-a", attachment]
        command += ["--", address]

        with subprocess.Popen(command,
                              stdin=subprocess.PIPE,
                              universal_newlines=True) as proc:
            proc.communicate(body)

    def send_email_to_student(student_test_to_score, subject_line):
        msu_id = get_value_from_data_list("MSU_Net_ID", student)
        commit_id = get_value_from_data_list("Commit", student)
        late_penalty = get_value_from_data_list("Late_Penalty", student)
        if late_penalty is None:
            late_penalty = 0
        raw_grade = get_value_from_data_list("grade", student)
        late_grade = get_late_grade(student)
        address = msu_id + "@msu.edu"

        lines = ["""
Results from grading commit id: {}
Current grade is: {}
Late penalty is: {}
Grade (not taking possible late penalty into account) is: {}

Raw Data (consult run_tests.py for details)
1 is a pass, 0 is a fail""".format(commit_id,
                                   late_grade,
                                   late_penalty,
                                   raw_grade)]
        for test, score in student:
            lines.append("{} <- {}".format(score, test))
        body = "\n".join(lines)

        send_single_email(address, subject_line, body)

    students_data_list = get_students_data_list(csv_file)
    for student in students_data_list:
        send_email_to_student(student, subject_line)
    send_single_email(INSTRUCTOR_EMAIL,
                      "Grades Sent: " + subject_line,
                      "Number Sent: {}".format(
                        len(students_data_list)),
                      attachment=csv_file)


def get_late_grade(data_list):
    late_penalty = get_value_from_data_list("Late_Penalty", data_list)
    if late_penalty is None:
        late_penalty = 0
    raw_grade = get_value_from_data_list("grade", data_list)
    return float(raw_grade) - float(late_penalty)


def get_value_from_data_list(key, data_list):
    for possible_key, value in data_list:
        if possible_key == key:
            return value
    return None


def get_students_data_list(csv_file):
    with open(csv_file, 'r') as csv_handle:
        reader = csv.reader(csv_handle)
        lines = []
        for line in reader:
            lines.append(line)
        header = lines[0]
        data = lines[1:]
        return [list(zip(header, row)) for row in data]


def convert_student_to_clone_url(student):
    repo_name = get_repo_name(student)
    return "git@github.com:{}/{}.git".format(GITHUB_ORG, repo_name)


def get_repo_name(student):
    return "{}-{}".format(student.msu_net_id, REPO_SUFFIX)


StudentRepoResults = collections.namedtuple(
    "StudentRepoResults",
    ['student', 'test_to_scores', 'git_commit_id'])


def copy_test_files(student_repo, grade_directory, base_repo_path):
    """
    Copies the files needed for testing into the repo.
    The files are copied from base repo.
    This is to ensure that the students can't modify the tests.
    """
    stu_tested_dir = os.path.join(student_repo, grade_directory)
    base_tested_dir = os.path.join(base_repo_path, grade_directory)

    source_dest = []
    if not os.path.exists(stu_tested_dir):
        os.makedirs(stu_tested_dir)
    for path in IN_TESTED_DIR_NEEDS:
        base_path = os.path.join(base_tested_dir, path)
        stu_path = os.path.join(stu_tested_dir, path)
        source_dest.append((base_path, stu_path))
    for source, dest in source_dest:
        try:
            subprocess.check_output(['rm', '-r', dest],
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as cpe:
            pass
        subprocess.check_output(['cp', '-rf', source, dest])


def get_test_results(arg):
    def get_commit_id(test_dir):
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=test_dir, universal_newlines=True)[:7]

    student, repos_dir, grade_directory, base_repo_path = arg
    stu_repo_path = get_repo_dir(student, repos_dir)
    test_dir = os.path.join(stu_repo_path, grade_directory)

    print("Grading Dir: {}".format(test_dir))
    sys.stdout.flush()
    copy_test_files(stu_repo_path, grade_directory, base_repo_path)

    git_commit_id = get_commit_id(test_dir)

    output_str = subprocess.check_output(
        ["./run_tests.py", "--run-machine-mode"],
        cwd=test_dir,
        universal_newlines=True)
    lines = output_str.split("\n")
    if not lines[-1]:
        del lines[-1]
    elements = map(lambda line: line.split(','), lines)
    test_to_scores = list(map(
        lambda pair: (pair[0], float(pair[1])),
        elements))
    return StudentRepoResults(student, test_to_scores, git_commit_id)


def grade_repos(students, repos_dir, base_repo_dir,
                grade_directory, tag_name, late_penalty):
    all_readme_file = "all_readmes.txt"
    base_repo_path = os.path.join(base_repo_dir, BASE_REPO_NAME)
    if PULL_CHANGES_FOR_BASE_REPO:
        print("pulling changes to base repository")
        subprocess.check_output(['git', 'pull', 'origin', 'master'],
                                cwd=base_repo_path)
        subprocess.check_output(['git', 'checkout', '-f', 'origin/master'],
                                cwd=base_repo_path)

    def check_all_tests_run(list_of_student_repo_results):
        all_tests = []
        for student_repo_results in list_of_student_repo_results:
            tests, scores = list(zip(*student_repo_results.test_to_scores))
            if not all_tests:
                all_tests = tests
            if all_tests != tests:
                raise AutograderError(
                    "Discovered tests don't match other students")

    def get_student_scores():
        pool = multiprocessing.Pool(NUM_POOL_WORKERS)

        args = [(student, repos_dir, grade_directory, base_repo_path)
                for student in students]
        if MULTI_ALLOWED:
            list_of_student_repo_results = list(
                pool.map(get_test_results, args))
        else:
            list_of_student_repo_results = [get_test_results(arg)
                                            for arg in args]
        check_all_tests_run(list_of_student_repo_results)
        return list_of_student_repo_results

    def split_tests_scores(student_repo_results):
        tests, scores = list(zip(*student_repo_results.test_to_scores))
        return tests, scores

    def write_to_csv(list_of_student_repo_results, grades_file, late_penalty):
        assert list_of_student_repo_results
        tests, _ = split_tests_scores(list_of_student_repo_results[0])
        header = ["MSU_Net_ID", "GitHub_Username", "Full_Name", "Commit",
                  "Late_Penalty"] + list(tests)
        rows = []
        for student_repo_results in list_of_student_repo_results:
            student = student_repo_results.student
            _, scores = split_tests_scores(student_repo_results)
            row = [student.msu_net_id, student.github_username,
                   student.full_name, student_repo_results.git_commit_id,
                   late_penalty] + list(scores)
            rows.append(row)
        rows.sort()
        with open(grades_file, 'w') as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

    def collect_readmes(all_readme_file):
        def get_readme_contents(student):
            stu_repo_path = get_repo_dir(student, repos_dir)
            test_dir = os.path.join(stu_repo_path, grade_directory)
            print("collecting README from {}".format(stu_repo_path))
            contents = ['', "=" * 40, str(student)]
            readme_path = os.path.join(test_dir, "README")
            if not os.path.exists(readme_path):
                readme_path = os.path.join(test_dir, "README.txt")
            if not os.path.exists(readme_path):
                contents.append("no README found")
                return contents
            with open(readme_path, 'rb') as readme_handle:
                file_contents = readme_handle.read().decode('ascii', 'ignore')
                contents.append(file_contents)
            return contents

        contents = [get_readme_contents(student) for student in students]
        with open(all_readme_file, 'w') as all_readme_handle:
            for content in contents:
                all_readme_handle.write("\n".join(content))

    checkout_repos(students, repos_dir, tag_name)

    list_of_student_repo_results = get_student_scores()
    grades_file = "grades_for_{}.csv".format(tag_name)
    write_to_csv(list_of_student_repo_results, grades_file, late_penalty)
    all_readme_file = "all_README_for_{}.txt".format(tag_name)
    collect_readmes(all_readme_file)


def merge_grades(old_master_csv, revisions_csv):
    def convert_to_names_to_scores(records):
        result = {}
        for student_scores in records:
            name = get_value_from_data_list("MSU_Net_ID", student_scores)
            result[name] = student_scores
        return result

    def write_to_file(records, file_name, header):
        records.sort()
        with open(file_name, 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(header)
            for record in records:
                data = [val for col, val in record]
                writer.writerow(data)

    def get_header(records):
        if not records:
            raise AutograderError("Can't write csv file with no grades. "
                                  "Bad csv files")
        row = records[0]
        return [col for col, val in row]

    old_master_grades = get_students_data_list(old_master_csv)
    revisions_grades = get_students_data_list(revisions_csv)
    old_master_name_to_scores = convert_to_names_to_scores(old_master_grades)
    revisions_name_to_scores = convert_to_names_to_scores(revisions_grades)

    new_master_grades = []
    improved_grades = []
    for name, scores in old_master_name_to_scores.items():
        new_scores = scores
        old_grade = get_late_grade(scores)
        if name in revisions_name_to_scores:
            new_grade = get_late_grade(revisions_name_to_scores[name])
            if new_grade >= old_grade:
                new_scores = revisions_name_to_scores[name]
                improved_grades.append(new_scores)
        new_master_grades.append(new_scores)

    header = get_header(new_master_grades)
    write_to_file(new_master_grades, "grades_master.csv", header)
    write_to_file(improved_grades, "grades_improved.csv", header)


def convert_to_D2L(csv_file, assignment_name):
    def get_rows(csv_file):
        rows = []
        with open(csv_file, 'r') as csv_handle:
            reader = csv.DictReader(csv_handle)
            for row in reader:
                username = row["MSU_Net_ID"]
                grade = float(row["grade"]) - float(row["Late_Penalty"])
                rows.append((username, grade, '#'))
        return rows
    rows = get_rows(csv_file)
    header = ("Username",
              assignment_name + " Points Grade",
              "End-of-Line Indicator")
    with open("{}_D2L.csv".format(assignment_name), 'w') as csv_handle:
        writer = csv.writer(csv_handle)
        writer.writerow(header)
        writer.writerows(rows)


def get_cmd_args():
    parser = argparse.ArgumentParser(description="""
Autograder for CSE450 (Translation of Programming Languages)""")
    config = parser.add_argument_group('configuration')
    config.add_argument('--student-repos', default="student_repos/",
                        help="""
Path to the directory containing the student github repositories.
Defaults to "./student_repos".""")
    config.add_argument('--students',
                        type=argparse.FileType('r'),
                        default="students.csv",
                        help="""
Path to the csv file contain the students info (Github usernames, ...).""")
    config.add_argument('--base_repo',
                        metavar="PATH_TO_BASE_CONTAINING_DIR_REPO",
                        default=".", help="""
Path to base repo (tube-main for CSE 450) containing folder.
Defaults to current directory.""")

    subparsers = parser.add_subparsers(dest='command', help='commands')

    subparsers.add_parser("pull", help="""
Fetches student repos and checks out origin/master.""")

    checkout = subparsers.add_parser("checkout", help="""
Check out a git reference (tag) in every repo.""")
    checkout.add_argument("tag_name")

    tag = subparsers.add_parser("tag", help="""
Tags HEAD commit.""")
    tag.add_argument("tag_name")

    subparsers.add_parser("clone", help="""Clone repos from Github.""")

    grade = subparsers.add_parser("grade", help="""
Grades student repos at an associated tag..
Stores the tests results (and grade if run_tests knows how) to "grades.csv".
Concatinates READMEs to "all_readmes.txt".""")
    grade.add_argument('grade_directory', metavar="DIRECTORY_TO_GRADE", help="""
Grade the specified directory.""")
    grade.add_argument('tag_name', metavar="TAG_TO_GRADE", help="""
Tag that should be checked out for grading.""")
    grade.add_argument('late_penalty', default=0.0, type=float, help="""
Late penalty to be applied, defaults to 0.""")

    send_email = subparsers.add_parser("send-email", help="""
Email students their grades.""")
    send_email.add_argument('subject_line', help="Email Subject Line")
    send_email.add_argument('csv_file',
                            help="CSV file from which to email students")

    merge_grades = subparsers.add_parser("merge-grades", help="""
Combine two csv files (master and revisions)
to a new master ("grades_master.csv")
with grades that were improved from master
(taking into account late penalty).
Also writes a new csv file ("grades_improved.csv") of the
grades that were better in the revision
""")
    merge_grades.add_argument('old_master_csv', help="Master csv file")
    merge_grades.add_argument('revisions_csv', help="Revisions csv file")

    convert_to_D2L = subparsers.add_parser("convert-to-D2L", help="""
Converts a csv file containing the test results for a project to a csv that
Desire2Learn can import.
""")
    convert_to_D2L.add_argument('csv_file', help="File to convert")
    convert_to_D2L.add_argument('grade_item_name',
                                help="D2L name for assignment")

    command = subparsers.add_parser("command",
                                    help="""Run command on every repo.""")
    command.add_argument('given_command')

    return parser.parse_args()


def main():
    args = get_cmd_args()
    students = get_students_from_file(args.students)
    if args.command == "clone":
        clone_repos_from_github(students, args.student_repos)
    elif args.command == "pull":
        pull_repos(students, args.student_repos)
    elif args.command == "tag":
        tag_repos(students, args.student_repos, args.tag_name)
    elif args.command == "grade":
        grade_repos(students,
                    args.student_repos,
                    args.base_repo,
                    args.grade_directory,
                    args.tag_name,
                    args.late_penalty)
    elif args.command == "send-email":
        send_email(args.subject_line, args.csv_file)
    elif args.command == "checkout":
        checkout_repos(students, args.student_repos, args.tag_name)
    elif args.command == "merge-grades":
        merge_grades(args.old_master_csv, args.revisions_csv)
    elif args.command == "convert-to-D2L":
        convert_to_D2L(args.csv_file, args.grade_item_name)
    elif args.command == "command":
        run_arbitary_command_on_repos(students,
                                      args.student_repos,
                                      args.given_command)
    else:
        print("command not found")
        exit(1)


if __name__ == "__main__":
    main()
