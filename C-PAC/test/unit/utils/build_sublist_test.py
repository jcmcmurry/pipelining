# test/unit/utils/build_sublist_test.py
#
# Author(s): Daniel Clark, 2015

# Import packages
from CPAC.utils.build_sublist import build_sublist

'''
This module performs unit testing on functions in the buildsublist
module in the CPAC/utils subpackage
'''

# Import packages
import unittest

# Tets case for cpac datasink
class BuildSublistTestCase(unittest.TestCase):
    '''
    This class is a test case for the build_sublist.py module

    Inherits
    --------
    unittest.TestCase class

    Attributes (class):
    ------------------
    see unittest.TestCase documentation

    Attributes (instance):
    '''

    # setUp method
    def setUp(self):
        '''
        Init unittest TestCase

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class

        Returns
        -------
        None
            this function does not return any values, but populates the
            instance attributes for:

            self.creds_path : string
                filepath to AWS keys credentials file
        '''

        # Import packages
        from CPAC.utils import test_init

        # Init variables
        sublist_outpath = '/tmp'
        sublist_name = 'test'

        # Download scan parameters file
        scan_params_url = 'https://s3.amazonaws.com/fcp-indi/data/Projects/'\
                          'ABIDE_Initiative/Resources/scan_parameters_abide.csv'
        scan_params_csv = test_init.download_resource_from_s3(scan_params_url)

        # Set up data config dictionary
        data_config_dict = {'anatomicalTemplate' : None,
                            'functionalTemplate' : None,
                            'subjectList' : None,
                            'exclusionSubjectList' : None,
                            'siteList' : None,
                            'scanParametersCSV' : scan_params_csv,
                            'outputSubjectListLocation' : sublist_outpath,
                            'subjectListName' : sublist_name,
                            'awsCredentialsFile' : None}


        # Add instance variables to TestCase
        self.data_config_dict = data_config_dict

    # Get the filepaths in a list from the subject list
    def _return_filepaths(self, sublist):
        '''
        Method to extract filepaths from a C-PAC subject list

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        sublist : list
            a list of sub dictionaries (C-PAC subject list)

        Returns
        -------
        file_paths : list
            a list of filepaths as strings
        '''

        # Import packages

        # Init variables
        file_paths = []

        # Iterate through the list and extract paths
        for sub_dict in sublist:
            anat = sub_dict['anat']
            try:
                funcs = [rest for rest in sub_dict['func'].values()]
            except KeyError:
                funcs = [rest for rest in sub_dict['rest'].values()]
            file_paths.append(anat)
            file_paths.extend(funcs)

        # Return file paths
        return file_paths

    # Check filepaths
    def _check_filepaths(self, file_paths, filter_list, include=True):
        '''
        Method to check a list of file paths to ensure that it does
        or does not contain filepaths with any element of filter_list
        in it

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        file_paths : list
            a list of filepaths as strings
        filter_list : list
            a list of strings that are used to check the filepaths list
        include : boolean (optional); default=True
            flag to indicate whether to check for inclusion (True) or
            exclusion (False) in filepaths from elements of filter_list

        Returns
        -------
        properly_filtered : boolean
            flag indicating whether the list passed in is properly
            filtered or not
        filtered_msg : string
            possible error message telling the user what filepath
            is in the list that shouldn't be
        '''

        # Make sure all sites are in the filepaths
        matches = []
        for filt_str in filter_list:
            if include:
                matches.extend(filter(lambda fp: filt_str in fp, file_paths))
            else:
                matches.extend(filter(lambda fp: filt_str not in fp,
                                      file_paths))

        # Keep only unique filepaths in matches
        matches = list(set(matches))

        # List matches length should be the same as file_paths
        if len(matches) == len(file_paths):
            properly_filtered = True
            filtered_msg = 'Success!'
        else:
            properly_filtered = False
            num_errs = len(file_paths) - len(matches)
            filtered_msg = 'Found %d files that should not be in list!'\
                           % num_errs

        # Return flag and message
        return properly_filtered, filtered_msg

    # Build subject list with passed-in data_config_dict
    def _return_sublist_filepaths(self, data_config_dict):
        '''
        '''

        # Import packages
        import yaml
        from CPAC.utils import build_sublist

        # Init variables
        data_config_yml = '/tmp/s3_test_data_config.yml'

        # Write out data config yaml
        with open(data_config_yml, 'w') as out_yml:
            out_yml.write(yaml.dump(data_config_dict))

        # Build subject list
        sublist = build_sublist.build_sublist(data_config_yml)

        # Get just the filepaths to test
        filepaths = self._return_filepaths(sublist)

        # Return flags and messages
        return filepaths

    # Test for including specific sites
    def test_s3_sublist_include_sites(self):
        '''
        Method to test that the subject list builder includes only
        desired sites from S3

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Init variables
        data_config_dict = self.data_config_dict
        include_sites = ['Caltech', 'OHSU', 'UM_1']

        # Set up S3 templates
        anat_s3_template = 's3://fcp-indi/data/Projects/ABIDE_Initiative/'\
                           'RawData/{site}/{participant}/{session}/{series}/mprage.nii.gz'
        func_s3_template = 's3://fcp-indi/data/Projects/ABIDE_Initiative/'\
                           'RawData/{site}/{participant}/{session}/{series}/rest.nii.gz'

        # Add include sites to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_s3_template
        data_config_dict['functionalTemplate'] = func_s3_template
        data_config_dict['siteList'] = include_sites

        # Return found filepaths from subject list
        filepaths = self._return_sublist_filepaths(data_config_dict)

        # And check them
        properly_filtered, filter_msg = \
            self._check_filepaths(filepaths, include_sites, include=True)

        # Assert resulting list is properly filtered
        self.assertTrue(properly_filtered, msg=filter_msg)

    # Test for including specific subs
    def test_s3_sublist_include_subs(self):
        '''
        Method to test that the subject list builder includes only
        desired subjects from S3

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Init variables
        data_config_dict = self.data_config_dict
        include_subs = ['0050142', '0050143', '0050144']

        # Set up S3 templates
        anat_s3_template = 'S3://fcp-indi/data/Projects/ABIDE_Initiative/'\
                           'RawData/{site}/{participant}/{session}/{series}/mprage.nii.gz'
        func_s3_template = 'S3://fcp-indi/data/Projects/ABIDE_Initiative/'\
                           'RawData/{site}/{participant}/{session}/{series}/rest.nii.gz'

        # Add include subs to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_s3_template
        data_config_dict['functionalTemplate'] = func_s3_template
        data_config_dict['subjectList'] = include_subs

        # Return found filepaths from subject list
        filepaths = self._return_sublist_filepaths(data_config_dict)

        # And check them
        properly_filtered, filter_msg = \
            self._check_filepaths(filepaths, include_subs, include=True)

        # Assert resulting lst is properly filtered
        self.assertTrue(properly_filtered, msg=filter_msg)

    # Test for excluding specific subs
    def test_s3_sublist_exclude_subs(self):
        '''
        Method to test that the subject list builder excludes only
        non-desired subjects from S3

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Init variables
        data_config_dict = self.data_config_dict
        exclude_subs = ['0050142', '0050143', '0050144']

        # Set up S3 templates
        anat_s3_template = 's3://fcp-indi/data/Projects/ABIDE_Initiative/'\
                           'RawData/{site}/{participant}/{session}/{series}/mprage.nii.gz'
        func_s3_template = 's3://fcp-indi/data/Projects/ABIDE_Initiative/'\
                           'RawData/{site}/{participant}/{session}/{series}/rest.nii.gz'

        # Add excluded subs to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_s3_template
        data_config_dict['functionalTemplate'] = func_s3_template
        data_config_dict['exclusionSubjectList'] = exclude_subs

        # Return found filepaths from subject list
        filepaths = self._return_sublist_filepaths(data_config_dict)

        # And check them
        properly_filtered, filter_msg = \
            self._check_filepaths(filepaths, exclude_subs, include=False)

        # Assert resulting list is properly filtered
        self.assertTrue(properly_filtered, msg=filter_msg)

    # Test for regular expression matching
    def test_s3_sublist_regexp_match(self):
        '''
        Method to test that the subject list builder includes only
        desired sites from S3

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Init variables
        data_config_dict = self.data_config_dict
        sites_match_regex = ['CMU_a', 'CMU_b', 'Caltech', 'Yale']

        # Set up S3 templates
        anat_s3_template = 's3://fcp-indi/data/Projects/ABIDE_Initiative/'\
                           'RawData/[CY]*/{participant}/*/{series}/mprage.nii.gz'
        func_s3_template = 's3://fcp-indi/data/Projects/ABIDE_Initiative/'\
                           'RawData/[CY]*/{participant}/*/{series}/rest.nii.gz'

        # Add include sites to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_s3_template
        data_config_dict['functionalTemplate'] = func_s3_template

        # Return found filepaths from subject list
        filepaths = self._return_sublist_filepaths(data_config_dict)

        # And check them
        properly_filtered, filter_msg = \
            self._check_filepaths(filepaths, sites_match_regex, include=True)

        # Assert resulting list is properly filtered
        self.assertTrue(properly_filtered, msg=filter_msg)

    # Test for including specific sites
    def test_local_sublist_include_sites(self):
        '''
        Method to test that the subject list builder includes only
        desired sites from S3

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Import packages
        import os
        from CPAC.utils import test_init

        # Init variables
        data_config_dict = self.data_config_dict
        include_sites = ['site_1']
        base_dir = test_init.return_resource_subfolder('input')

        # Set up local templates
        anat_template = os.path.join(base_dir,
                                     '{site}/{participant}/{session}/{series}/'\
                                     'mprage.nii.gz')
        func_template = os.path.join(base_dir,
                                     '{site}/{participant}/{session}/{series}/'\
                                     'rest.nii.gz')

        # Add include sites to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_template
        data_config_dict['functionalTemplate'] = func_template
        data_config_dict['siteList'] = include_sites

        # Return found filepaths from subject list
        filepaths = self._return_sublist_filepaths(data_config_dict)

        # And check them
        properly_filtered, filter_msg = \
            self._check_filepaths(filepaths, include_sites, include=True)

        # Assert resulting list is properly filtered
        self.assertTrue(properly_filtered, msg=filter_msg)

    # Test for including specific subs
    def test_local_sublist_include_subs(self):
        '''
        Method to test that the subject list builder includes only
        desired subjects from S3

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Import packages
        import os
        from CPAC.utils import test_init

        # Init variables
        data_config_dict = self.data_config_dict
        include_subs = ['0010042', '0010064', '0010128']
        base_dir = test_init.return_resource_subfolder('input')

        # Set up local templates
        anat_template = os.path.join(base_dir,
                                     '{site}/{participant}/{session}/{series}/'\
                                     'mprage.nii.gz')
        func_template = os.path.join(base_dir,
                                     '{site}/{participant}/{session}/{series}/'\
                                     'rest.nii.gz')

        # Add include sites to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_template
        data_config_dict['functionalTemplate'] = func_template
        data_config_dict['subjectList'] = include_subs

        # Return found filepaths from subject list
        filepaths = self._return_sublist_filepaths(data_config_dict)

        # And check them
        properly_filtered, filter_msg = \
            self._check_filepaths(filepaths, include_subs, include=True)

        # Assert resulting list is properly filtered
        self.assertTrue(properly_filtered, msg=filter_msg)

    # Test for excluding specific subs
    def test_local_sublist_exclude_subs(self):
        '''
        Method to test that the subject list builder excludes only
        non-desired subjects from S3

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Import packages
        import os
        from CPAC.utils import test_init

        # Init variables
        data_config_dict = self.data_config_dict
        exclude_subs = ['0010042', '0010064', '0010128']
        base_dir = test_init.return_resource_subfolder('input')

        # Set up local templates
        anat_template = os.path.join(base_dir,
                                     '{site}/{participant}/{session}/{series}/'\
                                     'mprage.nii.gz')
        func_template = os.path.join(base_dir,
                                     '{site}/{participant}/{session}/{series}/'\
                                     'rest.nii.gz')

        # Add include sites to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_template
        data_config_dict['functionalTemplate'] = func_template
        data_config_dict['exclusionSubjectList'] = exclude_subs

        # Return found filepaths from subject list
        filepaths = self._return_sublist_filepaths(data_config_dict)

        # And check them
        properly_filtered, filter_msg = \
            self._check_filepaths(filepaths, exclude_subs, include=False)

        # Assert resulting list is properly filtered
        self.assertTrue(properly_filtered, msg=filter_msg)

    # Test for regular expression matching
    def test_local_sublist_reorg(self):
        '''
        Method to test that the subject list builder includes only
        desired sites from S3

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Import packages
        import os
        from CPAC.utils import test_init

        # Init variables
        data_config_dict = self.data_config_dict
        subs_match_regex = ['0010042', '0010064', '0010128', '0021019', '0023008',
                            '0023008', '0023012', '0027011', '0027018',
                            '0027034', '0027037', '1019436', '1206380', '1418396']

        # Copy original inputs to all same folder with
        # {participant}_{series} in filenames
        base_dir = test_init.return_resource_subfolder('input_reorg_files')

        # Set up local templates
        anat_template = os.path.join(base_dir,
                                     'site{site}_mprage_sub{participant}_sess{session}_ser_{series}.nii.gz')
        func_template = os.path.join(base_dir,
                                     'site{site}_rest_sub{participant}_sess{session}_ser_{series}.nii.gz')

        # Add include sites to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_template
        data_config_dict['functionalTemplate'] = func_template

        # Return found filepaths from subject list
        filepaths = self._return_sublist_filepaths(data_config_dict)

        # And check them
        properly_filtered, filter_msg = \
            self._check_filepaths(filepaths, subs_match_regex, include=True)

        # Assert resulting list is properly filtered
        self.assertTrue(properly_filtered, msg=filter_msg)

    # Test for regular expression matching
    def test_local_sublist_regexp_match(self):
        '''
        Method to test that the subject list builder includes only
        desired sites from S3

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Import packages
        import os
        from CPAC.utils import test_init

        # Init variables
        data_config_dict = self.data_config_dict
        subs_match_regex = ['0010042', '0010064', '0010128', '0021019', '0023008',
                            '0023008', '0023012', '0027011', '0027018',
                            '0027034', '0027037', '1019436', '1206380', '1418396']

        # Copy original inputs to all same folder with
        # {participant}_{series} in filenames
        base_dir = test_init.return_resource_subfolder('input_reorg_files')

        # Set up local templates
        anat_template = os.path.join(base_dir,
                                     '[si]?*{site}_mprage_sub{participant}_sess{session}_ser_{series}.nii.gz')
        func_template = os.path.join(base_dir,
                                     '?[si]*{site}_rest_sub{participant}_sess{session}_ser_{series}.nii.gz')

        # Add include sites to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_template
        data_config_dict['functionalTemplate'] = func_template

        # Return found filepaths from subject list
        filepaths = self._return_sublist_filepaths(data_config_dict)

        # And check them
        properly_filtered, filter_msg = \
            self._check_filepaths(filepaths, subs_match_regex, include=True)

        # Assert resulting list is properly filtered
        self.assertTrue(properly_filtered, msg=filter_msg)

    # Function to test the custom glob pattern matcher
    def test_check_glob_for_patterns(self):
        '''
        '''

        # Import packages
        from CPAC.utils import build_sublist

        # Init variables
        prefix_delim = 's?[si]ite_[a-z]?'
        filepath = 'sisite_hi_sub001_sess1.nii.gz'
        correct_delim = 'sisite_hi'

        # Return filtered delimeter
        new_delim = build_sublist.check_for_glob_patterns(prefix_delim, filepath)

        # Assert equal
        err_msg = 'returned delim: %s does not match %s! Check function!' % \
                  (new_delim, correct_delim)
        self.assertEqual(new_delim, correct_delim, err_msg)

    # Test for un-specific template
    def test_ambiguous_template(self):
        '''
        Function that tests the subject list cannot be built properly
        with an over-ambiguous path template

        Parameters
        ----------
        self : BuildSublistTestCase
            a unittest.TestCase-inherited class
        '''

        # Import packages
        import os
        from CPAC.utils import build_sublist, test_init

        # Init variables
        # Init variables
        data_config_dict = self.data_config_dict

        # Copy original inputs to all same folder with
        # {participant}_{series} in filenames
        base_dir = test_init.return_resource_subfolder('input_reorg_files')

        # Set up local templates
        anat_template = os.path.join(base_dir,
                                     '{site}_mprage_{participant}_{session}_{series}.nii.gz')
        func_template = os.path.join(base_dir,
                                     '{site}_rest_{participant}_{session}_{series}.nii.gz')

        # Add include sites to data config dictionary
        data_config_dict['anatomicalTemplate'] = anat_template
        data_config_dict['functionalTemplate'] = func_template

        # Build subject list
        try:
            self._return_sublist_filepaths(data_config_dict)
        except Exception as exc:
            self.assertIsInstance(exc, Exception)

# Make module executable
if __name__ == '__main__':
    unittest.main()
