var TableManager = new function() {
	this.Tables = {};
	
	this.Add = function(id, sortcol) {
		this.Tables[id] = { sort_col: sortcol, sort_asc: true };
	}
	
	this.Delete = function(id) {
		delete this.Tables[id];
	}
	
	this.Sort = function(id, col, callback) {
		t = this.Tables[id];
		if (t["sort_col"] == col) {
			t["sort_asc"] = !t["sort_asc"];
		} else {
			t["sort_col"] = col;
			t["sort_asc"] = true;
		}
		this.Tables[id] = t;
		document.getElementById(id + '_column_' + col['sort']).setAttribute("class", "sortable " + (t["sort_asc"] ? "sort_asc" : "sort_dsc"));
		callback(t);
	}
}

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
				attrs += 'id="' + id + '_column_' + col['sort'] + '" onclick="TableManager.Sort(' + id + ', ' + col['sort'] + ');" class="sortable";
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

/*function DecodeTableResponse(id, update, resp) {
	var rows = resp.split('\n');
	var info = eval(rows[0]);
	if (info{"data"]) {
		var table = new TableBuilder(id, update ? null : info["head"]);
		var i = 1;
		while (i < rows.length) {
			r = rows[i].split('|');
			++i;
		}
	} else {
	}
}*/
