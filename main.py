#! /usr/bin/env python


import numpy as np
import pandas as pd
import shapefile
import imp

from bokeh.plotting import Figure
from bokeh.models.widgets import Slider, TextInput, Select
from bokeh.models import ColumnDataSource, HBox, WidgetBox, ImageURL
from bokeh.io import curdoc
from bokeh.models import HoverTool, PanTool, BoxZoomTool, WheelZoomTool, ResetTool


# Data from Yelp, and indexed on BoroCT2010
# Features: Restaurants,Shopping,Food,Health,Nightlife
yelp = pd.DataFrame.from_csv("data/cleaned_yelpdata.csv")
yelp["BoroCT2010"] = yelp.index
yelp.index = map(str, yelp["BoroCT2010"])


# 3 Features - Subway distance, Complaint, Crime rate
scc_shapefile = "data/shapefile/Manhattan-SubwayComplaintCrime"  
sf = shapefile.Reader(scc_shapefile)
shapes = sf.shapes()
allrecords = sf.records()
recd = pd.DataFrame(allrecords)
recd.columns = [i[0] for i in sf.fields[1:]]
recd.index = recd["BoroCT2010"]

neighborhoodDetails = pd.DataFrame.from_csv("data/nyct2010_neighborhoods.csv")
neighborhoodDetails.index = neighborhoodDetails["BoroCT2010"]


pricevals_dummy = [0]*len(shapes)
pricevals_real = pd.DataFrame.from_csv("data/Zipcode_based_Price.csv")["Price"]
imageurl_noprice = "data/legend_noprice.png"
imageurl_wprice = "data/legend_wprice.png"

pricevals = pricevals_real
imageurl = imageurl_wprice


print ("Number of shapes:", len(shapes))
ct_x = []
ct_y = []
for shape in shapes:
    lats = []
    lons = []
    for point in shape.points:
        lats.append(point[0])
        lons.append(point[1])
    ct_x.append(lats)
    ct_y.append(lons)

'''
 Colors:
    colors = ["#F1EEF6", "#D4B9DA", "#C994C7", "#DF65B0", "#DD1C77", "#980043"]
    bivariate color map 00 = bottom left, 20 = bottom right, 02 = top left, 22 = top right,
'''
colorsdict = {"00": "#E8E8E8", "10": "#E4ACAC", "20": "#C85A5A",
              "01": "#B0D5DF", "11": "#AD9EA5", "21": "#985356",
              "02": "#64acbe", "12": "627F8C", "22": "#574249"}



def getscore(userinputs): 
    merged = pd.concat([yelp, recd], axis=1)
    keepfeatures = merged[["Distance", "Crime_Ct", "Complaints", "restaurants", "food", "nightlife"]].applymap(float) + 1
    logfeatures = keepfeatures.applymap(np.log)
    tmpscore = logfeatures.apply(lambda x: (x - np.mean(x)) / np.std(x))

    # multiplier to differentiate good and bad factors
    multiplier = [-1, -1, -1, 1, 1, 1]
    newuservector = [userinputs[i]*multiplier[i] for i in range(len(userinputs))]

    thescore = tmpscore.dot(newuservector)
    compzscore = (thescore - np.mean(thescore))/np.std(thescore)
    return thescore


# Color mapping
def mapcolors(fscore, pricevallist):
    """
    Colorcode Mapping:

        00 = low fscore, high price (bottom-left)
        20 = high fscore, high price (bottom-right)
        02 = low fscore, low price (top-left)
        22 = high fscore, low price (top-right) 

    """
    # split fscore into 3 categories
    # adding colorcodes for each fscore
    split1 = np.percentile(fscore, 33)
    print split1
    split2 = np.percentile(fscore, 66)
    print split2

    fscore_colorcodes = []
    if split1 == split2:
        fscore_colorcodes = ["0"]*len(fscore)
    else:
        for i in fscore:
            # less than 33 percentile
            if i < split1:
                fscore_colorcodes.append("0")
            # less than 66 and more than 33 percentile
            elif i < split2:
                fscore_colorcodes.append("1")
            # greater than 66 percentile
            else:
                fscore_colorcodes.append("2")

    
    # split pricevallist into 3 categories
    # adding colorcodes for each pricevallist
    price_split1 = np.percentile(pricevallist, 33)
    price_split2 = np.percentile(pricevallist, 66)

    price_colorcodes = []
    if price_split1 == price_split2:
        price_colorcodes = ["0"]*len(pricevallist)
    else:
        for i in pricevallist:
            # less than 33 percentile
            if i < price_split1:
                price_colorcodes.append("2")
            # less than 66 and more than 33 percentile    
            elif i < price_split2:
                price_colorcodes.append("1")
            # greater than 66 percentile                
            else:
                price_colorcodes.append("0")

    
    # Mapping with Colors - Dict()
    colorlist = [colorsdict[fscore_colorcodes[x] + price_colorcodes[x]] for x in range(len(fscore_colorcodes))]
    return colorlist




# initial score
finalscore = getscore([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
ct_colors = mapcolors(finalscore, pricevals)
source = ColumnDataSource(data=dict(QI_colmap=ct_colors, ct_x=ct_x, ct_y=ct_y, score=finalscore, Price=pricevals, Neighborhood=neighborhoodDetails["NTAName"]))

hover = HoverTool(
        tooltips=[
            #("Area", "@Neighborhood"),
            ("Score", "@score"),
            ("Price", "@Price"),
        ]
    ) 

tools = [PanTool(), BoxZoomTool(), WheelZoomTool(), ResetTool(), hover]

p = Figure(title="Manhattan Nest Map", plot_width=800, plot_height=700, tools=tools)
           # tools="pan,wheel_zoom,reset,box_zoom,save")  # toolbar_location="top", #box_select,
p.grid.grid_line_alpha = 0

p.patches('ct_x', 'ct_y', source=source, fill_color='QI_colmap', fill_alpha=0.7, line_color="white", line_width=0.5)



# Set up widgets
text = TextInput(title="Map Name", value="Manhattan Nest")
feature1 = Slider(title="Subway Accessibility", value=0.5, start=0, end=1, step=.1)
feature2 = Slider(title="Safety", value=0.5, start=0, end=1, step=.1)
feature3 = Slider(title="Public Satisfaction", value=0.5, start=0, end=1, step=.1)
feature4 = Slider(title="Restaurants", value=0.5, start=0, end=1, step=.1)
feature5 = Slider(title="Grocery Stores", value=0.5, start=0, end=1, step=.1)
feature6 = Slider(title="Nightlife", value=0.5, start=0, end=1, step=.1)
price = Select(title="Show Affordability", options=["Yes", "No"])


# Set up callbacks
def update_title(attrname, old, new):
    p.title = text.value


text.on_change('value', update_title)


def update_data(attrname, old, new):
    # Get the current slider values
    f1user = feature1.value
    f2user = feature2.value
    f3user = feature3.value
    f4user = feature4.value
    f5user = feature5.value
    f6user = feature6.value
    showprice = price.value

    # Calculate score based on user input
    finalscore = getscore([f1user, f2user, f3user, f4user, f5user, f6user])

    # Calcualte color palette based on whether showing price or not
    if showprice == "Yes":
        pricevals = pricevals_real
        imageurl = imageurl_wprice
    else:
        pricevals = pricevals_dummy
        imageurl = imageurl_noprice
    ct_colors = mapcolors(finalscore, pricevals)


    source.data = dict(QI_colmap=ct_colors, ct_x=ct_x, ct_y=ct_y, score=finalscore, Price=pricevals, Neighborhood=neighborhoodDetails["NTAName"])
    

for w in [feature1, feature2, feature3, feature4, feature5, feature6, price]:
    w.on_change('value', update_data)


# Set up layouts and add to document
inputs = WidgetBox(children=[text, feature1, feature2, feature3, feature4, feature5, feature6, price])
#inputs = WidgetBox(children=[feature1, feature2, feature3])
# inputs = VBoxForm(children=[text])
curdoc().add_root(HBox(children=[p, inputs]))  # , width=800

