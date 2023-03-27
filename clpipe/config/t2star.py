from dataclasses import dataclass

@dataclass
class T2StarExtraction:
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

    ExclusionFile: str
    @property
    def ExclusionFile(self):
        return self._ExclusionFile
    @ExclusionFile.setter
    def ExclusionFile(self, value):
        if value is not None:
            self._ExclusionFile = value

    WorkingDirectory: str
    @property
    def WorkingDirectory(self):
        return self._WorkingDirectory
    @WorkingDirectory.setter
    def WorkingDirectory(self, value):
        if value is not None:
            self._WorkingDirectory = value

    MaskDirectory: str
    @property
    def MaskDirectory(self):
        return self._MaskDirectory
    @MaskDirectory.setter
    def MaskDirectory(self, value):
        if value is not None:
            self._MaskDirectory = value

    MaskSuffix: str
    @property
    def MaskSuffix(self):
        return self._MaskSuffix
    @MaskSuffix.setter
    def MaskSuffix(self, value):
        if value is not None:
            self._MaskSuffix = value

    MaskFileOverride: str
    @property
    def MaskFileOverride(self):
        return self._MaskFileOverride
    @MaskFileOverride.setter
    def MaskFileOverride(self, value):
        if value is not None:
            self._MaskFileOverride = value

    OutputDirectory: str
    @property
    def OutputDirectory(self):
        return self._OutputDirectory
    @OutputDirectory.setter
    def OutputDirectory(self, value):
        if value is not None:
            self._OutputDirectory = value

    OutputSuffix: str
    @property
    def OutputSuffix(self):
        return self._OutputSuffix
    @OutputSuffix.setter
    def OutputSuffix(self, value):
        if value is not None:
            self._OutputSuffix = value

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
