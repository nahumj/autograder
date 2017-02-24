import requests
import os.path



with open(os.path.expanduser("~/.hackerrank_token")) as ht:
    token = ht.read().strip()
base_url = 'https://www.hackerrank.com/x/api/v2'

test_url = "/tests"
payload = {'access_token': token}
r = requests.get(base_url + test_url, params=payload)
response = r.json()
tests = response['data']
id_names = [(test["id"], test["name"]) for test in tests]

example_id = 122432

test_results_url = "/tests/" + str(example_id) + "/candidates/"
payload = {'access_token': token}
r = requests.get(base_url + test_results_url, params=payload)
response = r.json()
completed = response['data']

example_assignment = completed[1]
email = example_assignment["email"]
print(email)
score_answer = [(q["score"], q["answer"]) for q in example_assignment["questions"]]

example_code = score_answer[0][1]
print(example_code)
