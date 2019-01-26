import numpy as np


def joint_mask(subjects, mask_file):
    """
    Creates a joint mask (intersection) common to all the subjects in a provided list
    and a provided mask
    
    Parameters
    ----------
    subjects : dict of strings
        A length `N` list of file paths of the nifti files of subjects
    mask_file : string
        Path to a mask file in nifti format
    
    Returns
    -------
    joint_mask : string
        Path to joint mask file in nifti format
    
    """
    import nibabel as nb
    import numpy as np
    import os
    from CPAC.pipeline.cpac_ga_model_generator import (
        create_merged_copefile, create_merge_mask)
    
    if not mask_file:
        files = list(subjects.values())
        cope_file = os.path.join(os.getcwd(), 'joint_cope.nii.gz')
        mask_file = os.path.join(os.getcwd(), 'joint_mask.nii.gz')
        create_merged_copefile(files, cope_file)
        create_merge_mask(cope_file, mask_file)

    return mask_file


def norm_cols(X):
    Xc = X - X.mean(0)
    return Xc / np.sqrt(Xc ** 2.).sum(axis=0)


def norm_subjects(subjects_data):
    return subjects_data.apply_along_axis(norm_cols, axis=0)


def ncor(normed_data, vox_inds):
    return normed_data[:, vox_inds].T.dot(normed_data)


def ncor_subjects(subjects_normed_data, vox_ind):
    nSubjects, _, nVoxels = subjects_normed_data.shape
    S                     = np.zeros((nSubjects, nVoxels))

    for i in range(nSubjects):
        S[i] = ncor(subjects_normed_data[i], vox_ind)
    
    return S


def fischers_transform(S):
    return np.arctanh(S)


def compute_distances(S0):
    S0   = norm_cols(S0.T).T
    dmat = 1 - S0.dot(S0.T)
    return dmat


def calc_mdmrs(D, regressor, cols, permutations):
    from CPAC.cwas.mdmr import mdmr

    voxels = D.shape[0]
    subjects = D.shape[1]
    
    F_set = np.zeros(voxels)
    p_set = np.zeros(voxels)

    cols = np.array(cols, dtype=np.int32)
    
    for i in range(voxels):
        F_set[i], p_set[i] = mdmr(D[i].reshape(subjects ** 2, 1), regressor, cols, permutations)
    
    return F_set, p_set


def calc_subdists(subjects_data, voxel_range):
    subjects      = len(subjects_data)
    voxels        = len(voxel_range)

    subjects_normed_data = np.apply_along_axis(norm_cols, axis=0, arr=subjects_data)
    D = np.zeros((voxels, subjects, subjects))
        
    for i, v in enumerate(voxel_range):
        S    = ncor_subjects(subjects_normed_data, v)
        S0   = np.delete(S, i, 1)  # remove autocorrelations
        S0   = fischers_transform(S0)
        D[i] = compute_distances(S0)
    
    return D


def calc_cwas(subjects_data, regressor, regressor_selected_cols, permutations, voxel_range):
    D            = calc_subdists(subjects_data, voxel_range)
    F_set, p_set = calc_mdmrs(D, regressor, regressor_selected_cols, permutations)
    return F_set, p_set


def nifti_cwas(subjects, mask_file, regressor_file, participant_column,
               columns_string, permutations, voxel_range):
    """
    Performs CWAS for a group of subjects
    
    Parameters
    ----------
    subjects : dict of strings:strings
        A length `N` dict of id and file paths of the nifti files of subjects
    mask_file : string
        Path to a mask file in nifti format
    regressor_file : string
        file path to regressor CSV or TSV file (phenotypic info)
    columns_string : string
        comma-separated string of regressor labels
    permutations : integer
        Number of pseudo f values to sample using a random permutation test
    voxel_range : ndarray
        Indexes from range of voxels (inside the mask) to perform cwas on.
        Index ordering is based on the np.where(mask) command
    
    Returns
    -------
    F_file : string
        .npy file of pseudo-F statistic calculated for every voxel
    p_file : string
        .npy file of significance probabilities of pseudo-F values
    voxel_range : tuple
        Passed on by the voxel_range provided in parameters, used to make parallelization
        easier
        
    """
    import pandas as pd
    import nibabel as nb
    import numpy as np
    import os
    from CPAC.cwas.cwas import calc_cwas

    try:
        regressor_data = pd.read_table(regressor_file, sep=None, engine="python",
                                       dtype={ participant_column: str })
    except:
        regressor_data = pd.read_table(regressor_file, sep=None, engine="python")
        regressor_data = regressor_data.astype({participant_column: str})

    # drop duplicates
    regressor_data = regressor_data.drop_duplicates()

    regressor_cols = list(regressor_data.columns)
    if not participant_column in regressor_cols:
        raise ValueError('Participant column was not found in regressor file.')

    if participant_column in columns_string:
        raise ValueError('Participant column can not be a regressor.')

    subject_ids = list(subjects.keys())
    subject_files = list(subjects.values())

    # check for inconsistency with leading zeroes
    # (sometimes, the sub_ids from individual will be something like
    #  '0002601' and the phenotype will have '2601')
    for index, row in regressor_data.iterrows():
        pheno_sub_id = str(row[participant_column])
        for sub_id in subject_ids:
            if str(sub_id).lstrip('0') == str(pheno_sub_id):
                regressor_data.at[index, participant_column] = str(sub_id)

    regressor_data.index = regressor_data[participant_column]

    # Keep only data from specific subjects
    ordered_regressor_data = regressor_data.loc[subject_ids]

    columns = columns_string.split(',')
    regressor_selected_cols = [i for i, c in enumerate(regressor_cols) if c in columns]

    if len(regressor_selected_cols) == 0:
        regressor_selected_cols = [i for i, c in enumerate(regressor_cols)]
    regressor_selected_cols = np.array(regressor_selected_cols)

    # Remove participant id column from the dataframe and convert it to a numpy matrix
    regressor = ordered_regressor_data \
                    .drop(columns=[participant_column]) \
                    .reset_index(drop=True) \
                    .as_matrix() \
                    .astype(np.float64)

    if len(regressor.shape) == 1:
        regressor = regressor[:, np.newaxis]
    elif len(regressor.shape) != 2:
        raise ValueError('Bad regressor shape: %s' % str(regressor.shape))
    
    if len(subject_files) != regressor.shape[0]:
        raise ValueError('Number of subjects does not match regressor size')
    
    mask = nb.load(mask_file).get_data().astype('bool')
    mask_indices = np.where(mask)

    subjects_data = [
        nb.load(subject_file).get_data().astype('float64')[mask_indices].T 
        for subject_file in subject_files
    ]
    
    F_set, p_set = calc_cwas(subjects_data, regressor, regressor_selected_cols, \
                             permutations, voxel_range)
    
    cwd = os.getcwd()
    F_file = os.path.join(cwd, 'pseudo_F.npy')
    p_file = os.path.join(cwd, 'significance_p.npy')

    np.save(F_file, F_set)
    np.save(p_file, p_set)
    
    return F_file, p_file, voxel_range


def create_cwas_batches(mask_file, batches):
    import nibabel as nb
    import numpy as np

    mask = nb.load(mask_file).get_data().astype('bool')
    voxels = mask.sum(dtype=int)

    return np.array_split(np.arange(voxels), batches)


def merge_cwas_batches(cwas_batches, mask_file):
    import numpy as np
    import nibabel as nb
    import os
    
    def volumize(mask, data):
        volume = np.zeros_like(mask, dtype=data.dtype)
        volume[np.where(mask==True)] = data
        return volume
    
    F_files, p_files, voxel_range = zip(*cwas_batches)
    voxels = np.array(np.concatenate(voxel_range))

    nii = nb.load(mask_file)
    mask = nii.get_data().astype('bool')
    
    F_set = np.zeros_like(voxels)
    p_set = np.zeros_like(voxels)
    for F_file, p_file, voxel_range in cwas_batches:
        F_set[voxel_range] = np.load(F_file)
        p_set[voxel_range] = np.load(p_file)
    
    F_vol = volumize(mask, F_set)
    p_vol = volumize(mask, p_set)
    
    cwd = os.getcwd()
    F_file = os.path.join(cwd, 'pseudo_F_volume.nii.gz')
    p_file = os.path.join(cwd, 'p_significance_volume.nii.gz')
    
    img = nb.Nifti1Image(F_vol, header=nii.get_header(), affine=nii.get_affine())
    img.to_filename(F_file)
    img = nb.Nifti1Image(p_vol, header=nii.get_header(), affine=nii.get_affine())
    img.to_filename(p_file)
    
    return F_file, p_file
