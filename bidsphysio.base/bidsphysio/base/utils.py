import gzip
import json
from pathlib import Path


def check_bidsphysio_outputs(outPrefix,
                             expectedPhysioLabels,
                             expectedFrequencies,
                             expectedDelay,
                             expectedDataFilePrefix,
                             ):
    """
    Auxiliary function to check the output of running dcm2bids

    Parameters
    ----------
    outPrefix : Path or str
        Prefix of the path of the output of dcm2bids (the bidsprefix arg).
        E.g.: '/tmp/mydir/sub-01_task-rest'
    expectedPhysioLabels : list
        List with the expected physio labels
    expectedFrequencies : list
        List of the expected frequencies for the recordings (in Hz.)
    expectedDelay : float
        Expected delay for the physio signals (in sec.)
    expectedDataFilePrefix : Path or str or None
        Prefix of the path to the file with the expected data
        (If we don't need to check the results, set to None)
        If there is only one expectedPhysioLabel, the expectedDataFilePrefix
        must be the whols file path (including extension)

    Returns
    -------

    """
    outPrefix = Path(outPrefix)
    if not isinstance(expectedPhysioLabels, list):
        expectedPhysioLabels = [expectedPhysioLabels]
    if not isinstance(expectedFrequencies, list):
        expectedFrequencies = [expectedFrequencies]

    json_files = sorted(outPrefix.parent.glob('*.json'))
    data_files = sorted(outPrefix.parent.glob('*.tsv*'))
    assert len(json_files) == len(data_files) == len(expectedPhysioLabels)

    for label, expFreq in zip(expectedPhysioLabels, expectedFrequencies):
        if len(expectedPhysioLabels) == 1:
            expectedFileBaseName = Path(outPrefix).name + '_physio'
        else:
            expectedFileBaseName = Path(str(outPrefix) + '_recording-' + label + '_physio').name
        expectedFileName = outPrefix.parent / expectedFileBaseName
        assert expectedFileName.with_suffix('.json') in json_files
        assert expectedFileName.with_suffix('.tsv.gz') in data_files

        # check content of the json file:
        with open(expectedFileName.with_suffix('.json')) as f:
            d = json.load(f)
            if isinstance(label, list):
                for c in d['Columns']:
                    assert c in label or c == 'trigger'
            else:
                assert d['Columns'] == [label, 'trigger']
            assert d['StartTime'] == expectedDelay
            assert d['SamplingFrequency'] == expFreq

        # check content of the tsv file:
        if expectedDataFilePrefix:
            if len(expectedPhysioLabels) == 1:
                expectedDataFile = expectedDataFilePrefix
            else:
                expectedDataFile = str(expectedDataFilePrefix) + label + '.tsv'
            with open(expectedDataFile, 'rt') as expected, \
                    gzip.open(expectedFileName.with_suffix('.tsv.gz'), 'rt') as f:
                for expected_line, written_line in zip(expected, f):
                    assert expected_line == written_line
