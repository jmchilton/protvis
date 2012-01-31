define([
	"dojo/_base/declare",
	"dojo/_base/connect",
	"dojox/form/Uploader"
],function(declare, connect, Uploader){
declare("dojox.form.AppendUploader", [Uploader], {
	_connectButton: function(){
		this._cons.push(connect.connect(this.inputNode, "change", this, function(evt){
			if(this.supports("multiple") && this.multiple) {
				if (!this._files) {
					this._files = new Array();
				}
				for (var i = 0; i < this.inputNode.files.length; ++i) {
					this._files.push(this.inputNode.files[i]);
				}
			} else {
				this._files = this.inputNode.files;
			}
			this.onChange(this.getFileList(evt));
			if(!this.supports("multiple") && this.multiple) this._createInput();
		}));

		if(this.tabIndex > -1){
			this.inputNode.tabIndex = this.tabIndex;

			this._cons.push(connect.connect(this.inputNode, "focus", this, function(){
				this.titleNode.style.outline= "1px dashed #ccc";
			}));
			this._cons.push(connect.connect(this.inputNode, "blur", this, function(){
				this.titleNode.style.outline = "";
			}));
		}
	},
	removeFile: function(index) {
		if (this._files && index > 0 && this._files.length >= index) {
			this._files.splice(index - 1, 1);
		}
		this.onChange(this.getFileList());
		if(!this.supports("multiple") && this.multiple) this._createInput();
	}
});

	dojox.form.UploaderOrg = dojox.form.AppendUploader;
	var extensions = [dojox.form.UploaderOrg];
	dojox.form.addUploaderPlugin = function(plug){
		// summary:
		// 		Handle Uploader plugins. When the dojox.form.addUploaderPlugin() function is called,
		// 		the dojox.form.Uploader is recreated using the new plugin (mixin).
		//
		extensions.push(plug);
		declare("dojox.form.AppendUploader", extensions, {});
	}

	return dojox.form.AppendUploader;
});
