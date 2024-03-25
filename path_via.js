// location_search.js


function searchLocations(locations) {
    var platform = new H.service.Platform({
        apikey: '9NG7mhhWwajOpKKRkizvWwswP58ceCRMoIeQXoRjjlM'
    });
    console.log("-----------");
    console.log(locations);

    if (!Array.isArray(locations)) {
        console.error('Error: locations is not an array');
    }
    var locationsArray = locations.split(',');
    console.log("-----------");
    console.log(locationsArray);

    var geocoder = platform.getSearchService();

    // Iterate over each location in the array
    locationsArray.forEach(function(location) {
        geocoder.geocode({
            q: location
        }, onSuccess, onError);
    });

    function onSuccess(result) {
        var location = result.items[0];
        if (location) {
            var position = location.position;
            map.setCenter(position);
            map.setZoom(15); // Set the zoom level to 15 (you can adjust as needed)
            var marker = new H.map.Marker(position);
            map.addObject(marker);
        } else {
            alert('Location not found.');
        }
    }

    function onError(error) {
        alert('Error occurred during geocoding.');
    }
}
