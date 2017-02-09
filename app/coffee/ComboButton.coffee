define 'ComboButton', [
    'react'
], (React) ->
    class ComboButton extends React.Component
        constructor: (props) ->
            super props

        optionEnabled: (value) ->
            false

        valueWithMetric: (value) =>
           if @optionEnabled value
               value + @metric value
           else
               "Do Not Monitor"

        metric: ->
            return ''

        clicked: (value) =>
            @props.onChange @props.property, value

        render: =>
            value = React.createElement "div", {key: @props.value, "data-id": "#{@props?.value}", ref: "dropdownValue" }, @valueWithMetric @props.value
            caret = React.createElement "span", {className: "caret"}
            button = React.createElement "button", {type: "button", ref: "dropdown", className: "btn btn-default dropdown-toggle", "data-toggle": "dropdown"}, [value, caret]
            optionItems = @options?.map (value) =>
                a  = React.createElement "a", {"data-id": "#{value}", onClick: () => @clicked(value)}, @valueWithMetric value
                options = React.createElement "li", {key: "#{value}"}, a
            dropdownMenu = React.createElement "ul", {className: "dropdown-menu", role: "menu"}, optionItems
            React.createElement "span", {className: "btn-group percentage"}, [button, dropdownMenu]


