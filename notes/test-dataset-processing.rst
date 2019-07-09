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

Turns out the processing command stops if bids validator finds any errors... which happens since the config.json is copied into the output bids folder

Deleting the created directories and removed the copied config file from the outputBids/ folder and going to re-run

CMD used:  fmriprep_process -config_file ./testingConfig.json -working_dir ./workingDirectory -output_dir ./preprocessedOutput -log_output_dir ./preprocessing_logs -submit -debug

It worked this time, now going to run post processing

CMD used: fmri_postprocess -config_file ./testingConfig.json -target_dir ./preprocessedOutput -output_dir ./postprocessedOutput -log_output_dir ./postprocessing_logs -submit -debug

Not sure what the -batch command really does? Tried it with and without -batch, neither seemed to submit to longleaf

Finally got it working, CMD used: fmri_postprocess -config_file ./testingConfig.json -target_dir ./preprocessedOutput/fmriprep -output_dir ./postprocessedOutput -log_output_dir ./postprocessing_logs -submit -debug 

Why no -batch?

Note: for target dir, had to do /fmriprep in preprocessed output, probably would be confusing for most people.

Going to run ROI Extraction now

CMD used: fmri_roi_extraction -config_file ./testingConfig.json -target_dir ./postprocessedOutput/ -target_suffix “preproc_bold_.nii” -output_dir ./roiextractedOutput -log_output_dir ./roiex_logs -submit -debug

Nothing was created but job was run "successfully"