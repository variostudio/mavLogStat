#Mavlink logfile analizer tools
## mavLogPlot.py 
### Shows flight statistics and draw track plot. 
#### Python modules required:
* mavlink 
* geopy
* folium

## mavLogStat.py  
### Shows flight statistics only
#### Python modules required:
* mavlink 
* geopy

## mavLogParams.py  
### Shows all parameters from log file
#### Python modules required:
* mavlink 

Each python module can be installed with `PIP` or in other way. Please consult python docs for more information:
https://packaging.python.org/tutorials/installing-packages/

Each script has syntax to run:
```
python mavLogPlot.py logfile.bin
python mavLogStat.py logfile.bin
python mavLogParams.py logfile.bin
```

In the case of `mavLogPlot.py` the resulting .html will be generated. You can open it in browser
