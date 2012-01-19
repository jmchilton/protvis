dependencies = {
	layers: [{
		name: "dojo.mini.js",
		dependencies: [
			"dojo.fx",
			"dijit.Dialog",
			"dojo._base.connect",
			"dijit.DynamicTooltip",
			"dojox.html.ellipsis",
			"dojox.gfx",
			"dojox.charting.widget.Chart2D",
			"dojox.charting.widget.Legend",
			"dojox.charting.MouseInteractionSupport"
		]}
	],
	prefixes: [
		[ "dijit", "../dijit" ],
		[ "dojox", "../dojox" ]
	]
}
