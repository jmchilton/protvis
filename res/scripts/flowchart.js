dojo.require("dojox.gfx");
var Surface, Group;
var Matrix = dojox.gfx.matrix, InitialMatrix = Matrix.translate(0, 0);
var CanvasW, CanvasH;
var BoxWidth = 120;
var BoxHeight = 45;
var BoxHSpacing = 50, BoxVSpacing = 30, BoxVSize = BoxVSpacing + BoxHeight;

function UpdateMatrix(){
	group.setTransform([m.scaleAt(scaling, CanvasW/2, CanvasH/2), InitialMatrix]);
}

function FlowChartCreate(files) {
	function GetTypeName(type) {
		if (type <= 0) {
			return "";
		} else if (type == 1) {
			return "MZML";
		} else if (type == 2) {
			return "MGF";
		} else if (type <= 9) {
			return "PepXML";
		} else {
			return "ProtXML";
		}
	}

	function MakeBox(file) {
		var color = file["missing"] ? "gray" : "black";
		var mat = Matrix.translate(file["x"], file["y"]);
		var g = Surface.createGroup().setTransform(mat);
		var box = g.createRect({x:-BoxWidth/2, y:-BoxHeight/2, width:BoxWidth, height:BoxHeight}).setFill("#eee").setStroke({color:color, width:2});
		g.createText({x:0, y:-3, text:file["name"], align:"middle"}).setFont({family:"Arial", size:"14px", weight:"bold"}).setFill("black");
		g.createText({x:0, y:14, text:GetTypeName(file["type"]), align:"middle"}).setFont({family:"Arial", size:"12px"}).setFill("black");
		var mover = null;//new dojox.gfx.Moveable(g);
		return { box:box, g:g, mat:mat, mover:mover, connections:[] };
	}

	function MakeConnection(file1, file2) {
		var color = (file1["missing"] || file2["missing"]) ? "gray" : "black";
		Surface.createLine({x1:file1["x"] + BoxWidth/2, y1:file1["y"], x2:file2["x"] - BoxWidth/2, y2:file2["y"]}).setStroke({color:color, width:2});
	}

	function InArray(arr, e) {
		for (var i in arr) {
			if (arr[i] == e) {
				return true;
			}
		}
		return false;
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
		files[i]["y"] = 0;//10;
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
	var boxes = new Array();
	for (var f in files) {
		boxes.push(MakeBox(files[f]));
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
}
