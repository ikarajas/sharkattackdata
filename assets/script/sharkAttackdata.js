(function($) {
    $.concat = function (a, b) {
	$.each(b, function(index, value) {
	    a.push(value);
	});
	return a;
    };

    Utils = {
	range: function(start, end) {
	    retval = [];
	    for (var i = start; i <= end; i++) {
		retval.push(i);
	    }
	    return retval;
	},

	getAttackCountsForYear: function(year, attacks) {
	    yearSet = $.grep(attacks, function(a, i) { return a.date !== null && a.date.getFullYear() === year; });
	    return {
		total: yearSet.length,
		fatal: $.grep(yearSet, function(a, i) { return a.fatal; }).length,
		unprovoked: $.grep(yearSet, function(a, i) { return a.unprovoked; }).length,
		unprovokedAndNonFatal: $.grep(yearSet, function(a, i) { return !a.fatal && a.unprovoked; }).length,
		fatalAndUnprovoked: $.grep(yearSet, function(a, i) { return a.fatal && a.unprovoked; }).length
	    };
	},

	calculateMovingAverageForYear: function(year, period, summaryData, getDataPoint) {
	    // summaryData format:
	    // {
	    // 	year: { prop1: point1, prop2: point2, propN: pointN, ... },
	    // 	yearN: { prop1: point1, prop2: point2, propN: pointN, ... },
	    // 	...
	    // }
	    
	    var startYear = year - period;
	    var endYear = year;
	    var sum = 0;
	    for (var i = startYear; i < endYear; i++) {
		sum += getDataPoint(summaryData[i]);
	    }
	    var retval = sum / period;
	    return retval;
	},

	initResizeHandler: function(eventNamespace, onResize) {
	    var resizeHandler = null;
	    $(window).on("resize." + eventNamespace, function(e){
		$(window).resize(function() {
		    clearTimeout(resizeHandler);
		    resizeHandler = setTimeout(function() {
			onResize();
		    }, 250);
		});
	    });
	}
    };

    Constants = {
	colorBase: "#2B3E50",
	colorBaseContrast: "#4E5D6C",
	colorBaseLightest: "#A6AEB6",
	colorMidRangeIncidents: "#336600",
	colorHighlight: "#DF691A",
	colorNeutral: "#5C8270",
	colorNeutralContrast: "#C2EDD9",
	colorFatal: "#B50000",
	colorFatalContrast: "#ED0000"
    };

    $.widget("SharkAttackData.PlaceWidget", {
	_create: function() {
	    var widget = this;
	    widget.data = this.element.data();
	    widget.chartBaseTextStyle = {
		color: "white",
		fontSize: "12",
		fontName: "Lato, 'Helvetica Neue', Helvetica, Arial, sans-serif"
	    };
	    Constants.colorNeutral = "#5C8270";
	    Constants.colorNeutralContrast = "#C2EDD9";
	    Constants.colorFatal = "#B50000";
	    Constants.colorFatalContrast = "#ED0000";
	    widget.pieChartWidth = 333;
	    widget.pieChartHeight = 150;
	    widget.loadingMessage = "Loading...";

	    function AttackPlaceSummaryViewModel() {
		var self = this;

		self.filterStatuses_fatal = {
		    fatal_only: "Fatal only",
		    non_fatal_only: "Non-fatal only",
		    fatal_and_non_fatal: "Fatal and non-fatal"
		}

		self.filterStatuses_provoked = {
		    provoked_only: "Provoked only",
		    unprovoked_only: "Unprovoked only",
		    provoked_and_unprovoked: "Provoked and unprovoked"
		}

		self.attacks = ko.observableArray();
		self.attacksLoaded = ko.observable(false);
		
		self.attackStatsByYear = ko.computed(function() {
		    return $.map(Utils.range(1900, (new Date()).getFullYear()), function(value, index) {
			return [[ value, Utils.getAttackCountsForYear(value, self.attacks()) ]];
		    });
		});

		self.attackStatsByYearDict = ko.computed(function() {
		    var retval = {};
		    $.each(self.attackStatsByYear(), function(index, value) {
			retval[value[0]] = value[1];
		    });
		    return retval;
		});

		self.attackStatsMovingAverageByYearDict = ko.computed(function() {
		    if (self.attacks().length == 0) {
			return [];
		    }

		    var period = 10;
		    var startDate = 1900 + period;
		    var endDate = (new Date()).getFullYear();
		    var asArray = $.map(Utils.range(startDate, endDate), function(value, index) {
			return [[
			    value,
			    {
				unprovoked: Utils.calculateMovingAverageForYear(value, period, self.attackStatsByYearDict(),
										function(yearSummary) { return yearSummary.unprovoked; }),
				fatal: Utils.calculateMovingAverageForYear(value, period, self.attackStatsByYearDict(),
									   function(yearSummary) { return yearSummary.fatal; })
			    }
			]];
		    });
		    var retval = {};
		    $.each(asArray, function(index, value) {
			retval[value[0]] = value[1];
		    });
		    return retval;
		});

		self.attacksFiltered = ko.computed(function() {
		    return $.grep(self.attacks(), function(a, i) {
			fatalCheckPass = true;

			var fatalState = self.filterDropdownFatalState();
			if (fatalState === self.filterStatuses_fatal.fatal_only && !a.fatal ||
			    fatalState === self.filterStatuses_fatal.non_fatal_only && a.fatal) {
			    fatalCheckPass = false;
			}

			provokedCheckPass = true;

			var provokedState = self.filterDropdownProvokedState();
			if (provokedState === self.filterStatuses_provoked.provoked_only && !a.provoked ||
			    provokedState === self.filterStatuses_provoked.unprovoked_only && a.provoked) {
			    provokedCheckPass = false;
			}

			return fatalCheckPass && provokedCheckPass;
		    })
		});

		self.noAttacksMatchFilterSettings = ko.computed(function() {
		    return self.attacksLoaded() && self.attacksFiltered().length === 0;
		});

		self.filterDropdownFatalState = ko.observable(self.filterStatuses_fatal.fatal_and_non_fatal);
		self.filterDropdownProvokedState = ko.observable(self.filterStatuses_provoked.provoked_and_unprovoked);
		
		self.isFiltered = ko.computed(function() {
		    return self.filterDropdownFatalState() !== self.filterStatuses_fatal.fatal_and_non_fatal ||
			self.filterDropdownProvokedState() !== self.filterStatuses_provoked.provoked_and_unprovoked;
		});

		self.filterStateSummary = ko.computed(function() {
		    if (self.isFiltered()) {
			return "Filtered (" + self.attacksFiltered().length + " shown, " + (self.attacks().length - self.attacksFiltered().length) + " hidden).";
		    }
		    return "";
		});

		self.summaryStats = {
		    totalCount: ko.computed(function() {
			return self.attacksLoaded() ? self.attacks().length : widget.loadingMessage;
		    }),
		    fatalCount: ko.computed(function() {
			return self.attacksLoaded() ? $.grep(self.attacks(), function(a, i) { return a.fatal; }).length : widget.loadingMessage;
		    }),
		    unprovokedCount: ko.computed(function() {
			return self.attacksLoaded() ? $.grep(self.attacks(), function(a, i) { return a.unprovoked; }).length : widget.loadingMessage;
		    }),
		    fatalAndUnprovokedCount: ko.computed(function() {
			return self.attacksLoaded() ? $.grep(self.attacks(), function(a, i) { return a.fatal && a.unprovoked; }).length : widget.loadingMessage;
		    })
		}
	    }

	    widget.vm = new AttackPlaceSummaryViewModel();

	    ko.applyBindings(widget.vm, widget.element[0]);

	    widget._setupEventHandlers();
	    widget._getAttacks();
	},

	_setupEventHandlers: function() {
	    var widget = this;

	    $(".btn-group.filter-on-fatal .dropdown-menu a").on("click.placeWidget", function(event) {
		event.preventDefault();
		var newStateKey = event.target.id.replace(/-/g, "_");
		widget.vm.filterDropdownFatalState(widget.vm.filterStatuses_fatal[newStateKey]);
	    });

	    $(".btn-group.filter-on-provoked .dropdown-menu a").on("click.placeWidget", function(event) {
		event.preventDefault();
		var newStateKey = event.target.id.replace(/-/g, "_");
		widget.vm.filterDropdownProvokedState(widget.vm.filterStatuses_provoked[newStateKey]);
	    });

	    Utils.initResizeHandler("placeWidget", function() {
		widget._drawCharts();
	    });
	},

	_onAttacksLoaded: function() {
	    var widget = this;
	    widget.vm.attacksLoaded(true);
	    if (widget.element.find(".charts").length > 0) {
		google.load("visualization", "1.0", { packages: ["corechart"], callback: function() { widget._onChartApiLoaded(); } });
	    }
	},
	
	_onChartApiLoaded: function() {
	    var widget = this;
	    widget._drawCharts();
	},

	
	_drawCharts: function() {
	    var widget = this;
	    widget._drawPieChart(
		"Fatal",
		"#fatal",
		[{ type: "string", name: "Type" }, { type: "number", name: "Value" }],
		[
		    ['Fatal', widget.vm.summaryStats.fatalCount()],
		    ['Non-Fatal', widget.vm.summaryStats.totalCount() - widget.vm.summaryStats.fatalCount()]
		]
	    );

	    widget._drawPieChart(
		"Unprovoked",
		"#unprovoked",
		[{ type: "string", name: "Type" }, { type: "number", name: "Value" }],
		[
		    ['Unprovoked', widget.vm.summaryStats.unprovokedCount()],
		    ['Provoked', widget.vm.summaryStats.totalCount() - widget.vm.summaryStats.unprovokedCount()]
		]
	    );

	    widget._drawPieChart(
		"Fatal and Unprovoked",
		"#fatal-and-unprovoked",
		[{ type: "string", name: "Type" }, { type: "number", name: "Value" }],
		[
		    ['Fatal and Unprovoked', widget.vm.summaryStats.fatalAndUnprovokedCount()],
		    ['Other', widget.vm.summaryStats.totalCount() - widget.vm.summaryStats.fatalAndUnprovokedCount()]
		]
	    );
	    
	    widget._drawTimelineChart();
	},
	
	_drawTimelineChart: function() {
	    var widget = this;
	    var tableDataRaw = $.map(widget.vm.attackStatsByYear(), function(value, index) {
		var year = value[0];
		var movingAverages = widget.vm.attackStatsMovingAverageByYearDict()[year];
		var fatalMovingAverage = movingAverages === undefined ? 0 : movingAverages.fatal;
		var unprovokedMovingAverage = movingAverages === undefined ? 0 : movingAverages.unprovoked;
		retval =  [[
		    year.toString(),
		    value[1].fatalAndUnprovoked, value[1].unprovokedAndNonFatal,
		    fatalMovingAverage, unprovokedMovingAverage
		]];
		return retval;
	    });
	    tableDataRaw.unshift(["Year", "Fatal", "Non-fatal", "Fatal (10 year moving average)", "All unprovoked (10 year moving average)"])

            var data = google.visualization.arrayToDataTable(tableDataRaw);
	    
	    // Note: use vAxis.gridLines.count and vAxis.format...
            var options = { titleTextStyle: widget.chartBaseTextStyle,
			    legend: { textStyle: widget.chartBaseTextStyle },
			    vAxis: { textStyle: widget.chartBaseTextStyle, baselineColor: "#fff", gridlines: { color: "#777"} },
			    hAxis: { textStyle: widget.chartBaseTextStyle },
			    fontName: widget.chartBaseTextStyle.fontName,
			    backgroundColor: { fill: "none" },
			    seriesType: "bars",
			    isStacked: true,
			    series: { 2: { type: "line" }, 3: { type: "line" } },
			    colors: [ Constants.colorFatal, Constants.colorNeutral, Constants.colorFatalContrast, Constants.colorNeutralContrast ]
			  };
	    
            var chart = new google.visualization.ComboChart($("#timeline")[0]);
            chart.draw(data, options);
	},

	_drawPieChart: function(title, elemSelector, columns, rows) {
	    var widget = this;

	    var $charts = widget.element.find(".charts");
	    var $chartElem = $charts.find(elemSelector);

	    var dt = new google.visualization.DataTable();
	    
	    $.each(columns, function(index, value) {
		dt.addColumn(value.type, value.name);
	    });
	    dt.addRows(rows);
	    
	    var options = { title: title,
			    titleTextStyle: widget.chartBaseTextStyle,
			    chartArea: { left: 0 },
			    legend: { textStyle: widget.chartBaseTextStyle },
			    tooltip: {textStyle: {
				color: "black",
				fontSize: widget.chartBaseTextStyle.fontSize,
				fontName: widget.chartBaseTextStyle.fontName
			    }},
			    backgroundColor: { fill: "none" },
			    slices: {
				0: { color: Constants.colorFatal },
				1: { color: Constants.colorNeutral },
			    }
			  };
	    
	    var chart = new google.visualization.PieChart($chartElem[0]);
	    chart.draw(dt, options);
	    $chartElem.removeClass("please-wait");
	},

	_getAttacks: function() {
	    var widget = this;
	    $.ajax({
		url: "/api/attacks",
		type: "GET",
		data: { country: widget.data.country, area: widget.data.area },
		success: function(result) {
		    widget.vm.attacks.push.apply(widget.vm.attacks, $.map(result, function(value, index) {
			return $.extend(value, {
			    date: (value.date === null) ? null : new Date(value.date),
			    provoked: !value.unprovoked,
			    unprovokedUserFriendly: value.unprovoked ? "Unprovoked" : "Provoked",
			    fatalUserFriendly: value.fatal ? "Fatal" : "Non-fatal",
			    detailsUrl: (function(v) {
				var retval = "";
				if (window.location.pathname.indexOf("/gsaf") === 0) {
				    retval += "/gsaf";
				}
				retval += "/attack/" + widget.data.country + "/" + v.areaNormalised + "/" + v.gsafCaseNumber;
				return retval;
			    })(value)
			});
		    }));
		    widget.element.find(".please-wait").removeClass("please-wait");
		    widget._onAttacksLoaded();
		}
	    });
	}
    });

    $.widget("SharkAttackData.PlacesListWidget", {
	_create: function() {
	    $(".order-countries .by-name").on("click.placesListWidget", function(e) {
		$('div.country-list-item').sortElements(function(a, b) {
		    return $(a).data().countryName > $(b).data().countryName ? 1 : -1;
		});
	    });
	    
	    $(".order-countries .by-total").on("click.placesListWidget", function(e) {
		$('div.country-list-item').sortElements(function(a, b) {
		    return $(a).data().countTotal > $(b).data().countTotal ? -1 : 1;
		});
	    });
	}
    });


    $.widget("SharkAttackData.WorldMapWidget", {
	_create: function() {
	    var widget = this;

	    function WorldMapViewModel() {
		var self = this;
		self.countries = ko.observableArray();

		self.chartingApiLoaded = ko.observable(false);
		self.countriesLoaded = ko.observable(false);
		self.readyToChart = ko.observable(false);

		var iCanHasCharts = function() {
		    if (self.chartingApiLoaded() && self.countriesLoaded()) {
			self.readyToChart(true);
		    }
		};

		self.chartingApiLoaded.subscribe(iCanHasCharts);
		self.countriesLoaded.subscribe(iCanHasCharts);
	    }

	    widget.vm = new WorldMapViewModel();
	    widget.vm.readyToChart.subscribe(function() { widget._drawMap(); });

	    // Reserve enough vertical space for the chart when it loads.
	    widget.element.height(widget.element.width() * (605/970));

	    widget.chartContainer = $("<div id='chart-container'></div>");
	    widget.element.append(widget.chartContainer);
	    widget.element.addClass("please-wait");
	    google.load("visualization", "1.0", { packages: ["geochart"], callback: function() { widget.vm.chartingApiLoaded(true); } });

	    widget._getCountries();

	    Utils.initResizeHandler("worldMapWidget", function() {
		widget._drawMap();
	    });
	},

	_getCountries: function() {
	    var widget = this;
	    $.ajax({
		url: "/api/countries",
		type: "GET",
		success: function(result) {
		    widget.vm.countries.push.apply(widget.vm.countries, result);
		    widget._onCountriesLoaded();
		}
	    });
	},

	_onCountriesLoaded: function() {
	    var widget = this;
	    widget.element.removeClass("please-wait");
	    widget.vm.countriesLoaded(true);
	},

	_drawMap: function() {
	    var widget = this;
	    var data = google.visualization.arrayToDataTable(
		$.concat(
		    [['Country', 'Unprovoked Incidents']],
		    $.map(widget.vm.countries(), function(value, index) {
			return [[ value.name, value.counts.unprovoked ]];
		    }))
	    );
	    
            var options = {
		backgroundColor: { fill: "none" },
		colorAxis: {
		    values: [0, 100, 2000],
		    colors: [ Constants.colorBaseLightest, Constants.colorMidRangeIncidents, Constants.colorHighlight ]
		}
	    };
	    
	    widget.element.css("height", "auto");
	    widget.chartContainer.empty();
            var chart = new google.visualization.GeoChart(widget.chartContainer[0]);
            chart.draw(data, options);
	}
    });

    $.fn.socialMediaButtons = function() {
	var element = this;

	var setPosition = function() {
	    var $elem = $(element);
	    var elemWidth = $elem.outerWidth();
	    var elemOffset = $elem.offset();

	    var $container = $("header");
	    var containerWidth = $container.outerWidth();

	    $elem.offset({ top: 10, left: containerWidth - elemWidth });
	};

	$(window).on("resize.socialMediaButtons", function(event) {
	    setPosition();
	});
	setPosition();
	return this;
    };

    $(document).ready(function() {
	$(".social-media-buttons").socialMediaButtons();

	$(".place-widget").PlaceWidget();
	$(".places-list-widget").PlacesListWidget();
	$(".world-map-widget").WorldMapWidget();
    });
})(jQuery);


/**
 * jQuery.fn.sortElements
 * --------------
 * @param Function comparator:
 *   Exactly the same behaviour as [1,2,3].sort(comparator)
 *   
 * @param Function getSortable
 *   A function that should return the element that is
 *   to be sorted. The comparator will run on the
 *   current collection, but you may want the actual
 *   resulting sort to occur on a parent or another
 *   associated element.
 *   
 *   E.g. $('td').sortElements(comparator, function(){
 *      return this.parentNode; 
 *   })
 *   
 *   The <td>'s parent (<tr>) will be sorted instead
 *   of the <td> itself.
 */
jQuery.fn.sortElements = (function(){
    
    var sort = [].sort;
    
    return function(comparator, getSortable) {
	
        getSortable = getSortable || function(){return this;};
	
        var placements = this.map(function(){
	    
            var sortElement = getSortable.call(this),
            parentNode = sortElement.parentNode,
	    
            // Since the element itself will change position, we have
            // to have some way of storing its original position in
            // the DOM. The easiest way is to have a 'flag' node:
            nextSibling = parentNode.insertBefore(
                document.createTextNode(''),
                sortElement.nextSibling
            );
	    
            return function() {
		
                if (parentNode === this) {
                    throw new Error(
                        "You can't sort elements if any one is a descendant of another."
                    );
                }
		
                // Insert before flag:
                parentNode.insertBefore(this, nextSibling);
                // Remove flag:
                parentNode.removeChild(nextSibling);
		
            };
	    
        });
	
        return sort.call(this, comparator).each(function(i){
            placements[i].call(getSortable.call(this));
        });
	
    };
    
})();
