import os

listSubDirs = [x for x in os.listdir('/nas02/depts/hopfinger/Games/rawdata/') if 'games' in x and '_' not in x]

listSubDirs = [x.replace('games', '') for x in listSubDirs]

submit_string = 'srun -n 1 --mem=4000 wrap="heudiconv -d /nas02/depts/hopfinger/Games/rawdata/Games\{subject\}/\{session\} -o /nas02/depts/hopfinger/Games/BIDs_Dir -b --minmeta -f /nas/longleaf/home/hlmorgan/hlmorgan_heuristic.py -s {sub} -ss {ses}"'

for dir in listSubDirs:
    print(submit_string.format(
        sub = dir,
        ses = 'pre'
    ))
    print(submit_string.format(
        sub=dir,
        ses='pre'
    ))

