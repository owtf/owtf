/**
 * Funtion to import a directory.
 * :params r require.context object.
 * returns a object with key as filename and value as content of file.
 * If you need to import recursively, use true in second argument of request.context object.
 * Example usage importDirectory(require.context('<directory>', true, /\.(js|jsx|jpg)$/));
 */

export function importDirectory(r) {
  let elem = {};
  r.keys().map((item, index) => {
    elem[item.replace("./", "")] = r(item);
  });
  return elem;
}
