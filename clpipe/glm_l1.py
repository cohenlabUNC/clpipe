import os
import glob
import logging
def glm_l1_propagate(glm_config):

    return 0



def _glm_l1_propagate(l1_block, glm_setup_options):

    if l1_block['ImageIncludeList'] is not "" and l1_block['ImageExcludeList'] is not "":
        raise ValueError("Only one of ImageIncludeList and ImageExcludeList should be non-empty")

    image_files = glob.glob(os.path.joinl1_block['TargetFolder'], "**", "*", os.path.joinl1_block['TargetFolder'], recursive = True)

    if l1_block['ImageIncludeList'] is not "":
        image_files = [file_path for file_path in image_files if os.path.basename(file_path) in l1_block['ImageIncludeList']]
        base_names = [os.path.basename(file_path) for file_path in image_files]

        files_not_found = [file for file in image_files if file not in base_names]
        if len(files_not_found):
            logging.warning("Did not find the following files: " + str(files_not_found))

    if l1_block['ImageIncludeList'] is not "":
        image_files = [file_path for file_path in image_files if
                       os.path.basename(file_path) not in l1_block['ImageExcludeList']]

#Design

#Step 1: Load in prototype, identify all needed lines
#Step 2: Load in paths for all image files, exclude/include as needed
#Step 3: run through all required image files, construct the file changes
#Step 3a: Change prototype and spit out into fsf output folder

