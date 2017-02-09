define 'PeriodCombo', [
    'ComboButton'
], (ComboButton) ->
    class PeriodCombo extends ComboButton
        ALERTING_DISABLED_VALUE = 0
        constructor: (props) ->
            super props
            @options = [ALERTING_DISABLED_VALUE, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30]

        metric: (value) ->
            if value is 1
                " minute"
            else
                " minutes"

        optionEnabled: (value) ->
            value isnt ALERTING_DISABLED_VALUE


