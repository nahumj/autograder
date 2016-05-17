#!/usr/bin/env python3
import sys
from zipfile import ZipFile
from glob import glob
import os.path
import subprocess
import shutil


def get_email(hr_filepath):
    hr_filename = os.path.split(hr_filepath)[-1]
    email_at_end = hr_filename.partition("_true_cache")[0]

    break_apart_underscores = email_at_end.split("_")
    before_at, after_at = break_apart_underscores[-2:]
    return before_at + "@" + after_at
    
def send_single_email(address, subject_line, body, attachment=None):
    command = ['mutt', '-e', '""set from=do-not-reply@cse.msu.edu""', '-s', subject_line]
    if attachment is not None:
        command += ["-a", attachment]
    command += [ "--", address]
    #print(command)
    #return
    with subprocess.Popen(command, stdin=subprocess.PIPE, universal_newlines=True) as proc:
        proc.communicate(body)


hr_zipfilename = sys.argv[1]

hr_zipfile = ZipFile(hr_zipfilename)
dir = hr_zipfilename + "_unziped"
hr_zipfile.extractall(path=dir)
pdfs = glob(dir + "/*/*.pdf")
for pdf in pdfs:
    email = get_email(pdf)
    send_single_email(email, "Your HackerRank Report", "Attached is a pdf of your HackerRank report", pdf)
shutil.rmtree(dir)


#pdf_zipinfos  = hr_zipfile.infolist()
#for pdf in pdf_zipinfos:
#    print(pdf.filename)
#    hr_zipfile.extract(pdf, "other_dir")
