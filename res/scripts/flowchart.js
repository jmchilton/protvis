dojo.require("dojox.gfx");
dojo.require("dojo._base.Color");

//Constants
var BoxSlotSpacing = 7;
var BoxSlots = 3;
var BoxWidth = 140;
var BoxHeight = 45;
var BoxHSpacing = 50, BoxVSpacing = (BoxSlots * 2 + 1) * BoxSlotSpacing, BoxVSize = BoxVSpacing + BoxHeight;
var Colors = [ "#ff5900", "#0d56ff", "#4dde00", "#a600a6", "#ff9700", "#2618b1", "#1049a9", "#009999", "#e9003a" ];

FlowChart = function(parent, files, OnSelect) {
	this.Surface = null;
	this.Matrix = dojox.gfx.matrix;
	this.Nodes = new Array();
	this.Selected = -1;
	
	var columns = new Array();
	var obj = this;
	var ruler = document.createElement('div');
	ruler.setAttribute("style", "position:absolute; visibility:hidden; height:auto; width:auto; font:bold 14px Arial; white-space:nowrap;");
	dojo.byId(parent).appendChild(ruler);
	
	function StringClip(str, width) {
		ruler.innerHTML = str;
		if (ruler.clientWidth <= width) {
			return str;
		}
		i = str.length;
		do {
			ruler.innerHTML = str.substr(0, --i) + "…";
		} while (ruler.clientWidth > width && i > 0);
		return str.substr(0, i) + "…";
	}
	
	function MakeBox(file) {
		var missing = file.type & 0x80;
		var color = missing ? "#808080" : Colors[file.index % Colors.length];
		var mat = obj.Matrix.translate(file.x, file.y);
		var g = obj.Surface.createGroup().setTransform(mat);
		var name = StringClip(file.name, BoxWidth - 6);
		var tname = GetTypeName(file.type, true);
		var box = g.createRect({x:-BoxWidth/2, y:-BoxHeight/2, width:BoxWidth, height:BoxHeight, r:5}).setFill({type:"linear", y1:-BoxHeight * 0.75, x2:0, y2:BoxHeight, colors:[{offset:0, color:"white"}, {offset:1, color:color}]}).setStroke({color:"black", width:2});
		var title_shaddow = g.createText({x:0, y:-3, text:name, align:"middle"}).setFont({family:"Arial", size:"14px", weight:"bold"}).setFill("transparent");
		var type_shaddow = g.createText({x:0, y:14, text:tname, align:"middle"}).setFont({family:"Arial", size:"12px"}).setFill("transparent");
		var title = g.createText({x:0, y:-3, text:name, align:"middle"}).setFont({family:"Arial", size:"14px", weight:"bold"}).setFill("black");
		var type = g.createText({x:0, y:14, text:tname, align:"middle"}).setFont({family:"Arial", size:"12px"}).setFill(missing ? "red" : "black");
		if (OnSelect) {
			g.connect("onmousedown", this, function(evt) { OnSelect(evt, file); });
		}
		g.rawNode.setAttribute("cursor", "pointer");
		return { box:box, title:title, type:type, g:g, mat:mat, slots_top:[], slots_bot:[], x:file.x, y:file.y, title_shaddow:title_shaddow, type_shaddow:type_shaddow, missing:missing };
	}
	
	function BoxFromPosition(col, y) {
		col = columns[col]
		for (var b in col) {
			if (files[col[b]]["y"] == file1["y"]) {
				return files[col[b]];
			}
		}
		return null;
	}

	function ConnectBoxes(files) {
		var deffered = new Array();
		
		function Lerp(a, b, f) {
			return (a * (1 - f)) + (b * f);
		}
		
		function CountConnections(side) {
			var len = 0;
			for (s in side) {
				len += side[s];
			}
			return len;
		}
		
		function NextSlot(box, side) {
			if (box[side].length < BoxSlots) {
				return box[side].push(1);
			}
			var minval = 65535;
			var minpos = 0;
			for (s in box[side]) {
				var c = box[side][s];
				if (c < minval) {
					minval = c;
					minpos = s;
				}
			}
			return minpos + 1;
		}
		
		function _RouteConnectionInline(col1, file2, path, side) {
			//find a list of all the bokes we must route past
			var boxes = new Array();
			var y = file2.y;
			for (var col = col1 + 1; col < file2.col; ++col) {
				var box = null;
				for (var c in columns[col]) {
					if (files[columns[col][c]].y == y) {
						box = obj.Nodes[columns[col][c]];
						break;
					}
				}
				boxes.push(box);
			}
			//find the path which has the most space and least crossovers
			if (!side) {
				var fulltop = 0, maxtop = 0;
				var fullbot = 0, maxbot = 0;
				for (var b in boxes) {
					if (boxes[b] != null) {
						maxtop = Math.max(maxtop, CountConnections(boxes[b].slots_top));
						maxbot = Math.max(maxbot, CountConnections(boxes[b].slots_bot));
						if (boxes[b].slots_top.length >= BoxSlots) {
							++fulltop;
						}
						if (boxes[b].slots_bot.length >= BoxSlots) {
							++fullbot;
						}
					}
				}
				side = fulltop < fullbot || (fulltop == fullbot && maxtop <= maxbot) ? -1 : 1;
			}
			var slot = side < 0 ? "slots_top" : "slots_bot";
			var x1 = path.last.x;
			var y1 = path.last.y;
			var b, x2, y2;
			for (var i in boxes) {
				b = boxes[i];
				x2 = b.x - BoxWidth / 2;
				y2 = y + side * (BoxHeight / 2 + NextSlot(b, slot) * BoxSlotSpacing);
				path.curveTo(Lerp(x1, x2, 0.8), y1, Lerp(x2, x1, 0.8), y2, x2, y2); //draw the curved start
				x1 = x2 + BoxWidth;
				path.lineTo(x1, y2); //draw the straight line segment
				y1 = y2;
			}
			x2 = file2.x - BoxWidth / 2;
			y2 = y;
			path.curveTo(Lerp(x1, x2, 0.8), y1, Lerp(x2, x1, 0.8), y, x2, y);
		}
		
		function RouteConnectionInline(file1, file2, stroke) {
			var path = obj.Surface.createPath().setStroke(stroke);
			var x1 = file1.x + BoxWidth / 2;
			path.moveTo(x1, file2.y);
			_RouteConnectionInline(file1.col, file2, path, 0);
		}
		
		function RouteConnection(file1, file2, stroke) {
			var path = obj.Surface.createPath().setStroke(stroke);
			var curcol = file1.col;
			var x1 = file1.x + BoxWidth / 2;
			var y1 = file1.y;
			path.moveTo(x1, y1);
			var sgn = 0;
			while (true) {
				var sign = file2.y > y1 ? 1 : -1;
				if (!sgn) {
					sgn = sign;
				}
				var heightdiff = Math.abs(file2.y - y1);
				++curcol;
				var closest = heightdiff;
				var closesti = -1;
				for (var i in columns[curcol]) {
					var c = columns[curcol][i];
					if (Math.abs(files[c].y - y1) <= closest && (files[c].y - y1) * sign > 0) {
						closest = Math.abs(files[c].y - y1);
						closesti = i;
					}
				}
				var b = columns[curcol][closesti];
				if (file2.y != files[b].y) {
					sgn = sign;
				}
				if (closesti < 0) {
					x1 += BoxWidth + BoxHSpacing;
					path.lineTo(x1, y1);
				} else {
					//x1 += BoxWidth + BoxHSpacing;
					y1 = files[b].y;
					if (file2.y != y1) {
						sgn = -sign;
					}
					var slot = sgn < 0 ? "slots_bot" : "slots_top";
					var x2 = x1 + BoxHSpacing;
					var y2 = y1 + -sgn * (BoxHeight / 2 + NextSlot(obj.Nodes[b], slot) * BoxSlotSpacing);
					path.curveTo(Lerp(path.last.x, x2, 0.8), path.last.y, Lerp(x2, path.last.x, 0.8), y2, x2, y2); //draw the curved start
					x1 = x2 + BoxWidth;
					path.lineTo(x1, y2);
				}
				if (file2.col - curcol == 1) {
					break;
				} else if (file2.y == y1) {
					_RouteConnectionInline(curcol, file2, path, -sgn);
					return;
				}
			}
			var x2 = file2.x - BoxWidth / 2;
			path.curveTo(Lerp(path.last.x, x2, 0.8), path.last.y, Lerp(x2, path.last.x, 0.8), file2.y, x2, file2.y);
		}
		
		function MakeConnection(file1, file2) {
			var stroke = {color:Colors[file1.index % Colors.length], width:2};
			if (file2.col == file1.col + 1) {
				if (file2.y == file1.y) {
					obj.Surface.createLine({x1:file1.x + BoxWidth/2, y1:file1.y, x2:file2.x - BoxWidth/2, y2:file2.y}).setStroke(stroke);
				} else {
					var x1 = file1.x + BoxWidth / 2;
					var x2 = file2.x - BoxWidth / 2;
					var path = obj.Surface.createPath().setStroke(stroke);
					path.moveTo(x1, file1.y);
					path.curveTo(Lerp(x1, x2, 0.8), file1.y, Lerp(x2, x1, 0.8), file2.y, x2, file2.y);
				}
			} else {
				if (file2.y == file1.y) {
					var direct = true;
					for (var col = file1.col + 1; col < file2.col; ++col) {
						for (var c in columns[col]) {
							if (files[columns[col][c]].y == file1.y) {
								direct = false;
								break;
							}
						}
					}
					if (direct) {
						//This is an empty cell, we can do a straight line across it
						obj.Surface.createLine({x1:file1.x + BoxWidth/2, y1:file1.y, x2:file2.x - BoxWidth/2, y2:file2.y}).setStroke(stroke);
					} else {
						if (file2.col - file1.col == 2) {
							RouteConnectionInline(file1, file2, stroke);
						} else {
							deffered.push([file1, file2, stroke]);
						}
						
					}
				} else {
					deffered.push([file1, file2, stroke]);
				}
			}
		}

		for (var f in files) {
			var deps = files[f].deps
			for (var d in deps) {
				if (deps[d] >= 0) {
					c = MakeConnection(files[f], files[deps[d]]);
				}
			}
		}
		var jumplen = 2;
		while (deffered.length > 0) {
			for (var i = deffered.length - 1; i >= 0; --i) {
				d = deffered[i];
				if (d[1].col - d[0].col == jumplen) {
					if (d[0].y == d[1].y) {
						RouteConnectionInline(d[0], d[1], d[2]);
					} else {
						RouteConnection(d[0], d[1], d[2]);
					}
					deffered.splice(i, 1);
				}
			}
			++jumplen;
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
			files[file].y += y;
			var deps = files[file].deps;
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
		var deps = files[file].deps.slice(0);
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

	this.Select = function(index) {
		if (this.Selected >= 0) {
			this.Nodes[this.Selected].box.setStroke({color:"black", width:2});
			this.Nodes[this.Selected].title_shaddow.setFill("transparent").setStroke({width:0});
			this.Nodes[this.Selected].type_shaddow.setFill("transparent").setStroke({width:0});
			this.Nodes[this.Selected].title.setFill("black");
			this.Nodes[this.Selected].type.setFill(this.Nodes[this.Selected].missing ? "red" : "black");
		}
		if (index >= 0) {
			var col = new dojo._base.Color([90,90,90]);
			this.Nodes[index].box.setStroke({color:"white", width:2});
			this.Nodes[index].title_shaddow.setFill(col).setStroke({color:col, width:2});
			if (!this.Nodes[index].missing) {
				this.Nodes[index].type_shaddow.setFill(col).setStroke({color:col, width:2});
			}
			this.Nodes[index].title.setFill("white");
			this.Nodes[index].type.setFill(this.Nodes[index].missing ? "red" : "white");
		}
		this.Selected = index;
	}

	this.UpdateStatus = function(index, status) {
		this.Nodes[index].type.rawNode.textContent = status;
	}
	
	var x = BoxWidth / 2 + 10;
	//seperate into columns of dependencies
	var can_depend = new Array();
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
				is = SubtractArray(is, SubtractArray(r.deps, can_depend));
			}
		}
		var col = columns.length;
		columns.push(new Array());
		for (var ii in is) {
			columns[col].push(is[ii]);
			remaining[is[ii]].col = col;
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

	this.Surface = dojox.gfx.createSurface(parent, 10 + BoxHSpacing * (columns.length - 1) + BoxWidth * columns.length + 10, height + 6 + BoxSlots * BoxSlotSpacing);
	for (var f in files) {
		this.Nodes.push(MakeBox(files[f]));
	}
	ConnectBoxes(files);
}
