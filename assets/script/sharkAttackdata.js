(function($) {
    $.widget("SharkAttackData.PlaceWidget", {
	_create: function() {
	    var widget = this;
	    widget.data = this.element.data();
	    widget.pieChartWidth = 370;
	    widget.pieChartHeight = 200;
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
	},

	_drawPieChart: function(title, elemSelector, columns, rows) {
	    var widget = this;
	    var dt = new google.visualization.DataTable();
	    
	    $.each(columns, function(index, value) {
		dt.addColumn(value.type, value.name);
	    });
	    dt.addRows(rows);
	    
	    var textStyle = {color: "white", fontSize: "12", fontName: "Lato, 'Helvetica Neue', Helvetica, Arial, sans-serif"};
	    var options = {title: title,
			   width: widget.pieChartWidth,
			   height: widget.pieChartHeight,
			   titleTextStyle: textStyle,
			   legend: {textStyle: textStyle},
			   tooltip: {textStyle: { color: "black", fontSize: textStyle.fontSize, fontName: textStyle.fontName }},
			   backgroundColor: { fill: "none" },
			   slices: {
			       0: {color: "red"},
			       1: {color: "gray"},
			   }
			  };
	    
	    var $charts = widget.element.find(".charts");
	    var $chartElem = $charts.find(elemSelector);
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

    $(document).ready(function() {
	$(".place-widget").PlaceWidget();
    });
})(jQuery);
