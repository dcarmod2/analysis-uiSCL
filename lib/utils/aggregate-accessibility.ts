import get from 'lodash/get'
import range from 'lodash/range'

const N_HISTOGRAM_BINS = 15

/**
 * Compute the accessibility, exported for use in comparison weighted average
 * accessibility.
 * @param weights a grid containing the weights (e.g. population)
 * @param aggregationArea a grid containing the aggregation area, with the
 *        percentage the aggregation area overlaps each cell, scaled between 0
 *        (no overlap) and 100,000 (full coverage)
 * @param accessibility a grid containing the accessibility (i.e. the regional
 *        analysis results)
 */
export default function getAggregateAccessibility(
  accessibility,
  aggregationArea,
  weights
) {
  const aa = get(aggregationArea, 'grid')
  if (weights == null || aa == null || accessibility == null) {
    return
  }

  if (accessibility.zoom !== weights.zoom || accessibility.zoom !== aa.zoom) {
    console.error('Zoom levels of all grids in weighted average must match!')
  }

  // find max and min value for histogram
  let maxAccessibility = 0
  let minAccessibility = Infinity

  // Pass one: find min and max from aggregationArea
  // aggregationArea is probably the smallest grid and is guaranteed to contain
  // all pixels
  for (let y = 0, pixel = 0; y < aa.height; y++) {
    // Transform to coordinates in other grid; all grids have same zoom, so
    // translate based on the difference in where the edges of the grid are
    const accessY = y + aa.north - accessibility.north
    for (let x = 0; x < aa.width; x++, pixel++) {
      if (aa.data[pixel] > 0) {
        const accessX = x + aa.west - accessibility.west
        const accessibilityThisCell = accessibility.contains(accessX, accessY)
          ? accessibility.data[accessY * accessibility.width + accessX]
          : 0

        minAccessibility = Math.min(accessibilityThisCell, minAccessibility)
        maxAccessibility = Math.max(accessibilityThisCell, maxAccessibility)
      }
    }
  }

  const spread = maxAccessibility - minAccessibility
  const bins = range(N_HISTOGRAM_BINS).map(() => 0)

  let sumOfWeights = 0
  // weight and accessibility value for each cell, used to compute percentiles
  const weightedAccessibility = []

  // pass two: accumulate into bins
  for (let y = 0, pixel = 0; y < aa.height; y++) {
    const accessY = y + aa.north - accessibility.north
    const weightY = y + aa.north - weights.north
    for (let x = 0; x < aa.width; x++, pixel++) {
      if (aa.data[pixel] > 0) {
        const accessX = x + aa.west - accessibility.west
        const accessibilityThisCell = accessibility.contains(accessX, accessY)
          ? accessibility.data[accessY * accessibility.width + accessX]
          : 0

        let binIndex = Math.floor(
          ((accessibilityThisCell - minAccessibility) / spread) *
            N_HISTOGRAM_BINS
        )

        if (binIndex > N_HISTOGRAM_BINS) console.error('invalid bin!')

        // avoid putting the highest accessibility cell beyond the histogram
        if (binIndex === N_HISTOGRAM_BINS) binIndex--

        // how much of this cell is within the aggregationArea
        const aggregationAreaWeightThisCell = aa.data[pixel] / 100000

        const weightX = x + aa.west - weights.west
        const weightThisCell = weights.contains(weightX, weightY)
          ? weights.data[weightY * weights.width + weightX]
          : 0

        const weight = aggregationAreaWeightThisCell * weightThisCell
        bins[binIndex] += aggregationAreaWeightThisCell * weightThisCell

        sumOfWeights += weight
        weightedAccessibility.push({
          weight,
          accessibility: accessibilityThisCell
        })
      }
    }
  }

  // Figure out percentiles
  let cumulativeWeight = 0
  // Preinitialize with null so 50th percentile is percentiles[50].
  // There is no zeroth percentile
  const percentiles = [0]
  const weightPerPercentile = sumOfWeights / 100
  let expectedWeight = weightPerPercentile
  weightedAccessibility.sort((a, b) => a.accessibility - b.accessibility)

  // we calculate and return an old-style weighted average for comparison purposes.
  let sumOfWeightedAccessibility = 0

  // We loop over the sorted weighted accessibility values. When we cross a
  // percentile boundary, we push that percentile onto the list
  weightedAccessibility.forEach(({accessibility, weight}) => {
    sumOfWeightedAccessibility += accessibility * weight

    cumulativeWeight += weight

    // while not if, possible to cross many percentiles with one high-density cell
    while (cumulativeWeight > expectedWeight) {
      // There is a percentile value somewhere within the values at this sample
      // We use > above, not >=, so that a percentile value that falls exactly
      // between two accessibility values will get the higher value, e.g. if 10
      // people have accessibility 50 and ten people have accessibility 60, we
      // want 60. This is because in the UI we say "x% of <people> have
      // accessibility y or higher," so we want y to be as high as possible
      // while still being a true statement.
      percentiles.push(accessibility)
      expectedWeight += weightPerPercentile
    }
  })

  // includes values 1 - 99
  // When the resolution of the data is low the last item may only define (say)
  // the 90th percentile, all remaining percentiles are just the max. Also
  // handles the case when there is no accessibility within the aggregation
  // area by returning all zeros.
  while (percentiles.length < 99) {
    percentiles.push(
      weightedAccessibility.length > 0
        ? weightedAccessibility[weightedAccessibility.length - 1].accessibility
        : 0
    )
  }

  const binWidth = spread / N_HISTOGRAM_BINS

  return {
    minAccessibility,
    maxAccessibility,
    percentiles,
    weightedAverage: sumOfWeightedAccessibility / sumOfWeights,
    bins: bins.map((value, idx) => ({
      value,
      min: minAccessibility + idx * binWidth,
      max: minAccessibility + (idx + 1) * binWidth
    }))
  }
}
