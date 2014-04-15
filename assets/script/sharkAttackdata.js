(function($) {
    $.widget("SharkAttackData.AttackPlaceSummary", {
	_create: function() {
	    var widget = this;
	    widget.data = this.element.data();

	    var drawCharts = function() {
		widget._drawPieChart(
		    "Fatal",
		    [{ type: "string", name: "Type" }, { type: "number", name: "Value" }],
		    [
			['Fatal', widget.data.fatalCount],
			['Non-Fatal', widget.data.totalCount - widget.data.fatalCount]
		    ]
		);

		widget._drawPieChart(
		    "Unprovoked",
		    [{ type: "string", name: "Type" }, { type: "number", name: "Value" }],
		    [
			['Unprovoked', widget.data.unprovokedCount],
			['Provoked', widget.data.totalCount - widget.data.unprovokedCount]
		    ]
		);

		widget._drawPieChart(
		    "Fatal and Unprovoked",
		    [{ type: "string", name: "Type" }, { type: "number", name: "Value" }],
		    [
			['Fatal and Unprovoked', widget.data.fatalAndUnprovokedCount],
			['Other', widget.data.totalCount - widget.data.fatalAndUnprovokedCount]
		    ]
		);
	    };
	    
	    google.load("visualization", "1.0", { packages: ["corechart"], callback: drawCharts });
	},

	_drawPieChart: function(title, columns, rows) {
	    var widget = this;
	    var dt = new google.visualization.DataTable();
	    
	    $.each(columns, function(index, value) {
		dt.addColumn(value.type, value.name);
	    });
	    dt.addRows(rows);
	    
	    var textStyle = {color: "white", fontSize: "12", fontName: "Lato, 'Helvetica Neue', Helvetica, Arial, sans-serif"};
	    var options = {title: title,
			   width: 370,
			   height: 200,
			   titleTextStyle: textStyle,
			   legend: {textStyle: textStyle},
			   tooltip: {textStyle: { color: "black", fontSize: textStyle.fontSize, fontName: textStyle.fontName }},
			   backgroundColor: { fill: "none" }
			  };
	    
	    var $charts = widget.element.find(".charts");
	    var $newChartElem = $("<div></div>");
	    foo = $charts.append($newChartElem);
	    var chart = new google.visualization.PieChart($newChartElem[0]);
	    chart.draw(dt, options);
	}
    });

    $.widget("SharkAttackData.PlaceWidget", {
	_create: function() {
	    var widget = this;
	    widget.data = this.element.data();
	    widget.vm = {
		attacks: ko.observableArray()
	    };

	    ko.applyBindings(widget.vm, widget.element[0]);
	    widget._getAttacks();
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
			    unprovokedUserFriendly: value.unprovoked ? "Unprovoked" : "Provoked",
			    fatalUserFriendly: value.fatal ? "Fatal" : "Non-fatal"
			});
		    }));
		    widget.element.find(".please-wait").removeClass("please-wait");
		}
	    });
	}
    });

    $(document).ready(function() {
	$(".attack-place-summary").AttackPlaceSummary();
	$(".place-widget").PlaceWidget();
    });
})(jQuery);
