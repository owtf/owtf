# Architecture
**Webpack** ​​is used as the build system.  
Dashboard, Home etc. are modules / React Components.

**src/main.js** is a file which is used by webpack to generate bundle. All React Components are imported here.
Webpack takes the full dependency tree and generate a single build/bundle.js.

**src/constants.js** holds all global constants. There is also **constants.js** file in some modules like Dashboard/constants.js which holds the constants which are only used by the same module.

# Installation

These commands should be run from OWTF root directory.

`$ npm install -g webpack`

`$ npm install --global gulp-cli`

`$ npm install`

> Please ensure that you have npm >= 3.10.3 and node >= 6.7.0. In case you do not have **npm** installed. Use [nvm](https://github.com/creationix/nvm) to install npm on your system. Debian packages may not work because they are no longer maintained.

# Build

## Production

This command should be run from OWTF root directory.

`$ npm run build`

For building production bundle, we use config **webpack.config.js**. It generally takes more time as compare to normal building as it is using modules like UglifyJs to compress the generating compiled JS code from JSX. It generates optimized and compressed code.

## Development

This command should be run from OWTF root directory.

`$ gulp`

It is not feasible for developer to manually build and wait for build every time he/she makes any change. For building development bundle, we use config **webpack-dev.config.js**. Here gulp is used as streaming build system. It automatically detects if any file is changed in src folder and re-generate the bundle which builds faster as it not using any optimization/compressing as production.

# Credits
Some special npm modules used in rendering bundle:

* [chart.js](https://github.com/reactjs/react-chartjs/)
* [rc-progress](https://github.com/react-component/progress)
* [react-notification](https://github.com/pburtchaell/react-notification)
* [react-timeago](https://www.npmjs.com/package/react-timeago)
