So the dicom_to_nifti_to_bids_converter_setup command is just to create a heuristic file? — I don’t need to do that because you provided me with one, right? 

Maybe dont call it ‘setup’, sounds kind of ambiguous if I wasnt 100% sure

Will people know to call module load python/3.6.6 every time? It’s only stated in the installation docs

CMD used: module load python/3.6.6

CMD used: Used grab_config_file -outputFile ./testingConfig.json

Only edit made to the config file was the bids directory

Just remember to make sure people know to use relative paths in the command options

CMD used: dicom_to_nifti_to_bids_converter -config_file ./testingConfig.json -heuristic_file ucla_schizkidsconv.py -dicom_directory ./raw_dicoms/{subject}_{session}/*/*/*/*/* -output_directory ./outputBids/ -submit -debug

Successful on first run, going to try validation now

No option to manually specify bids directory? Has to be through config file?

CMD used: bids_validate -config_file ./testingConfig.json -submit -debug

Why would I want to not submit?

Not sure how to interpret the output of the bids validation

Now going to try fmriprep preprocessing

CMD used:  fmriprep_process -config_file ./testingConfig.json -working_dir ./workingDirectory -output_dir ./preprocessedOutput -log_output_dir ./preprocessing_logs -submit -debug