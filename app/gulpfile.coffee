gulp = require 'gulp'
coffee = require 'gulp-coffee'
sourcemaps = require 'gulp-sourcemaps'
bower = require 'gulp-bower'
less = require 'gulp-less'
mainBowerFiles = require 'main-bower-files'
exists = require('path-exists').sync;

gulp.task 'bower-install', ->
    bower()

minBowerFiles = mainBowerFiles().map (path, index, arr) ->
    newPath = path.replace(/.([^.]+)$/g, '.min.$1')
    if exists newPath
        return newPath
    else
        return path

gulp.task 'collect-libs', ['bower-install'], ->
    gulp.src minBowerFiles
        .pipe gulp.dest 'js/vendor'

    # bootstrap_css_files = [
    # "bower_components/bootstrap/dist/css/bootstrap.min.css"
    # ]

    # gulp.src bootstrap_css_files
    # .pipe gulp.dest 'css'

buildCoffee = (pattern, destination) ->
    gulp.src pattern
        .pipe sourcemaps.init()
        .pipe coffee
            bare: true
        .pipe sourcemaps.write '.'
        .pipe gulp.dest destination

gulp.task 'client-coffee', ->
    buildCoffee ['coffee/*.coffee'], './js'


gulp.task 'less', ->
    gulp.src 'less/style.less'
        .pipe sourcemaps.init()
        .pipe less()
        .pipe sourcemaps.write '.'
        .pipe gulp.dest 'css'

gulp.task 'default', ['collect-libs', 'client-coffee', 'less']
