#!/usr/bin/python3

__author__ = "Nadim Rahman, Blaise Alako, Nima Pekseresht"

import argparse, hashlib, os
from datetime import datetime
from sra_objects import createAnalysisXML
from sra_objects import createSubmissionXML


##### TO EDIT IF APPLICABLE
analysis_attributes = {'PIPELINE_NAME': 'DTU_Evergreen', 'PIPELINE_VERSION': '1.0.0', 'SUBMISSION_TOOL': 'DTU_Evergreen'}           # Defining analysis attributes to be included in the analysis XML
centre_name = 'DTU_Evergreen_Test'
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
            li = f.readlines()
    else:
        if separator in string:
            li = list(string.split(separator))
        else:
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
        :return: List of dictionary/ies consisting file information
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
        analysis_obj = createAnalysisXML(self.alias, self.project_accession, self.run_accession, self.analysis_date, self.analysis_file, self.analysis_title, self.analysis_description, self.analysis_attributes, self.sample_accession, self.centre_name)
        analysis_xml = analysis_obj.build_analysis()
        return analysis_xml

    def build_submission_xml(self):
        analysis_xml_filename = 'analysis_{}.xml'.format(self.analysis_date)
        submission_obj = createSubmissionXML(self.alias, self.action, self.analysis_date, analysis_xml_filename, 'analysis', self.centre_name)
        submission_xml = submission_obj.build_submission()
        return submission_xml


def upload_and_submit(datestamp, test):
    """
    Create the curl command and submit the analyses
    :param analysis_xml: Analysis XML to submit
    :param submission_xml: Submission XML to submit
    :return: Curl command
    """
    # At the moment this returns an appropriate curl command, but would eventually be used to carry out the submission
    if test is True:
        command = 'curl -u Webin-XXXXX:PASSWORD -F "SUBMISSION=@submission_{}.xml" -F "ANALYSIS=@analysis_{}.xml" "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/"'.format(datestamp, datestamp)
    else:
        command = 'curl -u Webin-XXXXX:PASSWORD -F "SUBMISSION=@submission_{}.xml" -F "ANALYSIS=@analysis_{}.xml" "https://www.ebi.ac.uk/ena/submit/drop-box/submit/"'.format(datestamp, datestamp)

    print("*" * 100)
    print("CURL submission command: \n")
    print(command)
    print("*" * 100)



if __name__=='__main__':
    args = get_args()       # Get script arguments

    # Handle any metadata references
    if args.sample_list != None and "," in args.sample_list:
        samples = convert_to_list(args.sample_list, ",")
    elif args.sample_list != None:
        samples = convert_to_list(args.sample_list, "\n")

    if args.run_list != None and "," in args.run_list:
        runs = convert_to_list(args.run_list, ",")
    elif args.sample_list != None:
        runs = convert_to_list(args.run_list, "\n")

    files = convert_to_list(args.file, ",")

    # Define sections to include in analysis XML
    timestamp = datetime.now()
    analysis_date = timestamp.strftime("%Y-%m-%dT%H:%M:%S")        # Get a formatted date and time string

    alias = 'integrated_dtu_evergreen_{}'.format(analysis_date)     # Alias to be used in the submission, required to link the submission and analysis

    file_preparation_obj = file_handling(files)     # Instantiate object for analysis file handling information
    analysis_file = file_preparation_obj.construct_file_info()      # Obtain information on file/s to be submitted for the analysis XML
    analysis_filename = os.path.basename(args.file)

    analysis_title = "Analysis generated on {} from the processing of raw read sequencing data through DTU_Evergreen pipeline to generate a Phylogenetic tree.".format(analysis_date)
    analysis_description = "Phylogenetic tree analyses on data held within a data hub on {}. For more information on the DTU_Evergreen pipeline, please visit: XXX. This pipeline has been integrated into EMBL-EBI ENA/COMPARE Data Hubs system, for more information on data hubs, please visit: XXX.".format(analysis_date)

    action='ADD'        # What to do with the submission, ADD is the equivalent of submitting a new record

    # Create the analysis and submission XML for submission
    create_xml_object = create_xmls(alias, action, args.project, args.run_list, analysis_date, analysis_file, analysis_title, analysis_description, analysis_attributes, centre_name=centre_name)
    analysis_xml = create_xml_object.build_analysis_xml()
    submission_xml = create_xml_object.build_submission_xml()

    # Obtain a curl command for submission of the analysis
    upload_and_submit(analysis_date, args.test)

