/* globals maplibregl, MaplibrePreload */

/* eslint no-console: "warn" */
/* eslint max-depth: ["warn", 6] */
/* eslint no-unused-vars: ["error", { "vars": "local" } ] */

;(function (R) {
  'use strict'

  let that

  R.Map = function (options) {
    that = this

    const defaultOptions = {
      container: 'map',
      style: '/maps/combined-root.json',
      bearing: 0,
      pitch: 20,
      zoom: 14.5,
      center: [16.3659, 48.1998],
      minZoom: 7,
      maxZoom: 17.9,
    }

    options = { ...defaultOptions, ...options }
    this._options = options

    this._init()
  }

  R.Map.prototype._init = function () {
    const map = new maplibregl.Map(
      that._options,
    )
    new MaplibrePreload(map)
    that.map = map

    // map.on(
    //     "click",
    //     "radkummerkasten-issues",
    //     (e) => {
    //         map.easeTo({
    //             "center": e.features[0].geometry.coordinates, // schlecht
    //             "zoom": map.getZoom() + 0.1,
    //             "duration": 200,
    //         });
    //     }
    // );

    map.on(
      'mousemove',
      'radkummerkasten-issues',
      (e) => {
        // console.log("mousemove")
        if (e.features.length > 0) {
          map.setLayoutProperty(
            'radkummerkasten-issues',
            'icon-size',
            [
              'match',
              ['get', 'id'],
              e.features[0].properties.id,
              1.0,
              0.75,
            ],
          )
          map.setLayoutProperty(
            'radkummerkasten-issues',
            'symbol-sort-key',
            [
              'match',
              ['get', 'id'],
              e.features[0].properties.id,
              1,
              ['get', 'symbol-sort-key'],
            ],
          )
        }
        else {
          map.setLayoutProperty('radkummerkasten-issues', 'icon-size', 0.75)
          map.setLayoutProperty('radkummerkasten-issues', 'symbol-sort-key', ['get', 'symbol-sort-key'])
        }
      },
    )
    map.on(
      'mouseleave',
      'radkummerkasten-issues',
      () => {
        map.setLayoutProperty('radkummerkasten-issues', 'icon-size', 0.75)
        map.setLayoutProperty('radkummerkasten-issues', 'symbol-sort-key', ['get', 'symbol-sort-key'])
      },
    )

    map.on(
      'click',
      'radkummerkasten-issues-cluster',
      (e) => {
        // console.log(map.getZoom());
        // map.zoomTo(map.getZoom() + 1.0);
        // console.log(map.getZoom());
        // map.flyTo({center: e.features[0].geometry.coordinates});
        map.easeTo(
          {
            zoom: map.getZoom() + 1.0,
            center: e.features[0].geometry.coordinates,
            duration: 200,
          },
        )
      },
    )
  }
}(globalThis.R || (globalThis.R = {})))
