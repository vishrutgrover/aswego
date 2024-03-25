from flask import Flask, render_template, request, jsonify, redirect, url_for
from openai import OpenAI
import requests, json, datetime, flexpolyline
from functools import reduce
import os



app = Flask(__name__)
openai_api_key = os.getenv("MY_API_KEY")
client = OpenAI(api_key=openai_api_key)

HERE_API_KEY = "9NG7mhhWwajOpKKRkizvWwswP58ceCRMoIeQXoRjjlM"

initial_message = [{"role": "system", "content": "You are supposed to tell what the source location, destination location, name of the restaurants, name of the hotel, and all the other places mentioned in the prompt in the form of JSON."}]

messages = []

def extract_locations(lines):
  locations = {
      "source": None,
      "destination": None,
      "restaurants": [],
      "hotels": [],
      "places_to_visit": []
  }
  for line in lines:
    if line.startswith("Source Location:"):
      locations["source"] = line.replace("Source Location:", "").strip()
    elif line.startswith("Destination Location:"):
      locations["destination"] = line.replace("Destination Location:", "").strip()
    elif line.startswith("Restaurant:"):
      locations["restaurants"].append(line.replace("Restaurant:", "").strip())
    elif line.startswith("Hotel:"):
      locations["hotels"].append(line.replace("Hotel:", "").strip())
    elif line.startswith("Place to Visit:"):
      locations["places_to_visit"].append(line.replace("Place to Visit:", "").strip())
  return locations

def geocode(address):
        if requests.get("https://router.hereapi.com/v8/health").status_code!=200: print("Server Down") ; return -1
        response = requests.get(f"https://geocode.search.hereapi.com/v1/geocode?q={address + 'India'}&apiKey={HERE_API_KEY}")
        if response.status_code == 200:
            data = response.json()
            # Then, check if 'items' key is present and not empty
            if 'items' in data and data['items']:
                return list(data['items'][0]['position'].values())
            else:
                print(f"No geocoding result for {address}")
                return None
        else:
            print(f"Geocoding request failed with status code {response.status_code} for address: {address}")
            return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user_message = request.form.get('writeSomething')
        
        # Add user message to conversation
        messages.append({"role": "user", "content": user_message})
        print(messages)

        # Check if it's the first message and add initial message if needed
        print(messages)

        # Get the completion from the OpenAI model
        chat = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
        bot_reply = chat.choices[0].message.content
        print(bot_reply)
        # Add bot reply to conversation
        messages.append({"role": "assistant", "content": bot_reply})

        print(messages)

        # Pass messages list to the template for rendering
        return render_template('/webpage.html', messages=messages)
    else:
        
        # Render the template even for GET requests
        return render_template('/webpage.html', messages=[], initial_message=initial_message)
    
@app.route('/location', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        current_location = request.form.get('current-location-input')
        destination_location = request.form.get('destination-location-input')
        
        # Print the current and destination locations to the console
        print("Current Location:", current_location)
        print("Destination Location:", destination_location)

        return redirect(url_for('findPath', Cl=current_location, Dl=destination_location))
        
    print("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
    return render_template('/home.html')

@app.route('/path',  methods=['GET', 'POST'])
def findPath():
    print("start")
    current_location = request.args.get('Cl')
    destination_location = request.args.get('Dl')
    
    print("-1--", current_location, "--1=-", destination_location)
    if request.method == 'POST':
        current_location = request.form.get('current-location-input')
        destination_location = request.form.get('destination-location-input')
        print("-2--", current_location, "--2--", destination_location)
        stop_count = int(request.form['stop-count'])
        stops = [request.form[f'stop-{i+1}'] for i in range(stop_count)]
        stops_str = ','.join(stops)
        print("----", stops_str)
        return redirect(url_for('completePath', Cl=current_location, Dl=destination_location, stop_count=stop_count, stops=stops_str))
    
    print("--3--")
    return render_template('/path.html', current_location=current_location, destination_location=destination_location)


@app.route('/path/via', methods=['GET', 'POST'])
def completePath():
    locations=[]
    current_location = request.args.get('Cl')
    destination_location = request.args.get('Dl')
    stop_count = request.args.get('stop_count')
    stops = request.args.get('stops').split(',') 
    
    print(stops)
    print(type(stops))
    locations.append(current_location)
    locations.append(destination_location)
    for i in stops:
        locations.append(i)

    print(locations)
    location_str = '|'.join(locations)
    return redirect(url_for('completePoly',list_of_places=location_str))
 
@app.route("/path/poly", methods=['GET', 'POST'])
def completePoly():
    locstring = request.args.get("list_of_places")
    list_of_places = locstring.split('|')
    print(list_of_places)
    coords_of_places = [geocode(x) for x in list_of_places]
    print(coords_of_places)
    #geocoding error handling
    if None in coords_of_places: return f"Error Geocoding problem in place :{list_of_places[coords_of_places.index(None)]}"

    #making query dictionary
    t = datetime.datetime.now()
    query_dict = { "apiKey" : HERE_API_KEY,
                   "origin" : f"{coords_of_places[0][0]},{coords_of_places[0][1]}",
                   "destination" : f"{coords_of_places[1][0]},{coords_of_places[1][1]}",
                   "transportMode" : 'car',
                   "routingMode" : 'fast' ,
                   "departureTime" : f"{t.year}-{t.month}-{t.day}T{t.hour}:{t.minute}:{t.second}",
                   "alternatives" : 0,
                   "via" : [f"{c[0]},{c[1]}" for c in coords_of_places[2:]],
                   "return" : "polyline"}
    
    #making request
    route_query = f"https://router.hereapi.com/v8/routes"
    response = requests.get(route_query,params=query_dict)

    #error handling
    if response.status_code!=200: print("Request Failed",response.status_code) ; return -1

    #encoding multiple polylines into single polyline
    polylines = [unit_section['polyline'] for unit_section in response.json()["routes"][0]['sections']]
    decoded_polylines = [flexpolyline.decode(line) for line in polylines]
    singled_polyline_coords = reduce(lambda x,y:x+y, decoded_polylines)
    singled_polyline = flexpolyline.encode(singled_polyline_coords)
    print(singled_polyline)
    locstring = locstring.replace("|",",")
    print(locstring)
    out = "|".join([str(sc[0])+","+str(sc[1]) for sc in singled_polyline_coords])
    return render_template('/path_via.html',locations=locstring , singled_polyline=out)
    


if __name__ == '__main__':
    app.run(debug=True)
