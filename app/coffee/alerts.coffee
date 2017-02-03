define 'ComboButton', [
    'react'
], (React) ->
    class ComboButton extends React.Component
        constructor: (props) ->
            super props
            @state =
                metric: ""
                value: props.value
                options: []

        render: =>
            value = React.createElement "div", {"data-id": "#{@state?.value}"}, @state.value + @state.metric
            caret = React.createElement "span", {className: "caret"}
            button = React.createElement "button", {type: "button", className: "btn btn-default dropdown-toggle", "data-toggle": "dropdown"}, [value, caret]
            optionItems = @state.options.map (value) =>
                metric = @state.metric
                if value is 101
                    value = "Do Not Monitor"
                    metric = ""
                a  = React.createElement "a", {"data-id": "#{value}"}, value + metric
                options = React.createElement "li", {key: "#{value}"}, a
            dropdownMenu = React.createElement "ul", {className: "dropdown-menu", role: "menu"}, optionItems
            React.createElement "span", {className: "btn-group percentage"}, [button, dropdownMenu]

define 'PercentageCombo', [
    'ComboButton'
], (ComboButton) ->
    class PercentageCombo extends ComboButton
        constructor: (props) ->
            super props
            @state.metric = "%"
            @state.options = [101, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]

define 'PeriodCombo', [
    'ComboButton'
], (ComboButton) ->
    class PeriodCombo extends ComboButton
        constructor: (props) ->
            super props
            if @state.value is "1"
                @state.metric = " minute"
            else
                @state.metric = " minutes"
            @state.options = [101, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30]

define 'ProcessNameCombo', [
    'ComboButton'
], (ComboButton) ->
    class ProcessNameCombo extends ComboButton
        constructor: (props) ->
            super props
            @state.options = ["tabprotosrv", "vizqlserver"]


define 'ProcessSettings', [
    'PercentageCombo'
    "PeriodCombo"
    "ProcessNameCombo"
    'react'
], (PercentageCombo, PeriodCombo, ProcessNameCombo, React) ->
    class ProcessSettings extends React.Component
        constructor: (props) ->
            super props
            console.log @props
            @state = 
                details: @props.details

        render: =>
            process_name = React.createElement ProcessNameCombo, {value: @state.details.process_name}
            warningCaption = React.createElement "span", null, " Warning Alert at "
            warningPercentage = React.createElement PercentageCombo, {value: @state.details.threshold_warning}
            forCaption = React.createElement "span", null, " for "
            warningPeriod = React.createElement PeriodCombo, {value: "#{@state.details.period_warning}"}
            errorCaption = React.createElement "span", null, " Error Alert at "
            errorPercentage = React.createElement PercentageCombo, {value: @state.details.threshold_error}
            errorPeriod = React.createElement PeriodCombo, {value: "#{@state.details.period_error}"}
            deleteButton = React.createElement "span", {className: "btn-group"}, React.createElement "a", {className: "fa fa-2x fa-minus-circle", style: {color:"red"}}
            
            d = React.createElement "span", {key: @state.details.process_name}, [
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
            React.createElement "p", {key: "row #{@state.details.process_name}"}, d


define 'ItemList', [
    'ProcessSettings',
    'react'
], (ProcessSettings, React) ->
    class ItemList extends React.Component
        constructor: (props) ->
            super props
            @state =
                items: props.items

        render: =>
            itemlist = @state?.items?.map (item) ->
                item = React.createElement ProcessSettings, {key: "#{item.process_name}", details: item, processName: "#{item.process_name}"}
            itemlist.push React.createElement "a", {className: "fa fa-2x fa-plus-circle", style: {color:"green"}}

            React.createElement "div", {}, itemlist

require [
    'jquery'
    'ItemList'
    'react'
    'react-dom'
], ($, ItemList, React, ReactDOM) ->
    $.ajax
        type: 'GET'
        url: '/rest/alerts/processes'
        dataType: 'json'
        async: false
        success: (data) ->
            console.log data
            ReactDOM.render(
                React.createElement(ItemList, { items: data.config }, "Hello, world!"),
                document.getElementById 'root'
            )
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
