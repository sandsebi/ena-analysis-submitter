#!/usr/bin/python3

__author__ = "Nadim Rahman"

import argparse, os
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
    parser.add_argument('-r', '--run_list', help='ENA run accession/s to link with the analysis submission, accepts a list of accessions (e.g. ERRXXXXX, ERRXXXXX) or a file with a list of accessions separated by new line', required=True)
    parser.add_argument('-f', '--file', help='Files of analysis to submit to the project', type=str, required=True)
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
        li = list(string.split(separator))
    return li


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
        submission_obj = createSubmissionXML(self.alias, self.action, 'analysis_output.xml', 'analysis', centre_name=centre_name)
        submission_xml = submission_obj.build_submission()
        return submission_xml


def upload_and_submit(self):
    pass



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

    # Define sections to include in analysis XML
    timestamp = datetime.now()
    analysis_date = timestamp.strftime("%Y-%m-%dT%H:%M:%S")        # Get a formatted date and time string

    alias = 'integrated_dtu_evergreen_{}'.format(analysis_date)
    analysis_attributes = {'PIPELINE_NAME': 'DTU_Evergreen', 'PIPELINE_VERSION': '1.0.0', 'SUBMISSION_TOOL': 'DTU_Evergreen'}
    analysis_filename = os.path.basename(args.file)
    analysis_file = {'name': analysis_filename, 'type': 'other', 'md5_value': '66d8201ac47aacea575bb65d8ab5c53a'}
    analysis_title = "Analysis generated on {} from the processing of raw read sequencing data through DTU_Evergreen pipeline to generate a Phylogenetic tree.".format(analysis_date)
    analysis_description = "Phylogenetic tree analyses on data held within a data hub on {}. For more information on the DTU_Evergreen pipeline, please visit: XXX. This pipeline has been integrated into EMBL-EBI ENA/COMPARE Data Hubs system, for more information on data hubs, please visit: XXX.".format(analysis_date)
    centre_name = 'DTU_Evergreen_Test'

    action='ADD'
    schema='analysis'

    create_xml_object = create_xmls(alias, action, args.project, args.run_list, analysis_date, analysis_file, analysis_title, analysis_description, analysis_attributes, centre_name=centre_name)
    analysis_xml = create_xml_object.build_analysis_xml()
    submission_xml = create_xml_object.build_submission_xml()

