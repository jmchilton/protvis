define([
	"dojo/_base/fx",
	"dojo/dom-class",
	"dojo/_base/declare",
	"dojox/form/uploader/FileList"
],function(fx, domClass, declare, FileList){

return declare("dojox.form.uploader.FileList", [FileList], {
	templateString:	'<div class="dojoxUploaderFileList">' +
						'<div dojoAttachPoint="progressNode" class="dojoxUploaderFileListProgress"><div dojoAttachPoint="percentBarNode" class="dojoxUploaderFileListProgressBar"></div><div dojoAttachPoint="percentTextNode" class="dojoxUploaderFileListPercentText">0%</div></div>' +
						'<table class="dojoxUploaderFileListTable">'+
							'<thead><tr class="dojoxUploaderFileListHeader"><th class="dojoxUploaderDelete"><div class="dijitIconDelete dojoxUploaderDeleteRow" title="Empty list" onclick="dijit.byId(\'${uploaderId}\').reset();">&nbsp;</div></th><th class="dojoxUploaderIndex">${headerIndex}</th><th class="dojoxUploaderIcon">${headerType}</th><th class="dojoxUploaderFileName">${headerFilename}</th><th class="dojoxUploaderFileSize" dojoAttachPoint="sizeHeader">${headerFilesize}</th></tr></thead>'+
							'<tbody class="dojoxUploaderFileListContent" dojoAttachPoint="listNode">'+
							'</tbody>'+
						'</table>'+
						'<div>',

	_addRow: function(index, type, name, size){

		var c, r = this.listNode.insertRow(-1);
		c = r.insertCell(-1);
		domClass.add(c, "dojoxUploaderDelete");
		c.innerHTML = '<div class="dijitIconDelete dojoxUploaderDeleteRow" title="Remove file from list" onclick="dijit.byId(\'' + this.uploaderId + '\').removeFile(' + index + ');">&nbsp;</div>';
		
		c = r.insertCell(-1);
		domClass.add(c, "dojoxUploaderIndex");
		c.innerHTML = index;

		c = r.insertCell(-1);
		domClass.add(c, "dojoxUploaderIcon");
		c.innerHTML = type;

		c = r.insertCell(-1);
		domClass.add(c, "dojoxUploaderFileName");
		c.innerHTML = name;
		if(this._fileSizeAvail){
			c = r.insertCell(-1);
			domClass.add(c, "dojoxUploaderSize");
			c.innerHTML = this.convertBytes(size).value;
		}

		this.rowAmt++;
	}
});
});
