#!/usr/bin/env python3
"""
Script to create repos and teams.
See http://github3py.readthedocs.io/ for docs.
"""
from os import path
import re
from github3 import login
import csv
import argparse

TEAM_SUFFIX = "-team"
REPO_SUFFIX = "-repo"
ORGANIZATION_NAME = "CSE450-MSU"
INSTRUCTOR_BASE_REPO = "tube-main"

def get_org(org_name):
    with open(path.expanduser("~/.github_token"), "r") as handle:
        token = handle.read().strip()

    gh = login(token=token)
    return gh.organization(org_name)



def create_student_repos(org, usernames):
    print("Creating Repos")
    new_repo_names = {username + REPO_SUFFIX for username in usernames}
    for repo in org.iter_repos():
        if repo.name in new_repo_names:
            new_repo_names.remove(repo.name)
    print(new_repo_names)
    for new_repo_name in new_repo_names:
        org.create_repo(new_repo_name,
            private=True, has_issues=False, has_wiki=False)


def create_student_teams(org, usernames):
    print("Creating Teams")
    new_team_names = {username + TEAM_SUFFIX for username in usernames}
    for team in org.iter_teams():
        if team.name in new_team_names:
            new_team_names.remove(team.name)
    print(new_team_names)
    for new_team_name in new_team_names:
        team = org.create_team(new_team_name, permission="push")
        new_username = new_team_name[:-len(TEAM_SUFFIX)]
        team.invite(new_username)
        team.add_repo(ORGANIZATION_NAME + "/" + new_username + REPO_SUFFIX)

def create_or_add_to_all_student_team(org, rows):
    """
    Returns the rows with non-existent usernames.
    """
    for team in org.iter_teams():
        if team.name == "all-students":
            all_students_team = team
            break
    else:
        all_students_team = org.create_team("all-students", permission="pull")
    bad_rows = []
    for row in rows:
        username = row["github_username"]
        is_invited = all_students_team.invite(username)
        if not is_invited:
            bad_rows.append(row)
    for repo in org.iter_repos():
        if repo.name == INSTRUCTOR_BASE_REPO:
            base_repo = repo
            break
    else:
        print("Need to manually create instructor base repo named:" + INSTRUCTOR_BASE_REPO)
    all_students_team.add_repo(base_repo)
    return bad_rows

def delete_repos_and_teams(org):
    print("Deleting")
    for repo in org.iter_repos():
        if REPO_SUFFIX in repo.name:
            repo.delete()
    for team in org.iter_teams():
        if TEAM_SUFFIX in team.name:
            team.delete()

def print_repos_and_teams(org):
    for team in org.iter_teams():
        print("TEAM: {}".format(team.name))
    for repo in org.iter_repos():
        print("REPO: {}".format(repo.name))

def add_instructors_to_every_repo(org):
    for team in org.iter_teams():
        if team.name == "Instructors":
            instructor_team = team
            break
    else:
        instructor_team = org.create_team("Instructors", permission="admin")
    for repo in org.iter_repos():
        instructor_team.add_repo(repo)
    instructor_team.edit(instructor_team.name, permission="admin")

def load_github_usernames(student_info_csv):
    reader = csv.DictReader(open(student_info_csv, 'r'))
    rows = list(reader)
    return rows


def main():
    parser = argparse.ArgumentParser(description="""
    Script for making GitHub private repos for a class.
    Not for normal use (see nahumjos@msu.edu for instruction).
    """)
    parser.add_argument('student_info_csv')
    args = parser.parse_args()
    rows = load_github_usernames(args.student_info_csv)
    org = get_org(ORGANIZATION_NAME)

    bad_usernnames_rows = create_or_add_to_all_student_team(org, rows)
    all_usernames = {row["github_username"] for row in rows}
    bad_usernnames = {row["github_username"] for row in bad_usernnames_rows}
    print("Bad Username Rows:")
    for row in bad_usernnames_rows:
        print(row)
    print("Done with Bad Usernames")
    good_usernames = all_usernames - bad_usernnames
    create_student_repos(org, good_usernames)
    create_student_teams(org, good_usernames)
    add_instructors_to_every_repo(org)
    print_repos_and_teams(org)


if __name__ == "__main__":
    main()
