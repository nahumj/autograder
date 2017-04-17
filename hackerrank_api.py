import requests
import os.path
from pprint import pprint
import os
import string


def sanitize(input_):
    allowed_chars = string.ascii_letters + string.digits
    letters = [letter if letter in allowed_chars else '_' for letter in input_]
    return "".join(letters)


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
# print(id_names)
test_name = "CSE480 Homework #9"
test_id = id_names[test_name]

test_results_url = "/tests/" + str(test_id) + "/candidates/"
payload = {'access_token': token}
r = requests.get(base_url + test_results_url, params=payload)
response = r.json()
completed = response['data']
# pprint(completed)

test_name = sanitize(test_name)
os.makedirs(test_name, exist_ok=True)

email_to_response = {}
for student in completed:
    email = student["email"]
    student_folder = os.path.join(test_name, email)
    os.makedirs(student_folder, exist_ok=True)
    if "questions" not in student:
        break
    for question_number, question in enumerate(student["questions"]):
        solution = question["answer"]
        solution_path = os.path.join(student_folder,
                                     "q" + str(question_number + 1) + ".txt")
        with open(solution_path, "w") as file_handle:
            file_handle.writelines(solution)
