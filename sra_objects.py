#!/usr/bin/python3

__author__ = "Nadim Rahman, Nima Pakseresht, Blaise Alako"

from lxml import etree

class createAnalysisXML:
    # Class which handles creation of an analysis XML for submission to ENA
    def __init__(self, alias, project_accession, run_accession, analysis_date, analysis_file, analysis_title, analysis_description, analysis_attributes, sample_accession="", centre_name=""):
        self.alias = alias
        self.project_accession = project_accession
        self.run_accession = run_accession
        self.analysis_attributes = analysis_attributes
        self.analysis_date = analysis_date
        self.analysis_file = analysis_file
        self.analysis_title = analysis_title
        self.analysis_description = analysis_description
        self.sample_accession = sample_accession
        self.centre_name = centre_name

    def split_sub_elements(self, references, parent_element, element_name):
        """
        Split into sub elements
        :return:
        """
        if not isinstance(references, list):
            references = references.split(",")

        print(references)
        for reference in references:
            subElt = etree.SubElement(parent_element, element_name, accession=reference)
        return subElt

    def add_analysis_attributes(self, parent_element):
        """
        Create the analysis attributes section for the analysis XML
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
        analysis_set = etree.Element('ANALYSIS_SET')
        analysis_xml = etree.ElementTree(analysis_set)

        print(self.centre_name)
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
        runrefElt = self.split_sub_elements(self.run_accession, analysisElt, 'RUN_REF')

        analysis_type = etree.SubElement(analysisElt, 'ANALYSIS_TYPE')
        type = etree.SubElement(analysis_type, 'PATHOGEN_ANALYSIS')

        files = etree.SubElement(analysisElt, 'FILES')
        fileElt = etree.SubElement(files, 'FILE', filename=self.analysis_file.get('name'), filetype=self.analysis_file.get('type'), checksum_method="MD5", checksum = self.analysis_file.get('md5_value'))

        analysis_attributes = self.add_analysis_attributes(analysisElt)      # Create analysis attributes XML sub-element

        print('*' * 100)
        print('Final Analysis XML:\n')
        print(etree.tostring(analysis_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        print('*' * 100)

        analysis_xml.write('analysis_output.xml', pretty_print=True, xml_declaration=True, encoding='UTF-8')

        return analysis_xml


class createSubmissionXML:
    # Class which handles creation of a submission XML for submission to ENA
    def __init__(self, alias, action, source_xml, schema, centre_name=""):
        self.alias = alias
        self.centre_name = centre_name
        self.action = action
        self.source_xml = source_xml
        self.schema = schema

    def build_submission(self):
        submission_set = etree.Element('SUBMISSION_SET')
        submission_xml = etree.ElementTree(submission_set)

        submissionElt = etree.SubElement(submission_set, 'SUBMISSION', alias=self.alias, center_name=self.centre_name)
        actionsElt = etree.SubElement(submissionElt, 'ACTIONS')
        actionElt = etree.SubElement(actionsElt, 'ACTION')
        actionSub = etree.SubElement(actionElt, self.action, source=self.source_xml, schema=self.schema)

        print('*' * 100)
        print('Final Submission XML: \n')
        print(etree.tostring(submission_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        print('*' * 100)

        submission_xml.write('submission.xml', pretty_print=True, xml_declaration=True, encoding='UTF-8')