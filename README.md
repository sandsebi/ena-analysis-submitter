# ena-analysis-submitter

##Background
This tool has been developed to handle submissions of Pathogen Analysis objects into ENA. It's intended use is as an additional component to integrated workflows in the [Data Hubs]().

The tool uploads analysis data files and carries out the submission to a project, although possible for general use, these projects are generally associated with certain Data Hubs, and therefore result in analysis being submitted to the Data Hub.

##Usage
The tool expects knowledge of the following, prior to usage:

1. A valid INSDC project/study accession (e.g. PRJ...)
2. One or more valid INSDC run accession(s), submitted to the project defined in 1 (e.g. ERR...). The script accepts run accessions separated by commas or can read from a file with an accession per line.
3. One or more analysis files (full paths) to be submitted as part of the project in 1 and referring to the run(s) in 2. The script accepts file names separated by commas or can be read from a file with a file per line.

`python3 analysis_submission.py -p <PROJECT_ACCESSION> -r <RUN_ACCESSION(S)> -f <FILE_NAME(S)> -t`

`python3 analysis_submission.py --help` for more information.