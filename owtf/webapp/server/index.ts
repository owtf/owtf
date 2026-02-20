/**
 * Starts development server.
 *
 */
const express = require("express");
const logger = require("./logger");
const path = require("path");
const webpack = require("webpack");
const webpackDevMiddleware = require("webpack-dev-middleware");
const webpackHotMiddleware = require("webpack-hot-middleware");
const proxyMiddleware = require("http-proxy-middleware");
const webpackConfig = require("../webpack/dev.config");

const publicPath = webpackConfig.output.publicPath;
const app = express();
const compiler = webpack(webpackConfig);
const middleware = webpackDevMiddleware(compiler, {
  publicPath,
});
const port = 3000;
const host = "0.0.0.0";

app.use(middleware);
app.use(webpackHotMiddleware(compiler));
app.use(
  proxyMiddleware("/api", {
    target: "http://localhost:8009",
    pathRewrite: {
      "^/api": "/api",
    },
  }),
);

// Since webpackDevMiddleware uses memory-fs internally to store build
// artifacts, we use it instead
const fs = middleware.fileSystem;

app.get("*", (req: unknown, res: any) => {
  fs.readFile(path.join(compiler.outputPath, "index.html"), (err: unknown, file: any) => {
    if (err) {
      res.sendStatus(404);
    } else {
      res.send(file.toString());
    }
  });
});

// Start your app.
app.listen(port, host, (err: any) => {
  if (err) {
    return logger.error(err.message);
  }

  logger.appStarted(port, host);
  return undefined;
});
