import requests
import os.path
import pprint

with open(os.path.expanduser("~/.hackerrank_token")) as ht:
    token = ht.read().strip()
headers = {'Authorization': token}
base_url = 'https://www.hackerrank.com/x/api/v3'

test_url = "/tests"

r = requests.get(base_url + test_url, headers=headers)
assert r.status_code == 200
response = r.json()
#pprint.pprint(response)
tests = response['data']
id_names = {test["name"]: test["id"] for test in tests}
print(id_names)
test_name = "CSE480 Homework #6"
test_id = id_names[test_name]

test_results_url = "/tests/" + str(test_id) + "/candidates/"

r = requests.get(base_url + test_results_url, headers=headers)
response = r.json()
pprint.pprint(response)
completed = response['data']

example_assignment = completed[1]
email = example_assignment["email"]
print(email)
score_answer = [(q["score"], q["answer"]) for q in example_assignment["questions"]]

example_code = score_answer[0][1]
print(example_code)
