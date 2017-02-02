require [
  'jquery'
  'underscore'
  'configure'
  'common'
  'Dropdown'
  'OnOff'
  'bootstrap'
], ($, _, configure, common, Dropdown, OnOff) ->
  MONITOR_DROPDOWN_IDS = [
    'disk-watermark-low'
    'disk-watermark-high'
    'cpu-load-warn'
    'cpu-period-warn'
    'cpu-load-error'
    'cpu-period-error'
    'http-load-warn'
    'http-load-error'
  ]
  monitorData = null
  sectionData = {}

  ###
  # resetTestMessage()
  # Hide the test message paragraph.
  ###

  resetTestMessage = (name) ->
    $('#' + name + '-test-message').html ''
    $('#' + name + '-test-message').addClass 'hidden'
    $('#' + name + '-test-message').removeClass 'green red'
    return

  ###
  # getMonitorData()
  ###

  getMonitorData = ->
    data = {}
    i = 0
    while i < MONITOR_DROPDOWN_IDS.length
      id = MONITOR_DROPDOWN_IDS[i]
      data[id] = Dropdown.getValueById(id)
      i++
    data

  ###
  # setMonitorData()
  ###

  setMonitorData = (data) ->
    i = 0
    while i < MONITOR_DROPDOWN_IDS.length
      id = MONITOR_DROPDOWN_IDS[i]
      Dropdown.setValueById id, data[id]
      i++
    return

  ###
  # maySaveCancelMonitor()
  # Return true if the 'Monitors' section has changed.
  ###

  maySaveCancelMonitor = (data) ->
    !_.isEqual(data, monitorData)

  ###
  # saveMonitors()
  # Callback for the 'Save' button in the 'Monitors' section.
  ###

  saveMonitors = ->
    $('#save-monitors, #cancel-monitors').addClass 'disabled'
    data = getMonitorData()
    data['action'] = 'save'
    $.ajax
      type: 'POST'
      url: '/rest/alerts'
      data: data
      dataType: 'json'
      async: false
      success: ->
        delete data['action']
        monitorData = data
        return
      error: (jqXHR, textStatus, errorThrown) ->
        alert @url + ': ' + jqXHR.status + ' (' + errorThrown + ')'
        return
    validate()
    return

  ###
  # cancelMonitors()
  # Callback for the 'Cancel' button in the 'Monitors' section.
  ###

  cancelMonitors = ->
    setMonitorData monitorData
    $('#save-monitors, #cancel-monitors').addClass 'disabled'
    validate()
    return

  ###
  # getSectionData()
  ###

  getSectionData = (section) ->
    data = {}

    ### sliders ###

    $('.onoffswitch', section).each (index) ->
      id = $(this).attr('id')
      data[id] = OnOff.getValueById(id)
      return

    ### text inputs ###

    $('input[type=text]', section).each (index) ->
      id = $(this).attr('id')
      data[id] = $('#' + id).val()
      return

    ### password inputs ###

    $('input[type=password]', section).each (index) ->
      id = $(this).attr('id')
      data[id] = $('#' + id).val()
      return

    ### dropdowns ###

    $('.btn-group', section).each (index) ->
      id = $(this).attr('id')
      data[id] = Dropdown.getValueById(id)
      return
    data

  ###
  # setSectionData()
  ###

  setSectionData = (section, data) ->

    ### sliders ###

    $('.onoffswitch', section).each (index) ->
      id = $(this).attr('id')
      OnOff.setValueById id, data[id]
      return

    ### text inputs ###

    $('input[type=text]', section).each (index) ->
      id = $(this).attr('id')
      $(this).val data[id]
      return

    ### password inputs ###

    $('input[type=password]', section).each (index) ->
      id = $(this).attr('id')
      $(this).val data[id]
      return

    ### dropdowns ###

    $('.btn-group', section).each (index) ->
      id = $(this).attr('id')
      Dropdown.setValueById id, data[id]
      return
    return

  ###
  # callChangeCallback()
  # If a 'change' callback is attached to a given then section call it.
  ###

  callChangeCallback = (section) ->
    func = $(section).data('change')
    if func != null
      func section
    return

  ###
  # callValidateCallback()
  # If a 'validate' callback is attached to a given then section call it
  # and return the result.  Returns 'true' if no validate callback exists.
  ###

  callValidateCallback = (section) ->
    func = section.data('validate')
    if func != null
      return func(section)
    true

  ###
  # sectionCallback()
  # Change/Validate callback for a given section.
  ###

  sectionCallback = (section) ->
    name = section.attr('id')
    data = getSectionData(section)
    if _.isEqual(data, sectionData[name])
      $('button.save, button.cancel', section).addClass 'disabled'
    else
      if callValidateCallback(section)
        $('button.save', section).removeClass 'disabled'
      else
        $('button.save', section).addClass 'disabled'
      $('button.cancel', section).removeClass 'disabled'
    callChangeCallback section
    return

  ###
  # nodeCallback()
  # Callback for a particular element that validates the containing section.
  ###

  nodeCallback = (node) ->
    section = $(node).closest('section')
    sectionCallback section

  ###
  # widgetCallback()
  # Callback for a widget that validates the containing section.
  ###

  widgetCallback = ->
    nodeCallback @node

  ###
  # autoSave()
  ###

  autoSave = ->
    section = $(this).closest('section')
    name = section.attr('id')
    $('button.save, button.cancel', section).addClass 'disabled'
    data = getSectionData(section)
    $.ajax
      type: 'POST'
      url: '/api/v1/system'
      data: data
      success: ->
        sectionData[name] = data
        return
      error: (jqXHR, textStatus, errorThrown) ->
        alert @url + ': ' + jqXHR.status + ' (' + errorThrown + ')'
        return
    return

  ###
  # autoCancel()
  ###

  autoCancel = ->
    section = $(this).closest('section')
    name = section.attr('id')
    setSectionData section, sectionData[name]
    callChangeCallback section
    return

  ###
  # setAutoInputCallback()
  # Set a callback for whenever input is entered - likely for validation.
  # FIXME: remove when setInputCallback does this...
  ###

  setAutoInputCallback = (callback) ->
    selector = 'section.auto input[type="text"], ' + 'section.auto input[type="password"], ' + 'section.auto textarea'
    $(selector).on 'paste', ->
      setTimeout (->

        ### validate after paste completes by using a timeout. ###

        callback this
        return
      ), 100
      return
    selector = 'section.auto input[type="text"], ' + 'section.auto input[type="password"], ' + 'section.auto textarea'
    $(selector).on 'keyup', ->
      callback this
      return
    return

  ###
  # validate()
  # Enable/disable the buttons based on the field values.
  ###

  validate = ->
    configure.validateSection 'monitors', getMonitorData, maySaveCancelMonitor, maySaveCancelMonitor
    return

  ###
  # setup()
  # Inital setup after the AJAX call returns and the DOM tree is ready.
  ###

  setup = (data) ->
    Dropdown.setupAll data
    OnOff.setup()

    ### Monitoring ###

    setMonitorData data
    $('#save-monitors').bind 'click', saveMonitors
    $('#cancel-monitors').bind 'click', cancelMonitors
    monitorData = getMonitorData()

    ### validation ###

    Dropdown.setCallback validate
    OnOff.setCallback validate
    configure.setInputCallback validate

    ### implicitly calls validate() ###

    ### BEGIN: new auto-validation ###

    $('section.auto').each (index) ->
      name = $(this).attr('id')
      setSectionData this, data
      sectionData[name] = getSectionData(this)
      callChangeCallback this
      return
    $('section.auto button.save').bind 'click', autoSave
    $('section.auto button.cancel').bind 'click', autoCancel

    ### FIXME: overrides ###

    Dropdown.setCallback widgetCallback, 'section.auto .btn-group'
    OnOff.setCallback widgetCallback, 'section.auto .onoffswitch'
    setAutoInputCallback nodeCallback

    ### END: auto-validation ###

    return

  common.startMonitor false

  ### fire. ###

  $.ajax
    url: '/rest/alerts'
    success: (data) ->
      $().ready ->
        setup data
        return
      return
    error: common.ajaxError
  return
