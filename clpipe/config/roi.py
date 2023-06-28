from dataclasses import dataclass

@dataclass
class ROIExtractionOptions:
    TargetDirectory: str
    @property
    def TargetDirectory(self):
        return self._TargetDirectory
    @TargetDirectory.setter
    def TargetDirectory(self, value):
        if value is not None:
            self._TargetDirectory = value

    TargetSuffix: str
    @property
    def TargetSuffix(self):
        return self._TargetSuffix
    @TargetSuffix.setter
    def TargetSuffix(self, value):
        if value is not None:
            self._TargetSuffix = value

    OutputDirectory: str
    @property
    def OutputDirectory(self):
        return self._OutputDirectory
    @OutputDirectory.setter
    def OutputDirectory(self, value):
        if value is not None:
            self._OutputDirectory = value

    Atlases: list
    @property
    def Atlases(self):
        return self._Atlases
    @Atlases.setter
    def Atlases(self, value):
        if value is not None:
            self._Atlases = value

    RequireMask: bool
    @property
    def RequireMask(self):
        return self._RequireMask
    @RequireMask.setter
    def RequireMask(self, value):
        if value is not None:
            self._RequireMask = value

    PropVoxels: float
    @property
    def PropVoxels(self):
        return self._PropVoxels
    @PropVoxels.setter
    def PropVoxels(self, value):
        if value is not None:
            self._PropVoxels = value

    MemoryUsage: str
    @property
    def MemoryUsage(self):
        return self._MemoryUsage
    @MemoryUsage.setter
    def MemoryUsage(self, value):
        if value is not None:
            self._MemoryUsage = value

    TimeUsage: str
    @property
    def TimeUsage(self):
        return self._TimeUsage
    @TimeUsage.setter
    def TimeUsage(self, value):
        if value is not None:
            self._TimeUsage = value

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

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True
