import requests
import os.path
from pprint import pprint

output_filename = "output.html"

with open(os.path.expanduser("~/.hackerrank_token")) as ht:
    token = ht.read().strip()
base_url = 'https://www.hackerrank.com/x/api/v2'

test_url = "/tests"
payload = {'access_token': token}
r = requests.get(base_url + test_url, params=payload)
response = r.json()
tests = response['data']
id_names = {test["name"]: test["id"] for test in tests}
print(id_names)
test_name = "CSE480 Homework #6"
test_id = id_names[test_name]

test_results_url = "/tests/" + str(test_id) + "/candidates/"
payload = {'access_token': token}
r = requests.get(base_url + test_results_url, params=payload)
response = r.json()
completed = response['data']
pprint(completed)

email_to_response = {}
for student in completed:
    email = student["email"]
    if "questions" not in student:
        response = "<p>No submission</p>"
    else:
        answers = [q["answer"] for q in student["questions"]]
        if len(answers) < 7:
            response = "<p>No Limerick</p>"
        else:
            response = answers[6]
    email_to_response[email] = response

output = ["<h1>limericks</h1>"]
for email, response in email_to_response.items():
    output.append("<h2>{}</h2>".format(email))
    output.append(response)

with open(output_filename, 'w') as output_fp:
    output_fp.writelines(output)
