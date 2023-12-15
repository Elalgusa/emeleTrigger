import os, re, sys, pickle, time
from math import *
from array import array
import numpy as np
from optparse import OptionParser
import awkward as ak
import pandas as pd
from pandas.plotting import scatter_matrix

import numpy as np
from pyntcloud import PyntCloud

# viz
import networkx as nx
import matplotlib.pyplot as plt

#"Parser inputs"
pr = OptionParser(usage="%prog [options]")

def addbasePlotterOptions(pr):
  #Model type, experimental labels
  pr.add_option("-d","--datasets" , dest="datasets"   , type="string"      , default="datasets" , help="File to read dataset configuration from")
  pr.add_option("-l","--datasetlist"  , dest="datasetlist", type="string"  ,default="Disp_pt30,Both_pt30", help="Datasets to plot, in order to appear in legend")
  pr.add_option("-p","--plots"    , dest="plots"      , type="string"      , default="plots"    , help="File to read plot configuration from")
  pr.add_option("-q","--plotlist" , dest="plotThis"      , type="string"      , default="yields*"  , help="Plots to be activated")
  pr.add_option("--pdir"    , dest="pdir"      , type="string"      , default="."    , help="Where to put the plots into")
  pr.add_option("-o","--output"   , dest="output"     , type="string"      , default="out.root"    , help="Output root file")
  pr.add_option("--doPlots"       , dest="doPlots"    , action="store_true", default=False         , help="If activated, also do plots")
  pr.add_option("-v","--verbose"  , dest="verbose"    , action="store_true", default=False         , help="If activated, print verbose output")
  pr.add_option("-n","--normalize"  , dest="normalize"    , action="store_true", default=False         , help="Normalize histograms to unity")
  pr.add_option("--lspam", dest="lspam",   type="string", default="", help="Spam text on the left hand side")
  pr.add_option("--lspamPosition", dest="lspamPosition", type="float", nargs=4, default=(.16,.905,.60,.945), help="Position of the lspam: (x1,y1,x2,y2)")
  pr.add_option("-a", "--analysis", dest="analysis", type="string", default="none", help="Name of the folder of the analysis you want to make") #This folder should contain the plots file and datasets file. Optional modules are auxiliars and regions.
  pr.add_option("-awk", "--awkward", dest="awkward", type="store_true", default=True, help="Use awkward arrays instead of ROOT TTree")
  
addbasePlotterOptions(pr)
(options, args) = pr.parse_args()

# Import the modules from the analysis folder
sys.path.append('./' + options.analysis)
exec("from {dstMod} import *".format(dstMod = options.datasets))
exec("from {plotMod} import *".format(plotMod = options.plots))

def getDataset(datasetName):
  for key in datasets.keys():
    if key == datasetName:
      return datasets[key]
  print("Dataset {ds} not found in datasets file".format(ds = datasetName))
  return None

def getPlot(plotName):
  for key in plots.keys():
    if key == plotName:
      return plots[key]
  print("Plot {pl} not found in plots file".format(pl = plotName))
  return None

def getPlotList(plotList):
  plotList = plotList.split(",")
  plotList = [getPlot(plot) for plot in plotList]
  return plotList

def getDatasetList(datasetList):
  datasetList = datasetList.split(",")
  datasetList = [getDataset(dataset) for dataset in datasetList]
  return datasetList

def getPlotName(plot):
  return plot["name"]

def getDatasetName(dataset):
  return dataset["name"]

def getDataset(library, filename, treename):
    # Open the ROOT file and get the tree
    
    branches = uproot.open('%s:%s' %(filename,treename)) 
    print(branches.show())
    branches=branches.arrays(library=library) if library else branches.arrays()

    # Calculate deltaphis between layers, adding it to a new column
    # this will be our proxy to the magnetic field
    branches['stubDPhi'] = branches['stubPhi'].apply(lambda x: np.diff(x))

    return branches

def main_run():
    if options.verbose:
        print("Plotting the following datasets: {ds}".format(ds = options.datasetlist))
        print("Plotting the following plots: {pl}".format(pl = options.plotThis))

    # Get the datasets
    datasetList = getDatasetList(options.datasetlist)
    
    # Get the plots
    plotList = getPlotList(options.plotThis)


    # Create the output directory if it does not exist
    if not os.path.exists(options.pdir):
      os.makedirs(options.pdir) 


if __name__ == "__main__":
   main_run()

    



