

def main(pd, clust_name, **kwargs):
    '''
    Get center, radius and flags for semi automatic mode.
    '''
    mode = pd['mode']
    # Dummy values.
    pd['cl_cent_semi'], pd['cl_rad_semi'], pd['cl_f_regs_semi'],\
        pd['cent_flag_semi'], pd['rad_flag_semi'],\
        pd['freg_flag_semi'], pd['err_flag_semi'] = [], -1., 0, 0,\
        0, 0, 0
    # Mode is semi.
    if mode == 'semi':

        semi_file = 'semi_input.dat'
        # Flag to indicate if cluster was found in file.
        flag_clust_found = False
        with open(semi_file, "r") as f_cl_dt:
            for line in f_cl_dt:
                li = line.strip()
                # Skip comments.
                if not li.startswith("#"):
                    reader = li.split()

                    # Prevent empty lines with spaces detected as a cluster
                    # line from crashing the code.
                    if reader:
                        # If cluster is found in file.
                        if reader[0] == clust_name:
                            cl_cent_semi = [float(reader[1]), float(reader[2])]
                            cl_rad_semi = float(reader[3])
                            cl_f_regs_semi = int(reader[4])
                            cent_flag_semi, rad_flag_semi, freg_flag_semi, \
                                err_flag_semi = int(reader[5]), \
                                int(reader[6]), int(reader[7]), int(reader[8])
                            # Set flag to True if the cluster was found.
                            flag_clust_found = True

        # If cluster was found.
        if flag_clust_found:
            # Update 'semi' mode data to dictionary.
            pd['cl_cent_semi'], pd['cl_rad_semi'], pd['cl_f_regs_semi'],\
                pd['cent_flag_semi'], pd['rad_flag_semi'],\
                pd['freg_flag_semi'], pd['err_flag_semi'] = cl_cent_semi,\
                cl_rad_semi, cl_f_regs_semi, cent_flag_semi, rad_flag_semi,\
                freg_flag_semi, err_flag_semi
        else:
            # If the cluster was not found in the file, default to 'auto'.
            print ("  WARNING: cluster's name not found in 'semi_input.dat'\n"
                   "  file. Defaulting to 'auto' mode.")
            # Re-define mode parameter.
            pd['mode'] = 'auto'

    return pd
