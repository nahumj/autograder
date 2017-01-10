./github_repo_management.py 480_student_info.csv
rm -rf student_repos
./autograder.py --students=480_student_info.csv clone
./autograder.py --students=480_student_info.csv command "git remote add instructor git@github.com:CSE480-MSU/instructor-database.git"
./autograder.py --students=480_student_info.csv command "git pull instructor master"
./autograder.py --students=480_student_info.csv command "git push --force"
