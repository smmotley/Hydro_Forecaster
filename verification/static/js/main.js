import createMap from '/static/js/map.js'
import marker_clicked from '/static/js/util/marker_clicked.js'

mapboxgl.accessToken = JSON.parse(document.getElementById('create-map').textContent);

let geojson = {
    type: "FeatureCollection",
    features: [],
};

function json2geojson(json){
    for (var i = 0; i < json.data.length; i++) {
    geojson.features.push({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [json.data[i]["-lon"], json.data[i]["-lat"]]
        },
        "properties": {
            "id": json.data[i]["id"],
        }
    });
}
return geojson
}

createMap(map => {
    d3.json('/static/station_locations.json')
        .then((data) => {
            geojson = json2geojson(data);
            geojson.features.forEach(function(feature){

                // create a HTML element for each feature
                var el = document.createElement('div');
                el.className = 'marker';
                el.id = 'marker_' + feature.properties.id;

                let popup = new mapboxgl.Popup({
                    offset: 25,
                    closeButton: false,
                    closeOnClick: true
                }).setHTML(feature.properties.id);

                new mapboxgl.Marker(el)
                        .setLngLat(feature.geometry.coordinates)
                        .addTo(map)
                        .setPopup(popup);
                el.addEventListener('click', (e) =>
                {
                   let station_name = (e.target.id).split("_");
                   console.log(station_name);
                   marker_clicked(station_name[1])
                })

            });
        });
});