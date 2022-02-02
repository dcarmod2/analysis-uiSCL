import {memo} from 'react'

import message from 'lib/message'

// The x axis labels for the plot
const TIME_LABELS = [15, 30, 45, 60, 75, 90, 105, 120]

interface MinuteTicksProps {
  label?: boolean
  scale: (number) => number
  textHeight: number
}

/**
 * Render the minute axis ticks - shared by stacked percentile curves plot and
 * travel time distribution plot. We don't explicitly center the '15 minutes'
 * text; fudge the left side a bit so that the 15 appears centered.
 */
export default memo<MinuteTicksProps>(function MinuteTicks({
  label = true,
  scale,
  textHeight
}) {
  return (
    <>
      {TIME_LABELS.map((v, i, arr) => (
        <text
          x={i === 0 ? scale(v) - textHeight / 2 : scale(v)}
          y={0}
          key={`x-tick-${v}`}
          style={{
            textAnchor:
              i === arr.length - 1
                ? 'end' // Don't run off end, fudge position of last value.
                : i === 0
                ? 'start' // Don't center the whole '15 minutes' text.
                : 'middle'
          }}
        >
          {/* label first minute */}
          {label && i === 0 ? message('analysis.minutes', {minutes: v}) : v}
        </text>
      ))}
    </>
  )
})
