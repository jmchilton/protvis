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
