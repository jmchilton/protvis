dojo.require("dojox.gfx");
var Surface, Group;
var Matrix = dojox.gfx.matrix, InitialMatrix = Matrix.translate(0, 0);
var CanvasW, CanvasH;
var BoxWidth = 140;
var BoxHeight = 45;
var BoxHSpacing = 50, BoxVSpacing = 30, BoxVSize = BoxVSpacing + BoxHeight;
var Colors = [ "#ff5900", "#0d56ff", "#4dde00", "#a600a6", "#ff9700", "#2618b1", "#1049a9", "#009999", "#e9003a" ];
var Nodes = new Array();
var Selected = -1;

function UpdateMatrix(){
	group.setTransform([m.scaleAt(scaling, CanvasW/2, CanvasH/2), InitialMatrix]);
}

function FlowChartCreate(files, OnSelect) {
	function Lerp(a, b, f) {
		return (a * (1 - f)) + (b * f);
	}

	function MakeBox(file, selected) {
		var color = Colors[file["index"] % Colors.length];//file["missing"] ? "gray" : "black";
		var mat = Matrix.translate(file["x"], file["y"]);
		var g = Surface.createGroup().setTransform(mat);
		var box = g.createRect({x:-BoxWidth/2, y:-BoxHeight/2, width:BoxWidth, height:BoxHeight, r:5}).setFill({type:"linear", y1:-BoxHeight * 0.75, x2:0, y2:BoxHeight, colors:[{offset:0, color:"white"}, {offset:1, color:color}]}).setStroke({color:"black", width:2});
		var title = g.createText({x:0, y:-3, text:file["name"], align:"middle"}).setFont({family:"Arial", size:"14px", weight:"bold"}).setFill("black");
		var type = g.createText({x:0, y:14, text:GetTypeName(file["type"], true), align:"middle"}).setFont({family:"Arial", size:"12px"}).setFill("black");
		var mover = null;//new dojox.gfx.Moveable(g);
		g.connect("onmousedown", this,function(evt) { OnSelect(evt, file); });
		g.rawNode.setAttribute("cursor", "pointer");
		return { box:box, title:title, type:type, g:g, mat:mat, mover:mover, connections:[] };
	}

	function MakeConnection(file1, file2) {
		var stroke = {color:Colors[file1["index"] % Colors.length], width:2};//(file1["missing"] || file2["missing"]) ? "gray" : "black";
		if (file2["col"] == file1["col"] + 1) {
			if (file2["y"] == file1["y"]) {
				Surface.createLine({x1:file1["x"] + BoxWidth/2, y1:file1["y"], x2:file2["x"] - BoxWidth/2, y2:file2["y"]}).setStroke(stroke);
			} else {
				var x1 = file1["x"] + BoxWidth / 2;
				var x2 = file2["x"] - BoxWidth / 2;
				var path = Surface.createPath().setStroke(stroke);
				path.moveTo(x1, file1["y"]);
				path.curveTo(Lerp(x1, x2, 0.8), file1["y"], Lerp(x2, x1, 0.8), file2["y"], x2, file2["y"]);
			}
		} else {
			//FIXME: this won't work for everything
			if (file2["y"] == file1["y"]) {
				var x1 = file1["x"] + BoxWidth / 2;
				var x2 = x1 + BoxHSpacing;
				var x4 = file2["x"] - BoxWidth / 2;
				var x3 = x4 - BoxHSpacing;
				var y1 = file1["y"];
				var y2 = y1 + BoxHeight / 2 + 5;
				Surface.createLine({x1:x2, y1:y2, x2:x3, y2:y2}).setStroke(stroke);
				var path = Surface.createPath().setStroke(stroke);
				path.moveTo(x1, y1);
				path.curveTo(Lerp(x1, x2, 0.8), y1, Lerp(x2, x1, 0.8), y2, x2, y2);
				path.moveTo(x3, y2);
				path.curveTo(Lerp(x3, x4, 0.8), y2, Lerp(x4, x3, 0.8), y1, x4, y1);
			} else {
				var x1 = file2["x"] - BoxWidth / 2 - BoxHSpacing;
				var x2 = file2["x"] - BoxWidth / 2;
				Surface.createLine({x1:file1["x"] + BoxWidth/2, y1:file1["y"], x2:x1, y2:file1["y"]}).setStroke(stroke);
				var path = Surface.createPath().setStroke(stroke);
				path.moveTo(x1, file1["y"]);
				path.curveTo(Lerp(x1, x2, 0.8), file1["y"], Lerp(x2, x1, 0.8), file2["y"], x2, file2["y"]);
			}
		}
	}

	function SubtractArray(arr, sub) {
		var ret = new Array();
		for (var i in arr) {
			e = arr[i];
			if (!InArray(sub, e)) {
				ret.push(e);
			}
		}
		return ret;
	}

	function ReverseSort(a, b) {
		return b - a;
	}
	
	function OffsetChain(files, columns, file, col, y) {
		if (InArray(columns[col], file)) {
			files[file]["y"] += y;
			var deps = files[file]["deps"];
			if (deps && deps.length > 0) {
				for (var d in deps) {
					OffsetChain(files, columns, deps[d], col + 1, y);
				}
			}
		}
	}
	
	function CalcGroupHeight(count) {
		return BoxHeight * count + BoxVSpacing * (count - 1);
	}
	
	function GetBoxHeight(columns, files, col, file) {
		if (!InArray(columns[col], file)) {
			return 0;
		}
		var deps = files[file]["deps"].slice(0);
		if (deps && deps.length > 0) {
			var height = 0;
			var heights = new Array();
			for (var d = 0; d < deps.length;) {
				var h = GetBoxHeight(columns, files, col + 1, deps[d]);
				if (h > 0) {
					heights.push(h);
					height += h;
					++d;
				} else {
					deps.splice(d, 1);
				}
			}
			if (deps.length > 1) {
				var a;
				a = 0;
			}
			var offset = -CalcGroupHeight(height) / 2;
			for (var d in deps) {
				var h = CalcGroupHeight(heights[d]);
				OffsetChain(files, columns, deps[d], col + 1, offset + h / 2);
				offset += h + BoxVSpacing;
			}
			return height;
		}
		return 1;
	}
	
	var x = BoxWidth / 2 + 10;
	//seperate into columns of dependencies
	var can_depend = new Array();
	var columns = new Array();
	var remaining = files.slice(0);
	var indices = new Array();
	for (var i in files) {
		indices.push(i);
		files[i]["index"] = i;
		files[i]["y"] = 10;
	}
	indices.sort(ReverseSort);
	while (indices.length > 0) {
		var is = indices.slice(0);
		for (var ri in remaining) {
			r = remaining[ri];
			if (r) {
				is = SubtractArray(is, SubtractArray(r["deps"], can_depend));
			}
		}
		var col = columns.length;
		columns.push(new Array());
		for (var ii in is) {
			columns[col].push(is[ii]);
			remaining[is[ii]]["col"] = col;
			remaining[is[ii]] = null;
			can_depend.push(is[ii]);
			files[is[ii]]["x"] = x;
		}
		indices = SubtractArray(indices, is);
		x += BoxWidth + BoxHSpacing;
	}
	//layout each column
	var height = GetBoxHeight(columns, files, 0, columns[0][0]);
	height = CalcGroupHeight(height);
	OffsetChain(files, columns, columns[0][0], 0, height / 2);

	Surface = dojox.gfx.createSurface(dojo.byId("navigation_graph"), 10 + BoxHSpacing * (columns.length - 1) + BoxWidth * columns.length + 10, 10 + height + 10);
	for (var f in files) {
		Nodes.push(MakeBox(files[f]));
	}
	for (var f in files) {
		var deps = files[f]["deps"]
		for (var d in deps) {
			c = MakeConnection(files[f], files[deps[d]]);
			//boxes[f]["connections"].push({
		}
	}
}

function FlowChartSelect(index) {
	if (Selected >= 0) {
		Nodes[Selected].box.setStroke({color:"black", width:2});
		Nodes[Selected].title.setFill("black");
		Nodes[Selected].type.setFill("black");
	}
	if (index >= 0) {
		Nodes[index].box.setStroke({color:"white", width:2});
		Nodes[index].title.setFill("white");
		Nodes[index].type.setFill("white");
	}
	Selected = index;
}
