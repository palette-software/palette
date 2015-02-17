module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    less: {
      compileCore: {
        options: {
          strictMath: true,
          sourceMap: true,
          outputSourceFiles: true,
          sourceMapURL: '/app/module/palette/css/<%= pkg.name %>.css.map',
          sourceMapFilename: 'palette/css/<%= pkg.name %>.css.map'
        },
        src: 'less/style.less',
        dest: 'palette/css/style.css'
      }
    }

  });

  // Load the plugin that provides the "uglify" task.
  grunt.loadNpmTasks('grunt-contrib-less');

  // Default task(s).
  grunt.registerTask('default', ['less']);

};
