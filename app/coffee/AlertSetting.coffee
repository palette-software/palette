CPU_TYPE = "cpu"
MEMORY_TYPE = "memory"

define 'AlertSetting', [
    'ComboWithCaption'
    'PercentageCombo'
    'PeriodCombo'
    'MemoryCombo'
    'react'
], (ComboWithCaption, PercentageCombo, PeriodCombo, MemoryCombo, React) ->
    class AlertSetting extends React.Component
        render: =>
            threshold_property = 'threshold_' + @props.level
            capitalLevel = @props.level.charAt(0).toUpperCase() + @props.level.substr(1)
            comboType = if @props.type is CPU_TYPE then PercentageCombo else MemoryCombo
            value = React.createElement ComboWithCaption,
                comboClass: comboType
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
            React.createElement 'span', null, [value, duration]


