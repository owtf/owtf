/**
 * PRODUCTION WEBPACK CONFIGURATION
 */

 const HtmlWebpackPlugin = require('html-webpack-plugin');
 const webpack = require('webpack');
 const merge = require('webpack-merge');
 const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
 
 
 const production = {
 
     // Utilize long-term caching by adding content hashes (not compilation hashes) to compiled assets
     output: {
         filename: '[name].[chunkhash].js',
         chunkFilename: '[name].[chunkhash].chunk.js',
     },
     mode: 'production',
     optimization: {
         minimize: true,
         namedModules: true,
         namedChunks: true,
         removeAvailableModules: true,
         flagIncludedChunks: true,
         occurrenceOrder: false,
         usedExports: true,
         concatenateModules: true,
         sideEffects: true,
         splitChunks: {
             chunks: 'all',
             minSize: 3000,
             maxSize: 0,
             minChunks: 1,
             maxAsyncRequests: 5,
             maxInitialRequests: 3,
             automaticNameDelimiter: '~',
             automaticNameMaxLength: 30,
             name: true,
             cacheGroups: {
               vendors: {
                 test: /[\\/]node_modules[\\/]/,
                 priority: -10,
                 enforce: true,
                 reuseExistingChunk: true
               },
               default: {
                 minChunks: 2,
                 priority: -20,
                 reuseExistingChunk: true
               }
             }
           },
     },    
     plugins: [
         new webpack.optimize.ModuleConcatenationPlugin(),
         // Minify and optimize the index.html
         new HtmlWebpackPlugin({
             template: 'src/index.html',
             minify: {
                 removeComments: true,
                 collapseWhitespace: true,
                 removeRedundantAttributes: true,
                 useShortDoctype: true,
                 removeEmptyAttributes: true,
                 removeStyleLinkTypeAttributes: true,
                 keepClosingSlash: true,
                 minifyJS: true,
                 minifyCSS: true,
                 minifyURLs: true
             },
             inject: true
         })
     ]
 };
 
 module.exports = merge(production, require('./common.config'));