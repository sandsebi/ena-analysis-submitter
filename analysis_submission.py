#!/usr/bin/python3

__author__ = "Nadim Rahman, Blaise Alako, Nima Pekseresht"

import argparse, hashlib, os, subprocess, sys, time
from datetime import datetime
from sra_objects import createAnalysisXML
from sra_objects import createSubmissionXML


##### TO EDIT IF APPLICABLE
analysis_attributes = {'PIPELINE_NAME': 'COVID-19 Sequence Analysis Workflow', 'PIPELINE_VERSION': 'v1', 'SUBMISSION_TOOL': 'ENA_Analysis_Submitter', 'SUBMISSION_TOOL_VERSION': '1.0.0'}           # Defining analysis attributes to be included in the analysis XML
centre_name = 'VEO'
analysis_username = ''
analysis_password = ''
action = 'ADD'      # What to do with new submission, ADD is the equivalent of submitting a new record
###########################


def get_args():
    '''
    Define and obtain script arguments
    :return: Arguments object
    '''
    parser = argparse.ArgumentParser(prog='analysis_submission.py', formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
        + ============================================================ +
        |  European Nucleotide Archive (ENA) Analysis Submission Tool  |
        |                                                              |
        |  Tool to submit Pathogen analysis objects to an ENA project  |
        |  , mainly in the data hub context.                           |
        + =========================================================== +
        """)
    parser.add_argument('-p', '--project', help='Valid ENA project accession to submit analysis to (e.g. PRJXXXXXXX)', type=str, required=True)
    parser.add_argument('-s', '--sample_list', help='ENA sample accessions/s to link with the analysis submission, accepts a list of accessions (e.g. ERSXXXXX,ERSXXXXX) or a file with list of accessions separated by new line', required=False)
    parser.add_argument('-r', '--run_list', help='ENA run accession/s to link with the analysis submission, accepts a list of accessions (e.g. ERRXXXXX,ERRXXXXX) or a file with a list of accessions separated by new line', required=True)
    parser.add_argument('-f', '--file', help='Files of analysis to submit to the project, accepts a list of files (e.g. path/to/file1.csv.gz,path/to/file2.txt.gz)', type=str, required=True)
    parser.add_argument('-t', '--test', help='Specify whether to use ENA test server for submission', action='store_true')
    args = parser.parse_args()

    return args


def convert_to_list(string, separator):
    """
    Convert a string to a list by a particular separator
    :param string: String to convert to list
    :param separator: Separator to split string on
    :return: List
    """
    if separator == "\n":
        # Handle cases where the input string is a file location, reading a list from file
        with open(string) as f:
            li_read = f.read()
            li = li_read.splitlines()
    else:
        if separator in string:
            # If there is more than one sub-string specified
            li = list(string.split(separator))
        else:
            # If there is only on string
            li = [string]
    return li


class file_handling:
    def __init__(self, file_list):
        self.file_list = file_list

    def calculate_md5(self, file):
        """
        Calculate MD5 value for analysis data file to be submitted
        :param file: List of file(s) to be submitted
        :return: MD5 checksum value
        """
        print(file)
        return hashlib.md5(open(file, 'rb').read()).hexdigest()

    def construct_file_info(self):
        """
        Construct information on analysis data file(s) to be submitted
        :return: List of dictionary/ies consisting of file information
        """
        files_information = []
        for file in self.file_list:
            file_md5 = self.calculate_md5(file)     # Calculate an MD5 checksum value for file to be submitted
            file_information = {'name': file, 'type': 'other', 'md5_value': file_md5}       # Create dictionary of information
            files_information.append(file_information)
        return files_information


class create_xmls:
    def __init__(self, alias, action, project_accession, run_accession, analysis_date, analysis_file, analysis_title, analysis_description, analysis_attributes, sample_accession="", centre_name=""):
        self.alias = alias
        self.action = action
        self.project_accession = project_accession
        self.run_accession = run_accession
        self.analysis_attributes = analysis_attributes
        self.analysis_date = analysis_date
        self.analysis_file = analysis_file
        self.analysis_title = analysis_title
        self.analysis_description = analysis_description
        self.sample_accession = sample_accession
        self.centre_name = centre_name

    def build_analysis_xml(self):
        """
        Create an Analysis XML for submission
        :return:
        """
        analysis_obj = createAnalysisXML(self.alias, self.project_accession, self.run_accession, self.analysis_date, self.analysis_file, self.analysis_title, self.analysis_description, self.analysis_attributes, self.sample_accession, self.centre_name)
        analysis_xml = analysis_obj.build_analysis()
        return analysis_xml

    def build_submission_xml(self):
        """
        Create a Submission XML for submission
        :return:
        """
        analysis_xml_filename = 'analysis_{}.xml'.format(self.analysis_date)
        submission_obj = createSubmissionXML(self.alias, self.action, self.analysis_date, analysis_xml_filename, 'analysis', self.centre_name)
        submission_xml = submission_obj.build_submission()
        return submission_xml


class upload_and_submit:
    def __init__(self, analysis_file, analysis_username, analysis_password, datestamp, test):
        self.analysis_file = analysis_file
        self.analysis_username = analysis_username
        self.analysis_password = analysis_password
        self.datestamp = datestamp
        self.test = test

    def upload_to_ENA(self):
        """
        Upload data file(s) to ENA
        :return: Lists of successful file upload and list of any errors during upload
        """
        trialcount = 0
        upload_errors = []
        upload_success = []

        # Process each file that needs to be submitted
        for file in self.analysis_file:
            command = "curl -T {}  ftp://webin.ebi.ac.uk --user {}:{}".format(file.get('name'), self.analysis_username, self.analysis_password)         # Command to upload file to Webin
            md5downloaded = "curl -s ftp://webin.ebi.ac.uk/{} --user {}:{} | md5 | cut -f1 -d ' '".format(os.path.basename(file.get('name')), self.analysis_username, self.analysis_password)       # Command to check the MD5 value for the submitted file
            md5uploaded = file.get('md5_value')         # The MD5 calculated before the file upload
            print('-' * 100)
            print("CURL command:\n{}".format(command))
            print("MD5 Download command:\n{}".format(md5downloaded))
            print("MD5 uploaded:\n{}".format(md5uploaded))
            print('-' * 100)

            # Upload the file to Webin
            sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = sp.communicate()

            # Obtain the MD5 of the submitted file
            downloadmd5, downloaderr = subprocess.Popen(md5downloaded, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            downloadmd5 = downloadmd5.decode().strip(' \t\n\r')

            print('*' * 100)
            print("--> {} {} {} <--".format(os.path.basename(file.get('name')), md5uploaded, downloadmd5))
            print('*' * 100)

            if md5uploaded == downloadmd5:
                # File integrity proven with matching MD5 values pre and post upload
                if out:
                    upload_success.append(file.get('name'))
                    print("Standard output of subprocess:")
                    print(out.decode())
                if err:
                    upload_success.append(file.get('name'))
                    print("Standard error of subprocess:")
                    print(err.decode())
                if sp.returncode != 0:
                    upload_errors.append({file.get('name'): err.decode()})
                    print(err.decode(), file=sys.stderr)
                print("Returncode of subprocess:", sp.returncode)
                return upload_success, upload_errors
            else:
                # Failed file integrity check, try at least 10 times before failure
                print("Analysis file {} may be corrupt, MD5 values do not match.".format(file.get('name')))
                time.sleep(10)
                self.upload_to_ENA()
                trialcount += 1
                if trialcount > 10:
                    upload_errors.append({file.get('name'): err.decode()})
                    return upload_success, upload_errors

    def submit_data(self):
        """
        Coordinate the upload of data files and submission to ENA
        :return: Upload of file(s) and curl command
        """
        success, errors = self.upload_to_ENA()      # Upload the data files to ENA prior to submission

        # Attempt the submission if there are no errors reported in the file upload stage
        if not errors:
            if self.test is True:
                command = 'curl -u {}:{} -F "SUBMISSION=@submission_{}.xml" -F "ANALYSIS=@analysis_{}.xml" "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/"'.format(self.analysis_username, self.analysis_password, self.datestamp, self.datestamp)
            else:
                command = 'curl -u {}:{} -F "SUBMISSION=@submission_{}.xml" -F "ANALYSIS=@analysis_{}.xml" "https://www.ebi.ac.uk/ena/submit/drop-box/submit/"'.format(self.analysis_username, self.analysis_password, self.datestamp, self.datestamp)
            sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = sp.communicate()

            print("-" * 100)
            print("CURL submission command: \n")
            print(command)
            print("Returned output: \n")
            print(out.decode())
            print("-" * 100)

        else:
            print("File upload errors detected, aborted file upload:\n {}".format(errors))



if __name__=='__main__':
    args = get_args()       # Get script arguments

    # Handle any metadata references
    if args.sample_list != None and "," in args.sample_list:
        samples = convert_to_list(args.sample_list, ",")
    elif args.sample_list != None:
        samples = convert_to_list(args.sample_list, "\n")

    if args.run_list != None and "," in args.run_list:
        runs = convert_to_list(args.run_list, ",")
    elif args.run_list != None:
        runs = convert_to_list(args.run_list, "\n")

    files = convert_to_list(args.file, ",")

    # Define sections to include in analysis XML
    timestamp = datetime.now()
    analysis_date = timestamp.strftime("%Y-%m-%dT%H:%M:%S")        # Get a formatted date and time string

    #### CONFIGURABLE SECTION ####
    run = runs[0]
    sample = samples[0]
    alias = 'covid_sequence_analysis_workflow_{}_{}'.format(run, analysis_date)     # Alias to be used in the submission, required to link the submission and analysis
    analysis_title = "VEO SARS-CoV-2 systematically called variant data of public run {} and sample {}, part of the snapshot generated on 22/03/2021.".format(
        run, sample)
    analysis_description = "All public SARS-CoV-2 INSDC raw read data is streamed through the COVID Sequence Analysis Workflow to produce a set of uniform variant calls. For more information on the pipeline, visit https://github.com/enasequence/covid-sequence-analysis-workflow.".format(
        analysis_date)
    ##############################

    # Obtain file information
    file_preparation_obj = file_handling(files)     # Instantiate object for analysis file handling information
    analysis_file = file_preparation_obj.construct_file_info()      # Obtain information on file/s to be submitted for the analysis XML
    analysis_filename = os.path.basename(args.file)

    # Create the analysis and submission XML for submission
    create_xml_object = create_xmls(alias, action, args.project, runs, analysis_date, analysis_file, analysis_title, analysis_description, analysis_attributes, sample_accession=samples, centre_name=centre_name)
    analysis_xml = create_xml_object.build_analysis_xml()
    submission_xml = create_xml_object.build_submission_xml()

    # Upload data files and submit to ENA
    submission_obj = upload_and_submit(analysis_file, analysis_username, analysis_password, analysis_date, args.test)
    submission = submission_obj.submit_data()
