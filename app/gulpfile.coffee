gulp = require 'gulp'
coffee = require 'gulp-coffee'
sourcemaps = require 'gulp-sourcemaps'
bower = require 'gulp-bower'
mainBowerFiles = require 'main-bower-files'

gulp.task 'bower-install', ->
    bower()

gulp.task 'collect-libs', ['bower-install'], ->
    # gulp.src mainBowerFiles()
    #     .pipe gulp.dest 'static/libs'

    bootstrap_css_files = [
        "bower_components/bootstrap/dist/css/bootstrap.min.css"
    ]

    bootstrap_js_files = [
        "bower_components/bootstrap/dist/js/bootstrap.min.js"
    ]

    gulp.src bootstrap_js_files
        .pipe gulp.dest 'js/vendor'


    gulp.src bootstrap_css_files
        .pipe gulp.dest 'css'

buildCoffee = (pattern, destination) ->
    gulp.src pattern
        .pipe sourcemaps.init()
        .pipe coffee
            bare: true
        .pipe sourcemaps.write '.'
        .pipe gulp.dest destination

gulp.task 'client-coffee', ->
    buildCoffee ['coffee/*.coffee'], './js'



gulp.task 'default', ['collect-libs', 'client-coffee']
