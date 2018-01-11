let path = require('path');
let webpack = require('webpack');
let merge = require('webpack-merge');
const autoprefixer = require('autoprefixer');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const TARGET = process.env.npm_lifecycle_event;

let slash = require('slash');
let dirname = __dirname;
if (process.platform === 'win32') dirname = slash(dirname);

let common = {
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

let config = merge(common, {
    entry: [
        path.join(__dirname, 'src/main')
    ],
    resolveLoader: {
        modulesDirectories: [
            path.join(__dirname, 'node_modules'),
        ]
    },
    resolve: {
        extensions: ['', '.js', '.jsx']
    },
    module: {
        loaders: [{
            test: /\.jsx?$/,
            exclude: /node_modules/,
            loaders: ['babel', 'babel?presets[]=react,presets[]=es2015,presets[]=stage-0'],
            include: path.join(__dirname, 'src')
        },
        {
            test: /\.docx?$/,
            loaders: ['binary-loader'],
        }
      ]
    }

});

module.exports = config;
