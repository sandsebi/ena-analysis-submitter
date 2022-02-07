#!/usr/bin/env python

__author__ = "Nadim Rahman, Blaise Alako, Nima Pekseresht"

import argparse, hashlib, os, subprocess, time, yaml
from datetime import datetime
from sra_objects import createAnalysisXML
from sra_objects import createSubmissionXML



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
    parser.add_argument('-a', '--analysis_type', help='Type of analysis to submit. Options: PATHOGEN_ANALYSIS, COVID19_CONSENSUS, COVID19_FILTERED_VCF', choices=['PATHOGEN_ANALYSIS', 'COVID19_CONSENSUS', 'COVID19_FILTERED_VCF'], required=True)         # Can add more options if you wish to share more analysis types
    parser.add_argument('-au', '--analysis_username', help='Valid Webin submission account ID (e.g. Webin-XXXXX) used to carry out the submission', type=str, required=True)
    parser.add_argument('-ap', '--analysis_password', help='Password for Webin submission account', type=str, required=True)
    parser.add_argument('-t', '--test', help='Specify whether to use ENA test server for submission', action='store_true')
    args = parser.parse_args()
    return args


def read_config():
    """
    Read in the configuration file
    :return: A dictionary referring to tool configuration
    """
    with open("config.yaml") as f:
        configuration = yaml.safe_load(f)
    return configuration


def convert_to_list(string):
    """
    Convert a string to a list by a particular separator
    :param string: String to convert to list
    :param separator: Separator to split string on
    :return: List
    """
    if os.path.isfile(string):
        # Handle cases where the input string is a file location, reading a list from file
        with open(string) as f:
            li_read = f.read()
            li = li_read.splitlines()
    elif ',' in string:
        li = list(string.split(','))
    else:
        li = [string]
    return li


class file_handling:
    def __init__(self, file_list, file_type):
        self.file_list = file_list
        self.type = file_type

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
        for file in self.file_list:             # To be changed in future with dictionary of file types
            file_md5 = self.calculate_md5(file)  # Calculate an MD5 checksum value for file to be submitted
            if self.type == "COVID19_CONSENSUS":
                file_type = "fasta"
            elif self.type == "COVID19_FILTERED_VCF":
                file_type = "vcf"
            else:
                file_type = "other"
            file_information = {'name': file, 'type': file_type,
                                'md5_value': file_md5}  # Create dictionary of information
            files_information.append(file_information)
        return files_information


class create_xmls:
    def __init__(self, alias, project_accession, run_accession, analysis_date, analysis_file, analysis_title, analysis_description, configuration, analysis_type, sample_accession=""):
        self.alias = alias
        self.action = configuration['ACTION']
        self.project_accession = project_accession
        self.run_accession = run_accession
        self.analysis_date = analysis_date
        self.analysis_file = analysis_file
        self.analysis_title = analysis_title
        self.analysis_description = analysis_description
        self.analysis_attributes = {'PIPELINE_NAME': configuration['PIPELINE_NAME'], 'PIPELINE_VERSION': configuration['PIPELINE_VERSION'], 'SUBMISSION_TOOL': configuration['SUBMISSION_TOOL'], 'SUBMISSION_TOOL_VERSION': configuration['SUBMISSION_TOOL_VERSION']}
        self.analysis_type = analysis_type
        self.sample_accession = sample_accession
        self.centre_name = configuration['CENTER_NAME']

    def build_analysis_xml(self):
        """
        Create an Analysis XML for submission
        :return:
        """
        analysis_obj = createAnalysisXML(self.alias, self.project_accession, self.run_accession, self.analysis_date, self.analysis_file, self.analysis_title, self.analysis_description, self.analysis_attributes, self.analysis_type, self.sample_accession, self.centre_name)
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
    configuration = read_config()           # Configuration from YAML

    # Handle any metadata references
    samples = convert_to_list(args.sample_list)
    runs = convert_to_list(args.run_list)
    if ',' in args.file:
        files = list(args.file.split(','))
    else:
        files = [args.file]

    # Define sections to include in analysis XML
    timestamp = datetime.now()
    analysis_date = timestamp.strftime("%Y-%m-%dT%H:%M:%S")        # Get a formatted date and time string

    alias = configuration['ALIAS'] + '_' + str(analysis_date)

    # Obtain file information
    file_preparation_obj = file_handling(files, args.analysis_type)     # Instantiate object for analysis file handling information
    analysis_file = file_preparation_obj.construct_file_info()      # Obtain information on file/s to be submitted for the analysis XML

    # Create the analysis and submission XML for submission
    create_xml_object = create_xmls(alias, args.project, runs, analysis_date, analysis_file, configuration['TITLE'], configuration['DESCRIPTION'], configuration, args.analysis_type, sample_accession=samples)
    analysis_xml = create_xml_object.build_analysis_xml()
    submission_xml = create_xml_object.build_submission_xml()

    # Upload data files and submit to ENA
    submission_obj = upload_and_submit(analysis_file, args.analysis_username, args.analysis_password, analysis_date, args.test)
    submission = submission_obj.submit_data()
