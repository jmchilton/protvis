function BuildResults(results) {
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
			html += [
				"<tr class=\"info ", style, "\">",
				"<td><span class=\"peptide_full\">", r[5], "<span class=\"link peptide\" onclick=\"SearchPeptide('" + r[7] + "');\">", r[6], "</span>", r[7], "</span></td>", //peptide
				"<td style=\"text-align: center;\">", protein, "</td>", //protein
				"<td style=\"text-align: center;\">", r[9], "</td>", //massdiff
				"<td style=\"text-align: center;\"><span class=\"link\" onclick=\"DisplayScore('", r[6], "/", r[8], "'", ",0,", r[0], ",", r[1], ",", r[2], ");\">", r[10], "</span></td>", //score
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
		return disp + "<br/><table id=\"results\" border=\"1\" style=\"width: 100%;\">" + BuildHeader() + html + "</table>";
	}
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
