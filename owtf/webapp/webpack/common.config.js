/**
 * COMMON WEBPACK CONFIGURATION BETWEEN DEVELOPMENT AND PRODUCTION
 */

 const path = require("path");
 const webpack = require("webpack");
 const CleanWebpackPlugin = require("clean-webpack-plugin");
 const ExtractTextPlugin = require("extract-text-webpack-plugin");
 const MiniCssExtractPlugin = require("mini-css-extract-plugin");
 const devMode = process.env.NODE_ENV !== "production";
 
 const home = require("os").homedir();
 const owtfDir = path.join(home, ".owtf", "build");
 
 const PATHS = {
   app: path.join(process.cwd(), "src"),
   build: owtfDir
 };
 
 module.exports = {
   entry: [PATHS.app],
   output: {
     path: PATHS.build,
     publicPath: "/static/"
   },
   plugins: [
     new webpack.ProvidePlugin({
       // make fetch available
       fetch: "exports-loader?self.fetch!whatwg-fetch"
     }),
     new webpack.ContextReplacementPlugin(/moment[\\/]locale$/, /^\.\/(en)$/),
     // new MiniCssExtractPlugin({
     //   filename: "style.css",
     // }),
     // Always expose NODE_ENV to webpack, in order to use `process.env.NODE_ENV`
     // inside your code for any environment checks; UglifyJS will automatically
     // drop any unreachable code.
     new webpack.DefinePlugin({
       "process.env": {
         NODE_ENV: JSON.stringify(process.env.NODE_ENV)
       }
     }),
     new webpack.NamedModulesPlugin(),
     // new ExtractTextPlugin("styles.css"),
     new CleanWebpackPlugin([PATHS.build], {
       root: process.cwd()
     })
   ].concat(devMode ? [] : [new MiniCssExtractPlugin({
    filename: "[name].[contenthash].css",
    chunkFilename: "[id].[contenthash].css",
   })]),
   resolve: {
     modules: ["src", "node_modules"],
     extensions: [".js", ".jsx"]
   },
   module: {
     rules: [
       {
         test: /\.js$/, // Transform all .js files required somewhere with Babel
         exclude: /node_modules/,
         use: {
           loader: "babel-loader"
         }
       },

       {
         test: /\.(sa|sc|c)ss$/,
         use: [
           devMode ? "style-loader" : MiniCssExtractPlugin.loader,
           "css-loader",
           "sass-loader",
         ],
       },
       {
         test: /\.(eot|svg|otf|ttf|woff|woff2)$/,
         use: "file-loader"
       },
       {
         test: /\.(jpg|png|gif)$/,
         use: [
           "file-loader",
           {
             loader: "image-webpack-loader",
             options: {
               progressive: true,
               optimizationLevel: 7,
               interlaced: false
             }
           }
         ]
       },
       {
         test: /\.html$/,
         use: "html-loader"
       },
       {
         test: /\.json$/,
         use: "json-loader"
       },
       {
         test: /\.(mp4|webm)$/,
         use: {
           loader: "url-loader",
           options: {
             limit: 10000
           }
         }
       }
     ]
   }
 };