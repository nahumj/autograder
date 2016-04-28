from os import path

from github3 import login

with open(path.expanduser("~/.github_token"), "r") as handle:
    token = handle.read().strip()

#g = Github(token)
#o = g.get_organization("ZOOL851-MSU")
#print([repo.name for repo in o.get_repos()])

gh = login(token=token)
org = gh.organization("ZOOL851-MSU")

teams = list(org.teams())
for team in teams:
    print(team.as_dict())
