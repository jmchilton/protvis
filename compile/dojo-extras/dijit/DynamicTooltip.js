define([
	"dojo/_base/declare", // declare
	"./Tooltip",
], function(declare, domClass, MenuItem, template){

	return declare("dijit.DynamicTooltip", dijit.Tooltip, {
		isOpen: false,
		href: "",
		label: "Loading",
		preventCache: false,
		
		_onHover: function(/*Event*/ e){
			this.label = "<center><span class='dijitContentPaneLoading'>Loading results... Please wait</span></center>";
			var url = this.href + e.target.getAttribute("tipurl");
			dojo.xhrGet({
				url: url,
				tooltipWidget: this,
				load: function(response, ioArgs) {
					this.tooltipWidget.label = response;
					if (this.isOpen) {
						this.tooltipWidget.close();
						this.tooltipWidget.open(node);
					}
				},
				error: function() {
					this.tooltipWidget.label = "Error contacting server";
					if (isOpen) {
						this.tooltipWidget.close();
						this.tooltipWidget.open(node);
					}
				},
				preventCache: this.preventCache
			});
			this.inherited(arguments);
		},

		_setHrefAttr: function(/*String|Uri*/ href){
			// summary:
			//		Hook so attr("href", ...) works.
			// description:
			//		resets so next show loads new href
			//	href:
			//		url to the content you want to show, must be within the same domain as your mainpage

			this.href = href;
		},
		
		open: function(/*DomNode*/ target){
 			this.isOpen = true;
			this.inherited(arguments);
		},
		
		close: function(){
 			this.isOpen = false;
			this.inherited(arguments);
		}
	});
});
