# Control for showing one single line of process level
# alert settings.
# Consists of a process name selector, warning and error settings
# and a delete button.
define 'ProcessSettings', [
    'ComboWithCaption'
    'AlertSetting'
    'ProcessNameCombo'
    'react'
], (ComboWithCaption, AlertSetting, ProcessNameCombo, React) ->
    class ProcessSettings extends React.Component
        onChange: (property, value) =>
            @props.onChange @props.index, property, value

        render: =>
            process_name = React.createElement ComboWithCaption,
                comboClass: ProcessNameCombo
                comboParams:
                    value: @props.details.process_name
                    options: @props.processes
                    onChange: @onChange
                    property: 'process_name'

            warning = React.createElement AlertSetting,
                level: 'warning'
                type: @props.type
                details: @props.details
                onChange: @onChange

            error = React.createElement AlertSetting,
                level: 'error'
                type: @props.type
                details: @props.details
                onChange: @onChange

            deleteButton = React.createElement "span", {className: ""}, React.createElement "a", {className: "fa fa-2x fa-minus-circle", style: {color:"red"}, onClick: @props.remove}

            d = React.createElement "span", {key: @props.details.process_name}, [
                process_name
                warning
                error
                deleteButton
            ]
            React.createElement "p", {key: "row #{@props.details.process_name}"}, d


