import Docxtemplater from "docxtemplater";
import JSZip from "jszip";
import saveAs from "save-as";

const templateModules = import.meta.glob("./templates/**/*.docx", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

const templates = Object.entries(templateModules).reduce(
  (acc, [filePath, url]) => {
    const fileName = filePath.split("/").pop();
    if (fileName) {
      acc[fileName] = url;
    }
    return acc;
  },
  {} as Record<string, string>,
);

export const templatesNames = Object.keys(templates);

// Funtion responsible for generating docx from JSON using docxtemplater.
export async function getDocxReportFromJSON(json, template) {
  const templateUrl = templates[template];

  if (!templateUrl) {
    throw new Error(`Template '${template}' was not found.`);
  }

  const templateResponse = await fetch(templateUrl);
  const templateBuffer = await templateResponse.arrayBuffer();

  var zip = new JSZip(templateBuffer);
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
      properties: error.properties,
    };
    console.log(
      JSON.stringify({
        error: e,
      }),
    );
    // The error thrown here contains additional information when logged with JSON.stringify (it contains a property object).
    throw error;
  }

  var out = doc.getZip().generate({
    type: "blob",
    mimeType:
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  });
  saveAs(out, "report.docx");
}
