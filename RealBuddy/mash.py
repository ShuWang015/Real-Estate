import flask
import requests
import random
import keys

mash_api_url = 'https://mashvisor-api.p.rapidapi.com/'
zip_api_url = 'https://us-zipcode-code-information.p.rapidapi.com/'

app = flask.Flask(__name__)


zipHeader = {
      'X-RapidAPI-Key': keys.API_KEY_ONE,
      'X-RapidAPI-Host': 'us-zipcode-code-information.p.rapidapi.com'
    }

mashHeader = {
      'X-RapidAPI-Key': keys.API_KEY_ONE,
      'X-RapidAPI-Host': 'mashvisor-api.p.rapidapi.com'
    }



def getZipToLocation(zipcode):
    # # # # # # XXX Might have to edit parameter # # # # # 
    url = "https://us-zip-code-information.p.rapidapi.com/"

    querystring = {"zipcode":zipcode}

    headers = {
        "X-RapidAPI-Key": keys.API_KEY_TWO,
        "X-RapidAPI-Host": "us-zip-code-information.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    data = response.json()
    city = data[0]['City']
    state = data[0]['State']
    ### to get result, assign function to a variable 
    ###                then use the python dictionary 
    ###                syntax to access items
    return (state,city)
    
    


### return a list of ID
def getNeighborhoodID(state , city )  :
    url = mash_api_url + 'city/neighborhoods/' + state + '/' + city
    response = requests.get(url=url, headers=mashHeader)
    data = response.json()
    items = data['content']['results']
    ls = []
    for i in range(len(items)):
        j = items[i]['id']
        ls = ls + [j]
    return ls



def getNewPropertyList(zipcode, avg_price):
    ## get location first

    input = getZipToLocation(zipcode)
    idList = getNeighborhoodID(input[0],input[1])
    
    result = []
    ## add listing according to neighborhood ID
    for id in idList:
        if len(result)>=5:
            break
        url = mash_api_url + 'neighborhood/'+ str(id) + '/traditional/listing'
        param = {
            'state': input[0],
            'items': 1,
            'max_price': avg_price
        }

        response = requests.get(url=url, params=param, headers=mashHeader)
        data = response.json()
        if len(data['content']['results'])!= 0:
            raw = data['content']['results'][0]
            re = {
                'name' : raw['title'],
                'state' : raw['state'],
                'city' : raw['city'],
                'bed' : raw['beds'],
                'bath' : raw['baths'],
                'description' : raw['description'],
                'price' : raw['price'],
                'image' : raw['image'],
                'address' : raw['address'],
                'zipcode' : raw['zipcode'],
                'type' : raw['type']
            }

            result = result + [re]
    return result


def avg(zipcode):

    url = "https://realty-mole-property-api.p.rapidapi.com/zipCodes/" + str(zipcode)

    headers = {
        "X-RapidAPI-Key": keys.API_KEY_THE,
        "X-RapidAPI-Host": "realty-mole-property-api.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    data = response.json()

    avgRent = data["rentalData"]['averageRent']

    avgRent = str(avgRent) 

    return avgRent
