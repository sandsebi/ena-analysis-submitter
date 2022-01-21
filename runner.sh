#!/bin/sh
#BSUB -q
#BSUB -n
#BSUB -cwd
#BSUB -o
#BSUB -e
#BSUB -R
#BSUB -M
#BSUB -W

while IFS=$'\t' read -r -a row
do
  # Row indexed items: 0 = project accession, 1 = sample accession(s), 2 = run accession(s), 3 = name of analysis file to be submitted, 4 = type of analysis, e.g. PATHOGEN_ANALYSIS
  python3 analysis_submission.py -p ${row[0]} -s ${row[1]} -r ${row[2]} -f ${row[3]} -a ${row[4]} -t
done < submission_meta.txt
