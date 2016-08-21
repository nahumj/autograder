"""
Script to create repos and teams.
See http://github3py.readthedocs.io/ for docs.
"""
from os import path
import re
from github3 import login

TEAM_SUFFIX = "-team"
REPO_SUFFIX = "-repo"
ORGANIZATION_NAME = "CSE220-MSU"
STUDENT_USERNAMES = {"nahumj", "nahum-test"}

def get_org(org_name):
    with open(path.expanduser("~/.github_token"), "r") as handle:
        token = handle.read().strip()

    gh = login(token=token)
    return gh.organization(org_name)

def create_repos_and_teams(org, usernames):
    print("Creating")
    new_usernames = set(usernames)
    for team in org.teams():
        if team.name in usernames:
            new_usernames.remove(team.name)
    print(new_usernames)
    for new_username in new_usernames:
        team = org.create_team(new_username + TEAM_SUFFIX, permission="push")
        team.invite(new_username)
        org.create_repository(new_username + REPO_SUFFIX,
            private=True, has_issues=False, has_wiki=False, team_id=team.id)

def delete_repos_and_teams(org):
    print("Deleting")
    for repo in org.repositories():
        if REPO_SUFFIX in repo.name:
            repo.delete()
    for team in org.teams():
        if TEAM_SUFFIX in team.name:
            team.delete()

def print_repos_and_teams(org):
    for team in org.teams():
        print("TEAM: {}".format(team.name))
    for repo in org.repositories():
        print("REPO: {}".format(repo.name))

def add_instructors_to_every_repo(org):
    for team in org.teams():
        if team.name == "Instructors":
            instructor_team = team
            break
    else:
        instructor_team = org.create_team("Instructors", permission="admin")
    for repo in org.repositories():
        instructor_team.add_repository(repo)
    instructor_team.edit(instructor_team.name, permission="admin")


if __name__ == "__main__":
    org = get_org(ORGANIZATION_NAME)
    print_repos_and_teams(org)
    add_instructors_to_every_repo(org)
    #create_repos_and_teams(org, STUDENT_USERNAMES)
    #print_repos_and_teams(org)
    #delete_repos_and_teams(org)
    #print_repos_and_teams(org)
