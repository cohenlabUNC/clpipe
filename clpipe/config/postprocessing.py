from dataclasses import dataclass

DEFAULT_PROCESSING_STREAM = "default"

@dataclass
class TemporalFiltering:
    Implementation: str
    @property
    def Implementation(self):
        return self._Implementation
    @Implementation.setter
    def Implementation(self, value):
        if value is not None:
            self._Implementation = value

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

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class IntensityNormalization:
    Implementation: str
    @property
    def Implementation(self):
        return self._Implementation
    @Implementation.setter
    def Implementation(self, value):
        if value is not None:
            self._Implementation = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class SpatialSmoothing:
    Implementation: str
    @property
    def Implementation(self):
        return self._Implementation
    @Implementation.setter
    def Implementation(self, value):
        if value is not None:
            self._Implementation = value

    FWHM: int
    @property
    def FWHM(self):
        return self._FWHM
    @FWHM.setter
    def FWHM(self, value):
        if value is not None:
            self._FWHM = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class AROMARegression:
    Implementation: str
    @property
    def Implementation(self):
        return self._Implementation
    @Implementation.setter
    def Implementation(self, value):
        if value is not None:
            self._Implementation = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class Resample:
    ReferenceImage: str
    @property
    def ReferenceImage(self):
        return self._ReferenceImage
    @ReferenceImage.setter
    def ReferenceImage(self, value):
        if value is not None:
            self._ReferenceImage = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class ScrubTimepoints:
    TargetVariable: str
    Threshold: float
    ScrubAhead: int
    ScrubBehind: int
    ScrubContiguous: int
    InsertNA: bool
    
    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class TrimTimepoints:
    FromEnd: int
    @property
    def FromEnd(self):
        return self._FromEnd
    @FromEnd.setter
    def FromEnd(self, value):
        if value is not None:
            self._FromEnd = value

    FromBeginning: int
    @property
    def FromBeginning(self):
        return self._FromBeginning
    @FromBeginning.setter
    def FromBeginning(self, value):
        if value is not None:
            self._FromBeginning = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class ConfoundRegression:
    Implementation: str
    @property
    def Implementation(self):
        return self._Implementation
    @Implementation.setter
    def Implementation(self, value):
        if value is not None:
            self._Implementation = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class ProcessingStepOptions:
    TemporalFiltering: TemporalFiltering
    @property
    def TemporalFiltering(self):
        return self._TemporalFiltering
    @TemporalFiltering.setter
    def TemporalFiltering(self, value):
        if value is not None:
            self._TemporalFiltering = value

    IntensityNormalization: IntensityNormalization
    @property
    def IntensityNormalization(self):
        return self._IntensityNormalization
    @IntensityNormalization.setter
    def IntensityNormalization(self, value):
        if value is not None:
            self._IntensityNormalization = value

    SpatialSmoothing: SpatialSmoothing
    @property
    def SpatialSmoothing(self):
        return self._SpatialSmoothing
    @SpatialSmoothing.setter
    def SpatialSmoothing(self, value):
        if value is not None:
            self._SpatialSmoothing = value

    AROMARegression: AROMARegression
    @property
    def AROMARegression(self):
        return self._AROMARegression
    @AROMARegression.setter
    def AROMARegression(self, value):
        if value is not None:
            self._AROMARegression = value

    ScrubTimepoints: ScrubTimepoints
    @property
    def ScrubTimepoints(self):
        return self._ScrubTimepoints
    @ScrubTimepoints.setter
    def ScrubTimepoints(self, value):
        if value is not None:
            self._ScrubTimepoints = value
    
    Resample: Resample
    @property
    def Resample(self):
        return self._Resample
    @Resample.setter
    def Resample(self, value):
        if value is not None:
            self._Resample = value

    TrimTimepoints: TrimTimepoints
    @property
    def TrimTimepoints(self):
        return self._TrimTimepoints
    @TrimTimepoints.setter
    def TrimTimepoints(self, value):
        if value is not None:
            self._TrimTimepoints = value

    ConfoundRegression: ConfoundRegression
    @property
    def ConfoundRegression(self):
        return self._ConfoundRegression
    @ConfoundRegression.setter
    def ConfoundRegression(self, value):
        if value is not None:
            self._ConfoundRegression = value

    

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class MotionOutliers:
    Include: bool
    @property
    def Include(self):
        return self._Include
    @Include.setter
    def Include(self, value):
        if value is not None:
            self._Include = value

    ScrubVar: str
    @property
    def ScrubVar(self):
        return self._ScrubVar
    @ScrubVar.setter
    def ScrubVar(self, value):
        if value is not None:
            self._ScrubVar = value

    Threshold: float
    @property
    def Threshold(self):
        return self._Threshold
    @Threshold.setter
    def Threshold(self, value):
        if value is not None:
            self._Threshold = value

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

    ScrubContiguous: int
    @property
    def ScrubContiguous(self):
        return self._ScrubContiguous
    @ScrubContiguous.setter
    def ScrubContiguous(self, value):
        if value is not None:
            self._ScrubContiguous = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True



@dataclass
class ConfoundOptions:
    Columns: list
    @property
    def Columns(self):
        return self._Columns
    @Columns.setter
    def Columns(self, value):
        if value is not None:
            self._Columns = value

    MotionOutliers: MotionOutliers
    @property
    def MotionOutliers(self):
        return self._MotionOutliers
    @MotionOutliers.setter
    def MotionOutliers(self, value):
        if value is not None:
            self._MotionOutliers = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class BatchOptions:
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

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class PostProcessing:
    WorkingDirectory: str
    @property
    def WorkingDirectory(self):
        return self._WorkingDirectory
    @WorkingDirectory.setter
    def WorkingDirectory(self, value):
        if value is not None:
            self._WorkingDirectory = value

    WriteProcessGraph: bool
    @property
    def WriteProcessGraph(self):
        return self._WriteProcessGraph
    @WriteProcessGraph.setter
    def WriteProcessGraph(self, value):
        if value is not None:
            self._WriteProcessGraph = value

    TargetDirectory: str
    @property
    def TargetDirectory(self):
        return self._TargetDirectory
    @TargetDirectory.setter
    def TargetDirectory(self, value):
        if value is not None:
            self._TargetDirectory = value

    TargetImageSpace: str
    @property
    def TargetImageSpace(self):
        return self._TargetImageSpace
    @TargetImageSpace.setter
    def TargetImageSpace(self, value):
        if value is not None:
            self._TargetImageSpace = value

    TargetTasks: list
    @property
    def TargetTasks(self):
        return self._TargetTasks
    @TargetTasks.setter
    def TargetTasks(self, value):
        if value is not None:
            self._TargetTasks = value

    TargetAcquisitions: list
    @property
    def TargetAcquisitions(self):
        return self._TargetAcquisitions
    @TargetAcquisitions.setter
    def TargetAcquisitions(self, value):
        if value is not None:
            self._TargetAcquisitions = value

    OutputDirectory: str
    @property
    def OutputDirectory(self):
        return self._OutputDirectory
    @OutputDirectory.setter
    def OutputDirectory(self, value):
        if value is not None:
            self._OutputDirectory = value

    ProcessingSteps: list
    @property
    def ProcessingSteps(self):
        return self._ProcessingSteps
    @ProcessingSteps.setter
    def ProcessingSteps(self, value):
        if value is not None:
            self._ProcessingSteps = value

    ProcessingStepOptions: ProcessingStepOptions
    @property
    def ProcessingStepOptions(self):
        return self._ProcessingStepOptions
    @ProcessingStepOptions.setter
    def ProcessingStepOptions(self, value):
        if value is not None:
            self._ProcessingStepOptions = value

    ConfoundOptions: ConfoundOptions
    @property
    def ConfoundOptions(self):
        return self._ConfoundOptions
    @ConfoundOptions.setter
    def ConfoundOptions(self, value):
        if value is not None:
            self._ConfoundOptions = value

    BatchOptions: BatchOptions
    @property
    def BatchOptions(self):
        return self._BatchOptions
    @BatchOptions.setter
    def BatchOptions(self, value):
        if value is not None:
            self._BatchOptions = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True