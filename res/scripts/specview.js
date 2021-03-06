//This code is based off lorikeet. http://code.google.com/p/lorikeet/
//The graphing functionality has been completly rewritten to use dojo
//All the chemistry and maths is from lorikeet, or an optimised version thereof

dojo.require("dojo._base.connect");
dojo.require("dojo._base.event");

SpecViewer = function(container, opts) {
	this.Options = {
		sequence: null,
		scanNum: null,
		fileName: null,
		charge: null,
		precursorMz: null,
		staticMods: [],
		variableMods: [],
		ntermMod: 0, // additional mass to be added to the n-term
		ctermMod: 0, // additional mass to be added to the c-term 
		peaks: [],
		ms1peaks: null,
		ms1scanLabel: null,
		precursorPeaks: null,
		precursorPeakClickFn: null,
		zoomMs1: false,
		massError: 0.5, // mass tolerance for labeling peaks
		extraPeakSeries:[],
		hidePrecursor: true,
		peakAssignmentType: "intense", // intense OR close
		peakLabelType: "ion", // ion OR mz OR none
		neutralLosses: [], //Any combination of: "h2o", "nh3"
		massTypeOpt: "mono", // mono OR avg
		ionTableContainer: null, //the element to contain the ion table
		selectedIons: [["b", 1], ["y", 1]], //The ions to display
		tooltip: true,
		editable: false
	};
	if (Math.max(1, opts.charge - 1) >= 2) {
		this.Options.selectedIons.push(["b", 2]);
		this.Options.selectedIons.push(["y", 2]);
		if (Math.max(1, opts.charge - 1) >= 3) {
			this.Options.selectedIons.push(["b", 3]);
			this.Options.selectedIons.push(["y", 3]);
		}
	}
	dojo.mixin(this.Options, opts);
	this.maxInt = getMaxInt(this.Options.peaks);
	var selected = [];
	for (var i in this.Options.selectedIons) {
		selected.push(Ion.get(this.Options.selectedIons[i][0], this.Options.selectedIons[i][1]));
	}
	this.Options.selectedIons = selected;
	var obj = this;

	this.Container = container;
	this.massErrorChanged = false;
	this.massTypeChanged = false;
	this.peakAssignmentTypeChanged = false;
	this.peakLabelTypeChanged = false;
	this.selectedNeutralLossChanged = false;
	
	var ZoomHistory = new Array();

	this.PlotOptions = {
		axis: {
			y: {
				scale: 100.0 / this.maxInt,
				format: function(val, precision) { return FormatPrecision(val, precision) + "%"; }
			}
		},
		tooltip: {
			enable: this.Options.tooltip
		},
		editable: this.Options.editable,
		selection: {
			axis: "x",
			callback: function(isRange, range) {
				if (isRange) {
					var vr = dojo.clone(range);
					var datasets = obj.getDatasets();
					if (obj.PlotOptions.selection.axis.indexOf("y") < 0) {
						var maxInt = Number.NEGATIVE_INFINITY;
						for (var i in datasets) {
							var d = datasets[i].data;
							for (var j in d) {
								var v = d[j];
								if (v[0] >= range.x.min && v[0] <= range.x.max && v[1] > maxInt) {
									maxInt = v[1];
								}
							}
						}
						if (maxInt > 0) {
							range.y.max = maxInt * 1.1;
						}
					}
					if (obj.ZoomRange == null || range.x.min != obj.ZoomRange.x.min || range.x.max != obj.ZoomRange.x.max || range.y.max != obj.ZoomRange.y.min || range.y.min != obj.ZoomRange.y.max) {
						ZoomHistory.push(obj.ZoomRange);
						obj.ZoomRange = range;
						obj.createPlot(datasets);
					}
				} else if (obj.Options.editable) {
					//select ion
					console.log(range.x, range.y);
				}
			}
		},
		grid: {
			axis: "xy",
		},
		pan: function(range, pixels, finish) {
			obj.plot.DataGroup.applyTransform({dx:-pixels.x, dy:pixels.y});
		}
	};

	this.plot = null;			// MS/MS plot
	this.ms1plot = null;		// MS1 plot (only created when data is available)
	this.ZoomRange = null; 		// for zooming MS/MS plot
	this.ms1zoomRange = null;
	this.previousPoint = null; 	// for tooltips

	this.ionSeries = {a: [], b: [], c: [], x:[], y: [], z: []};
	this.ionSeriesMatch = {a: [], b: [], c: [], x: [], y: [], z: []};
	this.ionSeriesLabels = {a: [], b: [], c: [], x: [], y: [], z: []};

	function getMaxInt(peaks) {
		var maxInt = 0;
		for (var j = 0; j < peaks.length; j += 1) {
			var peak = peaks[j];
			if (peak[1] > maxInt) {
				maxInt = peak[1];
			}
		}
		return maxInt;
	}

	/*function createMs1Plot(zoomrange) {

		var data = [{data: this.Options.ms1peaks, color: "#bbbbbb", labelType: 'none', hoverable: false, clickable: false}];
		if(this.Options.precursorPeaks) {
			if(this.Options.precursorPeakClickFn)
				data.push({data: this.Options.precursorPeaks, color: "#ff0000", hoverable: true, clickable: true});
			else
				data.push({data: this.Options.precursorPeaks, color: "#ff0000", hoverable: false, clickable: false});
		}

		// the MS/MS plot should have been created by now.  This is a hack to get the plots aligned.
		// We will set the y-axis labelWidth to this value.
		var labelWidth = plot.getAxes().yaxis.labelWidth;

		var ms1plotOptions = {
			series: { peaks: {show: true, shadowSize: 0}, shadowSize: 0},
			grid: { show: true, 
					hoverable: true, 
					autoHighlight: true,
					clickable: true,
					borderWidth: 1,
					labelMargin: 1},
			selection: { mode: "xy", color: "#F0E68C" },
			xaxis: { tickLength: 2, tickColor: "#000" },
			yaxis: { tickLength: 0, tickColor: "#fff", ticks: [], labelWidth: labelWidth }
		};

		if(this.Zoomrange) {
			ms1plotOptions.xaxis.min = this.Zoomrange.xaxis.from;
			ms1plotOptions.xaxis.max = this.Zoomrange.xaxis.to;
			ms1plotOptions.yaxis.min = this.Zoomrange.yaxis.from;
			ms1plotOptions.yaxis.max = this.Zoomrange.yaxis.to;
		}

		var placeholder = container.find("#msplot");
		ms1plot = $.plot(placeholder, data, ms1plotOptions);

		// mark the current precursor peak
		if(this.Options.precursorPeaks) {
			var x,y, diff, precursorMz;

			// If we are given a precursor m/z use it
			if(this.Options.precursorMz) {
				precursorMz = this.Options.precursorMz;
			}
			// Otherwise calculate a theoretical m/z from the given sequence and charge
			else if(this.Options.sequence && this.Options.charge) {
				var mass = Peptide.getNeutralMassMono();
				precursorMz = Ion.getMz(mass, this.Options.charge);
			}

			if(precursorMz) {
				// find the closest actual peak
				for(var i = 0; i < this.Options.precursorPeaks.length; i += 1) {
					var pk = this.Options.precursorPeaks[i];
					var d = Math.abs(pk[0] - precursorMz);
					if(!diff || d < diff) {
						x = pk[0];
						y = pk[1];
						diff = d;
					}
				}
				if(diff <= 0.5) {
					var o = this.ms1plot.pointOffset({ x: x, y: y});
					var ctx = this.ms1plot.getCanvas().getContext("2d");
					ctx.beginPath();
					ctx.moveTo(o.left-10, o.top-5);
					ctx.lineTo(o.left-10, o.top + 5);
					ctx.lineTo(o.left-10 + 10, o.top);
					ctx.lineTo(o.left-10, o.top-5);
					ctx.fillStyle = "#008800";
					ctx.fill();
					placeholder.append('<div style="position:absolute;left:' + (o.left + 4) + 'px;top:' + (o.top-4) + 'px;color:#000;font-size:smaller">'+x.toFixed(2)+'</div>');
				}
			}
		}

		// mark the scan number if we have it
		o = this.ms1plot.getPlotOffset();
		if(this.Options.ms1scanLabel) {
			placeholder.append('<div style="position:absolute;left:' + (o.left + 4) + 'px;top:' + (o.top+4) + 'px;color:#666;font-size:smaller">MS1 scan: '+this.Options.ms1scanLabel+'</div>');
		}

		// zoom out icon on plot right hand corner
		if(this.Zoomrange) {
			placeholder.append('<div id="ms1plot_zoom_out" class="zoom_out_link"  style="position:absolute; left:' + (o.left + ms1plot.width() - 40) + 'px;top:' + (o.top+4) + 'px;"></div>');
			$("#ms1plot_zoom_out").click( function() {
				ms1zoomRange = null;
				createMs1Plot();
			});
		}

		if(this.Options.precursorPeaks) {
			placeholder.append('<div id="ms1plot_zoom_in" class="zoom_in_link"  style="position:absolute; left:' + (o.left + ms1plot.width() - 20) + 'px;top:' + (o.top+4) + 'px;"></div>');
			$("#ms1plot_zoom_in").click( function() {
				var ranges = {};
				ranges.yaxis = {};
				ranges.xaxis = {};
				ranges.yaxis.from = null;
				ranges.yaxis.to = null;
				ranges.xaxis.from = null;
				ranges.xaxis.to = null;
				var maxInt = 0;
				for(var p = 0; p < this.Options.precursorPeaks.length; p += 1) {
					if(this.Options.precursorPeaks[p][1] > maxInt)
						maxInt = this.Options.precursorPeaks[p][1];
				}
				ranges.yaxis.to = maxInt;
				createMs1Plot(ranges);
			});
		}
	}

	function setupMs1PlotInteractions() {

		var placeholder = container.find("#msplot");


		// allow clicking on plot if we have a function to handle the click
		if(this.Options.precursorPeakClickFn != null) {
			placeholder.bind("plotclick", function (event, pos, item) {

			   if (item) {
				//highlight(item.series, item.datapoint);
			   	this.Options.precursorPeakClickFn(item.datapoint[0]);
			   }
			});
		}

		// allow zooming the plot
		placeholder.bind("plotselected", function (event, ranges) {
			createMs1Plot(ranges);
			ms1zoomRange = ranges;
		});

	}*/

	this.createPlot = function(datasets) {
		var maxInt = 0;
		for (var i in datasets) {
			var d = datasets[i];
			var n = getMaxInt(d.data);
			if (n > maxInt) {
				maxInt = n;
			}
		}
	   	if(this.plot) {
	   		this.plot.Destroy();
	   	}
		if(!this.ZoomRange) {
			this.plot = new MsPlot(this.Container, datasets, this.PlotOptions);
		} else {
			var selectOpts = {};
			var po = dojo.clone(this.PlotOptions);
			if(po.selection.axis.indexOf("x") >= 0)
				po.axis.x = dojo.mixin(po.axis.x, this.ZoomRange.x);
			//if(po.selection.axis.indexOf("y") >= 0)
				po.axis.y = dojo.mixin(po.axis.y, this.ZoomRange.y);
			this.plot = new MsPlot(this.Container, datasets, po);

			// zoom out icon on plot right hand corner
			/*var o = this.plot.getPlotOffset();
			container.find("#msmsplot").append('<div id="ms2plot_zoom_out" class="zoom_out_link" style="position:absolute; left:' + (o.left + this.plot.width() - 20) + 'px;top:' + (o.top+4) + 'px"></div>');
			$("#ms2plot_zoom_out").click( function() {
				this.ResetZoom();
			});*/
		}
		// we have re-calculated and re-drawn everything..
		this.massTypeChanged = false;
		this.massErrorChanged = false;
		this.peakAssignmentTypeChanged = false;
		this.peakLabelTypeChanged = false;
		this.selectedNeutralLossChanged = false;
	}

	this.plotAccordingToChoices = function() {
		var data = this.getDatasets();
		if (data.length > 0) {
			this.makeIonTable();
			this.createPlot(data);
		}
	}

	// -----------------------------------------------
	// SELECTED DATASETS
	// -----------------------------------------------
	this.getDatasets = function() {
		function calculateTheoreticalSeries(selectedIons) {
			if(selectedIons) {
				var todoIonSeries = [];
				var todoIonSeriesData = [];
				for (var i = 0; i < selectedIons.length; i += 1) {
					var sion = selectedIons[i];
					if (!obj.massTypeChanged && obj.ionSeries[sion.type][sion.charge]) {
						continue; // already calculated
					} else {
						todoIonSeries.push(sion);
						obj.ionSeries[sion.type][sion.charge] = [];
						todoIonSeriesData.push(obj.ionSeries[sion.type][sion.charge]);
					}
				}
				if (obj.Options.sequence) {
					var massType = obj.Options.massTypeOpt;
					for (var i = 1; i < obj.Options.sequence.length; i += 1) {
						for (var j = 0; j < todoIonSeries.length; j += 1) {
							var tion = todoIonSeries[j];
							if (tion.term == "n")
								todoIonSeriesData[j].push(Ion.getSeriesIon(tion, obj.Options.sequence, i, massType));
							else if (tion.term == "c")
								todoIonSeriesData[j].unshift(Ion.getSeriesIon(tion, obj.Options.sequence, i, massType));
						}
					}
				}
			}
		}

		function calculateMatchingPeaks(ionSeries, allPeaks, massTolerance, peakAssignmentType) {
			var peakIndex = 0;
			var matchData = [];
			matchData[0] = []; // peaks
			matchData[1] = []; // labels -- ions;

			// sion -- theoretical ion
			// Returns the index of the matching peak, if one is found
			function getMatchForIon(sion, neutralLoss) {

				var bestPeak = null;
				if(!neutralLoss)
					sion.match = false; // reset;
				var ionmz;
				if(!neutralLoss)
					ionmz = sion.mz;
				else if(neutralLoss == 'h2o') {
					ionmz = Ion.getWaterLossMz(sion);
				} else if(neutralLoss = 'nh3') {
					ionmz = Ion.getAmmoniaLossMz(sion);
				}
				var bestDistance;

				for(var j = peakIndex; j < allPeaks.length; j += 1) {

					var peak = allPeaks[j];

					// peak is before the current ion we are looking at
					if(peak[0] < ionmz - massTolerance)
						continue;

					// peak is beyond the current ion we are looking at
					if(peak[0] > ionmz + massTolerance) {

						// if we found a matching peak for the current ion, save it
						if(bestPeak) {
							//console.log("found match "+sion.label+", "+ionmz+";  peak: "+bestPeak[0]);
							matchData[0].push([bestPeak[0], bestPeak[1]]);
							if(!neutralLoss) {
								matchData[1].push(sion.label);
								sion.match = true;
							} else if(neutralLoss == 'h2o') {
								matchData[1].push(sion.label+'o');
							} else if(neutralLoss = 'nh3') {
								matchData[1].push(sion.label+'*');
							}
						}
						peakIndex = j;
						break;
					}

					// peak is within +/- massTolerance of the current ion we are looking at

					// if this is the first peak in the range
					if(!bestPeak) {
						//console.log("found a peak in range, "+peak.mz);
						bestPeak = peak;
						bestDistance = Math.abs(ionmz - peak[0]);
						continue;
					}

					// if peak assignment method is Most Intense
					if(peakAssignmentType == "intense") {
						if(peak[1] > bestPeak[1]) {
							bestPeak = peak;
							continue;
						}
					}

					// if peak assignment method is Closest Peak
					if(peakAssignmentType == "close") {
						var dist = Math.abs(ionmz - peak[0]);
						if(!bestDistance || dist < bestDistance) {
							bestPeak = peak;
							bestDistance = dist;
						}
					}
				}
				return peakIndex;
			}

			for(var i = 0; i < ionSeries.length; i += 1) {
				var sion = ionSeries[i];
				// get match for water and or ammonia loss
				for(var n = 0; n < obj.Options.neutralLosses.length; ++n) {
					getMatchForIon(sion, obj.Options.neutralLosses[n]);
				}
				// get match for the ion
				peakIndex = getMatchForIon(sion);
			}

			return matchData;
		}

		function getSeriesMatches(selectedIonTypes) {
			var dataSeries = [];
			for(var j = 0; j < selectedIonTypes.length; ++j) {
				var ion = selectedIonTypes[j];
				if(obj.massErrorChanged || obj.massTypeChanged || obj.peakAssignmentTypeChanged || obj.selectedNeutralLossChanged || !obj.ionSeriesMatch[ion.type][ion.charge]) { // re-calculate only if mass error has changed OR  matching peaks for this series have not been calculated
					// calculated matching peaks
					var data = calculateMatchingPeaks(obj.ionSeries[ion.type][ion.charge], obj.Options.peaks, obj.Options.massError, obj.Options.peakAssignmentType);
					if(data && data.length > 0) {
						obj.ionSeriesMatch[ion.type][ion.charge] = data[0];
						obj.ionSeriesLabels[ion.type][ion.charge] = data[1];
					}
				}
				var labels = null;
				if (obj.Options.peakLabelType == "ion") {
					labels = obj.ionSeriesLabels[ion.type][ion.charge];
				} else if (obj.Options.peakLabelType == "mz") {
					var series = obj.ionSeriesMatch[ion.type][ion.charge];
					labels = new Array(series.length);
					for (i in series) {
						labels[i] = series[i][0].toFixed(2);
					}
				}
				dataSeries.push({data: obj.ionSeriesMatch[ion.type][ion.charge], color: ion.color, labels: labels});
			}
			return dataSeries;
		}

		function filterPeaks(peaks) {
			if (obj.Options.precursorMz && obj.Options.hidePrecursor) {
				var pks = peaks.slice(0);
				for (var i = pks.length - 1; i >= 0; --i) {
					var p = pks[i];
					if (p[0] >= obj.Options.precursorMz - obj.Options.massError * 2) {
						pks.splice(i, 1);
					}
				}
				return pks;
			}
			return peaks;
		}

		// selected ions
		calculateTheoreticalSeries(this.Options.selectedIons);

		// add the un-annotated peaks
		var data = [{data: filterPeaks(this.Options.peaks), color: "#bbbbbb"}];

		// add the annotated peaks
		var seriesMatches = getSeriesMatches(this.Options.selectedIons);
		for(var i = 0; i < seriesMatches.length; i += 1) {
			data.push(seriesMatches[i]);
		}

		// add any user specified extra peaks
		for(var i = 0; i < this.Options.extraPeakSeries.length; i += 1) {
			data.push(this.Options.extraPeakSeries[i]);
		}
		return data;
	}

	this.ResetZoom = function() {
		if (this.ZoomRange != null) {
			ZoomHistory.push(this.plot.ViewRange);
			this.ZoomRange = null;
			this.massErrorChanged = false;
			this.createPlot(this.getDatasets());
		}
	}

	this.UndoZoom = function() {
		if (ZoomHistory.length) {
			this.ZoomRange = ZoomHistory.pop();
			this.massErrorChanged = false;
			this.createPlot(this.getDatasets());
		}
	}

	this.SetAxisZoom = function(axis) {
		this.PlotOptions.selection.axis = axis;
		if (this.plot) {
			this.plot.SetSelection(axis);
		}
	}

	this.SetTooltip = function(show) {
		this.PlotOptions.tooltip.enable = show;
		if (this.plot) {
			this.plot.SetTooltip(show);
		}
	}

	this.SetGrid = function(axis, color) {
		if (axis != undefined) {
			this.PlotOptions.grid.axis = axis;
		}
		if (color != undefined) {
			this.PlotOptions.grid.color = color;
		}
		if (this.plot) {
			this.plot.SetGrid(axis, color);
		}
	}

	this.SetMassError = function(tol, match) {
		//this.ZoomRange = null; // zoom out fully
		if (tol != this.Options.massError) {
			this.Options.massError = tol;
			this.massErrorChanged = true;
		}
		this.Options.massTypeOpt = match;
		var ds = this.getDatasets();
		this.makeIonTable();
		this.createPlot(ds);
	}

	this.SetSelectedIons = function(ions /* [[ion, charge], ... */) {
		var selected = []
		for (i in ions) {
			selected.push(Ion.get(ions[i][0], ions[i][1]));
		}
		this.Options.selectedIons = selected;
		this.plotAccordingToChoices();
	}

	this.SetNeutralLosses = function(losses) {
		this.Options.neutralLosses = losses;
		this.selectedNeutralLossChanged = true;
		this.plotAccordingToChoices();
	}

	this.SetHidePrecursor = function(hide) {
		this.Options.hidePrecursor = hide;
		this.plotAccordingToChoices();
	}

	this.SetPeakAssignmentType = function(type) {
		this.Options.peakAssignmentType = type;
		this.peakAssignmentTypeChanged = true;
		this.plotAccordingToChoices();
	}

	this.SetPeakLabelType = function(type) {
		this.Options.peakLabelType = type;
		this.peakLabelTypeChanged = true;
		this.plotAccordingToChoices();
	}

	this.SetPeptide = function(opts) {
		var none = {
			sequence: null,
			staticMods: [],
			variableMods: [],
			ntermMod: 0,
			ctermMod: 0
		};
		dojo.mixin(this.Options, none, opts);
		//FIXME: update everything
		this.massTypeChanged = true;
		var ds = this.getDatasets();
		this.makeIonTable();
		this.createPlot(ds);
	}

	//---------------------------------------------------------
	// ION TABLE
	//---------------------------------------------------------
	this.makeIonTable = function() {
		if (this.Options.sequence) {
			function getSelectedIons(selectedIonTypes, term) {
				var ions = [];
				for(var i = 0; i < selectedIonTypes.length; i += 1) {
					var sion = selectedIonTypes[i];
					if((term == 'n' && (sion.type == "a" || sion.type == "b" || sion.type == "c")) || (term == 'c' && (sion.type == "x" || sion.type == "y" || sion.type == "z"))) {
						ions.push(sion);
					}
				}
				ions.sort(function(m,n) {
					return m.type == n.type ? m.charge - n.charge : m.type - n.type;
				});
				return ions;
			}

			function getCalculatedSeries(ion) {
				return obj.ionSeries[ion.type][ion.charge];
			}

			function round(number) {
				return number.toFixed(4);
			}

			if (this.Options.ionTableContainer) {
			 	// selected ions
				var ntermIons = getSelectedIons(this.Options.selectedIons, 'n');
				var ctermIons = getSelectedIons(this.Options.selectedIons, 'c');

				var myTable = '<table id="ionTable" cellpadding="2" class="font_small">';
				myTable += "<thead>";
				myTable += "<tr>";
				// nterm ions
				for(var i = 0; i < ntermIons.length; i += 1) {
					myTable += "<th>" +ntermIons[i].label+  "</th>";   
				}
				myTable += "<th>#</th>"; 
				myTable += "<th>Seq</th>"; 
				myTable += "<th>#</th>"; 
				// cterm ions
				for(var i = 0; i < ctermIons.length; i += 1) {
					myTable += "<th>" +ctermIons[i].label+  "</th>"; 
				}
				myTable += "</tr>";
				myTable += "</thead>";

				myTable += "<tbody>";
				for(var i = 0; i < this.Options.sequence.length; i += 1) {
					myTable +=   "<tr>";

					// nterm ions
					for(var n = 0; n < ntermIons.length; n += 1) {
						if(i < this.Options.sequence.length - 1) {
							var seriesData = getCalculatedSeries(ntermIons[n]);
							var cls = "";
							var style = "";
							if(seriesData[i].match) {
								cls="matchIon";
								style="style='background-color:"+Ion.getSeriesColor(ntermIons[n])+";'";
							}
							myTable += "<td class='"+cls+"' "+style+" >" +round(seriesData[i].mz)+  "</td>";  
						}
						else {
							myTable += "<td>&nbsp;</td>"; 
						} 
					}

					myTable += "<td class='numCell'>"+(i+1)+"</td>";
					if(Peptide.varMods[i+1])
						myTable += "<td class='seq modified'>"+this.Options.sequence[i]+"</td>";
					else
						myTable += "<td class='seq'>"+this.Options.sequence[i]+"</td>";
					myTable += "<td class='numCell'>"+(this.Options.sequence.length - i)+"</td>";

					// cterm ions
					for(var c = 0; c < ctermIons.length; c += 1) {
						if(i > 0) {
							var seriesData = getCalculatedSeries(ctermIons[c]);
							var idx = this.Options.sequence.length - i - 1;
							var cls = "";
							var style = "";
							if(seriesData[idx].match) {
								cls="matchIon";
								style="style='background-color:"+Ion.getSeriesColor(ctermIons[c])+";'";
							}
							myTable += "<td class='"+cls+"' "+style+" >" +round(seriesData[idx].mz)+"</td>";  
						}
						else {
							myTable += "<td>" +"&nbsp;"+  "</td>"; 
						} 
					}

				}
				myTable += "</tr>";

				myTable += "</tbody>";
				myTable += "</table>";

				this.Options.ionTableContainer.innerHTML = myTable;
			}
		}
	}

	this.showModInfo = function() {
		if (this.ModInfoContainer) {
			var modInfo = '<div>';
			if(this.Options.ntermMod || this.Options.ntermMod > 0) {
				modInfo += 'Add to N-term: <b>'+this.Options.ntermMod+'</b>';
			}
			if(this.Options.ctermMod || this.Options.ctermMod > 0) {
				modInfo += 'Add to C-term: <b>'+this.Options.ctermMod+'</b>';
			}
			modInfo += '</div>';

			if(this.Options.staticMods && this.Options.staticMods.length > 0) {
				modInfo += '<div style="margin-top:5px;">';
				modInfo += 'Static Modifications: ';
				for(var i = 0; i < this.Options.staticMods.length; i += 1) {
					var mod = this.Options.staticMods[i];
					//if(i > 0) modInfo += ', ';
					modInfo += "<div><b>"+mod.aa.code+": "+mod.modMass+"</b></div>";
				}
				modInfo += '</div>';
			}

			if(this.Options.variableMods && this.Options.variableMods.length > 0) {
				var modChars = [];
				var uniqvarmods = [];
				for(var i = 0; i < this.Options.variableMods.length; i += 1) {
					var mod = this.Options.variableMods[i];
					if(modChars[mod.aa.code])
						continue;
					modChars[mod.aa.code] = 1;
					uniqvarmods.push(mod);
				}  

				modInfo += '<div style="margin-top:5px;">';
				modInfo += 'Variable Modifications: ';
				for(var i = 0; i < uniqvarmods.length; i += 1) {
					var mod = uniqvarmods[i];
					modInfo += "<div><b>"+mod.aa.code+": "+mod.modMass+"</b></div>";
				}
				modInfo += '</div>';
			}

			this.ModInfoContainer.innerHTML = modInfo;
		}
	}

	// read the static modifications
	var parsedMods = [];
	for(var i = 0; i < this.Options.staticMods.length; i += 1) {
		var mod = this.Options.staticMods[i];
		parsedMods[i] = new Modification(AminoAcid.get(mod.aminoAcid), mod.modMass);
	}
	this.Options.staticMods = parsedMods;

	// read the variable modifications
	var parsedMods = [];
	for(var i = 0; i < this.Options.variableMods.length; i += 1) {
		var mod = this.Options.variableMods[i];
		parsedMods[i] = new VariableModification(mod.index, mod.modMass, AminoAcid.get(mod.aminoAcid));
	}
	this.Options.variableMods = parsedMods;

	var input = new Peptide(this.Options.sequence, this.Options.staticMods, this.Options.variableMods, this.Options.ntermMod, this.Options.ctermMod);

	this.showModInfo();


	var ds = this.getDatasets();
	this.makeIonTable();
	this.createPlot(ds); // Initial MS/MS Plot
	/*if(this.Options.ms1peaks && this.Options.ms1peaks.length > 0) {
		if(this.Options.zoomMs1 && this.Options.precursorMz) {
			this.ms1zoomRange = {xaxis: {}, yaxis: {}};
			this.ms1zoomRange.xaxis.from = this.Options.precursorMz - 5.0;
			this.ms1zoomRange.xaxis.to = this.Options.precursorMz + 5.0;
			var max_intensity = 0;
			for(var j = 0; j < this.Options.ms1peaks.length; j += 1) {
				var pk = this.Options.ms1peaks[j];
				if(pk[0] < this.Options.precursorMz - 5.0)
					continue;
				if(pk[0] > this.Options.precursorMz + 5.0)
					break;
				if(pk[1] > max_intensity)
					max_intensity = pk[1];
			}
			this.ms1zoomRange.yaxis.from = 0.0;
			this.ms1zoomRange.yaxis.to = max_intensity;
		}
		createMs1Plot(this.ms1zoomRange);
		setupMs1PlotInteractions();
	}*/
	//setupInteractions();
}

//Amino Acids
function AminoAcid(aaCode, aaShortName, aaName, monoMass, avgMass) {
   this.code = aaCode;
   this.shortName = aaShortName;
   this.name = aaName;
   this.mono = monoMass;
   this.avg = avgMass;
}

AminoAcid.A = new AminoAcid("A", "Ala", "Alanine",        71.037113805,  71.07790);
AminoAcid.R = new AminoAcid("R", "Arg", "Arginine",      156.101111050, 156.18568);
AminoAcid.N = new AminoAcid("N", "Asn", "Asparagine",    114.042927470, 114.10264);
AminoAcid.D = new AminoAcid("D", "Asp", "Aspartic Acid", 115.026943065, 115.08740);
AminoAcid.C = new AminoAcid("C", "Cys", "Cysteine",      103.009184505, 103.14290);
AminoAcid.E = new AminoAcid("E", "Glu", "Glutamine",     129.042593135, 129.11398);
AminoAcid.Q = new AminoAcid("Q", "Gln", "Glutamic Acid", 128.058577540, 128.12922);
AminoAcid.G = new AminoAcid("G", "Gly", "Glycine",        57.021463735,  57.05132);
AminoAcid.H = new AminoAcid("H", "His", "Histidine",     137.058911875, 137.13928);
AminoAcid.I = new AminoAcid("I", "Ile", "Isoleucine",    113.084064015, 113.15764);
AminoAcid.L = new AminoAcid("L", "Leu", "Leucine",       113.084064015, 113.15764);
AminoAcid.K = new AminoAcid("K", "Lys", "Lysine",        128.094963050, 128.17228);
AminoAcid.M = new AminoAcid("M", "Met", "Methionine",    131.040484645, 131.19606);
AminoAcid.F = new AminoAcid("F", "Phe", "Phenylalanine", 147.068413945, 147.17386);
AminoAcid.P = new AminoAcid("P", "Pro", "Proline",        97.052763875,  97.11518);
AminoAcid.S = new AminoAcid("S", "Ser", "Serine",         87.032028435,  87.07730);
AminoAcid.T = new AminoAcid("T", "Thr", "Threonine",     101.047678505, 101.10388);
AminoAcid.W = new AminoAcid("W", "Trp", "Tryptophan",    186.079312980, 186.20990);
AminoAcid.Y = new AminoAcid("Y", "Tyr", "Tyrosine",      163.063328575, 163.17326);
AminoAcid.V = new AminoAcid("V", "Val", "Valine",         99.068413945,  99.13106);

AminoAcid.get = function(aaCode) {
   return AminoAcid[aaCode] || new AminoAcid(aaCode, aaCode, 0.0, 0.0);
}

//Peptides
Peptide.sequence;
Peptide.staticMods;
Peptide.varMods;
Peptide.ntermMod;
Peptide.ctermMod;

function Peptide(seq, staticModifications, varModifications, ntermModification, ctermModification) {
	Peptide.sequence = seq;
	Peptide.ntermMod = ntermModification;
	Peptide.ctermMod = ctermModification;
	Peptide.staticMods = [];
	if(staticModifications) {
		for(var i = 0; i < staticModifications.length; i += 1) {
			var mod = staticModifications[i];
			Peptide.staticMods[mod.aa.code] = mod;
		}
	}

	Peptide.varMods = [];
	if(varModifications) {
		for(var i = 0; i < varModifications.length; i += 1) {
			var mod = varModifications[i];
			Peptide.varMods[mod.position] = mod;
		}
	}
}


// index: index in the seq.
// If this is a N-term sequence we will sum up the mass of the amino acids in the sequence up-to index (exclusive).
// If this is a C-term sequence we will sum up the mass of the amino acids in the sequence starting from index (inclusive)
// modification masses are added
Peptide.getSeqMassMono = function _seqMassMono(seq, index, term) {
	var mass = 0;
	if(seq) {
		if(term == "n") {
			for( var i = 0; i < index; i += 1) {
				var aa = AminoAcid.get(seq[i]);
				mass += aa.mono;
			}
		}
		if (term == "c") {
			for( var i = index; i < seq.length; i += 1) {
				var aa = AminoAcid.get(seq[i]);
				mass += aa.mono;
			}
		}
	}

	mass = _addTerminalModMass(mass, term);
	mass = _addResidueModMasses(mass, seq, index, term);
	return mass;
}

// index: index in the seq.
// If this is a N-term sequence we will sum up the mass of the amino acids in the sequence up-to index (exclusive).
// If this is a C-term sequence we will sum up the mass of the amino acids in the sequence starting from index (inclusive)
// modification masses are added
Peptide.getSeqMassAvg = function _seqMassAvg(seq, index, term) {
	var mass = 0;
	if(seq) {
		if(term == "n") {
			for( var i = 0; i < index; i += 1) {
				var aa = AminoAcid.get(seq[i]);
				mass += aa.avg;
			}
		}
		if (term == "c") {
			for( var i = index; i < seq.length; i += 1) {
				var aa = AminoAcid.get(seq[i]);
				mass += aa.avg;
			}
		}
	}

	mass = _addTerminalModMass(mass, term);
	mass = _addResidueModMasses(mass, seq, index, term);
	return mass;
}

// Returns the monoisotopic neutral mass of the peptide; modifications added. N-term H and C-term OH are added
Peptide.getNeutralMassMono = function _massNeutralMono() {
	var mass = 0;
	if(Peptide.sequence) {
		for(var i = 0; i < Peptide.sequence.length; i++) {
			var aa = AminoAcid.get(Peptide.sequence[i]);
			mass += aa.mono;
		}
	}

	mass = _addTerminalModMass(mass, "n");
	mass = _addTerminalModMass(mass, "c");
	mass = _addResidueModMasses(mass, Peptide.sequence, Peptide.sequence.length, "n");
	// add N-terminal H
	mass = mass + Ion.MASS_H_1;
	// add C-terminal OH
	mass = mass + Ion.MASS_O_16 + Ion.MASS_H_1;

	return mass;
}

//Returns the avg neutral mass of the peptide; modifications added. N-term H and C-term OH are added
Peptide.getNeutralMassAvg = function _massNeutralAvg() {
	var mass = 0;
	if(Peptide.sequence) {
		for(var i = 0; i < Peptide.sequence.length; i++) {
			var aa = AminoAcid.get(Peptide.sequence[i]);
			mass += aa.avg;
		}
	}

	mass = _addTerminalModMass(mass, "n");
	mass = _addTerminalModMass(mass, "c");
	mass = _addResidueModMasses(mass, Peptide.sequence, Peptide.sequence.length, "n");
	// add N-terminal H
	mass = mass + Ion.MASS_H;
	// add C-terminal OH
	mass = mass + Ion.MASS_O + Ion.MASS_H;

	return mass;
}

function _addResidueModMasses(seqMass, seq, index, term) {
	var mass = seqMass;

	// add any static modifications
	if(term == "n") {
		for(var i = 0; i < index; i += 1) {
			var mod = Peptide.staticMods[seq[i]];
			if(mod) {
				mass += mod.modMass;
			}
		}
	}
	if(term == "c") {
		for(var i = index; i < seq.length; i += 1) {
			var mod = Peptide.staticMods[seq[i]];
			if(mod) {
				mass += mod.modMass;
			}
		}
	}

	// add any variable modifications
	if(term == "n") {
		for(var i = 0; i < index; i += 1) {
			var mod = Peptide.varMods[i+1]; // varMods index in the sequence is 1-based
			if(mod) {
				mass += mod.modMass;
			}
		}
	}
	if(term == "c") {
		for(var i = index; i < seq.length; i += 1) {
			var mod = Peptide.varMods[i+1]; // varMods index in the sequence is 1-based
			if(mod) {
				mass += mod.modMass;
			}
		}
	}
	return mass;
}

function _addTerminalModMass(seqMass, term) {
	var mass = seqMass;
	// add any terminal modifications
	if(term == "n" && Peptide.ntermMod)
		mass += Peptide.ntermMod;
	if(term == "c" && Peptide.ctermMod)
		mass += Peptide.ctermMod;

	return mass;
}

function Modification(aminoAcid, mass) {
	this.aa = aminoAcid;
	this.modMass = mass;
}

function VariableModification(pos, mass, aminoAcid) {
	this.position = parseInt(pos);
	this.aa = aminoAcid;
	this.modMass = mass;
}

//Ions
function Ion (t, color, charge, terminus) {
	this.type = t;
	this.color = color;
	this.charge = charge;
	this.label = this.type;
	if(this.charge > 1)
		this.label += charge;
	this.label += "+";
	this.term = terminus;
}

// Source: http://en.wikipedia.org/wiki/Web_colors

// charge +1
Ion.A_1 = new Ion("a", "#008000", 1, "n"); // green
Ion.B_1 = new Ion("b", "#0000ff", 1, "n"); // blue
Ion.C_1 = new Ion("c", "#008B8B", 1, "n"); // dark cyan
Ion.X_1 = new Ion("x", "#4B0082", 1, "c"); // indigo
Ion.Y_1 = new Ion("y", "#ff0000", 1, "c"); // red
Ion.Z_1 = new Ion("z", "#FF8C00", 1, "c"); // dark orange

// charge +2
Ion.A_2 = new Ion("a", "#2E8B57", 2, "n"); // sea green
Ion.B_2 = new Ion("b", "#4169E1", 2, "n"); // royal blue
Ion.C_2 = new Ion("c", "#20B2AA", 2, "n"); // light sea green
Ion.X_2 = new Ion("x", "#800080", 2, "c"); // purple
Ion.Y_2 = new Ion("y", "#FA8072", 2, "c"); // salmon 
Ion.Z_2 = new Ion("z", "#FFA500", 2, "c"); // orange 

// charge +3
Ion.A_3 = new Ion("a", "#9ACD32", 3, "n"); // yellow green
Ion.B_3 = new Ion("b", "#00BFFF", 3, "n"); // deep sky blue
Ion.C_3 = new Ion("c", "#66CDAA", 3, "c"); // medium aquamarine
Ion.X_3 = new Ion("x", "#9932CC", 3, "c"); // dark orchid
Ion.Y_3 = new Ion("y", "#FFA07A", 3, "c"); // light salmon
Ion.Z_3 = new Ion("z", "#FFD700", 3, "n"); // gold

var _ions = [];
_ions["a"] = [];
_ions["a"][1] = Ion.A_1;
_ions["a"][2] = Ion.A_2;
_ions["a"][3] = Ion.A_3;
_ions["b"] = [];
_ions["b"][1] = Ion.B_1;
_ions["b"][2] = Ion.B_2;
_ions["b"][3] = Ion.B_3;
_ions["c"] = [];
_ions["c"][1] = Ion.C_1;
_ions["c"][2] = Ion.C_2;
_ions["c"][3] = Ion.C_3;
_ions["x"] = [];
_ions["x"][1] = Ion.X_1;
_ions["x"][2] = Ion.X_2;
_ions["x"][3] = Ion.X_3;
_ions["y"] = [];
_ions["y"][1] = Ion.Y_1;
_ions["y"][2] = Ion.Y_2;
_ions["y"][3] = Ion.Y_3;
_ions["z"] = [];
_ions["z"][1] = Ion.Z_1;
_ions["z"][2] = Ion.Z_2;
_ions["z"][3] = Ion.Z_3;

Ion.get = function _getIon(type, charge) {

	return _ions[type][charge];
}

Ion.getSeriesColor = function _getSeriesColor(ion) {

	return _ions[ion.type][ion.charge].color;
}


//-----------------------------------------------------------------------------
// Ion Series
//-----------------------------------------------------------------------------
var MASS_H_1 = 1.00782503207;  	// H(1)  Source: http://en.wikipedia.org/wiki/Isotopes_of_hydrogen
var MASS_C_12 = 12.0;           // C(12) Source: http://en.wikipedia.org/wiki/Isotopes_of_carbon
var MASS_N_14 = 14.0030740048;  // N(14) Source: http://en.wikipedia.org/wiki/Isotopes_of_nitrogen
var MASS_O_16 = 15.99491461956; // O(16) Source: http://en.wikipedia.org/wiki/Isotopes_of_oxygen

var MASS_H = 1.00782504; // Source: http://en.wikipedia.org/wiki/Isotopes_of_hydrogen
var MASS_C = 12.0107;    // Source: http://en.wikipedia.org/wiki/Isotopes_of_carbon
var MASS_N = 14.0067;	 // Source: http://en.wikipedia.org/wiki/Isotopes_of_nitrogen
var MASS_O = 15.9994;	 // Source: http://en.wikipedia.org/wiki/Isotopes_of_oxygen

var MASS_PROTON = 1.007276;

Ion.MASS_PROTON = MASS_PROTON;
Ion.MASS_H = MASS_H;
Ion.MASS_C = MASS_C;
Ion.MASS_N = MASS_N;
Ion.MASS_O = MASS_O;
Ion.MASS_H_1 = MASS_H_1;
Ion.MASS_C_12 = MASS_C_12;
Ion.MASS_N_14 = MASS_N_14;
Ion.MASS_O_16 = MASS_O_16;

// massType can be "mono" or "avg"
Ion.getSeriesIon = function _getSeriesIon(ion, sequence, idxInSeq, massType) {
	if(ion.type == "a")
		return new Ion_A (sequence, idxInSeq, ion.charge, massType);
	if(ion.type == "b")
		return new Ion_B (sequence, idxInSeq, ion.charge, massType);
	if(ion.type == "c")
		return new Ion_C (sequence, idxInSeq, ion.charge, massType);
	if(ion.type == "x")
		return new Ion_X (sequence, idxInSeq, ion.charge, massType);
	if(ion.type == "y")
		return new Ion_Y (sequence, idxInSeq, ion.charge, massType);
	if(ion.type == "z")
		return new Ion_Z (sequence, idxInSeq, ion.charge, massType);
}

function _makeIonLabel(type, index, charge) {
	var label = type+""+index;
	for(var i = 1; i <= charge; i+=1) 
		label += "+";
	return label;
}

function _getMz(neutralMass, charge) {
	return ( neutralMass + (charge * MASS_PROTON) ) / charge;
}

function _getWaterLossMz(sion) {
	var neutralMass = (sion.mz * sion.charge) - (sion.charge * MASS_PROTON);
	return _getMz((neutralMass - (MASS_H * 2 + MASS_O)), sion.charge);
}

function _getAmmoniaLossMz(sion) {
	var neutralMass = (sion.mz * sion.charge) - (sion.charge * MASS_PROTON);
	return _getMz((neutralMass - (MASS_H * 3 + MASS_N)), sion.charge);
}

Ion.getMz = _getMz;
Ion.getWaterLossMz = _getWaterLossMz;
Ion.getAmmoniaLossMz = _getAmmoniaLossMz;

function Ion_A (sequence, endIdxPlusOne, charge, massType) {
	// Neutral mass:  	 [N]+[M]-CHO  ; N = mass of neutral N terminal group
	var mass = 0;
	if(massType == "mono")
		mass = Peptide.getSeqMassMono(sequence, endIdxPlusOne, "n") - (MASS_C_12 + MASS_O_16);
	else if(massType == "avg")
		mass = Peptide.getSeqMassAvg(sequence, endIdxPlusOne, "n") - (MASS_C + MASS_O);
	this.charge = charge;
	this.mz = _getMz(mass, charge);
	this.label = _makeIonLabel("a",endIdxPlusOne, charge);
	this.match = false;
	this.term = "n";
	return this;
}

function Ion_B (sequence, endIdxPlusOne, charge, massType) {
	// Neutral mass:    [N]+[M]-H  ; N = mass of neutral N terminal group
	var mass = 0;
	if(massType == "mono")
		mass = Peptide.getSeqMassMono(sequence, endIdxPlusOne, "n");
	else if(massType == "avg")
		mass = Peptide.getSeqMassAvg(sequence, endIdxPlusOne, "n");
	this.charge = charge;
	this.mz = _getMz(mass, charge);
	this.label = _makeIonLabel("b", endIdxPlusOne, charge);
	this.match = false;
	this.term = "n";
	return this;
}

function Ion_C (sequence, endIdxPlusOne, charge, massType) {
	// Neutral mass:    [N]+[M]+NH2  ; N = mass of neutral N terminal group
	var mass = 0;
	if(massType == "mono")
		mass = Peptide.getSeqMassMono(sequence, endIdxPlusOne, "n") + MASS_H_1 + (MASS_N_14 + 2*MASS_H_1);
	else if(massType == "avg")
		mass = Peptide.getSeqMassAvg(sequence, endIdxPlusOne, "n") + MASS_H + (MASS_N + 2*MASS_H);
	this.charge = charge;
	this.mz = _getMz(mass, charge);
	this.label = _makeIonLabel("c", endIdxPlusOne, charge);
	this.match = false;
	this.term = "n";
	return this;
}

function Ion_X (sequence, startIdx, charge, massType) {
	// Neutral mass = [C]+[M]+CO-H ; C = mass of neutral C-terminal group (OH)
	var mass = 0;
	if(massType == "mono")
		mass = Peptide.getSeqMassMono(sequence, startIdx, "c") + 2*MASS_O_16 + MASS_C_12;
	else if(massType == "avg")
		mass = Peptide.getSeqMassAvg(sequence, startIdx, "c") + 2*MASS_O + MASS_C;
	this.charge = charge;
	this.mz = _getMz(mass, charge);
	this.label = _makeIonLabel("x", sequence.length - startIdx, charge);
	this.match = false;
	this.term = "c";
	return this;
}

function Ion_Y (sequence, startIdx, charge, massType) {
	// Neutral mass = [C]+[M]+H ; C = mass of neutral C-terminal group (OH)
	var mass = 0;
	if(massType == "mono")
		mass = Peptide.getSeqMassMono(sequence, startIdx, "c") + 2*MASS_H_1 + MASS_O_16;
	else if(massType == "avg")
		mass = Peptide.getSeqMassAvg(sequence, startIdx, "c") + 2*MASS_H + MASS_O;
	this.charge = charge;
	this.mz = _getMz(mass, charge);
	this.label = _makeIonLabel("y", sequence.length - startIdx, charge);
	this.match = false;
	this.term = "c";
	return this;
}

function Ion_Z (sequence, startIdx, charge, massType) {
	// Neutral mass = [C]+[M]-NH2 ; C = mass of neutral C-terminal group (OH)
	// We're really printing Z-dot ions so we add an H to make it OH+[M]-NH2 +H = [M]+O-N
	var mass = 0;
	if(massType == "mono")
		mass = Peptide.getSeqMassMono(sequence, startIdx, "c") + MASS_O_16 - MASS_N_14;
	else if(massType == "avg")
		mass = Peptide.getSeqMassAvg(sequence, startIdx, "c") + MASS_O - MASS_N;
	this.charge = charge;
	this.mz = _getMz(mass, charge);
	this.label = _makeIonLabel("z", sequence.length - startIdx, charge);
	this.match = false;
	this.term = "c";
	return this;
}

//The Graph
MsPlot = function(container, data, opts) {
	var obj = this;

	this.DataRange = {
		x: { min:Number.POSITIVE_INFINITY, max:Number.NEGATIVE_INFINITY },
		y: { min:Number.POSITIVE_INFINITY, max:Number.NEGATIVE_INFINITY }
	};
	if (dojo.isArray(data)) {
		for (var i in data) {
			DataRange(data[i]);
		}
	} else {
		DataRange(data);
		data = [data];
	}
	
	var defaults = {
		data: {
			x: this.DataRange.x,
			y: {
				min: 0,
				max: this.DataRange.y.max * 1.1 //FIXME
			}
		},
		axis: {
			x: {
				min: this.DataRange.x.min,
				max: this.DataRange.x.max,
				label: "m/z"
			},
			y: {
				min: 0,
				max: this.DataRange.y.max * 1.1,
				label: "Intensity"
			}
		},
		tooltip: {
			show: function(evt, pt, obj) {
				var closest = {i:-1, j:-1, dist:Number.POSITIVE_INFINITY};
				var m = { x: pt.x - obj.Padding[0], y: pt.y };
				for (var i in data) {
					for (var j in data[i].data) {
						var d = data[i].data[j];
						if (d[0] >= obj.ViewRange.x.min && d[0] <= obj.ViewRange.x.max && d[1] > obj.ViewRange.y.min) {
							var a = { x: (d[0] - obj.ViewRange.x.min) * obj.ScaleX, y: obj.GraphBottom - (d[1] - obj.ViewRange.y.min) * obj.ScaleY };
							if (a.y < m.y + 8) {
								var b = { x: a.x, y: obj.GraphBottom };
								var dist = Math.sqrt(Math.pow((b.y - a.y) * (m.x - a.x) + (b.x - a.x) * (m.y - a.y), 2) / (Math.pow(b.x - a.x, 2) + Math.pow(b.y - a.y, 2)));
								if (dist <= closest.dist) {
									closest = {i:i, j:j, dist:dist};
								}
							}
						}
					}
				}
				if (closest.i >= 0 && closest.dist < 10) {
					var d = data[closest.i].data[closest.j];
					var elem = dojo.position(container, false);
					if (this.Tooltip && this.Tooltip.i == closest.i && this.Tooltip.j == closest.j) {
						_t = this.Tooltip;
						//this.Tooltip.node.style.left = Math.round((d[0] - obj.ViewRange.x.min) * obj.ScaleX + obj.Padding[0] + elem.x - 5) + "px";
						this.Tooltip.node.style.top = (evt.pageY - this.Tooltip.node.offsetHeight / 2) + "px";
					} else {
						this.Tooltip = {i:closest.i, j:closest.j, pos:{x: Math.round((d[0] - obj.ViewRange.x.min) * obj.ScaleX + obj.Padding[0] + elem.x + 5), y: evt.pageY, w: -10, h: 1}};
						dijit.Tooltip.show('<div style="white-space:nowrap;">m/z: ' + d[0].toFixed(3) + "<br/>Intensity: " + d[1].toFixed(3) + "</div>", this.Tooltip.pos, ["after", "before"], false, "ltr");
						this.Tooltip.node = dijit.Tooltip._masterTT.domNode;
						this.Tooltip.node.setAttribute("style", "pointer-events:none;" + this.Tooltip.node.getAttribute("style"));
					}
				} else {
					this.hide();
				}
			}
		}
	};
	
	MixIn(defaults, opts);
	dojo.mixin(this, new BaseGraph(container, defaults));

	function DataRange(dataset) {
		for (var i in dataset.data) {
			var d = dataset.data[i];
			obj.DataRange.x.min = Math.min(obj.DataRange.x.min, d[0]);
			obj.DataRange.x.max = Math.max(obj.DataRange.x.max, d[0]);
			obj.DataRange.y.min = Math.min(obj.DataRange.y.min, d[1]);
			obj.DataRange.y.max = Math.max(obj.DataRange.y.max, d[1]);
		}
	}

	function RenderData(data) {
		for (var i in data.data) {
			var d = data.data[i];
			//if (d[0] >= obj.ViewRange.x.min && d[0] <= obj.ViewRange.x.max && d[1] > obj.ViewRange.y.min) {
				var x = (d[0] - obj.ViewRange.x.min) * obj.ScaleX + obj.Padding[0];
				var y = obj.GraphBottom - (d[1] - obj.ViewRange.y.min) * obj.ScaleY;
				var y2 = obj.GraphBottom + obj.ViewRange.y.min * obj.ScaleY;
				/*if (y < obj.Padding[1]) {
					y = obj.Padding[1];
				}*/
				obj.DataGroup.createLine({x1:x, y1:y2, x2:x, y2:y}).setStroke({color:data.color, width:1});
			//}
		}
		//Do the labels seperate so they show ontop of the peaks
		if (data.labels) {
			var rot = dojox.gfx.matrix.rotategAt;
			for (var i in data.data) {
				var d = data.data[i];
				//if (d[0] >= obj.ViewRange.x.min && d[0] <= obj.ViewRange.x.max && d[1] > obj.ViewRange.y.min) {
					var x = (d[0] - obj.ViewRange.x.min) * obj.ScaleX + obj.Padding[0];
					var y = obj.GraphBottom - (d[1] - obj.ViewRange.y.min) * obj.ScaleY;
					/*if (y < obj.Padding[1]) {
						y = obj.Padding[1];
					}*/
					obj.DataGroup.createText({x:x, y:y, text:data.labels[i], align:"start"}).setFont({family:"Arial", size:"13px"}).setFill(data.color).setTransform(rot(270, {x:x, y:y - 4}));
				//}
			}
		}
	}
	
	this.RenderData = function() {
		if (this.DataGroup) {
			this.DataGroup.clear();
		} else {
			this.DataGroup = this.AllData.createGroup();
		}
		for (var i in data) {
			RenderData(data[i]);
		}
	}
	
	this.RecalcLayout = function() {
		this.ScaleX = this.Width / (this.ViewRange.x.max - this.ViewRange.x.min);
		this.ScaleY = this.Height / (this.ViewRange.y.max - this.ViewRange.y.min);
		this.FrameGroup.clear();
		this.RenderFrame();
		this.RenderData();
	}
	
	this.Initialise();
}
