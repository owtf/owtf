import Docxtemplater from 'docxtemplater';
import {TARGET_API_URI} from '../constants.jsx';
import JSZip from 'jszip';
import template from './input.docx';
import saveAs from 'save-as';

// Funtion responsible for generating docx from JSON using docxtemplater.
function getDocxReportFromJSON(json) {
    var zip = new JSZip(template);

    var doc = new Docxtemplater();
    doc.loadZip(zip);

    //set the templateVariables
    doc.setData(json);

    try {
        // render the document (replace all occurences of tags.
        doc.render()
    } catch (error) {
        var e = {
            message: error.message,
            name: error.name,
            stack: error.stack,
            properties: error.properties
        }
        console.log(JSON.stringify({
            error: e
        }));
        // The error thrown here contains additional information when logged with JSON.stringify (it contains a property object).
        throw error;
    }

    var out = doc.getZip().generate({
        type: "blob",
        mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    })
    saveAs(out, 'report.docx');
}

/**
  * Funtion to generate docx format.
  * Uses REST API - /api/targets/<target_id>/export/
  * docxtemplater takes a JSON and docx template and outputs output docx.
  */

export function getDocx(target_id) {
    $.ajax({
        url: TARGET_API_URI + target_id + '/export/',
        type: 'GET',
        success: function(result) {
            getDocxReportFromJSON(result);
        },
        error: function(xhr, textStatus, serverResponse) {
            console.log("Server replied: " + serverResponse);
        }
    });
}
