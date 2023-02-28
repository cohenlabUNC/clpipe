from dataclasses import dataclass

@dataclass
class BetaSeries:
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

    OutputSuffix: str
    @property
    def OutputSuffix(self):
        return self._OutputSuffix
    @OutputSuffix.setter
    def OutputSuffix(self, value):
        if value is not None:
            self._OutputSuffix = value

    ConfoundSuffix: str
    @property
    def ConfoundSuffix(self):
        return self._ConfoundSuffix
    @ConfoundSuffix.setter
    def ConfoundSuffix(self, value):
        if value is not None:
            self._ConfoundSuffix = value

    Regress: bool
    @property
    def Regress(self):
        return self._Regress
    @Regress.setter
    def Regress(self, value):
        if value is not None:
            self._Regress = value

    NuisanceRegression: str
    @property
    def NuisanceRegression(self):
        return self._NuisanceRegression
    @NuisanceRegression.setter
    def NuisanceRegression(self, value):
        if value is not None:
            self._NuisanceRegression = value

    WhiteMatter: bool
    @property
    def WhiteMatter(self):
        return self._WhiteMatter
    @WhiteMatter.setter
    def WhiteMatter(self, value):
        if value is not None:
            self._WhiteMatter = value

    CSF: bool
    @property
    def CSF(self):
        return self._CSF
    @CSF.setter
    def CSF(self, value):
        if value is not None:
            self._CSF = value

    GlobalSignalRegression: bool
    @property
    def GlobalSignalRegression(self):
        return self._GlobalSignalRegression
    @GlobalSignalRegression.setter
    def GlobalSignalRegression(self, value):
        if value is not None:
            self._GlobalSignalRegression = value

    FilteringHighPass: float
    @property
    def FilteringHighPass(self):
        return self._FilteringHighPass
    @FilteringHighPass.setter
    def FilteringHighPass(self, value):
        if value is not None:
            self._FilteringHighPass = value

    FilteringLowPass: int
    @property
    def FilteringLowPass(self):
        return self._FilteringLowPass
    @FilteringLowPass.setter
    def FilteringLowPass(self, value):
        if value is not None:
            self._FilteringLowPass = value

    FilteringOrder: int
    @property
    def FilteringOrder(self):
        return self._FilteringOrder
    @FilteringOrder.setter
    def FilteringOrder(self, value):
        if value is not None:
            self._FilteringOrder = value

    TaskSpecificOptions: list
    @property
    def TaskSpecificOptions(self):
        return self._TaskSpecificOptions
    @TaskSpecificOptions.setter
    def TaskSpecificOptions(self, value):
        if value is not None:
            self._TaskSpecificOptions = value

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
