export default function createMap(onLoad, mapboxgl = window.mapboxgl) {
    let map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v10',
        center: [-121.43, 38.61],
        zoom: 9
    });
    map.on('load', () => onLoad(map))
}