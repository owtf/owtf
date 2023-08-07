import Docxtemplater from "docxtemplater";
import { importDirectory } from "../../utils/export";
import JSZip from "jszip";
import saveAs from "save-as";
import "@babel/polyfill";

//@ts-ignore
const templates = importDirectory(
  require.context("./templates/", true, /\.(docx)$/)
);

export const templatesNames = Object.keys(templates);

// Funtion responsible for generating docx from JSON using docxtemplater.
export function getDocxReportFromJSON(json, template) {
  //@ts-ignore
  var zip = new JSZip(templates[template]);
  var doc = new Docxtemplater();
  doc.loadZip(zip);

  //set the templateVariables
  doc.setData(json);

  try {
    // render the document (replace all occurences of tags.
    doc.render();
  } catch (error) {
    var e = {
      message: error.message,
      name: error.name,
      stack: error.stack,
      properties: error.properties
    };
    console.log(
      JSON.stringify({
        error: e
      })
    );
    // The error thrown here contains additional information when logged with JSON.stringify (it contains a property object).
    throw error;
  }

  var out = doc.getZip().generate({
    type: "blob",
    mimeType:
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  });
  saveAs(out, "report.docx");
}
