from os import path
import re
from github3 import login

with open(path.expanduser("~/.github_token"), "r") as handle:
    token = handle.read().strip()

gh = login(token=token)
org = gh.organization("CSE450-MSU")


repos = list(org.repositories())
for repo in repos:
    #print(repo)
    att = repo.as_dict()
    name = att["name"]
    if re.search("\-tube", name):
        repo.delete()
    


