from dataclasses import dataclass

@dataclass
class BIDSValidatorConfig:
    BIDSValidatorImage: str
    @property
    def BIDSValidatorImage(self):
        return self._BIDSValidatorImage
    @BIDSValidatorImage.setter
    def BIDSValidatorImage(self, value):
        if value is not None:
            self._BIDSValidatorImage = value

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

@dataclass
class Convert2BIDSConfig:
    #Add variable names exactly same as json file
    DICOMDirectory: str
    @property
    def DICOMDirectory(self):
        return self._DICOMDirectory
    @DICOMDirectory.setter
    def DICOMDirectory(self, value):
        if value is not None:
            self._DICOMDirectory = value

    BIDSDirectory: str
    @property
    def BIDSDirectory(self):
        return self._BIDSDirectory
    @BIDSDirectory.setter
    def BIDSDirectory(self, value):
        if value is not None:
            self._BIDSDirectory = value

    ConversionConfig: str
    @property
    def ConversionConfig(self):
        return self._ConversionConfig
    @ConversionConfig.setter
    def ConversionConfig(self, value):
        if value is not None:
            self._ConversionConfig = value

    DICOMFormatString: str
    @property
    def DICOMFormatString(self):
        return self._DICOMFormatString
    @DICOMFormatString.setter
    def DICOMFormatString(self, value):
        if value is not None:
            self._DICOMFormatString = value

    TimeUsage: str
    @property
    def TimeUsage(self):
        return self._TimeUsage
    @TimeUsage.setter
    def TimeUsage(self, value):
        if value is not None:
            self._TimeUsage = value

    MemUsage: str
    @property
    def MemUsage(self):
        return self._MemUsage
    @MemUsage.setter
    def MemUsage(self, value):
        if value is not None:
            self._MemUsage = value

    CoreUsage: str
    @property
    def CoreUsage(self):
        return self._CoreUsage
    @CoreUsage.setter
    def CoreUsage(self, value):
        if value is not None:
            self._CoreUsage = value

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
