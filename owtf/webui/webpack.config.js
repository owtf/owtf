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
        path: path.join(__dirname, 'public/build/'),
        filename: 'bundle.js',
        publicPath: path.join(__dirname, 'public/build/')
    }
};

var config = merge(common, {
    entry: [
        path.join(__dirname, 'src/main'),
        path.join(__dirname, 'scss/main')
    ],
    plugins: [
        new webpack.LoaderOptionsPlugin({
            minimize: true,
            debug: false,
        }),
        new ExtractTextPlugin('css/bundle.css', {
            allChunks: true
        }),
        new webpack.optimize.UglifyJsPlugin({
            compress: true,
            mangle: true
        })
    ],
    resolveLoader: {
        modules: [
            path.join(__dirname, 'node_modules'),
        ]
    },
    resolve: {
        extensions: ['.js', '.jsx', '.scss']
    },
    module: {
        loaders: [{
                test: /\.jsx?$/,
                exclude: /node_modules/,
                loaders: ['babel-loader', 'babel-loader?presets[]=react,presets[]=es2015,presets[]=stage-0'],
                include: path.join(__dirname, 'src')
            },
            {
                test: /\.docx?$/,
                loaders: ['binary-loader'],
            },
            {
                test: /\.(sass|scss|css)$/,
                loader: ExtractTextPlugin.extract(['css-loader', 'sass-loader'])
            },
            {
                test: /.(ttf|otf|eot|svg|woff(2)?)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                use: [{
                    loader: 'file-loader',
                    options: {
                        name: '[name].[ext]',
                        outputPath: 'fonts/', // where the fonts will go
                    }
                }]
            },
        ]
    }
});

module.exports = config;
