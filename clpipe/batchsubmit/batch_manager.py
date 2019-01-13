import json
from pkg_resources import resource_stream
from jsonschema import validate
class BatchManager:

    def __init__(self, batchsystemConfig):
        self.jobs = []
        config = json.load(resource_stream(__name__, "batchConfigs/" + batchsystemConfig))

    def addjob(self, job):
        self.jobs.append(job)

