var gulp = require('gulp');
var webpack = require('webpack-stream');

gulp.task('default', function() {
  return gulp.src('includes/src/main.js')
    .pipe(webpack( require('./webpack-dev.config.js') ))
    .pipe(gulp.dest('includes/build/'));
});

gulp.watch('includes/src/**/*.js', function(event) {
  console.log('File ' + event.path + ' was ' + event.type + ', running tasks...');
  return gulp.src('includes/src/main.js')
    .pipe(webpack( require('./webpack-dev.config.js') ))
    .pipe(gulp.dest('includes/build/'));
});
