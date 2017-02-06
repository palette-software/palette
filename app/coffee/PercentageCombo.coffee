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


