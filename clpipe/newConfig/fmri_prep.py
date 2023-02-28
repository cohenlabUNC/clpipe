from dataclasses import dataclass

@dataclass
class FMRIPrep:
    #Add variable names exactly same as json file
    BIDSDirectory: str
    @property
    def BIDSDirectory(self):
        return self._BIDSDirectory
    @BIDSDirectory.setter
    def BIDSDirectory(self, value):
        if value is not None:
            self._BIDSDirectory = value

    WorkingDirectory: str
    @property
    def WorkingDirectory(self):
        return self._WorkingDirectory
    @WorkingDirectory.setter
    def WorkingDirectory(self, value):
        if value is not None:
            self._WorkingDirectory = value

    OutputDirectory: str
    @property
    def OutputDirectory(self):
        return self._OutputDirectory
    @OutputDirectory.setter
    def OutputDirectory(self, value):
        if value is not None:
            self._OutputDirectory = value

    FMRIPrepPath: str
    @property
    def FMRIPrepPath(self):
        return self._FMRIPrepPath
    @FMRIPrepPath.setter
    def FMRIPrepPath(self, value):
        if value is not None:
            self._FMRIPrepPath = value

    FreesurferLicensePath: str
    @property
    def FreesurferLicensePath(self):
        return self._FreesurferLicensePath
    @FreesurferLicensePath.setter
    def FreesurferLicensePath(self, value):
        if value is not None:
            self._FreesurferLicensePath = value

    UseAROMA: bool
    @property
    def UseAROMA(self):
        return self._UseAROMA
    @UseAROMA.setter
    def UseAROMA(self, value):
        if value is not None:
            self._UseAROMA = value

    CommandLineOpts: str
    @property
    def CommandLineOpts(self):
        return self._CommandLineOpts
    @CommandLineOpts.setter
    def CommandLineOpts(self, value):
        if value is not None:
            self._CommandLineOpts = value

    TemplateFlowToggle: bool
    @property
    def TemplateFlowToggle(self):
        return self._TemplateFlowToggle
    @TemplateFlowToggle.setter
    def TemplateFlowToggle(self, value):
        if value is not None:
            self._TemplateFlowToggle = value

    TemplateFlowPath: str
    @property
    def TemplateFlowPath(self):
        return self._TemplateFlowPath
    @TemplateFlowPath.setter
    def TemplateFlowPath(self, value):
        if value is not None:
            self._TemplateFlowPath = value

    TemplateFlowTemplates: list
    @property
    def TemplateFlowTemplates(self):
        return self._TemplateFlowTemplates
    @TemplateFlowTemplates.setter
    def TemplateFlowTemplates(self, value):
        if value is not None:
            self._TemplateFlowTemplates = value

    FMapCleanupROIs: int
    @property
    def FMapCleanupROIs(self):
        return self._FMapCleanupROIs
    @FMapCleanupROIs.setter
    def FMapCleanupROIs(self, value):
        if value is not None:
            self._FMapCleanupROIs = value

    FMRIPrepMemoryUsage: str
    @property
    def FMRIPrepMemoryUsage(self):
        return self._FMRIPrepMemoryUsage
    @FMRIPrepMemoryUsage.setter
    def FMRIPrepMemoryUsage(self, value):
        if value is not None:
            self._FMRIPrepMemoryUsage = value

    FMRIPrepTimeUsage: str
    @property
    def FMRIPrepTimeUsage(self):
        return self._FMRIPrepTimeUsage
    @FMRIPrepTimeUsage.setter
    def FMRIPrepTimeUsage(self, value):
        if value is not None:
            self._FMRIPrepTimeUsage = value

    NThreads: str
    @property
    def NThreads(self):
        return self._NThreads
    @NThreads.setter
    def NThreads(self, value):
        if value is not None:
            self._NThreads = value

    LogDirectory: str
    @property
    def LogDirectory(self):
        return self._LogDirectory
    @LogDirectory.setter
    def LogDirectory(self, value):
        if value is not None:
            self._LogDirectory = value

    DockerToggle: bool
    @property
    def DockerToggle(self):
        return self._DockerToggle
    @DockerToggle.setter
    def DockerToggle(self, value):
        if value is not None:
            self._DockerToggle = value

    DockerFMRIPrepVersion: str
    @property
    def DockerFMRIPrepVersion(self):
        return self._DockerFMRIPrepVersion
    @DockerFMRIPrepVersion.setter
    def DockerFMRIPrepVersion(self, value):
        if value is not None:
            self._DockerFMRIPrepVersion = value
    
    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True
