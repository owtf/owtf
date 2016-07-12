var path = require('path');
var webpack = require('webpack');
var merge = require('webpack-merge');
const autoprefixer = require('autoprefixer');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const TARGET = process.env.npm_lifecycle_event;

var slash = require('slash');
var dirname = __dirname;
if (process.platform === 'win32') dirname = slash(dirname);

var common = {
    plugins: [
        new webpack.DefinePlugin({
            'TARGET': '"' + TARGET + '"'
        }),
        new webpack.DefinePlugin({
            '__base': '"' + dirname + '/"'
        }),
        new webpack.DefinePlugin({
            'process.env': {
                'NODE_ENV': JSON.stringify(process.env.NODE_ENV)
            }
        }),
    ],
    output: {
        path: path.join(__dirname, 'includes/build/'),
        filename: 'bundle.js',
        publicPath: 'includes/build/'
    }
};

var config = merge(common, {
    entry: [
        './includes/src/main'
    ],
    plugins: [
        new ExtractTextPlugin('react-toolbox.css', {
            allChunks: true
        }),
        new webpack.optimize.UglifyJsPlugin({
            compress: true,
            mangle: true
        })
    ],
    module: {
        loaders: [{
            test: /\.js$/,
            exclude: /node_modules/,
            loaders: ['babel', 'babel?presets[]=react,presets[]=es2015,presets[]=stage-0'],
            include: path.join(__dirname, 'includes/src')
        }, {
            test: /(\.scss|\.css)$/,
            loader: ExtractTextPlugin.extract('style', 'css?sourceMap&modules&importLoaders=1&localIdentName=[name]__[local]___[hash:base64:5]!postcss!sass')
        }]
    },
    postcss: [autoprefixer],
    sassLoader: {
        data: '@import "theme/_config.scss";',
        includePaths: [path.resolve(__dirname, 'includes/src')]
    },

});

module.exports = config;
