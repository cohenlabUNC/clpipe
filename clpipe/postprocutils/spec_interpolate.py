import numpy
import math
import logging


def spec_inter(arr, tr, ofreq, scrub_mask, hifreq, binSize):
    scrub_mask = numpy.asarray(scrub_mask)
    goodtpindex = numpy.asarray([[i for i, e in enumerate(scrub_mask) if e == 0]])
    badtpindex = numpy.asarray([[i for i, e in enumerate(scrub_mask) if e == 1]])
    tobs_good = (goodtpindex + 1) * tr
    timespan = tobs_good.max() - tobs_good.min()
    tpobs_all = numpy.arange(tr, tr * float(scrub_mask.shape[0] + 1), tr)
    freq = numpy.arange(
        1 / (timespan * ofreq),
        hifreq * tobs_good.shape[1] / (2 * timespan) + 1 / (timespan * ofreq),
        1 / (timespan * ofreq),
    )[numpy.newaxis]
    freqang = 2.0 * math.pi * freq
    offsets = numpy.arctan2(
        numpy.sin(numpy.matmul(numpy.transpose(2 * freqang), tobs_good)).sum(1),
        numpy.cos(numpy.matmul(numpy.transpose(2 * freqang), tobs_good)).sum(1),
    ) / (2 * freqang)
    costerm = numpy.cos(
        numpy.matmul(numpy.transpose(freqang), tobs_good) - (offsets * freqang).T
    )
    sinterm = numpy.sin(
        numpy.matmul(numpy.transpose(freqang), tobs_good) - (offsets * freqang).T
    )
    totbins = math.ceil(float(arr.shape[1]) / float(binSize))
    binnedRecon = []
    for bin in range(0, totbins):
        logging.debug("Bin " + str(bin) + " out of " + str(totbins))
        binVox = numpy.arange(bin * binSize, (bin + 1) * binSize, 1)
        binVox = numpy.delete(
            binVox, [i for i, e in enumerate(binVox) if e >= arr.shape[1]]
        )
        gooddata = arr[goodtpindex.T, binVox]
        cosMultTemp = [
            numpy.matmul(costerm[:, i][numpy.newaxis].T, gooddata[i, :][numpy.newaxis])
            for i in range(0, tobs_good.shape[1])
        ]
        cosmult = numpy.dstack(cosMultTemp)
        num = cosmult.sum(axis=2)
        dem = (numpy.power(costerm, 2)).sum(axis=1)[numpy.newaxis].T
        cosine = num / dem
        sinMultTemp = [
            numpy.matmul(sinterm[:, i][numpy.newaxis].T, gooddata[i, :][numpy.newaxis])
            for i in range(0, tobs_good.shape[1])
        ]
        sinmult = numpy.dstack(sinMultTemp)
        num = sinmult.sum(axis=2)
        dem = (numpy.power(sinterm, 2)).sum(axis=1)[numpy.newaxis].T
        sine = num / dem
        freqRep = numpy.dstack([freqang * tp for tp in tpobs_all])[0, :, :].T
        sin_t = numpy.sin(freqRep)
        cos_t = numpy.cos(freqRep)
        S = numpy.matmul(sin_t, sine)
        C = numpy.matmul(cos_t, cosine)
        temp = C + S
        binnedRecon.append(temp)
    recon = numpy.hstack(binnedRecon)
    recon_std = numpy.std(recon, 0, ddof=1)
    data_std = numpy.std(arr[goodtpindex, :], 1, ddof=1)
    data_std[data_std == 0] = -1
    with numpy.errstate(divide="ignore", invalid="ignore"):
        cor_factor = recon_std / data_std
        recon = recon / cor_factor
    numpy.nan_to_num(recon, copy=False)
    corr_arr = numpy.copy(arr)
    if badtpindex.shape[1] != 0:
        corr_arr[badtpindex, :] = recon[badtpindex, :]
    return corr_arr
