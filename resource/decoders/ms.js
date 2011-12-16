dojo.require("dojox.charting.widget.Chart2D");
dojo.require("dojox.charting.widget.Legend");

function BuildChart(ChartElem, LegendElem, data) {
	var SpecChart = new dojox.charting.Chart2D(ChartElem);
	SpecChart.addPlot("default", {
		type: "StackedAreas", //type of chart
		markers: false, //show markers at number points?
		tension: "S", //curve the lines on the plot?
		lines: true, //show lines?
		areas: false, //fill in areas?
		labelOffset: -30, //offset position for label
		shadows: { dx:2, dy:2, dw:2 } //add shadows to lines
	});
	SpecChart.addAxis("x");
	SpecChart.addAxis("y", { vertical:true });
	strokes = [ "red", "green", "blue" ];
	fills = [ "pink", "lightgreen", "lightblue" ];
	var i = 0
	for (var key in data) {
		SpecChart.addSeries(key, data[key], { stroke: strokes[i], fill: fills[i] });
		++i;
	}
	//new dojox.charting.action2d.Magnify(chart, "default");
	if (data.length > 1) {
		new dojox.charting.widget.Legend({chart: SpecChart}, LegendElem);
	}
	new dojox.charting.action2d.Tooltip(SpecChart, "default");
	SpecChart.render();
	return SpecChart;
}
