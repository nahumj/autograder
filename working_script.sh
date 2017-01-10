#./github_repo_management.py fake_student_info.csv
./autograder.py --students=demo_info.csv clone
./autograder.py --students=demo_info.csv command "git remote add instructor git@github.com:CSE480-MSU/instructor-database.git"
./autograder.py --students=demo_info.csv command "git pull instructor master"
./autograder.py --students=demo_info.csv command "git push"
