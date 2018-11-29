import createMap from '/static/js/map.js'
import marker_clicked from '/static/js/util/marker_clicked.js'

mapboxgl.accessToken = JSON.parse(document.getElementById('create-map').textContent);

let geojson = {
    type: "FeatureCollection",
    features: [],
};

function json2geojson(json){
    console.log(json)
    for (var i = 0; i < json.data.length; i++) {
    geojson.features.push({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [json.data[i]["-lon"], json.data[i]["-lat"]]
        },
        "properties": {
            "id": json.data[i]["id"],
            "info": json.data[i]["name"],
            "type": json.data[i]["type"]
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
                if (feature.properties.type == 'POWERHOUSE'){
                        el.style.backgroundImage = 'url(/static/images/pp_marker.png)';
                        el.style.width = '25px';
                        el.style.height = '30px';
                    }
                console.log(feature)

                let popup = new mapboxgl.Popup({
                    offset: 25,
                    closeButton: false,
                    closeOnClick: true
                }).setHTML(feature.properties.id +'<br>'+ feature.properties.info);

                new mapboxgl.Marker(el)
                        .setLngLat(feature.geometry.coordinates)
                        .addTo(map)
                        .setPopup(popup);
                el.addEventListener('click', (e) =>
                {
                   let station_name = (e.target.id).split("_");
                   //console.log(station_name);
                   marker_clicked(station_name[1])
                })
                el.addEventListener('mouseover', (e) =>
                {
                   let station_name = (e.target.id).split("_");
                   popup.addTo(map);
                   //console.log(station_name);
                })
                el.addEventListener('mouseout', (e) =>
                {
                   let station_name = (e.target.id).split("_");
                   popup.remove();
                   //console.log(station_name);
                })

            });
        });
});