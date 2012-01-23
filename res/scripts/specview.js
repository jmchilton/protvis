/*dojo.require("dojox.charting.widget.Chart2D");
dojo.require("dojox.charting.widget.Legend");*/
//dojo.require("dojox.charting.MouseInteractionSupport");

strokes = [ "red", "green", "blue" ];

function RenderGraph(ChartElem, LegendElem, data, info) {
	var SpecChart = new dojox.charting.Chart2D(ChartElem);
	SpecChart.addPlot("default", {
		type: "Default",
		markers: true,
		tension: 0,
		lines: true,
		areas: false,
		labelOffset: -30,
		animate:true
	});
	SpecChart.addAxis("x", { min:info["xmin"], max:info["xmax"] });
	SpecChart.addAxis("y", { max:info["ymax"], vertical:true });
	var i = 0
	for (var key in data) {
		var d = data[key];
		var vals = new Array();
		for (var v in d) {
			vals.push({x:d[v][0], y:d[v][1]});
		}
		SpecChart.addSeries(key, vals, {stroke: {color:strokes[i], width:2}});
		++i;
	}
	//new dojox.charting.action2d.Magnify(chart, "default");
	if (data.length > 1) {
		new dojox.charting.widget.Legend({chart: SpecChart}, LegendElem);
	}
	new dojox.charting.action2d.Tooltip(SpecChart, "default");
	//new dojox.charting.MouseIntegrationSupport(SpecChart, {enableZoom:true, enablePan:true});
	SpecChart.render();
	return SpecChart;
}

function RenderSpectrumGraph(title, container, data) {
	var xmin = 10000000, xmax = -1, ymax = -1;
	for (var i in data) {
		var d = data[i];
		xmin = Math.min(xmin, d[0]);
		xmax = Math.max(xmax, d[0]);
		ymax = Math.max(ymax, d[1]);
	}
	RenderGraph(container, null, {title:data}, {xmin:xmin, xmax:xmax, ymax:ymax});
}
