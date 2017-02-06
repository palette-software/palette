ALERTING_DISABLED_VALUE = 101

isThresholdEnabled = (value) ->
    value < ALERTING_DISABLED_VALUE

define 'ComboButton', [
    'react'
], (React) ->
    class ComboButton extends React.Component
        constructor: (props) ->
            super props

        optionEnabled: (value) ->
            false

        metric: ->
            return ''

        clicked: (value) =>
            # @setState
            #  value: value
            console.log "clicked", @props.property, value
            @props.onChange @props.property, value

        render: =>
            value = React.createElement "div", {key: @props.value, "data-id": "#{@props?.value}", ref: "dropdownValue" }, @props.value + @metric()
            caret = React.createElement "span", {className: "caret"}
            button = React.createElement "button", {type: "button", ref: "dropdown", className: "btn btn-default dropdown-toggle", "data-toggle": "dropdown"}, [value, caret]
            optionItems = @options?.map (value) =>
                metric = @metric()
                unless @optionEnabled value
                    value = "Do Not Monitor"
                    metric = ""
                a  = React.createElement "a", {"data-id": "#{value}", onClick: () => @clicked(value)}, value + metric
                options = React.createElement "li", {key: "#{value}"}, a
            dropdownMenu = React.createElement "ul", {className: "dropdown-menu", role: "menu"}, optionItems
            React.createElement "span", {className: "btn-group percentage"}, [button, dropdownMenu]

define 'PercentageCombo', [
    'ComboButton'
], (ComboButton) ->
    class PercentageCombo extends ComboButton
        constructor: (props) ->
            super props
            @options = [ALERTING_DISABLED_VALUE, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]

        metric: ->
            "%"

        optionEnabled: (value) ->
            value isnt  ALERTING_DISABLED_VALUE

define 'PeriodCombo', [
    'ComboButton'
], (ComboButton) ->
    class PeriodCombo extends ComboButton
        constructor: (props) ->
            super props
            @options = [ALERTING_DISABLED_VALUE, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30]

        metric: ->
            if @props.value is "1"
                @props.metric = " minute"
            else
                @props.metric = " minutes"

        optionEnabled: (value) ->
            value isnt ALERTING_DISABLED_VALUE

define 'ProcessNameCombo', [
    'ComboButton'
], (ComboButton) ->
    class ProcessNameCombo extends ComboButton
        constructor: (props) ->
            super props
            @options = props.options
            @props.metric = ''

        optionEnabled: (value) ->
            true

        render: =>
            super()


define 'ProcessSettings', [
    'PercentageCombo'
    "PeriodCombo"
    "ProcessNameCombo"
    'react'
], (PercentageCombo, PeriodCombo, ProcessNameCombo, React) ->
    class ProcessSettings extends React.Component
        constructor: (props) ->
            super props

        onChange: (property, value) =>
            @props.onChange @props.index, property, value

        render: =>
            process_name = React.createElement ProcessNameCombo, {value: @props.details.process_name, options: @props.processes, onChange: @onChange, property: 'process_name'}
            warningCaption = React.createElement "span", null, " Warning Alert at "
            warningPercentage = React.createElement PercentageCombo, {value: @props.details.threshold_warning, onChange: @onChange, property: 'threshold_warning'}
            forCaption = React.createElement "span", null, " for "
            warningPeriod = React.createElement PeriodCombo, {value: "#{@props.details.period_warning}", onChange: @onChange, property: 'period_warning'}
            errorCaption = React.createElement "span", null, " Error Alert at "
            errorPercentage = React.createElement PercentageCombo, {value: @props.details.threshold_error, onChange: @onChange, property: 'threshold_error'}
            errorPeriod = React.createElement PeriodCombo, {value: "#{@props.details.period_error}", onChange: @onChange, property: 'period_error'}
            deleteButton = React.createElement "span", {className: "btn-group"}, React.createElement "a", {className: "fa fa-2x fa-minus-circle", style: {color:"red"}}
            
            d = React.createElement "span", {key: @props.details.process_name}, [
                process_name
                warningCaption
                warningPercentage
                forCaption
                warningPeriod
                errorCaption
                errorPercentage
                forCaption
                errorPeriod
                deleteButton
            ]
            React.createElement "p", {key: "row #{@props.details.process_name}"}, d


define 'ProcessSettingsList', [
    'ProcessSettings',
    'react'
], (ProcessSettings, React) ->
    class ProcessSettingsList extends React.Component
        constructor: (props) ->
            super props

        render: =>
            processSettingsList = @props?.items?.map (item, index) =>
                item = React.createElement ProcessSettings, {key: "#{item.process_name}", index: index, details: item, processes: @props.processes, onChange: @props.onChange}
            processSettingsList.push React.createElement "a", {className: "fa fa-2x fa-plus-circle", style: {color:"green"}}

            React.createElement "div", {}, processSettingsList

define 'SaveCancel', [
    'react'
], (React) ->
    class SaveCancel extends React.Component
        enable: =>
            @refs.cancel.className = "cancel"
            @refs.save.className = "save"

        disable: =>
            @refs.cancel.className = "cancel disabled"
            @refs.save.className = "save disabled"

        cancel: =>
            @props.notifyCancel()
            @disable()

        save: =>
            @disable()

        render: =>
            cancel = React.createElement 'button', {ref: "cancel", type: 'button', id: 'cancel-processlist', className: 'cancel disabled', onClick: @cancel}, 'Cancel'
            save = React.createElement 'button', {ref: "save", type: 'button', id: 'save-processlist', className: 'save disabled', onClick: @save}, 'Save'
            React.createElement 'div', {className: 'save-cancel'}, [cancel, save]

require [
    'jquery'
    'ProcessSettingsList'
    'SaveCancel'
    'react'
    'react-dom'
], ($, ProcessSettingsList, SaveCancel, React, ReactDOM) ->
    class ProcessSection extends React.Component
        constructor: (props) ->
            super props
            @originalsJSON = JSON.parse(JSON.stringify(props.settings))
            @state =
                settings: @props.settings
                options: @props.options

        onChange: (index, property, value) =>
            current = @state.settings
            current[index][property] = value
            @setState
                settings: current
                options: @props.options
                
            @refs.saveCancel.enable()

        cancel: =>
            @setState
                settings: JSON.parse(JSON.stringify(@originalsJSON))
                options: @props.options

        render: =>
            processList = React.createElement ProcessSettingsList, { ref: "processList", items: @state.settings, processes: @state.options, onChange: @onChange}
            saveCancel = React.createElement SaveCancel, { ref: "saveCancel" , notifyCancel: @cancel }
            React.createElement 'div', null, [processList, saveCancel]
    $.ajax
        type: 'GET'
        url: '/rest/alerts/processes'
        dataType: 'json'
        async: false
        success: (data) ->
            filteredList = data.config.filter (item) ->
                isThresholdEnabled(item.threshold_warning) or isThresholdEnabled(item.threshold_error)

            availableProcesses = data.config.map (item) ->
                item.process_name

            processSection = React.createElement ProcessSection, { settings: filteredList, options: availableProcesses }

            ReactDOM.render processSection, document.getElementById('root')
        error: (jqXHR, textStatus, errorThrown) ->
            alert @url + ': ' + jqXHR.status + ' (' + errorThrown + ')'
            return



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
    # and return the result.    Returns 'true' if no validate callback exists.
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
