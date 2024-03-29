{
	"descriptions": [
		{
			"dataType": "anat",
			"modalityLabel": "T1w",
			"criteria": {
				"SeriesDescription": "*t1*"
			}
		},
		{
			"dataType": "func",
			"modalityLabel": "bold",
			"customLabels": "task-srt",
			"sidecarChanges": {
				"TaskName": "srt"
			},
			"criteria": {
				"SeriesDescription": "*_srt"
			}
		},
		{
			"dataType": "fmap",
			"modalityLabel": "epi",
			"customLabels": "dir-AP",
			"criteria": {
				"SeriesDescription": "*AP*"
			},
			"intendedFor": [
				1
			]
		}
	],
	"dcm2niixOptions": "-b y -ba y -z y -f '%3s_%f_%p_%t' -d 9"
}