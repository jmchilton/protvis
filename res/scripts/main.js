function TableBuilder(id, /*optinal:*/columns) {
	this.ID = id;
	this.Columns = columns.length;
	this.Rows = 0;
	this.HTML = '<div id="' + id + '"><table>';
	if (columns) {
		this.SetHead(columns);
	} else {
		var orig = document.getElementById(id);
		if (orig != null) {
			this.HTML += '<tr id="head">' + orig.getElementById("head").innerHTML + '</tr>';
		}
	}
	
	this.SetHead = function(columns) {
		this.HTML += '<tr id="head">';
		for (col in columns) {
			attrs = "";
			if (col["sort"]) {
				attrs += 'id="' + id + '_column_' + col['sort'] + '" onclick="TableManager.Sort(' + id + ', ' + col['sort'] + ');" class="sortable"';
			}
			this.HTML += '<th ' + attrs + '>' + col["title"] + '</th>';
		}
		this.HTML += '<tr>';
	}

	this.AddRow = function(columns, /*optinal:*/attrs) {
		var style = ((this.Rows % 2 == 0) ? 'norm' : 'alt');
		var attr = "";
		if (!attrs) {
			attr = ' class="' + style + '"';
		} else {
			if (attrs["class"]) {
				attrs["class"] += style;
			} else {
				attrs["class"] = style;
			}
			for (at in attrs) {
				attr += ' ' + at + '="' + attrs[at] + '"';
			}
		}
		this.HTML += '<tr' + attr + '>';
		for (col in columns) {
			this.HTML += '<td>' + col + '</td>';
		}
		this.HTML += '</tr>';
		++this.Rows;
	}
	
	this.ReplaceOriginal = function() {
		document.getElementById(id).innerHTML = this.GetHtml();
	}

	this.GetHtml = function() {
		return this.HTML + '</table></div>';
	}
}
			
function executeAjaxResponse(response) {
	var scripts = new Array();
	var start = 0;
	for (;;) {
		start = response.indexOf("<script", start);
		if (start < 0) {
			break;
		}
		start = response.indexOf(">", start) + 1;
		var end = response.indexOf("</script>", start);
		scripts.push(response.substring(start, end));
		start = end + 9;
	}
	for (var i = 0; i < scripts.length; ++i) {
		try {
			eval(scripts[i]);
		} catch (e) {
			if (console) {
				console.log(scripts[i]);
				console.log(e);
			}
		}
	}
}

RenderCoverage = function(chartdiv, sequence, peptides) {
	this.ApplyState = function(i, state) {
		var cls;
		if (this.Stuck[i]) {
			if (state == 0) {
				this.Boxes[i].setFill([0, 255, 0, 0.3]);
				cls = "stuck";
			} else {
				this.Boxes[i].setFill([0, 200, 0, 0.3]);
				cls = "stuckover";
			}
		} else {
			if (state == 0) {
				this.Boxes[i].setFill([0, 0, 255, 0.3]);
				cls = "row";
			} else {
				this.Boxes[i].setFill([255, 0, 0, 0.3]);
				cls = "decoy";
			}
		}
		dojo.byId(this.Container + "_" + i).setAttribute("class", cls + (((i % 2) == 0) ? "" : "odd"));
	}
	
	this.Over = function(index) {
		this.ApplyState(index, 1);
	}
	
	this.Out = function(index) {
		this.ApplyState(index, 0);
	}
	
	this.Click = function(index) {
		this.Stuck[index] = !this.Stuck[index];
		this.ApplyState(index, 1);
	}
	
	var Height = 20;
	this.AAs = sequence.length;
	this.Container = chartdiv;
	this.Surface = dojox.gfx.createSurface(chartdiv, "100%", Height);
	this.Surface.rawNode.setAttribute("viewBox", "0 0 " + sequence.length + " " + Height);
	this.Surface.rawNode.setAttribute("preserveAspectRatio", "none");
	this.Background = this.Surface.createRect({x:0, y:0, width:sequence.length, height:Height}).setFill("white");
	this.Group = this.Surface.createGroup();
	this.Stuck = new Array(peptides.length);
	this.Boxes = new Array(peptides.length);
	this.Offsets = new Array(peptides.length);
	for (var i in peptides) {
		var p = peptides[i];
		this.Offsets[i] = sequence.indexOf(p);
		this.Boxes[i] = this.Group.createRect({x:this.Offsets[i], y:0, width:p.length, height:Height}).setFill([0, 0, 255, 0.3]);
		this.Stuck[i] = 0;
	}
	this.Surface.connect("onmousemove", this, function(evt) {
		var s = this.Surface.rawNode;
		var boxes = this.Group.rawNode.childNodes;
		var mx = evt.offsetX * (s.viewBox.baseVal.width / s.clientWidth);
		for (var i = 0; i < boxes.length; ++i) {
			var b = boxes[i];
			if (mx >= b.x.baseVal.value && mx <= b.x.baseVal.value + b.width.baseVal.value) {
				this.ApplyState(i, 1);
			} else {
				this.ApplyState(i, 0);
			}
		}
	});
	this.Surface.connect("click", this, function(evt) {
		var s = this.Surface.rawNode;
		var boxes = this.Group.rawNode.childNodes;
		var mx = evt.offsetX * (s.viewBox.baseVal.width / s.clientWidth);
		for (var i = 0; i < boxes.length; ++i) {
			var b = boxes[i];
			if (mx >= b.x.baseVal.value && mx <= b.x.baseVal.value + b.width.baseVal.value) {
				this.Stuck[i] = !this.Stuck[i];
				this.ApplyState(i, 1);
			}
		}
	});
	this.Surface.connect("onmouseleave", this, function(evt) {
		for (var i in this.Boxes) {
			this.ApplyState(i, 0);
		}
	});
}

//FIXME: DEBUG
function dump(x) {
	var inspected = [];
	
	function is_duplicate(obj) {
		for(var i = 0; i < inspected.length; i++) {
		    if(inspected[i] === obj)
		        return true;
		}
		return false;
	}

	function inspector(obj, tab) {
		inspected.push(obj);
		for(var prop in obj) {
		    console.log(tab + prop);
		    if(!is_duplicate(obj) && typeof obj[prop] == 'object')
		        inspector(obj[prop], tab + "  ");
		}
	}
	
	inspector(x, "");
}
