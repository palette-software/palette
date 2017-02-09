# Control for showing process level alert configuration list
# Basically a list of ProcessSettings with an add button
define 'ProcessSettingsList', [
    'ProcessSettings',
    'react'
], (ProcessSettings, React) ->
    class ProcessSettingsList extends React.Component
        constructor: (props) ->
            super props

        remove: (index) =>
            =>
                @props.remove index

        render: =>
            processSettingsList = @props?.items?.map (item, index) =>
                item = React.createElement ProcessSettings,
                    key: "#{item.process_name}"
                    index: index
                    details: item
                    processes: @props.processes
                    onChange: @props.onChange
                    remove: @remove(index)
                    type: @props.type
            processSettingsList.push React.createElement "a", {className: "fa fa-2x fa-plus-circle", style: {color:"green"}, onClick: @props.add}

            React.createElement "div", {}, processSettingsList


