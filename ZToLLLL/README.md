# Code to produce ZToLLL(L) plots for HNL AN

There was no separate HNL framework set up, so for this small task the code is branched off from the ttg code:

```
cd $CMSSW_BASE/src;
git clone https://github.com/GhentAnalysis/ttg;
cd ttg;
git checkout smallHNLstuff
```

This branch might be quite heavily out of sync with the current ttg code though, but it only uses a few standard helper functions from ttg.

# Step 1: Creating histograms from the HNL tuples
*If you only need to tweak with the lay-out, you can go immediately to step 2*

* Make sure you have HNL displaced tuples available. Samples are read in using the ttg Sample class, so ask Kirill/Gianny on how to set up a tuples
file (example tuples\_2016.conf) if needed. Make sure the path to the tuples file in the createSampleList function in ./analyzeZToLLLLmass.py does
point to the correct tuples file.
* If you need to change something in the code, you can do it in ./analyzeZToLLLLmass.py which should be quite readable (at least compared to the original code I got),
although some stuff is still historic. The selection code could be a bit more complicated when you see it at first, but again, in its current for it should be readable.
* Analyze the MC/data, the jobs which will be sent to the T2 will be:
```
  ./analyzeZtoLLLLmass.py --year=2016 --dryRun
  ./analyzeZtoLLLLmass.py --year=2017 --dryRun
  ./analyzeZtoLLLLmass.py --year=2018 --dryRun
```
Remove the --dryRun argument, when you are sure everything looks correct:
```
  ./analyzeZtoLLLLmass.py --year=2016
  ./analyzeZtoLLLLmass.py --year=2017
  ./analyzeZtoLLLLmass.py --year=2018
```
If you need to overwrite existing files instead of only running recovery jobs, add --overwrite

Originally you would re-run the same also with the --dyExternal, --dyExternalAll and --dyInternal options:
```
  ./analyzeZtoLLLLmass.py --dyExternal --year=2016
  ./analyzeZtoLLLLmass.py --dyExternal --year=2017
  ./analyzeZtoLLLLmass.py --dyExternal --year=2018
  ./analyzeZtoLLLLmass.py --dyExternalAll --year=2016
  ./analyzeZtoLLLLmass.py --dyExternalAll --year=2017
  ./analyzeZtoLLLLmass.py --dyExternalAll --year=2018
  ./analyzeZtoLLLLmass.py --dyInternal --year=2016
  ./analyzeZtoLLLLmass.py --dyInternal --year=2017
  ./analyzeZtoLLLLmass.py --dyInternal --year=2018
```
But as you found the time/need to re-run the whole stuff here, and you have now tuples available with the zgEventType and hasInternalConversion information stored,
you might as well simply do things in a correct way and use an overlap algorithm between DY and ZGamma:
```
  ./analyzeZtoLLLLmass.py --overlapRemoved --year=2016
  ./analyzeZtoLLLLmass.py --overlapRemoved --year=2017
  ./analyzeZtoLLLLmass.py --overlapRemoved --year=2018
```
You now have all histograms available, ready to go for step 2


# Step 2: Combining the histograms into plots
The plots in the AN can be recreated using:
```
  ./plotZtoLLLLmass.py --dyExternal --year=2016
  ./plotZtoLLLLmass.py --dyExternal --year=2017
  ./plotZtoLLLLmass.py --dyExternal --year=2018
```
The script (mostly historic) is simply taking the histograms produced in step 1 and recombining them in plots. Most of the code are standard ROOT lay-out functions.
Using the --dyExternalAll argument, you also include DY events with external photons above 15 GeV, instead of only those between 0 and 15 GeV.
When you have also redone step 1, you might have the possibility to use a correct overlap removal between DY and ZGamma, instead of this strange internal/external split up (which works decently though for this purpose),
but this option is not yet added.
