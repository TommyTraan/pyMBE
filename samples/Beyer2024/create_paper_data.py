# Import pyMBE and other libraries
import pyMBE
from lib import analysis
import os 
import numpy as np
import pandas as pd
import argparse 

# Create an instance of pyMBE library
pmb = pyMBE.pymbe_library()

valid_fig_labels=["6a", "6b", "6c"]

parser = argparse.ArgumentParser(description='Script to create the data from Beyer2024')
parser.add_argument('--fig_label', 
                    type=str, 
                    required= True,  
                    help=f'Label of the corresponding figure in Beyer2024, currently supported: {valid_fig_labels}')
parser.add_argument('--mode', 
                    type=str, 
                    default= "long-run",  
                    help='Sets for how long the simulation runs, valid modes are "short-run" and "long-run"')
parser.add_argument('--plot', 
                    type=bool, 
                    default= False,  
                    help='Switch to activate/deactivate to plot the data"')
args = parser.parse_args()

# Inputs
fig_label=args.fig_label
mode=args.mode
plot=args.plot

# Sanity checks
if fig_label not in valid_fig_labels:
    raise ValueError(f"The figure label {fig_label} is not supported. Supported figure labels are {valid_fig_labels}")

valid_modes=["short-run","long-run"]
if mode not in valid_modes:
    raise ValueError(f"Mode {mode} is not currently supported, valid modes are {valid_modes}")

## Peptide plots (Fig. 6)

labels_fig6=["6a", "6b", "6c"]

if fig_label in labels_fig6:
    script_path=pmb.get_resource(f"samples/Beyer2024/peptide.py")
    if fig_label == "6a":
        sequence="K"*5+"D"*5
    elif fig_label == "6b":
        sequence="E"*5+"H"*5
    elif fig_label == "6c":
        sequence="nDSHAKRHHGYKRKFHHSHRGYc"
    else:
        raise RuntimeError()
    pH_range = np.linspace(2, 12, num=21)

    for pH in pH_range:
        run_command=f"python3 {script_path} --sequence {sequence} --pH {pH} --mode {mode}"
        print(run_command)
        #os.system(run_command)

# Read all files in the subdir
data_files=[]
time_series_folder_path=pmb.get_resource(f"samples/Beyer2024/time_series")

data=pd.DataFrame()

with os.scandir(time_series_folder_path) as subdirectory:
    # Gather all data
    for subitem in subdirectory:
        if subitem.is_file():
            if 'time_series' in subitem.name:
                # Get parameters from the file name
                data_dict=analysis.get_params_from_dir_name(subitem.name.replace('_time_series.csv', ''))
                file_data=pd.DataFrame(data_dict, index=[0])
                # Get the observables for binning analysis
                time_series_data=analysis.read_csv_file(path=f"{time_series_folder_path}/{subitem.name}")
                analyzed_data=analysis.block_analyze(full_data=time_series_data)
                data_dict.update(analyzed_data.to_dict())
                data = analysis.add_data_to_df(df=data,
                                               data_dict=data_dict,
                                               index=[len(data)])
                for param in data_dict.keys():
                    analyzed_data[param]=data_dict[param]

data_path=pmb.get_resource("samples/Beyer2024/")+"data"
if not os.path.exists(data_path):
    os.makedirs(data_path)

data.to_csv(f"{data_path}/fig{fig_label}.csv")

# Plot the data
if plot:

    # Import matplotlib for plotting
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    
    plt.rcParams["font.family"] = "serif"
    plt.tight_layout()
    mpl.rc('axes', linewidth=1)
    mpl.rcParams['lines.markersize'] = 5
    mpl.rcParams['lines.linewidth'] = 1.0

    width = 10
    height = 10
    plt.rc('font', size=22)
    plt.figure(figsize=(width,height), dpi=100)
    plt.grid(which='major', 
             color='#CCCCCC', 
             linestyle='--', 
             linewidth=0.6)

    # Set labels for the axes
    if fig_label in labels_fig6:
        plt.ylabel(r"Net charge $Z/e$")
        plt.xlabel(r"pH in the solution")
    else:
        raise RuntimeError()

    # Load pka set
    if fig_label in ["6a","6b"]:
        pka_path=pmb.get_resource("parameters/pka_sets/CRC1991.txt")
    elif fig_label == "6c":
        pka_path=pmb.get_resource("parameters/pka_sets/Nozaki1967.txt")
    else:
        raise RuntimeError()
    pmb.load_pka_set (filename=pka_path)
    
    # Load ref data    
    if fig_label == "6a":
        ref_path=pmb.get_resource("testsuite/data/Lunkad2021a.csv")
    elif fig_label == "6b":
        ref_path=pmb.get_resource("testsuite/data/Lunkad2021b.csv")
    elif fig_label == "6c":
        ref_path=pmb.get_resource("testsuite/data/Blanco2020a.csv")
    else:
        raise RuntimeError()
    
    ref_data=analysis.read_csv_file(path=ref_path)
    
    # Calculate Henderson-Hasselbalch (HH
    if fig_label in labels_fig6:
        pmb.define_peptide (name=sequence, 
                            sequence=sequence,
                            model="1beadAA")
    
    pH_range_HH = np.linspace(2, 12, num=1000)
    Z_HH = pmb.calculate_HH(object_name=sequence,
                            pH_list=pH_range_HH)

    # Plot HH
    plt.plot(pH_range_HH,
               Z_HH, 
               label=r"HH", 
               color="black")
    
    # Plot Ref data
    ref_data=ref_data.sort_values(by="pH",ascending=True)
    plt.errorbar(ref_data["pH"], 
                   ref_data["charge"], 
                   ref_data["charge_error"], 
                   linestyle="none", 
                   marker="s", 
                   label="Lunkad  et al.", 
                   ms=15,
                   color="C0")
    
    # Style for Blanco linestyle="none", marker="^", label="Blanco et al.", color="green",  markeredgewidth=1.5
    # Plot data produced by pyMBE
    
    data=data.astype({'pH': 'float'}).sort_values(by="pH")
    plt.errorbar(data["pH"], 
                   data["mean","charge"], 
                   yerr=data["err_mean","charge"], 
                   linestyle="none", 
                   marker="o", 
                   label="pyMBE", 
                   color="C1", 
                   fillstyle="none",
                   ms=15, 
                   markeredgewidth=1.5)
    
    # Save plot
    fig_path=pmb.get_resource("samples/Beyer2024")+"/figs"
    if not os.path.exists(fig_path):
        os.makedirs(fig_path)
    plt.legend()
    plt.savefig(f"{fig_path}/{fig_label}.png", 
                bbox_inches='tight')
    plt.close()





