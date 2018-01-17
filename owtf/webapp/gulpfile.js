let gulp = require('gulp');
let webpack = require('webpack-stream');

gulp.task('default', function() {
  return gulp.src('src/main.js')
    .pipe(webpack( require('./webpack-dev.config.js') ))
    .pipe(gulp.dest('public/build/'));
});

gulp.watch('src/**/*.js', function(event) {
  console.log('File ' + event.path + ' was ' + event.type + ', running tasks...');
  return gulp.src('src/main.js')
    .pipe(webpack( require('./webpack-dev.config.js') ))
    .pipe(gulp.dest('public/build/'));
});
