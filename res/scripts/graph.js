dojo.require("dojo._base.connect");
dojo.require("dojo._base.event");

function MixIn(dst, src) {
	for (var p in src) {
		var o = src[p];
		if (o) {
			if (o instanceof Array) {
				dst[p] = dojo.clone(o);
			} else if (o.constructor && o.call && o.apply) {
				dst[p] = o;
			} else if (o instanceof Object) {
				if (p in dst) {
					MixIn(dst[p], o);
				} else {
					dst[p] = dojo.clone(o);
				}
			} else {
				dst[p] = o;
			}
		} else {
			dst[p] = o;
		}
	}
}

function FormatPrecision(val, precision) {
	return val.toFixed(precision < 0 ? -precision : 0);
}

BaseGraph = function(container, opts) {
	this.Options = {
		axis: {
			x: {
				format: FormatPrecision,//function(value, precision)
				scale: 1,/*,
				min: number,
				max: number,
				label: string [optional]*/
			},
			y: {
				format: FormatPrecision,//function(value, precision)
				scale: 1/*,
				min: number,
				max: number,
				label: optional*/
			},
		},
		tooltip: {
			enable: false,
			/*show: function(evt, pt, obj),*/
			hide: function() {
				if (this.Tooltip) {
					dijit.Tooltip.hide(this.Tooltip.pos);
					this.Tooltip = null;
				}
			}
		},
		grid: {
			color: "#abd6ff",//standard css color
			axis: "" //any combination of 'x', 'y'
		}/*,
		selection: {
			callback: function(isRange, range),
			data: Object [optinal],
			axis: any combination of 'x', 'y'
		},
		pan: function(range, finished)*/
	};
	
	this.Padding = [60, 10, 10, 45]; //l, t, r, b
	this.DataRange = dojo.clone(opts.data);
	this.ViewRange = {
		x: { min:opts.axis.x.min, max:opts.axis.x.max },
		y: { min:opts.axis.y.min, max:opts.axis.y.max }
	};
	if (this.ViewRange.x.max - this.ViewRange.x.min < 0.00001) {
		var mid = (this.ViewRange.x.max + this.ViewRange.x.min) / 2;
		this.ViewRange.x.min = mid - 0.000005;
		this.ViewRange.x.max = mid + 0.000005;
	}
	if (this.ViewRange.y.max - this.ViewRange.y.min < 0.00001) {
		var mid = (this.ViewRange.y.max + this.ViewRange.y.min) / 2;
		this.ViewRange.y.min = mid - 0.000005;
		this.ViewRange.y.max = mid + 0.000005;
	}
	
	this.MixInOptions = function(opts) {
		MixIn(this.Options, opts);
	}

	this.MixInOptions(opts);
	
	this.RenderData = function() {
		//called when the grap is initalised and ready to render the data
	}
	
	this.RecalcLayout = function() {
		//called when the graph is resized
	}
	
	this.RenderFrame = function() {
		function Ticks(len, spacing, view) {
			var ticks = [];
			if (len > 0) {
				var max_ticks = len / spacing;
				var range = view.max - view.min;
				var scale = 1;
				var scaleMag = 0;
				if (range > max_ticks) {
					while (true) {
						if (range > max_ticks * scale * 10) {
							scale *= 10;
							++scaleMag;
						} else if (range > max_ticks * scale * 5) {
							scale *= 5;
							break;
						} else if (range > max_ticks * scale * 4) {
							scale *= 4;
							break;
						} else if (range > max_ticks * scale * 2) {
							scale *= 2;
							break;
						} else {
							break;
						}
					}
				} else if (range < max_ticks) {
					while (true) {
						if (range < max_ticks * scale / 10) {
							--scaleMag;
							scale /= 10;
						} else if (range < max_ticks * scale / 5) {
							--scaleMag;
							scale /= 5;
							break;
						} else if (range < max_ticks * scale / 4) {
							scaleMag -= 2;
							scale /= 4;
							break;
						} else if (range < max_ticks * scale / 2) {
							--scaleMag;
							scale /= 2;
							break;
						} else {
							break;
						}
					}
				}
				var m = Math.floor(view.min / scale) * scale;
				if (view.min == m) {
					ticks.push(m);
				}
				for (var i = m + scale; i <= view.max; i += scale) {
					ticks.push(i);
				}
			}
			return {ticks:ticks, precision:scaleMag};
		}

		this.FrameGroup.clear();
		this.FrameGroup.createRect({x:this.Padding[0] - 1, y:this.Padding[1] - 1, width:this.Width + 2, height:this.Height + 2}).setFill("white").setStroke({color:"black", width:1});
		//x-axis
		var ticks = Ticks(this.Width, 100, {min: this.ViewRange.x.min * this.Options.axis.x.scale, max: this.ViewRange.x.max * this.Options.axis.x.scale});
		for (var i = 0; i < ticks.ticks.length; ++i) {
			var x = (ticks.ticks[i] - this.ViewRange.x.min * this.Options.axis.x.scale) * this.ScaleX / this.Options.axis.x.scale + this.Padding[0];
			this.FrameGroup.createLine({x1:x, y1:this.GraphBottom + 1, x2:x, y2:this.GraphBottom + 4}).setStroke({color:"black", width:1});
			this.FrameGroup.createText({x:x, y:this.GraphBottom + 16, text:this.Options.axis.x.format(ticks.ticks[i], ticks.precision), align:"middle"}).setFont({family:"Arial", size:"10px"}).setFill("black");
			if (this.Options.grid.axis.indexOf("x") >= 0) {
				this.FrameGroup.createLine({x1:x, y1:this.Padding[1], x2:x, y2:this.GraphBottom}).setStroke({color:this.Options.grid.color, width:1, style:"Dash"});
			}
		}
		if (this.Options.axis.x.label) {
			this.FrameGroup.createText({x:this.Padding[0] + this.Width / 2, y:this.GraphBottom + 35, text:this.Options.axis.x.label, align:"middle"}).setFont({family:"Arial", size:"14px", weight:"bold"}).setFill("black");
		}
		//y axis
		ticks = Ticks(this.Height, 50, {min: this.ViewRange.y.min * this.Options.axis.y.scale, max: this.ViewRange.y.max * this.Options.axis.y.scale});
		for (var i = 0; i < ticks.ticks.length; ++i) {
			var y = this.GraphBottom - (ticks.ticks[i] - this.ViewRange.y.min * this.Options.axis.y.scale) * this.ScaleY / this.Options.axis.y.scale;
			this.FrameGroup.createLine({x1:this.Padding[0] - 1, y1:y, x2:this.Padding[0] - 4, y2:y}).setStroke({color:"black", width:1});
			this.FrameGroup.createText({x:this.Padding[0] - 6, y:y + 4, text:this.Options.axis.y.format(ticks.ticks[i], ticks.precision), align:"end"}).setFont({family:"Arial", size:"10px"}).setFill("black");
			if (this.Options.grid.axis.indexOf("y") >= 0) {
				this.FrameGroup.createLine({x1:this.Padding[0], y1:y, x2:this.Padding[0] + this.Width, y2:y}).setStroke({color:this.Options.grid.color, width:1, style:"Dash"});
			}
		}
		if (this.Options.axis.y.label) {
			var y = this.Padding[1] + this.Height / 2;
			this.FrameGroup.createText({x:17, y:y, text:this.Options.axis.y.label, align:"middle"}).setFont({family:"Arial", size:"14px", weight:"bold"}).setFill("black").setTransform(dojox.gfx.matrix.rotategAt(270, {x:17, y:y}));
		}
	}
	
	this.PointOnGraph = function(e) {
		var elem = dojo.position(container, true);
		return { x:e.pageX - elem.x, y:e.pageY - elem.y };
	}

	this.PointInGraph = function(pt) {
		return pt.x >= this.Padding[0] && pt.x <= this.Width + this.Padding[0] && pt.y >= this.Padding[1] && pt.y <= this.Height + this.Padding[1];
	}

	this.SetSelection = function(axis) {
		this.Options.selection.axis = axis;
	}
	
	this.SetTooltip = function(show) {
		if (show != this.Options.tooltip.enable) {
			this.Options.tooltip.enable = show;
			if (show) {
				this.SetupTooltip();
			} else {
				dojo.disconnect(this.ToolTipMove);
				dojo.disconnect(this.ToolTipOut);
				this.ToolTipMove = null;
				this.ToolTipOut = null;
			}
		}
	}
	
	this.SetGrid = function(axis, color) {
		var changed = false;
		if (axis != undefined && axis != this.Options.grid.axis) {
			this.Options.grid.axis = axis;
			changed = true;
		}
		if (color != undefined && color != this.Options.grid.color) {
			this.Options.grid.color = color;
			changed = true;
		}
		if (changed) {
			this.RenderFrame();
		}
	}

	this.Destroy = function() {
		this.Options.tooltip.hide();
		if (this.Options.tooltip.enable) {
			dojo.disconnect(this.ToolTipMove);
			dojo.disconnect(this.ToolTipOut);
		}
		this.Surface.destroy();
	}
	
	this.SetupTooltip = function() {
		this.ToolTipMove = this.Interact.connect("onmousemove", this, function(evt) {
			if (this.DragPoint == null && this.Options.tooltip) {
				var pt = this.PointOnGraph(evt);
				if (this.PointInGraph(pt)) {
					this.Options.tooltip.show(evt, pt, this);
				} else {
					this.Options.tooltip.hide();
				}
			}
		});
		this.ToolTipOut = this.Interact.connect("onmouseout", this, function(evt) {
			this.Options.tooltip.hide();
		});
	}
	
	this.Initialise = function() {
		this.Container = container;
		var cs = window.getComputedStyle(container, null);
		var wc = container.clientWidth - parseInt(cs.getPropertyValue('padding-left')) - parseInt(cs.getPropertyValue('padding-right')) - 3;
		var hc = container.clientHeight - parseInt(cs.getPropertyValue('padding-top')) - parseInt(cs.getPropertyValue('padding-bottom'));
		this.Surface = dojox.gfx.createSurface(container, wc, hc);
		this.FrameGroup = this.Surface.createGroup();
		this.Width = wc - this.Padding[0] - this.Padding[2];
		this.Height = hc - this.Padding[1] - this.Padding[3];
		this.GraphBottom = container.clientHeight - this.Padding[3];
		this.ScaleX = this.Width / (this.ViewRange.x.max - this.ViewRange.x.min);
		this.ScaleY = this.Height / (this.ViewRange.y.max - this.ViewRange.y.min);
		this.RenderFrame();
		this.RenderData();
		this.Handlers = {}
		this.Selection = null;
		this.DragPoint = null;
		this.Overlays = this.Surface.createGroup();
		this.Interact = this.Surface.createGroup();
		this.Interact.createRect({x:0, y:0, width:wc, height:hc}).setFill("rgba(0,0,0,0)").setStroke(null);
		this.Interact.connect("onmousedown", this, function(evt) {
			dojo._base.event.stop(evt);

			var pt = this.PointOnGraph(evt);
			if (this.Options.pan && (evt.which == 2 || evt.shiftKey)) {
				this.Options.tooltip.hide();
				var moved = false;
				this.DragPoint = {
					x: pt.x < this.Padding[0] ? this.Padding[0] : pt.x > this.Width + this.Padding[0] ? this.Width + this.Padding[0] : pt.x,
					y: pt.y < this.Padding[1] ? this.Padding[1] : pt.y > this.Height + this.Padding[1] ? this.Height + this.Padding[1] : pt.y,
					active: false,
					on: this.PointInGraph(pt)
				};
				this.Handlers.onmouseup = dojo.connect(window, "onmouseup", this, function(evt) {
					if (moved) {
						this.Options.pan(this.ViewRange, true);
					}
					this.DragPoint = null;
					for (var h in this.Handlers) {
						dojo.disconnect(this.Handlers[h]);
					}
					this.Handlers = {}
				});
				this.Handlers.onmousemove = dojo.connect(window, "onmousemove", this, function(evt) {
					var pt = this.PointOnGraph(evt);
					var x = (this.DragPoint.x - pt.x) / this.ScaleX;
					var y = (pt.y - this.DragPoint.y) / this.ScaleY;
					var vr = {
						x: {
							min: this.ViewRange.x.min + x,
							max: this.ViewRange.x.max + x
						},
						y: {
							min: this.ViewRange.y.min + y,
							max: this.ViewRange.y.max + y
						}
					}
					if (vr.x.min < this.DataRange.x.min) {
						vr.x.max += this.DataRange.x.min - vr.x.min;
						vr.x.min = this.DataRange.x.min;
					} else if (vr.x.max > this.DataRange.x.max) {
						vr.x.min += this.DataRange.x.max - vr.x.max;
						vr.x.max = this.DataRange.x.max;
					}
					if (vr.y.min < this.DataRange.y.min) {
						vr.y.max += this.DataRange.y.min - vr.y.min;
						vr.y.min = this.DataRange.y.min;
					} else if (vr.y.max > this.DataRange.y.max) {
						vr.y.min += this.DataRange.y.max - vr.y.max;
						vr.y.max = this.DataRange.y.max;
					}
					if (vr.x.min != this.ViewRange.x.min || vr.x.max != this.ViewRange.x.max || vr.y.min != this.ViewRange.y.min || vr.y.max != this.ViewRange.y.max) {
						this.ViewRange = vr;
						this.RenderFrame();
						this.Options.pan(this.ViewRange, false);
						moved = true;
						this.DragPoint.x = pt.x;
						this.DragPoint.y = pt.y;
					}
				});
			} else if (this.Options.selection) {
				if (this.Selection != null) {
					return;
				}
				this.Options.tooltip.hide();
				this.DragPoint = {
					x: pt.x < this.Padding[0] ? this.Padding[0] : pt.x > this.Width + this.Padding[0] ? this.Width + this.Padding[0] : pt.x,
					y: pt.y < this.Padding[1] ? this.Padding[1] : pt.y > this.Height + this.Padding[1] ? this.Height + this.Padding[1] : pt.y,
					active: false,
					on: this.PointInGraph(pt)
				};
				this.Handlers.onmouseup = dojo.connect(window, "onmouseup", this, function(evt) {
					var pt = this.PointOnGraph(evt);
					if (this.Options.selection.callback) {
						if (this.DragPoint.active) {
							var r = this.ViewRange;
							if (this.Options.selection.axis.indexOf("x") < 0) {
								var x1 = this.Padding[0];
								var x2 = this.Width + this.Padding[0];
							} else {
								var x1 = this.DragPoint.x;
								var x2 = pt.x < this.Padding[0] ? this.Padding[0] : pt.x > this.Width + this.Padding[0] ? this.Width + this.Padding[0] : pt.x;
							}
							if (this.Options.selection.axis.indexOf("y") < 0) {
								var y1 = this.Padding[1];
								var y2 = this.Height + this.Padding[1];
							} else {
								var y1 = this.DragPoint.y;
								var y2 = pt.y < this.Padding[1] ? this.Padding[1] : pt.y > this.Height + this.Padding[1] ? this.Height + this.Padding[1] : pt.y;
							}
							this.Options.selection.callback.call(this.Options.selection.data, true, { x:{ min: (Math.min(x1, x2) - this.Padding[0]) / this.ScaleX + r.x.min, max: (Math.max(x1, x2) - this.Padding[0]) / this.ScaleX + r.x.min }, y:{ min: (this.Height + this.Padding[1] - Math.max(y1, y2)) / this.ScaleY + r.y.min, max: (this.Height + this.Padding[1] - Math.min(y1, y2)) / this.ScaleY + r.y.min } });
						} else if (this.DragPoint.on && this.DragPoint.x == pt.x && this.DragPoint.y == pt.y) {
							var r = this.ViewRange;
							this.Options.selection.callback.call(this.Options.selection.data, false, { x:(this.DragPoint.x - this.Padding[0]) / this.ScaleX + r.x.min, y: (this.Height + this.Padding[1] - this.DragPoint.y) / this.ScaleY + r.y.min});
						}
					}
					if (this.Selection) {
						this.Overlays.remove(this.Selection);
						this.Selection = null;
					}
					this.DragPoint = null;
					for (var h in this.Handlers) {
						dojo.disconnect(this.Handlers[h]);
					}
					this.Handlers = {}
				});
				this.Handlers.onkeypress = dojo.connect(window, "onkeypress", this, function(evt) {
					if (evt.which == 27) {
						if (this.Selection) {
							this.Overlays.remove(this.Selection);
							this.Selection = null;
						}
						this.DragPoint = null;
						for (var h in this.Handlers) {
							dojo.disconnect(this.Handlers[h]);
						}
						this.Handlers = {}
					}
				});
				this.Handlers.onmousemove = dojo.connect(window, "onmousemove", this, function(evt) {
					var pt = this.PointOnGraph(evt);
					if (this.DragPoint != null) {
						dojo._base.event.stop(evt);
						if (this.DragPoint.active) {
							if (this.Options.selection.axis.indexOf("x") >= 0) {
								var x1 = this.DragPoint.x;
								var x2 = pt.x < this.Padding[0] ? this.Padding[0] : pt.x > this.Width + this.Padding[0] ? this.Width + this.Padding[0] : pt.x;
								this.Selection.rawNode.setAttribute("x", Math.min(x1, x2));
								this.Selection.rawNode.setAttribute("width", Math.max(x1, x2) - Math.min(x1, x2));
							}
							if (this.Options.selection.axis.indexOf("y") >= 0) {
								var y1 = this.DragPoint.y;
								var y2 = pt.y < this.Padding[1] ? this.Padding[1] : pt.y > this.Height + this.Padding[1] ? this.Height + this.Padding[1] : pt.y;
								this.Selection.rawNode.setAttribute("y", Math.min(y1, y2));
								this.Selection.rawNode.setAttribute("height", Math.max(y1, y2) - Math.min(y1, y2));
							}
						} else {
							if (Math.abs(pt.x - this.DragPoint.x) > 5 || Math.abs(pt.y - this.DragPoint.y) > 5) {
								if (!this.DragPoint.on && this.PointInGraph(pt)) {
									this.DragPoint.on = true;
								}
								if (this.DragPoint.on) {
									var x1 = this.DragPoint.x, y1 = this.DragPoint.y, x2 = pt.x, y2 = pt.y;
									if (this.Options.selection.axis.indexOf("x") < 0) {
										x1 = this.Padding[0];
										x2 = this.Width + this.Padding[0];
									}
									if (this.Options.selection.axis.indexOf("y") < 0) {
										y1 = this.Padding[1];
										y2 = this.Height + this.Padding[1];
									}
									var x1 = Math.min(x1, x2), y1 = Math.min(y1, y2), x2 = Math.max(x1, x2), y2 = Math.max(y1, y2);
									this.Selection = this.Overlays.createRect({x:x1, y:y1, width:x2 - x1, height:y2 - y1}).setFill("rgba(0,0,190,0.2)").setStroke({color:"rgba(0,0,190,0.7)", width:0.5});
									this.DragPoint.active = true;
								}
							}
						}
					}
				});
			}
		});
		var resizeTimeout = null;
		dojo.connect(window, "onresize", this, function(evt) {
			clearTimeout(resizeTimeout);
			var obj = this;
			resizeTimeout = setTimeout(function() {
				var cs = window.getComputedStyle(container, null);
				var wc = container.clientWidth - parseInt(cs.getPropertyValue('padding-left')) - parseInt(cs.getPropertyValue('padding-right')) - 3;
				var hc = container.clientHeight - parseInt(cs.getPropertyValue('padding-top')) - parseInt(cs.getPropertyValue('padding-bottom'));
				var w = wc - obj.Padding[0] - obj.Padding[2];
				var h = hc - obj.Padding[1] - obj.Padding[3];
				if (w != obj.Width || h != obj.Height) {
					obj.Width = w;
					obj.Height = h;
					obj.Surface.setDimensions(wc, hc);
					obj.RecalcLayout();
					obj.Interact.clear();
					obj.Interact.createRect({x:0, y:0, width:wc, height:hc}).setFill("rgba(0,0,0,0)").setStroke(null);
				}
			}, 250);
		});
		if (this.Options.tooltip.enable) {
			this.SetupTooltip();
		}
	}
}

LcPlot = function(container, opts) {
	var defaults = {/*
		minTime: 0,
		maxTime: 0,
		minMz: 0,
		maxMz: 0,
		maxIntensity: 0,
		datafile: 0,
		file: "",*/
		contrast: 0.5,
		show: {
			ms1smooth: false,
			ms1points: true,
			ms2: true
		},
		axis: {
			x: {
				//min:
				//max:
				label: "Retention Time (min)"
			},
			y: {
				//min:
				//max:
				label: "m/z"
			}
		},
		tooltip: {
			show: function(evt, pt, obj) {
			}
		},
		grid: {
			axis: "xy"
		}
	};
	MixIn(defaults, opts);
	dojo.mixin(this, new BaseGraph(container, defaults));
	this.DataRange = dojo.clone(opts.axis);
	this.DataRange.x.range = this.DataRange.x.max - this.DataRange.x.min;
	this.DataRange.y.range = this.DataRange.y.max - this.DataRange.y.min;
	
	this.SetContrast = function(value) {
		var range = "&x1=" + this.ViewRange.x.min + "&x2=" + this.ViewRange.x.max + "&y1=" + this.ViewRange.y.min + "&y2=" + this.ViewRange.y.max;
		if (this.Options.show.ms1smooth) {
			this.MS1SmoothGroup.remove(this.MS1Smooth);
			this.MS1Smooth = this.MS1SmoothGroup.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=1s&contrast=" + value + range + "&w=" + this.Width + "&h=" + this.Height });
		}
		if (this.Options.show.ms1points) {
			this.MS1PointsGroup.remove(this.MS1Points);
			this.MS1Points = this.MS1PointsGroup.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=1p&contrast=" + value + range + "&w=" + this.Width + "&h=" + this.Height });
		}
		this.Options.contrast = value;
	}
	
	this.SetVisible = function(show) {
		var range = "&x1=" + this.ViewRange.x.min + "&x2=" + this.ViewRange.x.max + "&y1=" + this.ViewRange.y.min + "&y2=" + this.ViewRange.y.max;
		if (show.ms1smooth != this.Options.show.ms1smooth) {
			if (show.ms1smooth) {
				this.MS1Smooth = this.MS1SmoothGroup.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=1s&contrast=" + this.Options.contrast + range + "&w=" + this.Width + "&h=" + this.Height });
			} else if (this.MS1Smooth != null) {
				this.MS1SmoothGroup.remove(this.MS1Smooth);
				this.MS1Smooth = null;
			}
			this.Options.show.ms1smooth = show.ms1smooth;
		}
		if (show.ms1points != this.Options.show.ms1points) {
			if (show.ms1points) {
				this.MS1Points = this.MS1PointsGroup.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=1p&contrast=" + this.Options.contrast + range + "&w=" + this.Width + "&h=" + this.Height });
			} else if (this.MS1Points != null) {
				this.MS1PointsGroup.remove(this.MS1Points);
				this.MS1Points = null;
			}
			this.Options.show.ms1points = show.ms1points;
		}
		if (show.ms2 != this.Options.show.ms2) {
			if (show.ms2) {
				this.MS2 = this.MS2Group.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=2" + range + "&w=" + this.Width + "&h=" + this.Height });
			} else if (this.MS2 != null) {
				this.MS2Group.remove(this.MS2);
				this.MS2 = null;
			}
			this.Options.show.ms2 = show.ms2;
		}
	}
	
	this.Zoom = function(range) {
		if (!range) {
			range = {
				x: { min:opts.axis.x.min, max:opts.axis.x.max },
				y: { min:opts.axis.y.min, max:opts.axis.y.max }
			};
		}
		if (range.x.min == this.ViewRange.x.min && range.x.max == this.ViewRange.x.max && range.y.min == this.ViewRange.y.min && range.y.max == this.ViewRange.y.max) {
			return false;
		}
		this.ViewRange = range;
		this.ScaleX = this.Width / (this.ViewRange.x.max - this.ViewRange.x.min);
		this.ScaleY = this.Height / (this.ViewRange.y.max - this.ViewRange.y.min);
		this.FrameGroup.clear();
		this.RenderFrame();
		range = range ? "&x1=" + range.x.min + "&x2=" + range.x.max + "&y1=" + range.y.min + "&y2=" + range.y.max : "";
		if (this.Options.show.ms1smooth) {
			this.MS1SmoothGroup.remove(this.MS1Smooth);
			this.MS1Smooth = this.MS1SmoothGroup.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=1s&contrast=" + this.Options.contrast + range + "&w=" + this.Width + "&h=" + this.Height });
		}
		if (this.Options.show.ms1points) {
			this.MS1PointsGroup.remove(this.MS1Points);
			this.MS1Points = this.MS1PointsGroup.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=1p&contrast=" + this.Options.contrast + range + "&w=" + this.Width + "&h=" + this.Height });
		}
		if (this.Options.show.ms2) {
			this.MS2Group.remove(this.MS2);
			this.MS2 = this.MS2Group.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=2" + range + "&w=" + this.Width + "&h=" + this.Height });
		}
		return true;
	}
	
	this.RecalcLayout = function() {
		this.Zoom(this.ViewRange);
	}
	
	this.RenderData = function() {
		this.MS1SmoothGroup = this.Surface.createGroup();
		this.MS1PointsGroup = this.Surface.createGroup();
		this.MS2Group = this.Surface.createGroup();
		if (this.Options.show.ms1smooth) {
			this.MS1Smooth = this.MS1SmoothGroup.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=1s&contrast=0.5&w=" + this.Width + "&h=" + this.Height });
		} else {
			this.MS1Smooth = null;
		}
		if (this.Options.show.ms1points) {
			this.MS1Points = this.MS1PointsGroup.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=1p&contrast=0.5&w=" + this.Width + "&h=" + this.Height });
		} else {
			this.MS1Points = null;
		}
		if (this.Options.show.ms2) {
			this.MS2 = this.MS2Group.createImage({ x:this.Padding[0], y:this.Padding[1], width:this.Width, height:this.Height, src:"lc?file=" + this.Options.file + "&n=" + this.Options.datafile + "&level=2&w=" + this.Width + "&h=" + this.Height });
		} else {
			this.MS2 = null;
		}
	}
	this.Initialise();
}
