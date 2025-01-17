# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ** University of Illinois, Urbana-Champaign
 # ============================*
 
 
 
import os
import netCDF4
import numpy as np
import datetime
from scipy import stats


def parse_steps():

    steps_param_fcst = os.environ.get('FCST_STEPS','')
    steps_list_fcst = steps_param_fcst.split("+")

    steps_param_obs = os.environ.get('OBS_STEPS','')
    steps_list_obs = steps_param_obs.split("+")

    return steps_list_fcst, steps_list_obs


def write_mpr_file(data_obs,data_fcst,lats_in,lons_in,time_obs,time_fcst,mname,desc,fvar,funit,flev,ovar,ounit,olev,maskname,obslev,outfile):

    dlength = len(lons_in)
    bdims = data_obs.shape

    index_num = np.arange(0,dlength,1)+1

    # Get the length of the model, FCST_VAR, FCST_LEV, OBS_VAR, OBS_LEV, VX_MASK
    mname_len = str(max([5,len(mname)])+3)
    desc_len = str(max([4,len(mname)])+1)
    mask_len = str(max([7,len(maskname)])+3)
    fvar_len = str(max([8,len(fvar)])+3)
    funit_len = str(max([8,len(funit)])+3)
    flev_len = str(max([8,len(flev)])+3)
    ovar_len = str(max([7,len(ovar)])+3)
    ounit_len = str(max([8,len(ounit)])+3)
    olev_len = str(max([7,len(olev)])+3)

    format_string = '%-7s %-'+mname_len+'s %-'+desc_len+'s %-12s %-18s %-18s %-12s %-17s %-17s %-'+fvar_len+'s ' \
        '%-'+funit_len+'s %-'+flev_len+'s %-'+ovar_len+'s %-'+ounit_len+'s %-'+olev_len+'s %-10s %-'+mask_len+'s ' \
        '%-13s %-13s %-13s %-13s %-13s %-13s %-9s\n'
    format_string2 = '%-7s %-'+mname_len+'s %-'+desc_len+'s %-12s %-18s %-18s %-12s %-17s %-17s %-'+fvar_len+'s ' \
        '%-'+funit_len+'s %-'+flev_len+'s %-'+ovar_len+'s %-'+ounit_len+'s %-'+olev_len+'s %-10s %-'+mask_len+'s ' \
        '%-13s %-13s %-13s %-13s %-13s %-13s %-9s %-10s %-10s %-10s %-12.4f %-12.4f %-10s %-10s %-12.4f %-12.4f ' \
        '%-10s %-10s %-10s %-10s\n'

     # Write the file
    for y in range(bdims[0]):
        for dd in range(bdims[1]):
            if time_fcst['valid'][y][dd]:
                ft_stamp = time_fcst['lead'][y][dd]+'L_'+time_fcst['valid'][y][dd][0:8]+'_' \
                    +time_fcst['valid'][y][dd][9:15]+'V'
                mpr_outfile_name = outfile+'_'+ft_stamp+'.stat'
                with open(mpr_outfile_name, 'w') as mf:
                    mf.write(format_string % ('VERSION', 'MODEL', 'DESC', 'FCST_LEAD', 'FCST_VALID_BEG', 'FCST_VALID_END',
                        'OBS_LEAD', 'OBS_VALID_BEG', 'OBS_VALID_END', 'FCST_VAR', 'FCST_UNITS', 'FCST_LEV', 'OBS_VAR', 
                        'OBS_UNITS', 'OBS_LEV', 'OBTYPE', 'VX_MASK', 'INTERP_MTHD', 'INTERP_PNTS', 'FCST_THRESH', 
                        'OBS_THRESH', 'COV_THRESH', 'ALPHA', 'LINE_TYPE'))
                    for dpt in range(dlength):
                        mf.write(format_string2 % ('V9.1',mname,desc,time_fcst['lead'][y][dd],time_fcst['valid'][y][dd],
                            time_fcst['valid'][y][dd],time_obs['lead'][y][dd],time_obs['valid'][y][dd],
                            time_obs['valid'][y][dd],fvar,funit,flev,ovar,ounit,olev,'ADPUPA',maskname,
                            'NEAREST','1','NA','NA','NA','NA','MPR',str(dlength),str(index_num[dpt]),'NA',
                            lats_in[dpt],lons_in[dpt],obslev,'NA',data_fcst[y,dd,dpt],data_obs[y,dd,dpt],'NA','NA',
                            'NA','NA'))


def read_nc_met(infiles,invar,nseasons,dseasons):

    print("Reading in Data")

    # Check to make sure that everything is not set to missing:
    if all('missing' == fn for fn in infiles):
        raise Exception('No input files found as given, check paths to input files')

    #Find the first non empty file name so I can get the variable sizes
    locin = next(sub for sub in infiles if sub != 'missing')
    indata = netCDF4.Dataset(locin)
    lats = indata.variables['lat'][:]
    lons = indata.variables['lon'][:]
    invar_arr = indata.variables[invar][:]
    indata.close()

    var_3d = np.empty([len(infiles),len(invar_arr[:,0]),len(invar_arr[0,:])])
    init_list = []
    valid_list = []
    lead_list = []

    for i in range(0,len(infiles)):

        #Read in the data
        if (infiles[i] != 'missing'):
            indata = netCDF4.Dataset(infiles[i])
            new_invar = indata.variables[invar][:]

            init_time_str = indata.variables[invar].getncattr('init_time')
            valid_time_str = indata.variables[invar].getncattr('valid_time')
            lead_dt = datetime.datetime.strptime(valid_time_str,'%Y%m%d_%H%M%S') - datetime.datetime.strptime(init_time_str,'%Y%m%d_%H%M%S')
            leadmin,leadsec = divmod(lead_dt.total_seconds(), 60)
            leadhr,leadmin = divmod(leadmin,60)
            lead_str = str(int(leadhr)).zfill(2)+str(int(leadmin)).zfill(2)+str(int(leadsec)).zfill(2)
            indata.close()
        else:
            new_invar = np.empty((1,len(var_3d[0,:,0]),len(var_3d[0,0,:])),dtype=np.float)
            init_time_str = ''
            valid_time_str = ''
            lead_str = ''
            new_invar[:] = np.nan
        init_list.append(init_time_str)
        valid_list.append(valid_time_str)
        lead_list.append(lead_str)
        var_3d[i,:,:] = new_invar

    var_4d = np.reshape(var_3d,[nseasons,dseasons,len(var_3d[0,:,0]),len(var_3d[0,0,:])])

    # Reshape time arrays and store them in a dictionary
    init_list_2d = np.reshape(init_list,[nseasons,dseasons])
    valid_list_2d = np.reshape(valid_list,[nseasons,dseasons])
    lead_list_2d = np.reshape(lead_list,[nseasons,dseasons])
    time_dict = {'init':init_list_2d,'valid':valid_list_2d,'lead':lead_list_2d}

    return var_4d,lats,lons,time_dict


def reorder_fcst_regimes(kmeans_fcst,perc_fcst,wrc_fcst,wrnum_fcst,fcst_order):

    # Reorder the data so that the weather regime patterns match between
    # the forecast and observations, is needed
    kmeans_fcst_new = np.empty(kmeans_fcst.shape,dtype=float)
    perc_fcst_new = np.empty(perc_fcst.shape,dtype=float)
    wrc_fcst_new = np.empty(wrc_fcst.shape,dtype=float)
    for wrn in np.arange(wrnum_fcst):
        perc_fcst_new[wrn] = perc_fcst[fcst_order[wrn]-1]
        kmeans_fcst_new[wrn,:,:] = kmeans_fcst[fcst_order[wrn]-1,:,:]
        wrc_cur = np.where(wrc_fcst == fcst_order[wrn])
        wrc_fcst_new[wrc_cur] = wrn + 1

    return kmeans_fcst_new,perc_fcst_new,wrc_fcst_new


def reorder_fcst_regimes_correlate(kmeans_obs,kmeans_fcst,perc_fcst,wrc_fcst,wrnum_fcst):

    # Correlate between the forecast and obs weather regimes to find the max correlation
    # Use the max correlation in reordering the forecast to match the observations
    matching_order = np.empty(wrnum_fcst,dtype=int)
    for wrr in np.arange(wrnum_fcst):
        corr_arr = np.empty(wrnum_fcst,dtype=float)
        for owr in np.arange(wrnum_fcst):
            curcorr = stats.pearsonr(kmeans_obs[wrr,:,:].flatten(),kmeans_fcst[owr,:,:].flatten())
            corr_arr[owr] = curcorr[0]
        matching_order[wrr] = corr_arr.argmax()+1

    # Call the reorder_fcst_regimes to reorder
    matching_order = list(matching_order)
    kmeans_fcst_new,perc_fcst_new,wrc_fcst_new = reorder_fcst_regimes(kmeans_fcst,perc_fcst,wrc_fcst,wrnum_fcst,matching_order)

    return kmeans_fcst_new,perc_fcst_new,wrc_fcst_new 
