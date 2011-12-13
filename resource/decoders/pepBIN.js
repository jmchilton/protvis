function BuildResults(results, buildid) {
	var r;
	var rows = results.split('\n');
	if (rows.length <= 1) {
		if (rows.length == 0) {
			r = results.split(' ');
		} else {
			r = rows[0].split(' ');
		}
		return "None of the " + r[2] + " queries matched your filter";
	} else {
		var html = "";
		var tipIDs = new Array();
		var i = 1;
		while (i < rows.length) {
			r = rows[i].split(' ');
			++i;
			var style = (i % 2) ? "alt" : "norm";
			var protein = r[8];
			if (protein[0] == '/') {
				style = "decoy_" + style;
				protein = protein.substring(1);
			}
			var id = "peptide_" + buildid + "_" + i;
			tipIDs.push(id);
			html += [
				"<tr class=\"info ", style, "\" style=\"text-align: center;\">",
				"<td style=\"text-align: left;\"><span class=\"peptide_full\">", r[5], "<span id=\"" + id + "\" class=\"link peptide\" onclick=\"SearchPeptide('" + r[6] + "');\">", r[6], "</span>", r[7], "</span></td>", //peptide
				"<td>", protein, "</td>", //protein
				"<td>", r[9], "</td>", //massdiff
				"<td><span class=\"link\" onclick=\"DisplayScore('", r[6], "/", protein, "',0,", r[0], ",", r[1], ",", r[2], ");\">", r[10], "</span></td>", //score
				"</tr>",
				"<tr class=\"desc ", style, "\"><td colspan=\"4\">", r.slice(11).join(" "), "</td></tr>" //protein description
			].join("");
			if (r[3] > 1) {
				//r[4] is the total hits in query
				html += "<tr class=\"" + style + "\"><td colspan=\"4\"><span class=\"link\" onclick=\"DisplayQuery(" + r[0] + ");\">" + (r[3] - 1) + " more results in this spectrum query</span></td></tr>";
			}
		}
		r = rows[0].split(' ');
 		var disp;
 		if (rows < 2) {
 			disp = "None of the " + r[2] + " queries match your filter";
		} else if (rows.length == 2) {
			disp = "Displaying the only result";
		} else if (rows.length - 1 == r[1]) {
			disp = "Displaying all " + r[1] + " results";
		} else {
			disp = "Displaying " + (parseInt(r[0]) + 1) + "-" + (rows.length - 1) + " of " + r[1] + " results";
		}
		return [disp + "<br/><table id=\"results\" border=\"1\" style=\"width: 100%;\">" + BuildResultsHeader() + html + "</table>", tipIDs];
	}
}

function BuildPeptideResults(results) {
	var r;
	var rows = results.split('\n');
	var html = "";
	var i = 2;
	//Data
	while (i < rows.length) {
		r = rows[i].split(' ');
		var style = (i % 2) ? "alt" : "norm";
		++i;
		html += [
			"<tr class=\"info ", style, "\" style=\"text-align: center;\">",
			"<td style=\"text-align: left;\">", r[0], "</td>", //spectrum
			"<td>", r[1], "</td>", //massdiff
			"<td>", r[2], "</td>", //score
			"<td>", r[3], "</td>", //engine
			"<td>", r[4], "</td>", //engine score
			"</tr>",
		].join("");
	}
	//Spectrums
	r = rows[1].split(' ');
	spectrums = r.length;
	i = 0;
	specs = "<div id=\"spectrum_list\" style=\"display: none;\"><table><tr><th>Spectrum</th><th>Occurrences</th></tr>";
	while (i < spectrums) {
		s = r[i].split('/')
		var style = (i % 2) ? "alt" : "norm";
		specs += "<tr class=\"" + style + "\"><td>" + s[1] + "</td><td style=\"text-align: center;\">" + s[0] + "</td></tr>";
		++i;
	}
	specs += "</table></div>"
	//Header
	r = rows[0].split(' ');
	var disp;
	if (rows.length == 3) {
		disp = "Displaying the only occurrence of <b>" + r[2] + "</b>";
	} else {
		if (rows.length - 2 == r[1]) {
			disp = "Displaying all " + r[1] + " occurrences of <b>" + r[2] + "</b>";
		} else {
			disp = "Displaying " + (parseInt(r[0]) + 1) + "-" + (rows.length - 2) + " of " + r[1] + " occurrences of <b>" + r[2] + "</b>";
		}
		disp += "<br/>";
		var first = true;
		if (r[3] > 0) {
			disp += r[3] + " from X-Tandem";
			first = false;
		}
		if (r[4] > 0) {
			if (first) {
				first = false;
			} else {
				disp += ", "
			}
			disp += r[4] + " from Mascot";
		}
		if (r[5] > 0) {
			if (first) {
				first = false;
			} else {
				disp += ", "
			}
			disp += r[5] + " from Omssa";
		}
		disp += "<div><span class=\"link\" onclick=\"ToggleSpectrums();\">Results are from " + spectrums + " unique spectrums</span>" + specs + "</div>"
	}
	return "<br/>" + disp + "<br/><table border=\"1\" style=\"width: 100%;\">" + BuildPeptidesHeader() + html + "</table>";
}

function BuildSpectrumQuery(results) {
}

function BuildScores(scores) {
	var rows = scores.split('\n');
	var i = 1;
	scores = "";
	while (i < rows.length) {
		r = rows[i].split(' ');
		++i;
		var style = (i % 2) ? "alt" : "norm";
		scores += "<tr class=\"" + style + "\" style=\"text-align: center;\"><td>" + r.slice(1).join(" ") + "</td><td>" + r[0] + "</td></tr>";
	}
	return [rows[0], "<table id=\"results\" style=\"width: 100%;\"><tr><th>Name</th><th>Value</th></tr>" + scores + "</table>"];
}

var ResultsVisible = false;

function ToggleSpectrums() {
	if (ResultsVisible) {
		dojo.fx.wipeOut({ node: dojo.byId("spectrum_list") }).play();
		ResultsVisible = false;
	} else {
		dojo.fx.wipeIn({ node: dojo.byId("spectrum_list") }).play();
		ResultsVisible = true;
	}
}
