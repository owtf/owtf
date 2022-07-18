/**
 * Funtion to import a directory.
 * :params r require.context object.
 * returns a object with key as filename and value as content of file.
 * If you need to import recursively, use true in second argument of request.context object.
 * Example usage importDirectory(require.context('<directory>', true, /\.(js|jsx|jpg)$/));
 */

export const importDirectory: object = (r: __WebpackModuleApi.RequireContext) => {
  let elem: any = {};
  r.keys().forEach((item: string) => {
    elem[item.replace("./", "")] = r(item);
  });
  return elem;
}
