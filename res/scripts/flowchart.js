dojo.require("dojox.gfx");
var Surface, Group;
var Matrix = dojox.gfx.matrix, InitialMatrix = m.translate(0, 0);
var CanvasW, CanvasH;
var BoxWidth = 70;
var BoxHeight = 35;

function UpdateMatrix(){
	group.setTransform([m.scaleAt(scaling, CanvasW/2, CanvasH/2), InitialMatrix]);
}

function FlowChartCreate(files) {
	function MakeBox(file) {
		var color = file["missing"] ? "gray" : "black";
		var mat = m.translate(file["x"], file["y"]);
		var g = Surface.createGroup().setTransform(mat);
		var box = surface.createRect({x: -BoxWidth/2, y: -BoxHeight/2, width: BoxWidth/2, height: BoxHeight/2}).setFill("#eee").setStroke({color: color, width: 2});
		return {box: box, g: g, mat: mat, connections: []};
	}

	function MakeConnection(file1, file2) {
		var color = (file1["missing"] || file2["missing"]) ? "gray" : "black";
		surface.createLine({x1: file1["x"] + BoxWidth/2, y1: file1["y"], x2: file2["x"] - BoxWidth/2, y2: file2["y"]}).setStroke({color: color, width: 2}),
	}
	
	
	
	Surface = dojox.gfx.createSurface(dojo.byId("navigation_graph"), 700, 200);
	var boxes = new Array();
	for (f in files) {
		boxes.push(MakeBox(files[f]));
	}
	for (f in files) {
		for (d in files.depends) {
			c = MakeConnection(f, files[f].depends[d]);
			//boxes[f]["connections"].push({
		}
	}
}

function FlowChartSelect(index) {
}
