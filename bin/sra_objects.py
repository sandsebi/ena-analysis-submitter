#!/usr/bin/env python

__author__ = "Nadim Rahman"

from lxml import etree
import os

import logging
import sys

#Creating and Configuring Logger

Log_Format = "%(levelname)s %(asctime)s - %(message)s"

logging.basicConfig(stream = sys.stdout, 
                    filemode = "w",
                    format = Log_Format, 
                    level = logging.DEBUG)

logger = logging.getLogger()

logger.debug("sra_objects: ")

class createAnalysisXML:
    # Class which handles creation of an analysis XML component of the Webin XML
    def __init__(self, webin_elt, alias, project_accession, analysis_date, analysis_file, analysis_title, analysis_description, analysis_attributes, analysis_type, sample_accession="", run_accession="", centre_name=""):
        self.webin_elt = webin_elt
        self.alias = alias
        self.project_accession = project_accession
        self.analysis_date = analysis_date
        self.analysis_file = analysis_file
        self.analysis_title = analysis_title
        self.analysis_description = analysis_description
        self.analysis_attributes = analysis_attributes
        self.analysis_type = analysis_type
        self.sample_accession = sample_accession
        self.run_accession = run_accession
        self.centre_name = centre_name

    def split_sub_elements(self, references, parent_element, element_name):
        """
        Split into sub elements
        :param references: The accessions which are to be referenced in the final XML object
        :param parent_element: Parent element to add the references to
        :param element_name: Name of the element which holds the reference
        :return: A complete XML sub-element which is added to the final XMl object
        """
        if not isinstance(references, list):
            references = references.split(",")

        for reference in references:
            subElt = etree.SubElement(parent_element, element_name, accession=reference)
        return subElt

    def build_file_element(self, parent_element):
        """
        Create the files element within the XML using the analysis file information list of dictionaries
        :param parent_element: Element to add the files section to
        :return: Adding run section of XML
        """
        for file in self.analysis_file:
            filename = os.path.basename(file.get('name'))       # Do not need full path in analysis XMl, just the file name - as it is being retrieved from Webin upload area
            fileElt = etree.SubElement(parent_element, 'FILE', filename=filename, filetype=file.get('type'), checksum_method="MD5", checksum=file.get('md5_value'))
        return fileElt

    def add_analysis_attributes(self, parent_element):
        """
        Create the analysis attributes section for the analysis XML
        :param parent_element: Name of element to add section to
        :return: Analysis attributes XML sub-element
        """
        analysis_attributes = etree.SubElement(parent_element, 'ANALYSIS_ATTRIBUTES')

        for item in self.analysis_attributes.items():
            analysis_attribute = etree.SubElement(analysis_attributes, 'ANALYSIS_ATTRIBUTE')
            etree.SubElement(analysis_attribute, 'TAG').text = item[0]
            etree.SubElement(analysis_attribute, 'VALUE').text = item[1]

    def build_analysis(self):
        """
        Build the analysis XML for submission
        :return: Analysis XML
        """
        analysis_set = etree.SubElement(self.webin_elt, 'ANALYSIS_SET')        # Define the analysis XML object

        if self.centre_name != "":
            analysisElt = etree.SubElement(analysis_set, 'ANALYSIS', alias=self.alias, center_name=self.centre_name, analysis_date=self.analysis_date)
        else:
            analysisElt = etree.SubElement(analysis_set, 'ANALYSIS', alias=self.alias, analysis_date=self.analysis_date)

        title = etree.SubElement(analysisElt, 'TITLE')
        title.text = self.analysis_title

        description = etree.SubElement(analysisElt, 'DESCRIPTION')
        description.text = self.analysis_description

        # ELEMENT EXAMPLE FORMAT FOR FOLLOWING REFERENCES = etree.SubElement(analysisElt, 'STUDY_REF', accession=self.project_accession)
        projectrefElt = self.split_sub_elements(self.project_accession, analysisElt, 'STUDY_REF')
        if self.sample_accession != "":
            samplerefElt = self.split_sub_elements(self.sample_accession, analysisElt, 'SAMPLE_REF')
        if self.run_accession != "":
            runrefElt = self.split_sub_elements(self.run_accession, analysisElt, 'RUN_REF')

        analysis_type = etree.SubElement(analysisElt, 'ANALYSIS_TYPE')
        print(self.analysis_type)
        type = etree.SubElement(analysis_type, self.analysis_type)

        files = etree.SubElement(analysisElt, 'FILES')
        fileElt = self.build_file_element(files)

        analysis_attributes = self.add_analysis_attributes(analysisElt)      # Create analysis attributes XML sub-element

        print('*' * 100)
        print('Analysis XML:\n')
        print(etree.tostring(analysis_set, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        print('*' * 100)

        return analysis_set


class createSubmissionXML:
    # Class which handles creation of a submission XML component of the Webin XML
    def __init__(self, webin_elt, alias, action, centre_name=""):
        self.webin_elt = webin_elt
        self.alias = alias
        self.action = action
        self.centre_name = centre_name

    def build_submission(self):
        """
        Build the submission XML which accompanies the analysis XML for submission
        :return: Submission XML object
        """
        submission_set = etree.SubElement(self.webin_elt, 'SUBMISSION_SET')

        submissionElt = etree.SubElement(submission_set, 'SUBMISSION', alias=self.alias, center_name=self.centre_name)
        actionsElt = etree.SubElement(submissionElt, 'ACTIONS')
        actionElt = etree.SubElement(actionsElt, 'ACTION')
        actionSub = etree.SubElement(actionElt, self.action)

        print('*' * 100)
        print('Submission XML: \n')
        print(etree.tostring(submission_set, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        print('*' * 100)

        return submission_set


class createWebinXML:
    # Class which handles creation of a Webin XML to be used for the submission to ENA
    def __init__(self, alias, configuration, project_accession, analysis_date, timestamp_now, analysis_file, analysis_type, parent_dir, sample_accession="", run_accession=""):
        self.alias = alias
        self.centre_name = configuration['CENTER_NAME']
        self.action = configuration['ACTION']
        self.project_accession = project_accession
        self.analysis_date = analysis_date
        self.timestamp_now = timestamp_now
        self.analysis_file = analysis_file
        self.analysis_title = configuration['TITLE']
        self.analysis_description = configuration['DESCRIPTION']
        self.analysis_attributes = {'PIPELINE_NAME': configuration['PIPELINE_NAME'], 'PIPELINE_VERSION': configuration['PIPELINE_VERSION'], 'SUBMISSION_TOOL': configuration['SUBMISSION_TOOL'], 'SUBMISSION_TOOL_VERSION': configuration['SUBMISSION_TOOL_VERSION']}
        self.analysis_type = analysis_type
        self.parent_dir = parent_dir
        self.sample_accession = sample_accession
        self.run_accession = run_accession

    def build_webin(self):
        """
        Build the Webin XML for submission to the ENA
        :return: Webin XML object
        """
        # Create the Webin XML object - will be used to append Submission and Analysis XML objects
        webin_parent = etree.Element('WEBIN')
        webin_xml = etree.ElementTree(webin_parent)

        # Include Submission component of Webin XML
        submission_obj = createSubmissionXML(webin_parent, self.alias, self.action, self.centre_name)
        self.submission_xml = submission_obj.build_submission()

        # Include Analysis component of Analysis XML
        analysis_obj = createAnalysisXML(webin_parent, self.alias, self.project_accession, self.analysis_date, self.analysis_file, self.analysis_title, self.analysis_description, self.analysis_attributes, self.analysis_type, self.sample_accession, self.run_accession, self.centre_name)
        self.analysis_xml = analysis_obj.build_analysis()

        print('*' * 100)
        print('Final Webin XML: \n')
        print('*' * 100)
        logger.debug(f'{webin_xml} webin_xml: ')
        print(etree.tostring(webin_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        print('*' * 100)

        # Save the submission XML to a file
        xml_filename = 'webin_{}.xml'.format(self.timestamp_now)
        logger.debug(f'{self.parent_dir,xml_filename} xml_filepath before: ')
        xml_filepath = os.path.join(self.parent_dir, xml_filename)
        xml_filepath = xml_filepath.encode().decode('unicode_escape')
        logger.debug(f'{self.parent_dir, xml_filename} xml_filepath after: ')
        webin_xml.write(xml_filepath, pretty_print=True, xml_declaration=True, encoding='UTF-8')

        return webin_xml
