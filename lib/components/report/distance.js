import message from 'lib/message'
import React from 'react'

/** conversions from km to target unit */
const conversions = {
  km: 1,
  mi: 1 / 1.609,
  furlong: 4.97096
}

/** render distance in appropriate units */
/** if left with defaults, will return e.g. 16 km (10 mi) */
export default function Distance(p) {
  const {km, units = ['km', 'mi']} = p
  const main = `${Math.round(km * conversions[units[0]] * 10) / 10} ${message(
    `report.units.${units[0]}`
  )}`

  const addl = units
    .slice(1)
    .map(
      (unit) =>
        `${Math.round(km * conversions[unit] * 10) / 10} ${message(
          `report.units.${unit}`
        )}`
    )
    .join(',')

  return (
    <span>
      {main} ({addl})
    </span>
  )
}
