define 'AlertSetting', [
    'ComboWithCaption'
    'PercentageCombo'
    'PeriodCombo'
    'react'
], (ComboWithCaption, PercentageCombo, PeriodCombo, React) ->
    class AlertSetting extends React.Component
        render: =>
            threshold_property = 'threshold_' + @props.level
            capitalLevel = @props.level.charAt(0).toUpperCase() + @props.level.substr(1)
            percentage = React.createElement ComboWithCaption,
                comboClass: PercentageCombo
                caption: ' ' + capitalLevel + ' Alert at '
                comboParams:
                    value: @props.details[threshold_property]
                    onChange: @props.onChange
                    property: threshold_property

            period_property = 'period_' + @props.level
            duration = React.createElement ComboWithCaption,
                comboClass: PeriodCombo
                caption: ' for '
                comboParams:
                    value: @props.details[period_property]
                    onChange: @props.onChange
                    property: period_property
            React.createElement 'span', null, [percentage, duration]


