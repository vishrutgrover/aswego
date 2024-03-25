// location_search.js

var map; // Declare map variable globally to access it across functions

function searchLocation(currentLocation, destinationLocation) {
    var platform = new H.service.Platform({
        apikey: 'JRo2rEIRPPC3ZzqqBMiJ9PjEg8oG1qD67P08byN1fIM'
    });

    var geocoder = platform.getSearchService();
    
    // Geocode current location
    geocoder.geocode({ q: currentLocation }, function(currentResult) {
        var currentPosition = currentResult.items[0].position;
        
        // Geocode destination location
        geocoder.geocode({ q: destinationLocation }, function(destinationResult) {
            var destinationPosition = destinationResult.items[0].position;
            
            // Remove previous markers if any
            if (map) {
                map.removeObjects(map.getObjects());
            }

            // Center the map between current and destination positions
            var boundingBox = new H.geo.Rect(currentPosition.lat, currentPosition.lng, destinationPosition.lat, destinationPosition.lng);
            map.getViewModel().setLookAtData({bounds: boundingBox});

            // Add markers for current and destination positions
            map.addObject(new H.map.Marker(currentPosition));
            map.addObject(new H.map.Marker(destinationPosition));
            map.setCenter(currentPosition);
            map.setZoom(15);
        }, onError);
    }, onError);

    function onError(error) {
        alert('Error occurred during geocoding.');
    }
}