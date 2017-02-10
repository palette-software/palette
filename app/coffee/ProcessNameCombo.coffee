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


