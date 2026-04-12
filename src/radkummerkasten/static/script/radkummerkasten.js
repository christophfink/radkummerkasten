/* globals */

/* eslint no-console: "warn" */
/* eslint max-depth: ["warn", 6] */
/* eslint no-unused-vars: ["error", { "vars": "local" } ] */

;(function (R) {
  'use strict'

  // console.log("Radkummerkasten!")

  document.addEventListener('DOMContentLoaded', function () {
    const radkummerkasten = new R.Map({

    })
    globalThis.radkummerkasten = radkummerkasten
  })
})(globalThis.R || (globalThis.R = {}))
