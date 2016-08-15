#! /usr/bin/env python2.7

import os
import rauth
import time
import pprint
import imp
import json
import shapefile


# Parameters for Yelp api
def yelp_parameters(bbox,category,offset):
  params = {}
  params["term"] = category
  params["bounds"] = "{},{}|{},{}".format(str(bbox[1]),str(bbox[0]),str(bbox[3]),str(bbox[2]))
  params["limit"] = "20"
  params["offset"] = offset
  return params

# API response from paramaters and key
def yelp_results(params):
  details = open ('config.json')
  cred = json.load(details)
  # Yelp's access details
  session = rauth.OAuth1Session(
    consumer_key = cred['consumer_key']
    ,consumer_secret = cred['consumer_secret']
    ,access_token = cred['token']
    ,access_token_secret = cred['token_secret'])
     
  request = session.get("http://api.yelp.com/v2/search",params=params)
  data = request.json()
  session.close()

  return data




def apiCount(shape,categories):
  categoryCounts = []
  for i in range(len(categories)):
    responseCount = 0
    offset = 0

    while (responseCount == offset and offset <1000):
      params = yelp_parameters(shape.bbox,categories[i],offset)
      response = len(yelp_results(params)['businesses'])
      responseCount += response
      offset += 20

    categoryCounts += [responseCount]
  return categoryCounts


def getData(shapes,refs):
  categories = ["active","art","beautysvc","education",
                 "food","health","localservices","nightlife",
                 "religiousorgs","restaurants","shopping"]
  results = []

  for i in range(len(shapes)):
    counts = apiCount(shapes[i],categories)
    results.append([refs[i][1]]+counts)
    print results

  return results

scc_shapefile = "data/shapefile/Manhattan-SubwayComplaintCrime"  
data = shapefile.Reader(scc_shapefile)
result = getData(data.shapes(),data.records())
print result

                                  