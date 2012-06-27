GetGPMDBPeptides = function(div, pepseq){
    require(["dojo/_base/xhr"],
    function(xhr) {
        var req_content={}
        req_content.peptideseq=pepseq
        xhr.get({
            url: "gpmdb_peptide",
            content: req_content,
            load: function(result) {
                dojo.byId(div).innerHTML=result
            }
        });
    });
}