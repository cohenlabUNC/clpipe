# This script was written by Dr. Michael Hallquist and is copied from https://github.com/UNCDEPENdLab/fmri_processing_scripts/blob/master/fsl_regfilt.R

#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

if (length(args) < 3 || length(args) > 5) {
  stop("Expects at least three arguments: input_file, melodic_mix, motion_ics_file, <njobs=4>, <output_fname>.", call.=FALSE)
}

#handle package dependencies
for (pkg in c("speedglm", "oro.nifti", "doParallel", "tictoc", "pracma")) {
  if (!suppressMessages(require(pkg, character.only=TRUE))) {
    message("Installing missing package dependency: ", pkg)
    install.packages(pkg, repo="https://archive.linux.duke.edu/cran/")
    suppressMessages(require(pkg, character.only=TRUE))
  }
}

#core worker function to implement 'non-aggressive' approach in which all component time series are predictors and we only pull out partial effectse of noise components
partialLm <- function(y, X, ivs=NULL) {
  m <- speedlm.fit(y=y, X=X, intercept=FALSE)
  pred <- X[,ivs] %*% coef(m)[ivs]
  return(as.vector(y - pred))
}

# set defaults
njobs <- 4
output_fname <- "ica_aroma/denoised_func_data_nonaggr"

dataset <- args[[1]]
melodic.mix.df <- args[[2]]
motion_components <- args[[3]]

if (length(args) > 3) njobs <- as.integer(args[[4]])
if (length(args) > 4) output_fname <- args[[5]]

output_fname <- sub("\\.nii(\\.gz)*$", "", output_fname, perl = TRUE) # strip extension to avoid double extension in writeNIfTI

stopifnot(file.exists(dataset))
stopifnot(file.exists(motion_components))  

message("Running fslRegFilt.R with ", njobs, " jobs")
message("Reading input dataset: ", dataset)
fmri_ts_data <- readNIfTI(dataset, reorient=FALSE)

melmix <- data.matrix(read.table(melodic.mix.df, header=FALSE, colClasses="numeric"))

nonconst <- apply(fmri_ts_data, c(1,2,3), function(ts) { !all(ts==ts[1]) })
mi <- which(nonconst==TRUE, arr.ind=TRUE)

toprocess <- apply(fmri_ts_data, 4, function(x) x[nonconst]) # becomes a voxels x timepoints matrix
rownames(toprocess) <- 1:nrow(toprocess) #used to set progress bar inside loop
message("fMRI data to analyze consist of ", nrow(toprocess), " voxels and ", ncol(toprocess), " timepoints")

#contains a comma-separated list of flagged components
badics <- as.numeric(strsplit(scan(motion_components, what="character"), ",")[[1]])
cat("The following components will be removed from the data using partial regression:\n")
cat(paste(badics, collapse=", "), "\n\n")

if (njobs > 1) {
    cl <- parallel::makePSOCKcluster(njobs, outfile = "")
    registerDoParallel(cl)
} else {
    registerDoSEQ()
}

message("Starting voxelwise partial regression fitting")
tic("partialLm fitting")
system.time(res <- foreach(v=iter(toprocess, by="row"), .noexport="fmri_ts_data", .packages="speedglm", .inorder=TRUE, .multicombine=TRUE, .combine=rbind) %dopar% { #, .options.snow = opts
  it <- as.numeric(row.names(v)[1]) #use row number to set progress bar
  if (it %% 1000 == 0) { cat("  Fitting voxel: ", it, "\n") }

  partialLm(matrix(v, ncol=1), melmix, badics)
})
toc()

if (njobs > 1) {
  stopCluster(cl)
}

#back to old repmat strategy
miassign <- cbind(pracma::repmat(mi, ncol(res), 1), rep(1:ncol(res), each=nrow(res)))

fmri_ts_data@.Data[miassign] <- res

#add min/max to header to have it play well across packages
fmri_ts_data@cal_min <- min(fmri_ts_data)
fmri_ts_data@cal_max <- max(fmri_ts_data)
writeNIfTI(fmri_ts_data, filename = output_fname)
