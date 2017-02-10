define 'ComboWithCaption', [
    'react'
], (React) ->
    class ComboWithCaption extends React.Component
        render: =>
            combo = React.createElement @props.comboClass, @props.comboParams
            children = []
            if @props.caption?
                children.push React.createElement 'span', null, @props.caption
            children.push combo
            React.createElement 'span', null, children



