from dataclasses import dataclass

@dataclass
class PostProcessing:
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

    DropCSV: str
    @property
    def DropCSV(self):
        return self._DropCSV
    @DropCSV.setter
    def DropCSV(self, value):
        if value is not None:
            self._DropCSV = value

    Regress: bool
    @property
    def Regress(self):
        return self._Regress
    @Regress.setter
    def Regress(self, value):
        if value is not None:
            self._Regress = value

    Confounds: list
    @property
    def Confounds(self):
        return self._Confounds
    @Confounds.setter
    def Confounds(self, value):
        if value is not None:
            self._Confounds = value

    ConfoundsQuad: list
    @property
    def ConfoundsQuad(self):
        return self._ConfoundsQuad
    @ConfoundsQuad.setter
    def ConfoundsQuad(self, value):
        if value is not None:
            self._ConfoundsQuad = value

    ConfoundsDerive: list
    @property
    def ConfoundsDerive(self):
        return self._ConfoundsDerive
    @ConfoundsDerive.setter
    def ConfoundsDerive(self, value):
        if value is not None:
            self._ConfoundsDerive = value

    ConfoundsQuadDerive: list
    @property
    def ConfoundsQuadDerive(self):
        return self._ConfoundsQuadDerive
    @ConfoundsQuadDerive.setter
    def ConfoundsQuadDerive(self, value):
        if value is not None:
            self._ConfoundsQuadDerive = value

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

    OversamplingFreq: int
    @property
    def OversamplingFreq(self):
        return self._OversamplingFreq
    @OversamplingFreq.setter
    def OversamplingFreq(self, value):
        if value is not None:
            self._OversamplingFreq = value

    PercentFreqSample: int
    @property
    def PercentFreqSample(self):
        return self._PercentFreqSample
    @PercentFreqSample.setter
    def PercentFreqSample(self, value):
        if value is not None:
            self._PercentFreqSample = value

    Scrubbing: bool
    @property
    def Scrubbing(self):
        return self._Scrubbing
    @Scrubbing.setter
    def Scrubbing(self, value):
        if value is not None:
            self._Scrubbing = value

    ScrubVar: str
    @property
    def ScrubVar(self):
        return self._ScrubVar
    @ScrubVar.setter
    def ScrubVar(self, value):
        if value is not None:
            self._ScrubVar = value

    ScrubFDThreshold: float
    @property
    def ScrubFDThreshold(self):
        return self._ScrubFDThreshold
    @ScrubFDThreshold.setter
    def ScrubFDThreshold(self, value):
        if value is not None:
            self._ScrubFDThreshold = value

    ScrubAhead: int
    @property
    def ScrubAhead(self):
        return self._ScrubAhead
    @ScrubAhead.setter
    def ScrubAhead(self, value):
        if value is not None:
            self._ScrubAhead = value

    ScrubBehind: int
    @property
    def ScrubBehind(self):
        return self._ScrubBehind
    @ScrubBehind.setter
    def ScrubBehind(self, value):
        if value is not None:
            self._ScrubBehind = value

    ScrubContig: int
    @property
    def ScrubContig(self):
        return self._ScrubContig
    @ScrubContig.setter
    def ScrubContig(self, value):
        if value is not None:
            self._ScrubContig = value

    RespNotchFilter: bool
    @property
    def RespNotchFilter(self):
        return self._RespNotchFilter
    @RespNotchFilter.setter
    def RespNotchFilter(self, value):
        if value is not None:
            self._RespNotchFilter = value

    MotionVars: list
    @property
    def MotionVars(self):
        return self._MotionVars
    @MotionVars.setter
    def MotionVars(self, value):
        if value is not None:
            self._MotionVars = value

    RespNotchFilterBand: list
    @property
    def RespNotchFilterBand(self):
        return self._RespNotchFilterBand
    @RespNotchFilterBand.setter
    def RespNotchFilterBand(self, value):
        if value is not None:
            self._RespNotchFilterBand = value

    PostProcessingMemoryUsage: str
    @property
    def PostProcessingMemoryUsage(self):
        return self._PostProcessingMemoryUsage
    @PostProcessingMemoryUsage.setter
    def PostProcessingMemoryUsage(self, value):
        if value is not None:
            self._PostProcessingMemoryUsage = value

    PostProcessingTimeUsage: str
    @property
    def PostProcessingTimeUsage(self):
        return self._PostProcessingTimeUsage
    @PostProcessingTimeUsage.setter
    def PostProcessingTimeUsage(self, value):
        if value is not None:
            self._PostProcessingTimeUsage = value

    NThreads: str
    @property
    def NThreads(self):
        return self._NThreads
    @NThreads.setter
    def NThreads(self, value):
        if value is not None:
            self._NThreads = value

    SpectralInterpolationBinSize: int
    @property
    def SpectralInterpolationBinSize(self):
        return self._SpectralInterpolationBinSize
    @SpectralInterpolationBinSize.setter
    def SpectralInterpolationBinSize(self, value):
        if value is not None:
            self._SpectralInterpolationBinSize = value

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