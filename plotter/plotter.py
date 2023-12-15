#!/usr/bin/env python
import os, re, ROOT, sys, pickle, time
from pprint import pprint
from math import *
from array import array
from DataFormats.FWLite import Events, Handle
import numpy as np
from optparse import OptionParser


ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(True)
# Put tick marks on top and RHS of plots
ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)

#Just to prevent some weird bugs
#os.system("find . -name '*.pyc' -delete")

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
  pr.add_option("-L","--load"     , dest="load"       , type="string"      , default="NONE"        , help="Load histograms from this root file instead of running the whole samples")
  pr.add_option("--doPlots"       , dest="doPlots"    , action="store_true", default=False         , help="If activated, also do plots")
  pr.add_option("-v","--verbose"  , dest="verbose"    , action="store_true", default=False         , help="If activated, print verbose output")
  pr.add_option("-n","--normalize"  , dest="normalize"    , action="store_true", default=False         , help="Normalize histograms to unity")
  pr.add_option("--lspam", dest="lspam",   type="string", default="", help="Spam text on the left hand side")
  pr.add_option("--lspamPosition", dest="lspamPosition", type="float", nargs=4, default=(.16,.905,.60,.945), help="Position of the lspam: (x1,y1,x2,y2)")
  pr.add_option("-a", "--analysis", dest="analysis", type="string", default="none", help="Name of the folder of the analysis you want to make") #This folder should contain the plots file and datasets file. Optional modules are auxiliars and regions.

addbasePlotterOptions(pr)
(options, args) = pr.parse_args()

# Import the modules from the analysis folder
sys.path.append('./' + options.analysis)
exec("from {dstMod} import *".format(dstMod = options.datasets))
exec("from {plotMod} import *".format(plotMod = options.plots))


class plotter(object):
    def __init__(self, options = None, nJobs = -1, iJob = -1):
        self.filterDatasets()
        self.filterPlots()
        self.verbose = options.verbose
        self.options = options

        if not(os.path.exists(options.pdir)):
            try: 
                os.makedirs(options.pdir) #In multithread sometimes it gives an error because it tries to create the folder many times
            except:
                pass
            os.system("git clone https://github.com/musella/php-plots.git "+options.pdir)

    def filterDatasets(self):
        self.datasets = {}
        if type(options.datasetlist) != type([0,1]):
            options.datasetlist = (options.datasetlist).split(",")
        for key in datasets:
            if key in options.datasetlist:
                self.datasets[key] = datasets[key]
        self.ordereddatasets = options.datasetlist

    def filterPlots(self):
        self.plots = {}
        for key in plots:
            if re.match(options.plotThis,key):
                if "executer" in plots[key].keys() and not(type(self).__name__ == plots[key]["executer"]):
                    print("[WARNING] Plot %s being skipped by executer==%s configuration option"%(key, plots[key]["executer"]))
                    continue
                self.plots[key] = plots[key]

    def run(self):
        if self.verbose: print("Loading files....")
        self.loadFiles()
        if self.verbose: print("Creating edm handles....")
        self.createHandles()
        if self.verbose: print("Initializating histograms....")
        self.createHistograms()
        if self.verbose: print("Will load events from file %s"%self.options.load)
        self.loadHistogramsFromFile()
        if self.options.doPlots and self.nJobs == -1: # Don't let the plotter run if split
            if self.verbose: print("Now producing plots...")
            self.producePlots()


    def doSpam(self,text,x1,y1,x2,y2,align=12,fill=False,textSize=0.033,_noDelete={}):
        cmsprel = ROOT.TPaveText(x1,y1,x2,y2,"NDC")
        cmsprel.SetTextSize(textSize)
        cmsprel.SetFillColor(0)
        cmsprel.SetFillStyle(1001 if fill else 0)
        cmsprel.SetLineStyle(2)
        cmsprel.SetLineColor(0)
        cmsprel.SetTextAlign(align)
        cmsprel.SetTextFont(42)
        cmsprel.AddText(text)
        _noDelete[text] = cmsprel; ## so it doesn't get deleted by PyROOT
        cmsprel.Draw("same")
        return cmsprel

    def producePlots(self):
        for plot in self.plots:
            regions = self.plots[plot]["regions"]()
        for region in regions:
            p = self.plots[plot]
            canvas = ROOT.TCanvas("c","c", 800,600)
            canvas.cd()
            canvas.SetLeftMargin(0.15)
            canvas.SetBottomMargin(0.15)
            tleg   = ROOT.TLegend(p["legend"][0], p["legend"][1],p["legend"][2],p["legend"][3])
            tleg.SetTextSize(0.03)
            tleg.SetTextFont(42)
            tleg.SetFillColor(0)
            tleg.SetShadowColor(0)
            tleg.SetFillStyle(0)
            tleg.SetBorderSize(0)
            hists = []
            first=True
            #atLeastOne = False
            maximum = 0
            for dset in self.ordereddatasets:  #Need to this to calculate the maximum with the scaling
                hTemp = self.histograms[plot][region][dset]
                if p["scale"] == 'Rate':
                    hTemp.Scale(1./self.files[dset][0].size() * 40e6) ##Note: wrong statistic unc. (compute as in efficiency)
                elif p["scale"] == 'RateOMTF':
                    hTemp.Scale(1./self.files[dset][0].size() * 2544*11.246) ##Note: wrong statistic unc. (compute as in efficiency)
                else:
                    hTemp.Scale(p["scale"])
                maximum = max(hTemp.GetMaximum(), maximum)
            
            for dset in self.ordereddatasets:
                hTemp = self.histograms[plot][region][dset]
                #if float(hTemp.Integral()) == 0.0: #jump if the histo was not filled
                #  continue
                #atLeastOne = True 
                hTemp.SetLineColor(self.datasets[dset]["color"])
                hTemp.SetMarkerColor(self.datasets[dset]["color"])
                hTemp.SetTitle(";%s;%s"%(p["xlabel"], p["ylabel"]))
                hTemp.GetXaxis().SetRangeUser(p["xrange"][0],p["xrange"][1])
                hTemp.GetXaxis().SetTitleOffset(1.1)
                if len(p["yrange"]) != 0:
                    hTemp.GetYaxis().SetRangeUser(p["yrange"][0],p["yrange"][1])
                if len(p["yrange"]) == 0:
                    hTemp.GetYaxis().SetRangeUser(0,maximum*1.2)
                if self.options.normalize:
                    hTemp.Scale(1./(hTemp.Integral()+0.001))
                    hTemp.GetYaxis().SetRangeUser(0,0.4)
                if "LogY" in p.keys() and p["LogY"]:
                    hTemp.SetMinimum(1)
                    canvas.SetLogy()
                if "LogX" in p.keys() and p["LogX"]:
                    hTemp.GetXaxis().SetRangeUser(p["xrange"][0]+0.1,p["xrange"][1])             
                    canvas.SetLogx()
                if "xlabels" in p.keys():
                    for i, label in enumerate(p["xlabels"]):
                        hTemp.GetXaxis().SetBinLabel(i+1, label)
                tleg.AddEntry(hTemp, self.datasets[dset]["label"], 'l')
                hists.append(hTemp)
                if first:
                    hTemp.Draw("hist")
                    first=False
                else:
                    hTemp.Draw("hist same")
            if p["plotLegend"]:
                tleg.Draw("same")
            if options.lspam != "":
                self.doSpam(options.lspam, options.lspamPosition[0], options.lspamPosition[1], options.lspamPosition[2], options.lspamPosition[3])
            self.doSpam(p["regions"](region = region) + p["ExtraSpam"], .6,.905,.97,.945 )

            canvas.Update()  
            canvas.Print(p["savename"].replace("[PDIR]",options.pdir).replace("[REGION]",region)+".pdf")
            canvas.Print(p["savename"].replace("[PDIR]",options.pdir).replace("[REGION]",region)+".png")
            canvas.Close()

def loadFiles(self):
    self.files = {}
    for dataset in self.ordereddatasets:
        if type(self.datasets[dataset]["samples"]) != type(["a","b"]): 
            self.files[dataset] = [Events(self.datasets[dataset]["samples"])]
        else: 
            self.files[dataset] = [Events(self.datasets[dataset]["samples"])]

def createHistograms(self):
    self.histograms = {}
    plotsToRemove = [] #list to fill with all the plots to remove
    for plot in self.plots:
        self.histograms[plot] = {}
        for region in self.plots[plot]["regions"]():
            self.histograms[plot][region] = {}
            for dataset in self.ordereddatasets:
                if self.plots[plot]["onlyData-onlyMC"][0] == self.plots[plot]["onlyData-onlyMC"][1] and self.plots[plot]["onlyData-onlyMC"][0] == True:
                    raise Exception("It is not possible to have onlyData and onlyMC flags both on true")
                elif self.plots[plot]["onlyData-onlyMC"][0] == True and self.datasets[dataset]["data"] == False:
                    continue
                elif self.plots[plot]["onlyData-onlyMC"][1] == True and self.datasets[dataset]["data"] == True:
                    continue

                self.histograms[plot][region][dataset] = eval(self.plots[plot]["template"].replace("[DATASET]", dataset+ "_" + str(self.iJob) if self.iJob >= 0 else dataset).replace("[REGION]", region))
                ###Create the directory to save the histograms if it doesn't exist
                savedirectory = ''.join([x + "/" for x in self.plots[plot]["savename"].replace("[PDIR]",options.pdir).replace("[REGION]",region).split("/")][:-1])
                if not os.path.isdir(savedirectory):
                    try:
                        os.makedirs(savedirectory)
                    except:
                        pass
                    os.system("cp ~/www/public/index.php %s"%savedirectory)
            if len(self.histograms[plot][region]) == 0: #remove the plot if there is no histo to plot. This may cause troubles if data and MC are inputs at the same time
                plotsToRemove.append(plot)
    for plotToRemove in plotsToRemove:
        self.plots.pop(plotToRemove, None)

def loadHistogramsFromFile(self):
    theFile = ROOT.TFile(self.options.load, "READ")
    for plot in self.plots:
        for region in self.plots[plot]["regions"]():
            for dataset in self.ordereddatasets:
                self.histograms[plot][region][dataset] = theFile.Get(self.histograms[plot][region][dataset].GetName())



