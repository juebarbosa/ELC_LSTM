/*
 * 3DCityDB-Web-Map-Client
 * http://www.3dcitydb.org/
 * 
 * Copyright 2015 - 2017
 * Chair of Geoinformatics
 * Technical University of Munich, Germany
 * https://www.gis.bgu.tum.de/
 * 
 * The 3DCityDB-Web-Map-Client is jointly developed with the following
 * cooperation partners:
 * 
 * virtualcitySYSTEMS GmbH, Berlin <http://www.virtualcitysystems.de/>
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 *     
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**-----------------------------------------Separate Line-------------------------------------------------**/

// URL controller
var urlController = new UrlController();

/*---------------------------------  set globe variables  ----------------------------------------*/
// BingMapsAPI Key for Bing Imagery Layers and Geocoder
// If this is not valid, the Bing Imagery Layers will be removed and the Bing Geocoder will be replaced with OSM Nominatim
var bingToken = urlController.getUrlParaValue('bingToken', window.location.href, CitydbUtil);
if (Cesium.defined(bingToken) && bingToken !== "") {
    Cesium.BingMapsApi.defaultKey = bingToken;
}

// Define clock to be animated per default
var clock = new Cesium.Clock({
    shouldAnimate: true
});

// create 3Dcitydb-web-map instance
var shadows = urlController.getUrlParaValue('shadows', window.location.href, CitydbUtil);
var terrainShadows = urlController.getUrlParaValue('terrainShadows', window.location.href, CitydbUtil);

var cesiumViewerOptions = {
    selectedImageryProviderViewModel: Cesium.createDefaultImageryProviderViewModels()[1],
    timeline: true,
    animation: true,
    fullscreenButton: false,
    shadows: (shadows == "true"),
    terrainShadows: parseInt(terrainShadows),
    clockViewModel: new Cesium.ClockViewModel(clock)
}

// If neither BingMapsAPI key nor ionToken is present, use the OpenStreetMap Geocoder Nominatim
var ionToken = urlController.getUrlParaValue('ionToken', window.location.href, CitydbUtil);
if (Cesium.defined(ionToken) && ionToken !== "") {
    Cesium.Ion.defaultAccessToken = ionToken;
}
if ((!Cesium.defined(Cesium.BingMapsApi.defaultKey) || Cesium.BingMapsApi.defaultKey === "")
    && (!Cesium.defined(ionToken) || ionToken === "")) {
    cesiumViewerOptions.geocoder = new OpenStreetMapNominatimGeocoder();
}

var cesiumViewer = new Cesium.Viewer('cesiumContainer', cesiumViewerOptions);

adjustIonFeatures();

navigationInitialization('cesiumContainer', cesiumViewer);

var cesiumCamera = cesiumViewer.scene.camera;
var webMap = new WebMap3DCityDB(cesiumViewer);

// set default input parameter value and bind the view and model
var addLayerViewModel = {
    url: "",
    name: "",
    layerDataType: "",
    layerProxy: false,
    layerClampToGround: true,
    gltfVersion: "",
    thematicDataUrl: "",
    thematicDataSource: "",
    tableType: "",
    // googleSheetsApiKey: "",
    // googleSheetsRanges: "",
    // googleSheetsClientId: "",
    cityobjectsJsonUrl: "",
    minLodPixels: "",
    maxLodPixels: "",
    maxSizeOfCachedTiles: 200,
    maxCountOfVisibleTiles: 200
};
Cesium.knockout.track(addLayerViewModel);
Cesium.knockout.applyBindings(addLayerViewModel, document.getElementById('citydb_addlayerpanel'));

var addWmsViewModel = {
    name: '',
    iconUrl: '',
    tooltip: '',
    url: '',
    layers: '',
    additionalParameters: '',
    proxyUrl: '/proxy/'
};
Cesium.knockout.track(addWmsViewModel);
Cesium.knockout.applyBindings(addWmsViewModel, document.getElementById('citydb_addwmspanel'));

var addTerrainViewModel = {
    name: '',
    iconUrl: '',
    tooltip: '',
    url: ''
};
Cesium.knockout.track(addTerrainViewModel);
Cesium.knockout.applyBindings(addTerrainViewModel, document.getElementById('citydb_addterrainpanel'));

var addSplashWindowModel = {
    url: '',
    showOnStart: ''
};
Cesium.knockout.track(addSplashWindowModel);
Cesium.knockout.applyBindings(addSplashWindowModel, document.getElementById('citydb_addsplashwindow'));

// Splash controller
var splashController = new SplashController(addSplashWindowModel);

/*---------------------------------  Load Configurations and Layers  ----------------------------------------*/

initClient();

// Store clicked entities
var clickedEntities = {};

function initClient() {
    // adjust cesium navigation help popup for splash window
    splashController.insertSplashInfoHelp();
    // read splash window from url
    splashController.getSplashWindowFromUrl(window.location.href, urlController, jQuery, CitydbUtil, Cesium);

    // init progress indicator gif
    document.getElementById('loadingIndicator').style.display = 'none';

    // activate mouseClick Events		
    webMap.activateMouseClickEvents(true);
    webMap.activateMouseMoveEvents(true);
    webMap.activateViewChangedEvent(true);

    // add Copyrights, TUM, 3DCityDB or more...
    var creditDisplay = cesiumViewer.scene.frameState.creditDisplay;

    var citydbCreditLogo = new Cesium.Credit('<a href="https://www.3dcitydb.org/" target="_blank"><img src="https://3dcitydb.org/3dcitydb/fileadmin/public/logos/3dcitydb_logo.png" title="3DCityDB"></a>');
    creditDisplay.addDefaultCredit(citydbCreditLogo);

    var tumCreditLogo = new Cesium.Credit('<a href="https://www.gis.bgu.tum.de/en/home/" target="_blank">© 2018 Chair of Geoinformatics, TU Munich</a>');
    creditDisplay.addDefaultCredit(tumCreditLogo);

    // activate debug mode
    var debugStr = urlController.getUrlParaValue('debug', window.location.href, CitydbUtil);
    if (debugStr == "true") {
        cesiumViewer.extend(Cesium.viewerCesiumInspectorMixin);
        cesiumViewer.cesiumInspector.viewModel.dropDownVisible = false;
    }

    // set title of the web page
    var titleStr = urlController.getUrlParaValue('title', window.location.href, CitydbUtil);
    if (titleStr) {
        document.title = titleStr;
    }

    // It's an extended Geocoder widget which can also be used for searching object by its gmlid.
    cesiumViewer.geocoder.viewModel._searchCommand.beforeExecute.addEventListener(function (info) {
        var callGeocodingService = info.args[0];
        if (callGeocodingService != true) {
            var gmlId = cesiumViewer.geocoder.viewModel.searchText;
            info.cancel = true;
            cesiumViewer.geocoder.viewModel.searchText = "Searching now.......";
            zoomToObjectById(gmlId, function () {
                cesiumViewer.geocoder.viewModel.searchText = gmlId;
            }, function () {
                cesiumViewer.geocoder.viewModel.searchText = gmlId;
                cesiumViewer.geocoder.viewModel.search.call(this, true);
            });
        }
    });

    // inspect the status of the showed and cached tiles	
    inspectTileStatus();

    // display current infos of active layer in the main menu
    observeActiveLayer();

    // Zoom to desired camera position and load layers if encoded in the url...	
    zoomToDefaultCameraPosition().then(function (info) {
        var layers = urlController.getLayersFromUrl(window.location.href, CitydbUtil, CitydbKmlLayer, Cesium3DTilesDataLayer, Cesium);
        loadLayerGroup(layers);

        var basemapConfigString = urlController.getUrlParaValue('basemap', window.location.href, CitydbUtil);
        if (basemapConfigString) {
            var viewMoModel = Cesium.queryToObject(Object.keys(Cesium.queryToObject(basemapConfigString))[0]);
            for (key in viewMoModel) {
                addWmsViewModel[key] = viewMoModel[key];
            }
            addWebMapServiceProvider();
        }
        
        var cesiumWorldTerrainString = urlController.getUrlParaValue('cesiumWorldTerrain', window.location.href, CitydbUtil);
        if(cesiumWorldTerrainString === "true") {
            // if the Cesium World Terrain is given in the URL --> activate, else other terrains
            cesiumViewer.terrainProvider = Cesium.createWorldTerrain();
            var baseLayerPickerViewModel = cesiumViewer.baseLayerPicker.viewModel;
            baseLayerPickerViewModel.selectedTerrain = baseLayerPickerViewModel.terrainProviderViewModels[1];
        } else {
            var terrainConfigString = urlController.getUrlParaValue('terrain', window.location.href, CitydbUtil);
            if (terrainConfigString) {
                var viewMoModel = Cesium.queryToObject(Object.keys(Cesium.queryToObject(terrainConfigString))[0]);
                for (key in viewMoModel) {
                    addTerrainViewModel[key] = viewMoModel[key];
                }
                addTerrainProvider();
            }
        }
    });

    // jump to a timepoint
    var dayTimeStr = urlController.getUrlParaValue('dayTime', window.location.href, CitydbUtil);
    if (dayTimeStr) {
        var julianDate = Cesium.JulianDate.fromIso8601(decodeURIComponent(dayTimeStr));
        var clock = cesiumViewer.cesiumWidget.clock;
        clock.currentTime = julianDate;
        clock.shouldAnimate = false;
    }

    // add a calendar picker in the timeline using the JS library flatpickr
    var clockElement = document.getElementsByClassName("cesium-animation-blank")[0];
    flatpickr(clockElement, {
        enableTime: true,
        defaultDate: new Date(new Date().toUTCString().substr(0, 25)), // force flatpickr to use UTC
        enableSeconds: true,
        time_24hr: true,
        clickOpens: false
    });
    clockElement.addEventListener("change", function () {
        var dateValue = clockElement.value;
        var cesiumClock = cesiumViewer.clock;
        cesiumClock.shouldAnimate = false; // stop the clock
        cesiumClock.currentTime = Cesium.JulianDate.fromIso8601(dateValue.replace(" ", "T") + "Z");
        // update timeline also
        var cesiumTimeline = cesiumViewer.timeline;
        var lowerBound = Cesium.JulianDate.addHours(cesiumViewer.clock.currentTime, -12, new Object());
        var upperBound = Cesium.JulianDate.addHours(cesiumViewer.clock.currentTime, 12, new Object());
        cesiumTimeline.updateFromClock(); // center the needle in the timeline
        cesiumViewer.timeline.zoomTo(lowerBound, upperBound);
        cesiumViewer.timeline.resize();
    });
    clockElement.addEventListener("click", function () {
        if (clockElement._flatpickr.isOpen) {
            clockElement._flatpickr.close();
        } else {
            clockElement._flatpickr.open();
        }
    });
    cesiumViewer.timeline.addEventListener("click", function() {
        clockElement._flatpickr.setDate(new Date(Cesium.JulianDate.toDate(cesiumViewer.clock.currentTime).toUTCString().substr(0, 25)));
    })

    // Bring the cesium navigation help popup above the compass
    var cesiumNavHelp = document.getElementsByClassName("cesium-navigation-help")[0];
    cesiumNavHelp.style.zIndex = 99999;

    // If the web client has a layer, add an onclick event to the home button to fly to this layer
    var cesiumHomeButton = document.getElementsByClassName("cesium-button cesium-toolbar-button cesium-home-button")[0];
    cesiumHomeButton.onclick = function () {
        zoomToDefaultCameraPosition();
    }
}

function observeActiveLayer() {
    var observable = Cesium.knockout.getObservable(webMap, '_activeLayer');

    observable.subscribe(function (selectedLayer) {
        if (Cesium.defined(selectedLayer)) {
            document.getElementById(selectedLayer.id).childNodes[0].checked = true;

            updateAddLayerViewModel(selectedLayer);
        }
    });

    function updateAddLayerViewModel(selectedLayer) {
        addLayerViewModel.url = selectedLayer.url;
        addLayerViewModel.name = selectedLayer.name;
        addLayerViewModel.layerDataType = selectedLayer.layerDataType;
        addLayerViewModel.layerProxy = selectedLayer.layerProxy;
        addLayerViewModel.layerClampToGround = selectedLayer.layerClampToGround;
        addLayerViewModel.gltfVersion = selectedLayer.gltfVersion;
        addLayerViewModel.thematicDataUrl = selectedLayer.thematicDataUrl;
        addLayerViewModel.thematicDataSource = selectedLayer.thematicDataSource;
        addLayerViewModel.tableType = selectedLayer.tableType;
        // addLayerViewModel.googleSheetsApiKey = selectedLayer.googleSheetsApiKey;
        // addLayerViewModel.googleSheetsRanges = selectedLayer.googleSheetsRanges;
        // addLayerViewModel.googleSheetsClientId = selectedLayer.googleSheetsClientId;
        addLayerViewModel.cityobjectsJsonUrl = selectedLayer.cityobjectsJsonUrl;
        addLayerViewModel.minLodPixels = selectedLayer.minLodPixels;
        addLayerViewModel.maxLodPixels = selectedLayer.maxLodPixels;
        addLayerViewModel.maxSizeOfCachedTiles = selectedLayer.maxSizeOfCachedTiles;
        addLayerViewModel.maxCountOfVisibleTiles = selectedLayer.maxCountOfVisibleTiles;
    }
}

function adjustIonFeatures() {
    // If ion token is not available, remove Cesium World Terrain from the Terrain Providers
    if (!Cesium.defined(ionToken) || ionToken === "") {
        var terrainProviders = cesiumViewer.baseLayerPicker.viewModel.terrainProviderViewModels;
        i = 0;
        while (i < terrainProviders.length) {
            if (terrainProviders[i].name.indexOf("Cesium World Terrain") !== -1) {
                //terrainProviders[i]._creationCommand.canExecute = false;
                terrainProviders.remove(terrainProviders[i]);
            } else {
                i++;
            }
        }

        // Set default imagery to an open-source terrain
        cesiumViewer.baseLayerPicker.viewModel.selectedTerrain = terrainProviders[0];
        console.warn("Due to invalid or missing ion access token from user, Cesium World Terrain has been removed. Please enter your ion access token using the URL-parameter \"ionToken=<your-token>\" and refresh the page if you wish to use ion features.");

        // Cesium ion uses Bing Maps by default -> no need to insert Bing token if an ion token is already available

        // If neither BingMapsAPI key nor ion access token is present, remove Bing Maps from the Imagery Providers
        if (!Cesium.defined(Cesium.BingMapsApi.defaultKey) || Cesium.BingMapsApi.defaultKey === "") {
            var imageryProviders = cesiumViewer.baseLayerPicker.viewModel.imageryProviderViewModels;
            var i = 0;
            while (i < imageryProviders.length) {
                if (imageryProviders[i].name.indexOf("Bing Maps") !== -1) {
                    //imageryProviders[i]._creationCommand.canExecute = false;
                    imageryProviders.remove(imageryProviders[i]);
                } else {
                    i++;
                }
            }

            // Set default imagery to ESRI World Imagery
            cesiumViewer.baseLayerPicker.viewModel.selectedImagery = imageryProviders[3];

            // Disable auto-complete of OSM Geocoder due to OSM usage limitations
            // see https://operations.osmfoundation.org/policies/nominatim/#unacceptable-use
            cesiumViewer._geocoder._viewModel.autoComplete = false;

            console.warn("Due to invalid or missing Bing access token from user, all Bing Maps have been removed. Please enter your Bing Maps API token using the URL-parameter \"bingToken=<your-token>\" and refresh the page if you wish to use Bing Maps.");
        } else {
            console.error("A Bing token has been detected. This requires an ion token to display the terrain correctly. Please either remove the Bing token in the URL to use the default terrain and imagery, or insert an ion token in addition to the existing Bing token to use Cesium World Terrain and Bing Maps.")
            CitydbUtil.showAlertWindow("OK", "Error loading terrain", "A Bing token has been detected. This requires an ion token to display the terrain correctly. Please either remove the Bing token in the URL to use the default terrain and imagery, or insert an ion token in addition to the existing Bing token to use Cesium World Terrain and Bing Maps. Please refer to <a href='https://github.com/3dcitydb/3dcitydb-web-map/releases/tag/v1.9.0' target='_blank'>https://github.com/3dcitydb/3dcitydb-web-map/releases/tag/v1.9.0</a> for more information.");
        }
    }
}

/*---------------------------------  methods and functions  ----------------------------------------*/

function inspectTileStatus() {
    setInterval(function () {
        var cachedTilesInspector = document.getElementById('citydb_cachedTilesInspector');
        var showedTilesInspector = document.getElementById('citydb_showedTilesInspector');
        var layers = webMap._layers;
        var numberOfshowedTiles = 0;
        var numberOfCachedTiles = 0;
        var numberOfTasks = 0;
        var tilesLoaded = true;
        for (var i = 0; i < layers.length; i++) {
            var layer = layers[i];
            if (layers[i].active) {
                if (layer instanceof CitydbKmlLayer) {
                    numberOfshowedTiles = numberOfshowedTiles + Object.keys(layers[i].citydbKmlTilingManager.dataPoolKml).length;
                    numberOfCachedTiles = numberOfCachedTiles + Object.keys(layers[i].citydbKmlTilingManager.networklinkCache).length;
                    numberOfTasks = numberOfTasks + layers[i].citydbKmlTilingManager.taskNumber;
                }
                if (layer instanceof Cesium3DTilesDataLayer) {
                    numberOfshowedTiles = numberOfshowedTiles + layer._tileset._selectedTiles.length;
                    numberOfCachedTiles = numberOfCachedTiles + layer._tileset._statistics.numberContentReady;
                    tilesLoaded = layer._tileset._tilesLoaded;
                }
            }
        }
        showedTilesInspector.innerHTML = 'Number of showed Tiles: ' + numberOfshowedTiles;
        cachedTilesInspector.innerHTML = 'Number of cached Tiles: ' + numberOfCachedTiles;

        var loadingTilesInspector = document.getElementById('citydb_loadingTilesInspector');
        if (numberOfTasks > 0 || !tilesLoaded) {
            loadingTilesInspector.style.display = 'block';
        } else {
            loadingTilesInspector.style.display = 'none';
        }
    }, 200);
}

function listHighlightedObjects() {
    var highlightingListElement = document.getElementById("citydb_highlightinglist");

    emptySelectBox(highlightingListElement, function() {
        var highlightedObjects = webMap.getAllHighlightedObjects();
        for (var i = 0; i < highlightedObjects.length; i++) {
            var option = document.createElement("option");
            option.text = highlightedObjects[i];
            highlightingListElement.add(option);
            highlightingListElement.selectedIndex = 0;
        }
    });
}

function listHiddenObjects() {
    var hidddenListElement = document.getElementById("citydb_hiddenlist");

    emptySelectBox(hidddenListElement, function() {
        var hiddenObjects = webMap.getAllHiddenObjects();
        for (var i = 0; i < hiddenObjects.length; i++) {
            var option = document.createElement("option");
            option.text = hiddenObjects[i];
            hidddenListElement.add(option);
            hidddenListElement.selectedIndex = 0;
        }
    });
}

function emptySelectBox(selectElement, callback) {
    for (var i = selectElement.length - 1; i >= 0; i--) {
        selectElement.remove(1);
    }

    callback();
}

function flyToClickedObject(obj) {
    // The web client stores clicked or ctrlclicked entities in a dictionary clickedEntities with {id, entity} as KVP.
    // The function flyTo from Cesium Viewer will be first employed to fly to the selected entity.
    // NOTE: This flyTo function will fail if the target entity has been unloaded (e.g. user has moved camera away).
    // In this case, the function zoomToObjectById shall be used instead.
    // NOTE: This zoomToObjectById function requires a JSON file containing the IDs and coordinates of objects.
    cesiumViewer.flyTo(clickedEntities[obj.value]).then(function (result) {
        if (!result) {
            zoomToObjectById(obj.value);
        }
    }).otherwise(function (error) {
        zoomToObjectById(obj.value);
    });

    obj.selectedIndex = 0;
}

function saveLayerSettings() {
    var activeLayer = webMap.activeLayer;
    applySaving('url', activeLayer);
    applySaving('name', activeLayer);
    applySaving('layerDataType', activeLayer);
    applySaving('layerProxy', activeLayer);
    applySaving('layerClampToGround', activeLayer);
    applySaving('gltfVersion', activeLayer);
    applySaving('thematicDataUrl', activeLayer);
    applySaving('thematicDataSource', activeLayer);
    applySaving('tableType', activeLayer);
    // applySaving('googleSheetsApiKey', activeLayer);
    // applySaving('googleSheetsRanges', activeLayer);
    // applySaving('googleSheetsClientId', activeLayer);
    applySaving('cityobjectsJsonUrl', activeLayer);
    applySaving('minLodPixels', activeLayer);
    applySaving('maxLodPixels', activeLayer);
    applySaving('maxSizeOfCachedTiles', activeLayer);
    applySaving('maxCountOfVisibleTiles', activeLayer);
    console.log(activeLayer);

    // Update Data Source
    thematicDataSourceAndTableTypeDropdownOnchange();

    // update GUI:
    var nodes = document.getElementById('citydb_layerlistpanel').childNodes;
    for (var i = 0; i < nodes.length; i += 3) {
        var layerOption = nodes[i];
        if (layerOption.id == activeLayer.id) {
            layerOption.childNodes[2].innerHTML = activeLayer.name;
        }
    }

    document.getElementById('loadingIndicator').style.display = 'block';
    var promise = activeLayer.reActivate();
    Cesium.when(promise, function (result) {
        document.getElementById('loadingIndicator').style.display = 'none';
    }, function (error) {
        CitydbUtil.showAlertWindow("OK", "Error", error.message);
        document.getElementById('loadingIndicator').style.display = 'none';
    })

    function applySaving(propertyName, activeLayer) {
        var newValue = addLayerViewModel[propertyName];
        if (propertyName === 'maxLodPixels' && newValue == -1) {
            newValue = Number.MAX_VALUE;
        }
        if (Cesium.isArray(newValue)) {
            activeLayer[propertyName] = newValue[0];
        } else {
            activeLayer[propertyName] = newValue;
        }
    }
}

function loadLayerGroup(_layers) {
    if (_layers.length == 0)
        return;

    document.getElementById('loadingIndicator').style.display = 'block';
    _loadLayer(0);

    function _loadLayer(index) {
        var promise = webMap.addLayer(_layers[index]);
        Cesium.when(promise, function (addedLayer) {
            console.log(addedLayer);
            var options = getDataSourceControllerOptions(addedLayer);
            addedLayer.dataSourceController = new DataSourceController(addedLayer.thematicDataSource, signInController, options);
            addEventListeners(addedLayer);
            addLayerToList(addedLayer);
            if (index < (_layers.length - 1)) {
                index++;
                _loadLayer(index);
            } else {
                webMap._activeLayer = _layers[0];
                document.getElementById('loadingIndicator').style.display = 'none';

                // show/hide glTF version based on the value of Layer Data Type
                layerDataTypeDropdownOnchange();

                thematicDataSourceAndTableTypeDropdownOnchange();
            }
        }).otherwise(function (error) {
            CitydbUtil.showAlertWindow("OK", "Error", error.message);
            console.log(error.stack);
            document.getElementById('loadingIndicator').style.display = 'none';
        });
    }
}

function addLayerToList(layer) {
    var radio = document.createElement('input');
    radio.type = "radio";
    radio.name = "dummyradio";
    radio.onchange = function (event) {
        var targetRadio = event.target;
        var layerId = targetRadio.parentNode.id;
        webMap.activeLayer = webMap.getLayerbyId(layerId);
        console.log(webMap.activeLayer);
    };

    var checkbox = document.createElement('input');
    checkbox.type = "checkbox";
    checkbox.id = "id";
    checkbox.checked = layer.active;
    checkbox.onchange = function (event) {
        var checkbox = event.target;
        var layerId = checkbox.parentNode.id;
        var citydbLayer = webMap.getLayerbyId(layerId);
        if (checkbox.checked) {
            console.log("Layer " + citydbLayer.name + " is visible now!");
            citydbLayer.activate(true);
        } else {
            console.log("Layer " + citydbLayer.name + " is not visible now!");
            citydbLayer.activate(false);
        }
    };

    var label = document.createElement('label')
    label.appendChild(document.createTextNode(layer.name));

    var layerOption = document.createElement('div');
    layerOption.id = layer.id;
    layerOption.appendChild(radio);
    layerOption.appendChild(checkbox);
    layerOption.appendChild(label);

    label.ondblclick = function (event) {
        event.preventDefault();
        var layerId = event.target.parentNode.id;
        var citydbLayer = webMap.getLayerbyId(layerId);
        citydbLayer.zoomToStartPosition();
    }

    var layerlistpanel = document.getElementById("citydb_layerlistpanel")
    layerlistpanel.appendChild(layerOption);
}

function addEventListeners(layer) {

    function auxClickEventListener(object) {
        var objectId;
        var targetEntity;
        if (layer instanceof CitydbKmlLayer) {
            targetEntity = object.id;
            objectId = targetEntity.name;
        } else if (layer instanceof Cesium3DTilesDataLayer) {
            console.log(object);
            if (!(object._content instanceof Cesium.Batched3DModel3DTileContent))
                return;

            var featureArray = object._content._features;
            if (!Cesium.defined(featureArray))
                return;
            var objectId = featureArray[object._batchId].getProperty("id");
            if (!Cesium.defined(objectId))
                return;

            targetEntity = new Cesium.Entity({
                id: objectId
            });
            cesiumViewer.selectedEntity = targetEntity;
        }

        // Save this clicked object for later use (such as zooming using ID)
        clickedEntities[objectId] = targetEntity;

        return [objectId ,targetEntity];
    }

    layer.registerEventHandler("CLICK", function (object) {
        var res = auxClickEventListener(object);
        createInfoTable(res, layer);
    });

    layer.registerEventHandler("CTRLCLICK", function (object) {
        auxClickEventListener(object);
    });
}

function zoomToDefaultCameraPosition() {
    var deferred = Cesium.when.defer();
    var latitudeStr = urlController.getUrlParaValue('latitude', window.location.href, CitydbUtil);
    var longitudeStr = urlController.getUrlParaValue('longitude', window.location.href, CitydbUtil);
    var heightStr = urlController.getUrlParaValue('height', window.location.href, CitydbUtil);
    var headingStr = urlController.getUrlParaValue('heading', window.location.href, CitydbUtil);
    var pitchStr = urlController.getUrlParaValue('pitch', window.location.href, CitydbUtil);
    var rollStr = urlController.getUrlParaValue('roll', window.location.href, CitydbUtil);

    if (latitudeStr && longitudeStr && heightStr && headingStr && pitchStr && rollStr) {
        var cameraPostion = {
            latitude: parseFloat(latitudeStr),
            longitude: parseFloat(longitudeStr),
            height: parseFloat(heightStr),
            heading: parseFloat(headingStr),
            pitch: parseFloat(pitchStr),
            roll: parseFloat(rollStr)
        }
        return flyToCameraPosition(cameraPostion);
    } else {
        return zoomToDefaultCameraPosition_expired();
    }

    return deferred;
}

function zoomToDefaultCameraPosition_expired() {
    var deferred = Cesium.when.defer();
    var cesiumCamera = cesiumViewer.scene.camera;
    var latstr = urlController.getUrlParaValue('lat', window.location.href, CitydbUtil);
    var lonstr = urlController.getUrlParaValue('lon', window.location.href, CitydbUtil);

    if (latstr && lonstr) {
        var lat = parseFloat(latstr);
        var lon = parseFloat(lonstr);
        var range = 800;
        var heading = 6;
        var tilt = 49;
        var altitude = 40;

        var rangestr = urlController.getUrlParaValue('range', window.location.href, CitydbUtil);
        if (rangestr)
            range = parseFloat(rangestr);

        var headingstr = urlController.getUrlParaValue('heading', window.location.href, CitydbUtil);
        if (headingstr)
            heading = parseFloat(headingstr);

        var tiltstr = urlController.getUrlParaValue('tilt', window.location.href, CitydbUtil);
        if (tiltstr)
            tilt = parseFloat(tiltstr);

        var altitudestr = urlController.getUrlParaValue('altitude', window.location.href, CitydbUtil);
        if (altitudestr)
            altitude = parseFloat(altitudestr);

        var _center = Cesium.Cartesian3.fromDegrees(lon, lat);
        var _heading = Cesium.Math.toRadians(heading);
        var _pitch = Cesium.Math.toRadians(tilt - 90);
        var _range = range;
        cesiumCamera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(lon, lat, _range),
            orientation: {
                heading: _heading,
                pitch: _pitch,
                roll: 0
            },
            complete: function () {
                deferred.resolve("fly to the desired camera position");
            }
        });
    } else {
        // default camera postion
        deferred.resolve("fly to the default camera position");
        ;
    }
    return deferred;
}

function flyToCameraPosition(cameraPosition) {
    var deferred = Cesium.when.defer();
    var cesiumCamera = cesiumViewer.scene.camera;
    var longitude = cameraPosition.longitude;
    var latitude = cameraPosition.latitude;
    var height = cameraPosition.height;
    cesiumCamera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(longitude, latitude, height),
        orientation: {
            heading: Cesium.Math.toRadians(cameraPosition.heading),
            pitch: Cesium.Math.toRadians(cameraPosition.pitch),
            roll: Cesium.Math.toRadians(cameraPosition.roll)
        },
        complete: function () {
            deferred.resolve("fly to the desired camera position");
        }
    });
    return deferred;
}

// Creation of a scene link for sharing with other people..
function showSceneLink() {
    var tokens = {
        ionToken: ionToken,
        bingToken: bingToken
    }
    var sceneLink = urlController.generateLink(
        webMap,
        addWmsViewModel,
        addTerrainViewModel,
        addSplashWindowModel,
        tokens,
        signInController,
        googleClientId,
        splashController,
        cesiumViewer,
        Cesium
    );
    CitydbUtil.showAlertWindow("OK", "Scene Link", '<a href="' + sceneLink + '" style="color:#c0c0c0" target="_blank">' + sceneLink + '</a>');
}

// Clear Highlighting effect of all highlighted objects
function clearhighlight() {
    var layers = webMap._layers;
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].active) {
            layers[i].unHighlightAllObjects();
        }
    }
    cesiumViewer.selectedEntity = undefined;
}

// hide the selected objects
function hideSelectedObjects() {
    var layers = webMap._layers;
    var objectIds;
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].active) {
            objectIds = Object.keys(layers[i].highlightedObjects);
            layers[i].hideObjects(objectIds);
        }
    }
}

// show the hidden objects
function showHiddenObjects() {
    var layers = webMap._layers;
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].active) {
            layers[i].showAllObjects();
        }
    }
}

function zoomToObjectById(gmlId, callBackFunc, errorCallbackFunc) {
    gmlId = gmlId.trim();
    var activeLayer = webMap._activeLayer;
    if (Cesium.defined(activeLayer)) {
        var cityobjectsJsonData = activeLayer.cityobjectsJsonData;
        if (!cityobjectsJsonData) {
            if (Cesium.defined(errorCallbackFunc)) {
                errorCallbackFunc.call(this);
            }
        } else {
            var obj = cityobjectsJsonData[gmlId];
        }
        if (obj) {
            var lon = (obj.envelope[0] + obj.envelope[2]) / 2.0;
            var lat = (obj.envelope[1] + obj.envelope[3]) / 2.0;
            flyToMapLocation(lat, lon, callBackFunc);
        } else {
            // TODO
            var thematicDataUrl = webMap.activeLayer.thematicDataUrl;
            webmap._activeLayer.dataSourceController.fetchData(gmlId, function (result) {
                if (!result) {
                    if (Cesium.defined(errorCallbackFunc)) {
                        errorCallbackFunc.call(this);
                    }
                } else {
                    var centroid = result["CENTROID"];
                    if (centroid) {
                        var res = centroid.match(/\(([^)]+)\)/)[1].split(",");
                        var lon = parseFloat(res[0]);
                        var lat = parseFloat(res[1]);
                        flyToMapLocation(lat, lon, callBackFunc);
                    } else {
                        if (Cesium.defined(errorCallbackFunc)) {
                            errorCallbackFunc.call(this);
                        }
                    }
                }
            }, 1000);

            // var promise = fetchDataFromGoogleFusionTable(gmlId, thematicDataUrl);
            // Cesium.when(promise, function (result) {
            //     var centroid = result["CENTROID"];
            //     if (centroid) {
            //         var res = centroid.match(/\(([^)]+)\)/)[1].split(",");
            //         var lon = parseFloat(res[0]);
            //         var lat = parseFloat(res[1]);
            //         flyToMapLocation(lat, lon, callBackFunc);
            //     } else {
            //         if (Cesium.defined(errorCallbackFunc)) {
            //             errorCallbackFunc.call(this);
            //         }
            //     }
            // }, function () {
            //     if (Cesium.defined(errorCallbackFunc)) {
            //         errorCallbackFunc.call(this);
            //     }
            // });
        }
    } else {
        if (Cesium.defined(errorCallbackFunc)) {
            errorCallbackFunc.call(this);
        }
    }
}

function flyToMapLocation(lat, lon, callBackFunc) {
    var cesiumWidget = webMap._cesiumViewerInstance.cesiumWidget;
    var scene = cesiumWidget.scene;
    var camera = scene.camera;
    var canvas = scene.canvas;
    var globe = scene.globe;
    var clientWidth = canvas.clientWidth;
    var clientHeight = canvas.clientHeight;
    camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(lon, lat, 2000),
        complete: function () {
            var intersectedPoint = globe.pick(camera.getPickRay(new Cesium.Cartesian2(clientWidth / 2, clientHeight / 2)), scene);
            var terrainHeight = Cesium.Ellipsoid.WGS84.cartesianToCartographic(intersectedPoint).height;
            var center = Cesium.Cartesian3.fromDegrees(lon, lat, terrainHeight);
            var heading = Cesium.Math.toRadians(0);
            var pitch = Cesium.Math.toRadians(-50);
            var range = 100;
            camera.lookAt(center, new Cesium.HeadingPitchRange(heading, pitch, range));
            camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
            if (Cesium.defined(callBackFunc)) {
                callBackFunc.call(this);
            }
        }
    })
}

function addNewLayer() {
    var _layers = new Array();
    var options = {
        url: addLayerViewModel.url.trim(),
        name: addLayerViewModel.name.trim(),
        layerDataType: addLayerViewModel.layerDataType.trim(),
        layerProxy: (addLayerViewModel.layerProxy === true),
        layerClampToGround: (addLayerViewModel.layerClampToGround === true),
        gltfVersion: addLayerViewModel.gltfVersion.trim(),
        thematicDataUrl: addLayerViewModel.thematicDataUrl.trim(),
        thematicDataSource: addLayerViewModel.thematicDataSource.trim(),
        tableType: addLayerViewModel.tableType.trim(),
        // googleSheetsApiKey: addLayerViewModel.googleSheetsApiKey.trim(),
        // googleSheetsRanges: addLayerViewModel.googleSheetsRanges.trim(),
        // googleSheetsClientId: addLayerViewModel.googleSheetsClientId.trim(),
        cityobjectsJsonUrl: addLayerViewModel.cityobjectsJsonUrl.trim(),
        minLodPixels: addLayerViewModel.minLodPixels,
        maxLodPixels: addLayerViewModel.maxLodPixels == -1 ? Number.MAX_VALUE : addLayerViewModel.maxLodPixels,
        maxSizeOfCachedTiles: addLayerViewModel.maxSizeOfCachedTiles,
        maxCountOfVisibleTiles: addLayerViewModel.maxCountOfVisibleTiles
    }
    
    // since Cesium 3D Tiles also require name.json in the URL, it must be checked first
    var layerDataTypeDropdown = document.getElementById("layerDataTypeDropdown");
    if (layerDataTypeDropdown.options[layerDataTypeDropdown.selectedIndex].value === 'Cesium 3D Tiles') {
        _layers.push(new Cesium3DTilesDataLayer(options));
    } else if (['kml', 'kmz', 'json', 'czml'].indexOf(CitydbUtil.get_suffix_from_filename(options.url)) > -1) {
        _layers.push(new CitydbKmlLayer(options));
    }

    loadLayerGroup(_layers);
}

function removeSelectedLayer() {
    var layer = webMap.activeLayer;
    if (Cesium.defined(layer)) {
        var layerId = layer.id;
        document.getElementById(layerId).remove();
        webMap.removeLayer(layerId);
        // update active layer of the globe webMap
        var webMapLayers = webMap._layers;
        if (webMapLayers.length > 0) {
            webMap.activeLayer = webMapLayers[0];
        } else {
            webMap.activeLayer = undefined;
        }
    }
}

function addWebMapServiceProvider() {
    var baseLayerPickerViewModel = cesiumViewer.baseLayerPicker.viewModel;
    var wmsProviderViewModel = new Cesium.ProviderViewModel({
        name: addWmsViewModel.name.trim(),
        iconUrl: addWmsViewModel.iconUrl.trim(),
        tooltip: addWmsViewModel.tooltip.trim(),
        creationFunction: function () {
            return new Cesium.WebMapServiceImageryProvider({
                url: new Cesium.Resource({url: addWmsViewModel.url.trim(), proxy: addWmsViewModel.proxyUrl.trim().length == 0 ? null : new Cesium.DefaultProxy(addWmsViewModel.proxyUrl.trim())}),
                layers: addWmsViewModel.layers.trim(),
                parameters: Cesium.queryToObject(addWmsViewModel.additionalParameters.trim())
            });
        }
    });
    baseLayerPickerViewModel.imageryProviderViewModels.push(wmsProviderViewModel);
    baseLayerPickerViewModel.selectedImagery = wmsProviderViewModel;
}

function removeImageryProvider() {
    var baseLayerPickerViewModel = cesiumViewer.baseLayerPicker.viewModel;
    var selectedImagery = baseLayerPickerViewModel.selectedImagery;
    baseLayerPickerViewModel.imageryProviderViewModels.remove(selectedImagery);
    baseLayerPickerViewModel.selectedImagery = baseLayerPickerViewModel.imageryProviderViewModels[0];
}

function addTerrainProvider() {
    var baseLayerPickerViewModel = cesiumViewer.baseLayerPicker.viewModel;
    var demProviderViewModel = new Cesium.ProviderViewModel({
        name: addTerrainViewModel.name.trim(),
        iconUrl: addTerrainViewModel.iconUrl.trim(),
        tooltip: addTerrainViewModel.tooltip.trim(),
        creationFunction: function () {
            return new Cesium.CesiumTerrainProvider({
                url: addTerrainViewModel.url.trim()
            });
        }
    })
    baseLayerPickerViewModel.terrainProviderViewModels.push(demProviderViewModel);
    baseLayerPickerViewModel.selectedTerrain = demProviderViewModel;
}

function removeTerrainProvider() {
    var baseLayerPickerViewModel = cesiumViewer.baseLayerPicker.viewModel;
    var selectedTerrain = baseLayerPickerViewModel.selectedTerrain;
    baseLayerPickerViewModel.terrainProviderViewModels.remove(selectedTerrain);
    baseLayerPickerViewModel.selectedTerrain = baseLayerPickerViewModel.terrainProviderViewModels[0];
}

function createScreenshot() {
    cesiumViewer.render();
    var imageUri = cesiumViewer.canvas.toDataURL();
    var imageWin = window.open("");
    imageWin.document.write("<html><head>" +
            "<title>" + imageUri + "</title></head><body>" +
            '<img src="' + imageUri + '"width="100%">' +
            "</body></html>");
    return imageWin;
}

function printCurrentview() {
    var imageWin = createScreenshot();
    imageWin.document.close();
    imageWin.focus();
    imageWin.print();
    imageWin.close();
}

function toggleShadows() {
    cesiumViewer.shadows = !cesiumViewer.shadows;
    if (!cesiumViewer.shadows) {
        cesiumViewer.terrainShadows = Cesium.ShadowMode.DISABLED;
    }
}

function toggleTerrainShadows() {
    if (cesiumViewer.terrainShadows == Cesium.ShadowMode.ENABLED) {
        cesiumViewer.terrainShadows = Cesium.ShadowMode.DISABLED;
    } else {
        cesiumViewer.terrainShadows = Cesium.ShadowMode.ENABLED;
        if (!cesiumViewer.shadows) {
            CitydbUtil.showAlertWindow("OK", "Switching on terrain shadows now", 'Please note that shadows for 3D models will also be switched on.',
                    function () {
                        toggleShadows();
                    });
        }
    }
}

// source https://www.w3resource.com/javascript-exercises/javascript-regexp-exercise-9.php
function isValidUrl(str) {
    regexp =  /^(?:(?:https?|ftp):\/\/)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})))(?::\d{2,5})?(?:\/\S*)?$/;
    return regexp.test(str);
}

function createInfoTable(res, citydbLayer) {
    var thematicDataSourceDropdown = document.getElementById("thematicDataSourceDropdown");
    var selectedThematicDataSource = thematicDataSourceDropdown.options[thematicDataSourceDropdown.selectedIndex].value;
    var gmlid = selectedThematicDataSource === "KML" ? res[1]._id : res[0];
    var cesiumEntity = res[1];

    var thematicDataUrl = citydbLayer.thematicDataUrl;
    cesiumEntity.description = "Loading feature information...";

    citydbLayer.dataSourceController.fetchData(gmlid, function (kvp) {
        if (!kvp) {
            cesiumEntity.description = 'No feature information found';
        } else {
            console.log(kvp);
            var html = '<table class="cesium-infoBox-defaultTable" style="font-size:10.5pt"><tbody>';
            for (var key in kvp) {
                var iValue = kvp[key];
                // check if this value is a valid URL
                if (isValidUrl(iValue)) {
                    iValue = '<a href="' + iValue + '" target="_blank">' + iValue + '</a>';
                }
                html += '<tr><td>' + key + '</td><td>' + iValue + '</td></tr>';
            }
            html += '</tbody></table>';

            cesiumEntity.description = html;
        }
    }, 1000, cesiumEntity);

    // Create the button
    const button = createButtonHouseholds(gmlid);

                // check if this value is a valid URL
//                if (key === "num_of_building_units") {
//                    iValue += '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
//                        + `<button id="showDetails" type="button">Show Details</button>`;
//                } else if (isValidUrl(iValue)) {
//                    // Convert valid URLs to clickable links
//                    iValue = '<a href="' + iValue + '" target="_blank">' + iValue + '</a>';
//                }
//
//                html += '<tr><td>' + key + '</td><td>' + iValue + '</td></tr>';
//            }
//            html += '</tbody></table>';


    //createButtonHouseholds(gmlid)

    // fetchDataFromGoogleFusionTable(gmlid, thematicDataUrl).then(function (kvp) {
    //     console.log(kvp);
    //     var html = '<table class="cesium-infoBox-defaultTable" style="font-size:10.5pt"><tbody>';
    //     for (var key in kvp) {
    //         html += '<tr><td>' + key + '</td><td>' + kvp[key] + '</td></tr>';
    //     }
    //     html += '</tbody></table>';
    //
    //     cesiumEntity.description = html;
    // }).otherwise(function (error) {
    //     cesiumEntity.description = 'No feature information found';
    // });
}


function createButtonHouseholds(gmlid) {
    // Create a button element
    var button = document.createElement("button");
    button.innerHTML = "Show Details";

    // Style the button
    button.style.position = "absolute";
    button.style.top = "136px"; // 140 pixels from the top
    button.style.right = "22px"; // 22 pixels from the right
    button.style.height = "21px"; // Set button height
    button.style.width = "110px";
    button.style.padding = "2 8px"; // Adjust padding for height
    button.style.fontSize = "12px";
    button.style.cursor = "pointer";
    button.style.zIndex = "1000"; // Ensure it appears above other elements
    button.style.backgroundColor = "white"; // White button color
    button.style.color = "black"; // Black text color
    button.style.border = "1px solid #ccc"; // Add a light border for better visibility
    button.style.borderRadius = "4px";
    button.style.boxShadow = "0 2px 4px rgba(0, 0, 0, 0.2)";

    // Add a click event listener to the button
    button.addEventListener("click", function () {
        //alert("clicked");
        displayHouseholdsTable(gmlid);
    });

    // Add the button to the body
    document.body.appendChild(button);

    // Add a click event listener to the Cesium InfoBox close button
    const infoBoxCloseButton = document.querySelector(".cesium-infoBox-close");
    if (infoBoxCloseButton) {
        // Add an event listener to the close button
        infoBoxCloseButton.addEventListener("click", function () {
            // Remove the button from the DOM when the InfoBox closes
            if (button.parentNode) {
                button.parentNode.removeChild(button);
            }
        });
    }
}


function displayHouseholdsTable(gmlid) {
    // Define the path to the CSV file
    const csvFilePath = `tables_data_households/${gmlid}.csv`;

    // Fetch the CSV file
    fetch(csvFilePath)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Could not fetch the file: ${response.statusText}`);
            }
            return response.text();
        })
        .then(csvText => {
            // Parse the CSV file
            const rows = csvText.split("\n").map(row => row.split(","));
            const headers = rows[0].slice(1); // Skip the first column for headers
            const dataRows = rows.slice(1).map(row => row.slice(1)); // Skip the first column for data

            // Add an extra header for the "Load Profile" column
            headers.push("Actions");

            // Create a container for the table and close button
            const container = document.createElement("div");
            container.style.position = "fixed";
            container.style.top = "300px"; 
            container.style.right = "1px";
            container.style.width = "474px"; // Increased width for additional column
            container.style.backgroundColor = "rgba(0, 0, 0, 0.6)"; // Slightly transparent black background
            container.style.borderRadius = "4px";
            container.style.overflow = "hidden";
            container.style.zIndex = "999"; // Ensure visibility
            container.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.3)";

            // Check if a container already exists and remove it
            const existingContainer = document.querySelector(`#table-container-${gmlid}`);
            if (existingContainer) {
                existingContainer.remove();
            }

            // Add a close button
            const closeButton = document.createElement("button");
            closeButton.innerHTML = "X";
            closeButton.style.position = "absolute";
            closeButton.style.top = "0px";
            closeButton.style.right = "10px";
            closeButton.style.backgroundColor = "transparent";
            closeButton.style.color = "white";
            closeButton.style.border = "none";
            
            closeButton.style.width = "25px";
            closeButton.style.height = "25px";
            closeButton.style.cursor = "pointer";
            closeButton.style.fontSize = "12px";
            closeButton.style.fontWeight = "bold";
            closeButton.style.textAlign = "center";
            closeButton.style.lineHeight = "25px";
            closeButton.addEventListener("click", function () {
                container.remove(); // Remove the table container
            });

            container.appendChild(closeButton);

            const tableWrapper = document.createElement("div");
            tableWrapper.style.maxHeight = "300px";
            tableWrapper.style.overflowY = "auto"; 
            tableWrapper.style.marginTop = "20px";
            tableWrapper.style.paddingRight = "5px"; 

            // Create the table element
            const table = document.createElement("table");
            table.style.width = "100%";
            table.style.borderCollapse = "collapse";
            table.style.backgroundColor = "transparent";
            table.style.color = "white"; // White text
            table.style.fontFamily = "Arial, sans-serif";
            table.style.fontSize = "12px";

            // Add table headers
            const thead = document.createElement("thead");
            const headerRow = document.createElement("tr");
            headers.forEach(header => {
                const th = document.createElement("th");
                th.innerText = header;
                th.style.backgroundColor = "rgba(51, 51, 51, 0.8)"; // Semi-transparent dark grey for header row
                th.style.color = "white";
                th.style.padding = "10px";
                th.style.textAlign = "center";
                th.style.fontWeight = "bold";
                th.style.borderBottom = "1px solid rgba(255, 255, 255, 0.5)";
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Add table rows with alternating transparent shades of grey
            const tbody = document.createElement("tbody");
            dataRows.forEach((row, index) => {
                if (row.length > 0) { // Skip empty lines
                    const tr = document.createElement("tr");
                    const rowColor = index % 2 === 0 ? "rgba(74, 74, 74, 0.7)" : "rgba(92, 92, 92, 0.7)"; // Alternating shades of transparent grey
                    tr.style.backgroundColor = rowColor;

                    // Add table data cells
                    row.forEach(cell => {
                        const td = document.createElement("td");
                        td.innerText = cell;
                        td.style.padding = "8px";
                        td.style.textAlign = "center";
                        td.style.borderBottom = "1px solid rgba(255, 255, 255, 0.5)";
                        tr.appendChild(td);
                    });

                    // Add a cell for the "Load Profile" button
                    const actionTd = document.createElement("td");
                    const loadProfileButton = document.createElement("button");
                    loadProfileButton.innerText = "Load Profile";
                    loadProfileButton.style.padding = "5px 10px";
                    loadProfileButton.style.fontSize = "12px";
                    loadProfileButton.style.backgroundColor = "white"; // White background
                    loadProfileButton.style.color = "black"; // Black text
                    loadProfileButton.style.border = "1px solid darkgrey"; // Dark grey border
                    loadProfileButton.style.borderRadius = "4px";
                    loadProfileButton.style.cursor = "pointer";

                    // Call "getBdewLoadProfile" on button click
                    loadProfileButton.addEventListener("click", function () {
                        getBdewLoadProfile(gmlid, index + 1); // Pass gmlid and row index
                    });

                    actionTd.appendChild(loadProfileButton);
                    actionTd.style.textAlign = "center";
                    actionTd.style.borderBottom = "1px solid rgba(255, 255, 255, 0.5)";
                    tr.appendChild(actionTd);

                    tbody.appendChild(tr);
                }
            });
            table.appendChild(tbody);

            
            tableWrapper.appendChild(table);
            container.appendChild(tableWrapper);

            // Add the container to the body
            document.body.appendChild(container);
        })
        .catch(error => {
            console.error("Error fetching or parsing the CSV file:", error);
        });
}


function getBdewLoadProfile(gmlid, rowIndex) {
    // Function to create a reusable close button
    function createCloseButton(popup) {
        const closeButton = document.createElement("button");
        closeButton.innerHTML = "&times;"; // Unicode for "X"
        closeButton.style.position = "absolute";
        closeButton.style.top = "10px";
        closeButton.style.right = "10px";
        closeButton.style.padding = "5px";
        closeButton.style.fontSize = "16px";
        closeButton.style.backgroundColor = "transparent";
        closeButton.style.border = "none";
        closeButton.style.color = "gray";
        closeButton.style.cursor = "pointer";
        closeButton.addEventListener("click", () => {
            document.body.removeChild(popup); // Properly remove the popup
        });
        return closeButton;
    }

    // Create a popup window
    const popup = document.createElement("div");
    popup.style.position = "absolute";
    popup.style.top = "50%";
    popup.style.left = "50%";
    popup.style.transform = "translate(-50%, -50%)";
    popup.style.padding = "20px";
    popup.style.backgroundColor = "white";
    popup.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.2)";
    popup.style.borderRadius = "8px";
    popup.style.zIndex = "1000";
    popup.style.textAlign = "center";

    // Add close button to popup
    popup.appendChild(createCloseButton(popup));

    const message = document.createElement("p");
    message.innerText = "Do you want to plot the Daily, Monthly, or Yearly Load Profile?";
    message.style.marginBottom = "20px";
    message.style.fontSize = "16px";
    popup.appendChild(message);

    // Small note about available data
    const smallNote = document.createElement("small");
    smallNote.innerText = "Data available for the year 2024";
    smallNote.style.display = "block";
    smallNote.style.marginBottom = "20px";
    smallNote.style.color = "gray";
    popup.appendChild(smallNote);

    // Create "Daily" button
    const dailyButton = document.createElement("button");
    dailyButton.innerText = "Daily";
    dailyButton.style.padding = "10px 20px";
    dailyButton.style.margin = "5px";
    dailyButton.style.backgroundColor = "#007BFF";
    dailyButton.style.color = "white";
    dailyButton.style.border = "none";
    dailyButton.style.borderRadius = "4px";
    dailyButton.style.cursor = "pointer";
    dailyButton.addEventListener("click", () => {
        popup.innerHTML = ""; // Clear the popup content
        popup.appendChild(createCloseButton(popup)); // Add close button to new content

        const newMessage = document.createElement("p");
        newMessage.innerText = "Which day do you want to plot the load profile for?";
        newMessage.style.marginBottom = "20px";
        newMessage.style.fontSize = "16px";
        popup.appendChild(newMessage);

        const inputField = document.createElement("input");
        inputField.type = "text";
        inputField.placeholder = "e.g., 15.01";
        inputField.style.marginBottom = "20px";
        inputField.style.padding = "10px";
        inputField.style.border = "1px solid #ccc";
        inputField.style.borderRadius = "4px";
        inputField.style.width = "75%";
        popup.appendChild(inputField);

        const submitButton = document.createElement("button");
        submitButton.innerText = "Submit";
        submitButton.style.padding = "10px 20px";
        submitButton.style.marginTop = "10px";
        submitButton.style.backgroundColor = "#28a745";
        submitButton.style.color = "white";
        submitButton.style.border = "none";
        submitButton.style.borderRadius = "4px";
        submitButton.style.cursor = "pointer";
        submitButton.addEventListener("click", () => {
            const day = inputField.value.trim();
            if (!/^\d{2}\.\d{2}$/.test(day)) {
                alert("Please enter a valid date in the format dd.mm");
                return;
            }
            document.body.removeChild(popup); // Close popup
            plotLoadProfile(gmlid, rowIndex, "daily", day);
        });
        popup.appendChild(submitButton);
    });
    popup.appendChild(dailyButton);

    // Create "Monthly" button
    const monthlyButton = document.createElement("button");
    monthlyButton.innerText = "Monthly";
    monthlyButton.style.padding = "10px 20px";
    monthlyButton.style.margin = "5px";
    monthlyButton.style.backgroundColor = "#007BFF";
    monthlyButton.style.color = "white";
    monthlyButton.style.border = "none";
    monthlyButton.style.borderRadius = "4px";
    monthlyButton.style.cursor = "pointer";
    monthlyButton.addEventListener("click", () => {
        popup.innerHTML = ""; // Clear the popup content
        popup.appendChild(createCloseButton(popup)); // Add close button to new content

        const newMessage = document.createElement("p");
        newMessage.innerText = "Which month do you want to plot the load profile for?";
        newMessage.style.marginBottom = "20px";
        newMessage.style.fontSize = "16px";
        popup.appendChild(newMessage);

        const inputField = document.createElement("input");
        inputField.type = "text";
        inputField.placeholder = "e.g., 01 for January";
        inputField.style.marginBottom = "20px";
        inputField.style.padding = "10px";
        inputField.style.border = "1px solid #ccc";
        inputField.style.borderRadius = "4px";
        inputField.style.width = "75%";
        popup.appendChild(inputField);

        const submitButton = document.createElement("button");
        submitButton.innerText = "Submit";
        submitButton.style.padding = "10px 20px";
        submitButton.style.marginTop = "10px";
        submitButton.style.backgroundColor = "#28a745";
        submitButton.style.color = "white";
        submitButton.style.border = "none";
        submitButton.style.borderRadius = "4px";
        submitButton.style.cursor = "pointer";
        submitButton.addEventListener("click", () => {
            const month = inputField.value.trim();
            if (!/^\d{2}$/.test(month) || parseInt(month, 10) < 1 || parseInt(month, 10) > 12) {
                alert("Please enter a valid month in the format mm");
                return;
            }
            document.body.removeChild(popup); // Close popup
            plotLoadProfile(gmlid, rowIndex, "monthly", month);
        });
        popup.appendChild(submitButton);
    });
    popup.appendChild(monthlyButton);

    // Create "Yearly" button
    const yearlyButton = document.createElement("button");
    yearlyButton.innerText = "Yearly";
    yearlyButton.style.padding = "10px 20px";
    yearlyButton.style.margin = "5px";
    yearlyButton.style.backgroundColor = "#007BFF";
    yearlyButton.style.color = "white";
    yearlyButton.style.border = "none";
    yearlyButton.style.borderRadius = "4px";
    yearlyButton.style.cursor = "pointer";
    yearlyButton.addEventListener("click", () => {
        document.body.removeChild(popup); // Close popup
        plotLoadProfile(gmlid, rowIndex, "yearly");
    });
    popup.appendChild(yearlyButton);

    // Append the popup to the body
    document.body.appendChild(popup);
}



function plotLoadProfile(gmlid, rowIndex, type, userInput) {
    const filePaths = {
        bdew: `tables_data_households/${gmlid}_W${(rowIndex - 1)}_H0SLP_LSTM.csv`,
        bdew_s: `tables_data_households/${gmlid}_W${(rowIndex - 1)}_H0SLP_Stats.csv`,
        lstm: `tables_data_households/${gmlid}_W${(rowIndex - 1)}_LSTM.csv`
    };

    console.log("Fetching files:", filePaths);

    Promise.all([
        fetch(filePaths.bdew).then(response => {
            if (!response.ok) {
                throw new Error(`Could not fetch the file ${filePaths.bdew}: ${response.statusText}`);
            }
            return response.text();
        }),
        fetch(filePaths.bdew_s).then(response => {
            if (!response.ok) {
                throw new Error(`Could not fetch the file ${filePaths.bdew_s}: ${response.statusText}`);
            }
            return response.text();
        }),
        fetch(filePaths.lstm).then(response => {
            if (!response.ok) {
                throw new Error(`Could not fetch the file ${filePaths.lstm}: ${response.statusText}`);
            }
            return response.text();
        })
    ])
        .then(([bdewCsv, bdewSCsv, lstmCsv]) => {
            const processData = (csvText, type, userInput) => {
                const rows = csvText.split("\n").filter(row => row.trim() !== "");
                console.log("Rows:", rows);
                const xData = [];
                const yData = [];

                if (type === "daily") {
                    const targetDate = `2024-${userInput.split(".")[1]}-${userInput.split(".")[0]}`;

                    for (let i = 0; i < 24; i++) {
                        xData.push(`${String(i).padStart(2, "0")}:00`);
                    }

                    for (let row of rows) {
                        const [timestamp, value] = row.split(",");
                        const date = timestamp?.trim().substring(0, 10);
                        const time = timestamp?.trim().substring(11, 16);
                        if (date === targetDate && xData.includes(time)) {
                            yData.push(parseFloat(value));
                        }
                    }
                } else if (type === "monthly") {
                    const targetMonth = `2024-${userInput.padStart(2, "0")}`;

                    for (let row of rows) {
                        const [timestamp, value] = row.split(",");
                        const month = timestamp?.trim().substring(0, 7);
                        if (month === targetMonth) {
                            xData.push(timestamp.trim());
                            yData.push(parseFloat(value));
                        }
                    }
                } else if (type === "yearly") {
                    for (let row of rows) {
                        const [timestamp, value] = row.split(",");
                        xData.push(timestamp?.trim());
                        yData.push(parseFloat(value));
                    }
                }

                console.log(`xData (${type} - ${userInput}):`, xData);
                console.log(`yData (${type} - ${userInput}):`, yData);

                if (xData.length === 0 || yData.length === 0) {
                    throw new Error(`No data available for ${type} with input ${userInput}`);
                }

                return { xData, yData };
            };

            const bdewData = processData(bdewCsv, type, userInput);
            const bdewSData = processData(bdewSCsv, type, userInput);
            const lstmData = processData(lstmCsv, type, userInput);

            if (bdewData.xData.length !== lstmData.xData.length || bdewData.xData.length !== bdewSData.xData.length) {
                console.warn("Mismatched xData lengths. Adjusting to match...");
                const minLength = Math.min(bdewData.xData.length, bdewSData.xData.length, lstmData.xData.length);
                bdewData.xData = bdewData.xData.slice(0, minLength);
                bdewData.yData = bdewData.yData.slice(0, minLength);
                bdewSData.xData = bdewSData.xData.slice(0, minLength);
                bdewSData.yData = bdewSData.yData.slice(0, minLength);
                lstmData.xData = lstmData.xData.slice(0, minLength);
                lstmData.yData = lstmData.yData.slice(0, minLength);
            }

            const plotPopup = document.createElement("div");
            plotPopup.style.position = "absolute";
            plotPopup.style.top = "50px";
            plotPopup.style.left = "50px";
            plotPopup.style.width = "800px";
            plotPopup.style.height = "600px";
            plotPopup.style.backgroundColor = "white";
            plotPopup.style.borderRadius = "10px";
            plotPopup.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.3)";
            plotPopup.style.padding = "10px";
            plotPopup.style.zIndex = "1000";

            const title = document.createElement("h2");
            if (type === "daily") {
                title.innerText = `Daily Load Profile (${userInput}.2024)`;
            } else if (type === "monthly") {
                const monthNames = {
                    "01": "January",
                    "02": "February",
                    "03": "March",
                    "04": "April",
                    "05": "May",
                    "06": "June",
                    "07": "July",
                    "08": "August",
                    "09": "September",
                    "10": "October",
                    "11": "November",
                    "12": "December"
                };
                const monthName = monthNames[userInput.padStart(2, "0")] || "Invalid Month";
                title.innerText = `Monthly Load Profile (${monthName} 2024)`;
            } else if (type === "yearly") {
                title.innerText = "Yearly Load Profile (2024)";
            }
            title.style.textAlign = "center";
            title.style.marginBottom = "10px";
            plotPopup.appendChild(title);

            const closeButton = document.createElement("button");
            closeButton.innerText = "Close";
            closeButton.style.position = "absolute";
            closeButton.style.top = "10px";
            closeButton.style.right = "10px";
            closeButton.style.padding = "5px 10px";
            closeButton.style.backgroundColor = "#FF5C5C";
            closeButton.style.color = "white";
            closeButton.style.border = "none";
            closeButton.style.borderRadius = "4px";
            closeButton.style.cursor = "pointer";
            closeButton.addEventListener("click", () => {
                document.body.removeChild(plotPopup);
            });
            plotPopup.appendChild(closeButton);

            const chartDiv = document.createElement("div");
            chartDiv.id = "chart_div";
            chartDiv.style.width = "100%";
            chartDiv.style.height = "400px";
            plotPopup.appendChild(chartDiv);

            const exportButton = document.createElement("button");
            exportButton.innerText = "Export";
            exportButton.style.position = "absolute";
            exportButton.style.right = "20px";
            exportButton.style.top = "50%";
            exportButton.style.transform = "translateY(-50%)";
            exportButton.style.padding = "10px 20px";
            exportButton.style.backgroundColor = "#D3D3D3";
            exportButton.style.color = "black";
            exportButton.style.border = "1px solid #ccc";
            exportButton.style.borderRadius = "4px";
            exportButton.style.cursor = "pointer";
            exportButton.addEventListener("click", () => {
                downloadCSV(bdewData, `${gmlid}_W${rowIndex}_H0SLP_LSTM_${type}.csv`);
                downloadCSV(bdewSData, `${gmlid}_W${rowIndex}_H0SLP_Stats_${type}.csv`);
                downloadCSV(lstmData, `${gmlid}_W${rowIndex}_LSTM_${type}.csv`);
            });
            plotPopup.appendChild(exportButton);

            function downloadCSV(data, fileName) {
                const csvContent = ["Time,Value", ...data.xData.map((x, i) => `${x},${data.yData[i]}`)].join("\n");
                const blob = new Blob([csvContent], { type: "text/csv" });
                const link = document.createElement("a");
                link.href = URL.createObjectURL(blob);
                link.download = fileName;
                link.click();
            }

            document.body.appendChild(plotPopup);

            google.charts.load("current", { packages: ["corechart"] });
            google.charts.setOnLoadCallback(() => drawChart(bdewData, bdewSData, lstmData));

            function drawChart(bdewData, bdewSData, lstmData) {
                const chartData = [["Time", "H0SLP_LSTM", "H0SLP_Stats", "LSTM"]];

                for (let i = 0; i < bdewData.xData.length; i++) {
                    chartData.push([
                        bdewData.xData[i] || bdewSData.xData[i] || lstmData.xData[i],
                        bdewData.yData[i] || 0,
                        bdewSData.yData[i] || 0,
                        lstmData.yData[i] || 0
                    ]);
                }

                const data = google.visualization.arrayToDataTable(chartData);

                const options = {
                    title: "Electricity Consumption [kWh]",
                    width: 800,
                    height: 500,
                    legend: { position: "bottom" },
                    hAxis: { title: "Time" },
                    vAxis: { title: "kWh" },
                    series: {
                        0: { color: "#1f77b4" },
                        1: { color: "#2ca02c" },
                        2: { color: "#ff7f0e" }
                    }
                };

                const chart = new google.visualization.LineChart(chartDiv);
                chart.draw(data, options);
            }
        })
        .catch(error => {
            console.error("Error fetching or processing CSV files:", error);
        });
}




// JavaScript function to display another table on button click
function displayAdditionalTable(gmlid, cesiumEntity) {
    //const gmlid = cesiumEntity.name;// assuming gmlid corresponds to the entity name

    console.log("Button clicked with gmlid:", gmlid);

    // Define the path to the CSV file based on gmlid
    const csvFilePath = `tables_data_households/${gmlid}.csv`;

    // Fetch the CSV file
    fetch(csvFilePath)
        .then(response => {
            if (!response.ok) throw new Error('Could not find CSV file.');
            return response.text();
        })
        .then(csvData => {
            // Parse CSV data and generate HTML table
            const additionalTableHtml = generateHtmlTableFromCsv(csvData);

            // Append the additional table to the existing description
            cesiumEntity.description += additionalTableHtml;
        })
        .catch(error => {
            console.error('Error loading CSV file:', error);
        });
}

// Function to parse CSV and convert it to an HTML table
function generateHtmlTableFromCsv(csvData) {
    // Split the CSV data into rows
    const rows = csvData.trim().split('\n').map(row => row.split(','));

    // Start the HTML table
    let html = `
        <table class="cesium-infoBox-defaultTable" style="font-size:10.5pt; margin-top:10px;">
            <thead>
                <tr>
                    <th>Household ID</th>
                    <th>Number of Inhabitants</th>
                    <th>Area (sq m)</th>
                    <th>Yearly Energy Consumption (kWh)</th>
                </tr>
            </thead>
            <tbody>
    `;

    // Generate table rows from CSV data
    for (let i = 1; i < rows.length; i++) { // Skip header row
        const [id, residents, area, yearly_enery_consumption] = rows[i];
        html += `
            <tr>
                <td>${id}</td>
                <td>${residents}</td>
                <td>${area}</td>
                <td>${yearly_enery_consumption}</td>
            </tr>
        `;
    }

    // Close the table
    html += '</tbody></table>';
    return html;
}


function fetchDataFromGoogleSpreadsheet(gmlid, thematicDataUrl) {
    var kvp = {};
    var deferred = Cesium.when.defer();

    var spreadsheetKey = thematicDataUrl.split("/")[5];
    var metaLink = 'https://spreadsheets.google.com/feeds/worksheets/' + spreadsheetKey + '/public/full?alt=json-in-script';

    Cesium.jsonp(metaLink).then(function (meta) {
        console.log(meta);
        var feedCellUrl = meta.feed.entry[0].link[1].href;
        feedCellUrl += '?alt=json-in-script&min-row=1&max-row=1';
        Cesium.jsonp(feedCellUrl).then(function (cellData) {
            var feedListUrl = meta.feed.entry[0].link[0].href;
            feedListUrl += '?alt=json-in-script&sq=gmlid%3D';
            feedListUrl += gmlid;
            Cesium.jsonp(feedListUrl).then(function (listData) {
                for (var i = 1; i < cellData.feed.entry.length; i++) {
                    var key = cellData.feed.entry[i].content.$t;
                    var value = listData.feed.entry[0]['gsx$' + key.toLowerCase().replace(/_/g, '')].$t;
                    kvp[key] = value;
                }
                deferred.resolve(kvp);
            }).otherwise(function (error) {
                deferred.reject(error);
            });
        }).otherwise(function (error) {
            deferred.reject(error);
        });
    }).otherwise(function (error) {
        deferred.reject(error);
    });

    return deferred.promise;
}

function fetchDataFromGoogleFusionTable(gmlid, thematicDataUrl) {
    var kvp = {};
    var deferred = Cesium.when.defer();

    var tableID = urlController.getUrlParaValue('docid', thematicDataUrl, CitydbUtil);
    var sql = "SELECT * FROM " + tableID + " WHERE GMLID = '" + gmlid + "'";
    var apiKey = "AIzaSyAm9yWCV7JPCTHCJut8whOjARd7pwROFDQ";
    var queryLink = "https://www.googleapis.com/fusiontables/v2/query";
    new Cesium.Resource({url: queryLink, queryParameters: {sql: sql, key: apiKey}}).fetch({responseType: 'json'}).then(function (data) {
        console.log(data);
        var columns = data.columns;
        var rows = data.rows;
        for (var i = 0; i < columns.length; i++) {
            var key = columns[i];
            var value = rows[0][i];
            kvp[key] = value;
        }
        console.log(kvp);
        deferred.resolve(kvp);
    }).otherwise(function (error) {
        deferred.reject(error);
    });
    return deferred.promise;
}

function showInExternalMaps() {
    var mapOptionList = document.getElementById('citydb_showinexternalmaps');
    var selectedIndex = mapOptionList.selectedIndex;
    mapOptionList.selectedIndex = 0;

    var selectedEntity = cesiumViewer.selectedEntity;
    if (!Cesium.defined(selectedEntity))
        return;

    var selectedEntityPosition = selectedEntity.position;
    var wgs84OCoordinate;

    if (!Cesium.defined(selectedEntityPosition)) {
        var boundingSphereScratch = new Cesium.BoundingSphere();
        cesiumViewer._dataSourceDisplay.getBoundingSphere(selectedEntity, false, boundingSphereScratch);
        wgs84OCoordinate = Cesium.Ellipsoid.WGS84.cartesianToCartographic(boundingSphereScratch.center);
    } else {
        wgs84OCoordinate = Cesium.Ellipsoid.WGS84.cartesianToCartographic(selectedEntityPosition._value);

    }
    var lat = Cesium.Math.toDegrees(wgs84OCoordinate.latitude);
    var lon = Cesium.Math.toDegrees(wgs84OCoordinate.longitude);
    var mapLink = "";

    switch (selectedIndex) {
        case 1:
            //mapLink = 'https://www.mapchannels.com/dualmaps7/map.htm?lat=' + lat + '&lng=' + lon + '&z=18&slat=' + lat + '&slng=' + lon + '&sh=-150.75&sp=-0.897&sz=1&gm=0&bm=2&panel=s&mi=1&md=0';
            //mapLink = 'https://www.google.com/maps/embed/v1/streetview?location=' + lat + ',' + lon + '&key=' + 'AIzaSyBRXHXasDb8PGOXCfQP7r7xQiAQXo3eIQs';
            //mapLink = 'https://maps.googleapis.com/maps/api/streetview?size=400x400&location=' + lat + ',' + lon + '&fov=90&heading=235&pitch=10' + '&key=AIzaSyBRXHXasDb8PGOXCfQP7r7xQiAQXo3eIQs';
            mapLink = 'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=' + lat + ',' + lon;
            break;
        case 2:
            mapLink = 'https://www.openstreetmap.org/index.html?lat=' + lat + '&lon=' + lon + '&zoom=20';
            break;
        case 3:
            mapLink = 'https://www.bing.com/maps/default.aspx?v=2&cp=' + lat + '~' + lon + '&lvl=19&style=o';
            break;
        case 4:
            mapLink = 'https://www.mapchannels.com/dualmaps7/map.htm?x=' + lon + '&y=' + lat + '&z=16&gm=0&ve=4&gc=0&bz=0&bd=0&mw=1&sv=1&sva=1&svb=0&svp=0&svz=0&svm=2&svf=0&sve=1';
            break;
        default:
        //	do nothing...
    }

    window.open(mapLink);
}

function layerDataTypeDropdownOnchange() {
    var layerDataTypeDropdown = document.getElementById("layerDataTypeDropdown");
    if (layerDataTypeDropdown.options[layerDataTypeDropdown.selectedIndex].value !== "COLLADA/KML/glTF") {
        document.getElementById("gltfVersionDropdownRow").style.display = "none";
        document.getElementById("layerProxyAndClampToGround").style.display = "none";
    } else {
        document.getElementById("gltfVersionDropdownRow").style.display = "";
        document.getElementById("layerProxyAndClampToGround").style.display = "";
    }
    addLayerViewModel["layerDataType"] = layerDataTypeDropdown.options[layerDataTypeDropdown.selectedIndex].value;
}

function thematicDataSourceAndTableTypeDropdownOnchange() {
    if (webMap && webMap._activeLayer) {
        var thematicDataSourceDropdown = document.getElementById("thematicDataSourceDropdown");
        var selectedThematicDataSource = thematicDataSourceDropdown.options[thematicDataSourceDropdown.selectedIndex].value;

        var tableTypeDropdown = document.getElementById("tableTypeDropdown");
        var selectedTableType = tableTypeDropdown.options[tableTypeDropdown.selectedIndex].value;

        addLayerViewModel["thematicDataSource"] = selectedThematicDataSource;
        addLayerViewModel["tableType"] = selectedTableType;

        // if (selectedThematicDataSource == "GoogleSheets") {
        //     document.getElementById("rowGoogleSheetsApiKey").style.display = "table-row";
        //     document.getElementById("rowGoogleSheetsRanges").style.display = "table-row";
        //     document.getElementById("rowGoogleSheetsClientId").style.display = "table-row";
        // } else {
        //     document.getElementById("rowGoogleSheetsApiKey").style.display = "none";
        //     document.getElementById("rowGoogleSheetsRanges").style.display = "none";
        //     document.getElementById("rowGoogleSheetsClientId").style.display = "none";
        // }

        var options = getDataSourceControllerOptions(webMap._activeLayer);
        // Mashup Data Source Service
        webMap._activeLayer.dataSourceController = new DataSourceController(selectedThematicDataSource, signInController, options);
    }
}

function getDataSourceControllerOptions(layer) {
    var dataSourceUri = layer.thematicDataUrl === "" ? layer.url : layer.thematicDataUrl;
    var options = {
        // name: "",
        // type: "",
        // provider: "",
        uri: dataSourceUri,
        tableType: layer.tableType,
        thirdPartyHandler: {
            type: "Cesium",
            handler: layer ? layer._citydbKmlDataSource : undefined
        },
        // ranges: addLayerViewModel.googleSheetsRanges,
        // apiKey: addLayerViewModel.googleSheetsApiKey,
        // clientId: addLayerViewModel.googleSheetsClientId
        clientId: googleClientId ? googleClientId : "",
        proxyPrefix: layer.layerProxy ? CitydbUtil.getProxyPrefix(dataSourceUri) : ""
    };
    return options;
}

// Sign in utilities
var googleClientId = urlController.getUrlParaValue('googleClientId', window.location.href, CitydbUtil);
if (googleClientId) {
    var signInController = new SigninController(googleClientId);
}

// Mobile layouts and functionalities
var mobileController = new MobileController();
