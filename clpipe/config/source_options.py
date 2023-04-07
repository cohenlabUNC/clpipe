from dataclasses import dataclass

@dataclass
class SourceOptions:
    SourceURL: str
    @property
    def SourceURL(self):
        return self._SourceURL
    @SourceURL.setter
    def SourceURL(self, value):
        if value is not None:
            self._SourceURL = value

    DropoffDirectory: str
    @property
    def DropoffDirectory(self):
        return self._DropoffDirectory
    @DropoffDirectory.setter
    def DropoffDirectory(self, value):
        if value is not None:
            self._DropoffDirectory = value

    TempDirectory: str
    @property
    def TempDirectory(self):
        return self._TempDirectory
    @TempDirectory.setter
    def TempDirectory(self, value):
        if value is not None:
            self._TempDirectory = value

    CommandLineOpts: str
    @property
    def CommandLineOpts(self):
        return self._CommandLineOpts
    @CommandLineOpts.setter
    def CommandLineOpts(self, value):
        if value is not None:
            self._CommandLineOpts = value

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

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True
